#!/usr/bin/env python3
"""
Comprehensive scan for new files:
- Stories in input/
- Images in images/
- Audio files in output/
Updates 0_input_all_stories.txt and dashboard
"""

import logging
from pathlib import Path
from input_file_manager import InputFileManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def scan_and_update():
    """Scan all folders and update input file with new findings."""

    manager = InputFileManager()
    rows = manager.read_rows()

    input_dir = Path("input")
    images_dir = Path("images")
    output_dir = Path("output")

    # Count all files
    story_files = {f.stem: f for f in input_dir.glob("*.txt")
                   if f.name != "0_input_all_stories.txt"}
    image_files = {f.stem: f for f in images_dir.glob("*.*")
                   if f.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif']}
    audio_files = {f.stem: f for f in output_dir.glob("*.mp3")}

    # Get max story number (highest numbered story)
    max_story_num = 0
    for stem in story_files.keys():
        try:
            num = int(stem.split("_")[0])
            max_story_num = max(max_story_num, num)
        except (ValueError, IndexError):
            pass

    logger.info(f"[*] Found stories 1-{max_story_num}")
    logger.info(f"[*] Found {len(image_files)} image files")
    logger.info(f"[*] Found {len(audio_files)} audio files")

    updated_count = 0

    # Update rows with file status
    for row in rows:
        numbering = row['numbering']
        story_name = row['story_name']

        # Check for story text file
        found_story = False
        for file_stem, file_path in story_files.items():
            parts = file_stem.split("_", 1)
            if parts and parts[0] == numbering:
                found_story = True
                break

        if found_story:
            if row['status_story'] != 'X':
                row['status_story'] = 'X'
                updated_count += 1
                logger.info(f"[+] Story #{numbering}: Found text file → status_story=X")
        else:
            if row['status_story'] == 'X':
                # File no longer exists, revert status
                row['status_story'] = 'O'
                updated_count += 1
                logger.info(f"[-] Story #{numbering}: Text file missing → status_story=O")

        # Check for image file
        if row['status_picture'] != 'X':
            for file_stem, file_path in image_files.items():
                if file_stem == numbering or file_stem.startswith(f"{numbering}_"):
                    row['status_picture'] = 'X'
                    updated_count += 1
                    logger.info(f"[+] Story #{numbering}: Found image file")
                    break

        # Check for audio file
        if row['status_audio'] != 'X':
            for file_stem, file_path in audio_files.items():
                if file_stem == f"{numbering}_{story_name}":
                    row['status_audio'] = 'X'
                    # Extract duration from file if possible
                    try:
                        from mutagen.mp3 import MP3
                        audio = MP3(file_path)
                        duration = int(audio.info.length)
                        row['seconds'] = str(duration)
                        logger.info(f"[+] Story #{numbering}: Found audio file ({duration}s)")
                    except ImportError:
                        # mutagen not installed, skip duration extraction
                        logger.info(f"[+] Story #{numbering}: Found audio file")
                    except Exception as e:
                        # Other error reading audio
                        logger.info(f"[+] Story #{numbering}: Found audio file")
                    updated_count += 1
                    break

    # Save updated rows
    if updated_count > 0:
        manager.save_rows(rows, f"Comprehensive scan: updated {updated_count} files")
        logger.info(f"[+] Updated input file: {updated_count} changes")
        logger.info("[+] Dashboard automatically updated")
        return {
            "success": True,
            "updated": updated_count,
            "stories": max_story_num,
            "images": len(image_files),
            "audio": len(audio_files)
        }
    else:
        logger.info("[-] No new files detected")
        return {
            "success": True,
            "updated": 0,
            "stories": max_story_num,
            "images": len(image_files),
            "audio": len(audio_files)
        }


if __name__ == "__main__":
    result = scan_and_update()
    print(f"Scan complete: {result}")
