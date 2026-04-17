#!/usr/bin/env python3
"""
Audio generation for all stories:
- Generate MP3 files from story text
- Update 0_input_all_stories.txt with status_audio and seconds
- Only generate for stories with status_story_json=X and status_audio=O
"""

import logging
import sys
import os
from pathlib import Path
from dotenv import load_dotenv
from input_file_manager import InputFileManager

# Load .env file
load_dotenv()

# Add parent directory to path to import sibling modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from project_2_tts_voice_generator.src.elevenlabs_client import ElevenLabsClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def generate_audio_files():
    """Generate audio files for all stories with JSON but no audio."""

    manager = InputFileManager()
    rows = manager.read_rows()

    input_dir = Path("input")
    output_dir = Path("output")
    output_dir.mkdir(parents=True, exist_ok=True)

    generated_count = 0
    skipped_count = 0
    error_count = 0

    # Initialize TTS generator
    try:
        tts = ElevenLabsClient()
        logger.info("[+] ElevenLabs TTS initialized")
    except Exception as e:
        logger.error(f"[-] Failed to initialize TTS: {e}")
        return {
            "success": False,
            "generated": 0,
            "skipped": 0,
            "error": error_count,
            "message": f"TTS initialization failed: {e}"
        }

    # Process each story
    for row in rows:
        numbering = row['numbering']
        story_name = row['story_name']
        status_story_json = row.get('status_story_json', 'O')
        status_audio = row.get('status_audio', 'O')

        # Only process if JSON exists and audio not yet generated
        if status_story_json != 'X':
            continue

        if status_audio == 'X':
            logger.info(f"[*] Story #{numbering}: Audio already exists (skipping)")
            skipped_count += 1
            continue

        # Find story file (by numbering, handles apostrophes/underscores)
        story_files = list(input_dir.glob(f"{numbering}_*.txt"))
        if not story_files:
            logger.warning(f"[-] Story #{numbering}: Story file not found")
            error_count += 1
            continue

        story_file = story_files[0]

        try:
            # Read story text
            with open(story_file, 'r', encoding='utf-8') as f:
                text = f.read().strip()

            # Generate audio file
            audio_file = output_dir / f"{numbering}_{story_name}.mp3"
            logger.info(f"[+] Story #{numbering}: Generating audio...")

            try:
                # Generate audio bytes using ElevenLabs (Tomasz - Expressive & Deep)
                audio_bytes = tts.generate_audio(text, voice_preset="tomasz_z")

                # Write to file
                with open(audio_file, 'wb') as f:
                    f.write(audio_bytes)

                if not audio_file.exists():
                    logger.error(f"[-] Story #{numbering}: Audio file not created")
                    error_count += 1
                    continue
            except Exception as e:
                logger.error(f"[-] Story #{numbering}: Audio generation failed: {e}")
                error_count += 1
                continue

            # Get audio duration using ffprobe
            duration_extracted = False
            try:
                import subprocess
                import time
                # Small delay to ensure file is fully written
                time.sleep(0.5)

                # Use ffprobe to get duration
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
                    logger.info(f"[+] Story #{numbering}: Audio created ({duration}s)")
                    duration_extracted = True
                else:
                    logger.warning(f"[!] Story #{numbering}: ffprobe could not read duration")
            except FileNotFoundError:
                logger.warning(f"[!] Story #{numbering}: ffprobe not found (ffmpeg not installed?)")
            except Exception as e:
                logger.warning(f"[!] Story #{numbering}: Could not read duration: {e}")

            # If duration not extracted, log warning but still save
            if not duration_extracted:
                logger.warning(f"[!] Story #{numbering}: Duration NOT filled in seconds column")

            row['status_audio'] = 'X'
            generated_count += 1

            # IMPORTANT: Save after each story to update dashboard immediately
            manager.save_rows(rows, f"Audio generated for story #{numbering}")

        except Exception as e:
            logger.error(f"[-] Story #{numbering}: Error generating audio: {e}")
            error_count += 1
            continue

    # Final save with summary
    logger.info(f"[+] Audio generation final save")

    logger.info(f"[+] Audio generation complete:")
    logger.info(f"    Generated: {generated_count} files")
    logger.info(f"    Skipped: {skipped_count} files")
    logger.info(f"    Errors: {error_count} files")

    return {
        "success": True,
        "generated": generated_count,
        "skipped": skipped_count,
        "error": error_count
    }


if __name__ == "__main__":
    result = generate_audio_files()
    print(f"Result: {result}")
