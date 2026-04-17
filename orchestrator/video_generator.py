#!/usr/bin/env python3
"""
Video generation for all stories:
- Create MP4 videos from audio + image
- Update 0_input_all_stories.txt with status_video=X
- Only generate for stories with status_audio=X and status_video=O
"""

import logging
import sys
from pathlib import Path
from input_file_manager import InputFileManager

# Load .env file
from dotenv import load_dotenv
load_dotenv()

# Add parent directory to path to import sibling modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from project_3_video_creator.src.video_generator import VideoGenerator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def generate_videos():
    """Generate video files for all stories with audio but no video."""

    manager = InputFileManager()
    rows = manager.read_rows()

    images_dir = Path("images")
    output_dir = Path("output")
    output_dir.mkdir(parents=True, exist_ok=True)

    generated_count = 0
    skipped_count = 0
    error_count = 0

    # Initialize video generator
    try:
        video_gen = VideoGenerator()
        logger.info("[+] Video Generator initialized")
    except Exception as e:
        logger.error(f"[-] Failed to initialize video generator: {e}")
        return {
            "success": False,
            "generated": 0,
            "skipped": 0,
            "error": error_count,
            "message": f"Video generator initialization failed: {e}"
        }

    # Process each story
    for row in rows:
        numbering = row['numbering']
        story_name = row['story_name']
        status_audio = row.get('status_audio', 'O')
        status_video = row.get('status_video', 'O')

        # Only process if audio exists and video not yet generated
        if status_audio != 'X':
            continue

        if status_video == 'X':
            logger.info(f"[*] Story #{numbering}: Video already exists (skipping)")
            skipped_count += 1
            continue

        # Find audio file
        audio_files = list(output_dir.glob(f"{numbering}_*.mp3"))
        if not audio_files:
            logger.warning(f"[-] Story #{numbering}: Audio file not found")
            error_count += 1
            continue

        audio_file = audio_files[0]

        # Find image file (by numbering, handles various names)
        image_files = list(images_dir.glob(f"{numbering}*"))
        if not image_files:
            logger.warning(f"[-] Story #{numbering}: Image file not found")
            error_count += 1
            continue

        image_file = image_files[0]

        try:
            # Create video file
            video_file = output_dir / f"{numbering}_{story_name}_video.mp4"
            logger.info(f"[+] Story #{numbering}: Generating video...")

            # Generate video
            result = video_gen.create_video(
                image_path=str(image_file),
                audio_path=str(audio_file),
                output_path=str(video_file),
                resize=True,
                target_size=(1080, 1920)  # Instagram Reels format
            )

            if not video_file.exists():
                logger.error(f"[-] Story #{numbering}: Video file not created")
                error_count += 1
                continue

            row['status_video'] = 'X'
            generated_count += 1

            # IMPORTANT: Save after each story to update dashboard immediately
            manager.save_rows(rows, f"Video generated for story #{numbering}")
            logger.info(f"[+] Story #{numbering}: Video created")

        except Exception as e:
            logger.error(f"[-] Story #{numbering}: Error generating video: {e}")
            error_count += 1
            continue

    # Final save with summary
    logger.info(f"[+] Video generation final save")

    logger.info(f"[+] Video generation complete:")
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
    result = generate_videos()
    print(f"Result: {result}")
