#!/usr/bin/env python3
"""
Scan for existing audio files and update 0_input_all_stories.txt
This prevents re-generating audio for stories that already have MP3 files.
"""

import logging
from pathlib import Path
from input_file_manager import InputFileManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def scan_and_update_audio():
    """Scan output folder for audio files and extract duration for stories with status_audio=X but seconds=0."""

    manager = InputFileManager()
    rows = manager.read_rows()

    output_dir = Path("output")
    updated_count = 0

    # Find all audio files
    audio_files = {f.stem: f for f in output_dir.glob("*.mp3")}

    logger.info(f"[*] Found {len(audio_files)} audio files in output/")

    # Update rows with duration extraction
    for row in rows:
        numbering = row['numbering']
        story_name = row['story_name']
        status_audio = row.get('status_audio', 'O')
        seconds = row.get('seconds', '0')

        # Only process if: status_audio=X AND seconds=0 (or empty)
        if status_audio != 'X':
            continue

        if seconds and seconds != '0' and seconds.strip():
            # Already has duration, skip
            continue

        # Check if audio file exists (by numbering, handles apostrophes/underscores)
        audio_file = None
        for audio_stem in audio_files.keys():
            # Match by numbering prefix (e.g., "25_" matches any "25_*.mp3")
            if audio_stem.startswith(f"{numbering}_"):
                audio_file = audio_files[audio_stem]
                break

        if not audio_file:
            logger.warning(f"[-] Story #{numbering}: Has audio=X but MP3 file not found")
            continue

        # Extract duration using ffprobe
        try:
            import subprocess

            ffprobe_path = r"C:\ffmpeg\bin\ffprobe.exe"
            cmd = [
                ffprobe_path,
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1:noprint_wrappers=1",
                str(audio_file)
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

            if result.returncode == 0 and result.stdout.strip():
                duration = int(float(result.stdout.strip()))
                row['seconds'] = str(duration)
                logger.info(f"[+] Story #{numbering}: Extracted duration ({duration}s)")
                updated_count += 1
            else:
                logger.warning(f"[!] Story #{numbering}: ffprobe could not read duration")
        except FileNotFoundError:
            logger.warning(f"[!] Story #{numbering}: ffprobe not found")
        except Exception as e:
            logger.warning(f"[!] Story #{numbering}: Could not read duration: {e}")

    # Save updated rows
    if updated_count > 0:
        manager.save_rows(rows, f"Audio scan: filled seconds for {updated_count} stories")
        logger.info(f"[+] Updated {updated_count} stories with audio duration")
    else:
        logger.info("[-] No stories with missing duration found")

    return {
        "success": True,
        "updated": updated_count,
        "total_audio": len(audio_files)
    }


if __name__ == "__main__":
    result = scan_and_update_audio()
    print(f"Result: {result}")
