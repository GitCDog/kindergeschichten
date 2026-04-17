#!/usr/bin/env python3
"""Generate video files with embedded audio using imageio."""

import os
import sys
import subprocess
from pathlib import Path
import logging
import yaml

sys.path.insert(0, str(Path(__file__).parent.parent))

from input_reader import InputReader


class VideoCreatorWithAudio:
    """Create videos with embedded audio."""

    def __init__(self, config_path: str = "config.yaml", output_dir: str = "output", images_dir: str = "images"):
        """Initialize video creator."""
        self.config = self._load_config(config_path)
        self.logger = self._setup_logging()
        self.output_dir = Path(output_dir)
        self.images_dir = Path(images_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file."""
        try:
            with open(config_path, "r") as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            raise ValueError(f"Config file not found: {config_path}")

    def _setup_logging(self) -> logging.Logger:
        """Setup logging."""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.StreamHandler(),
            ],
        )
        return logging.getLogger(__name__)

    def find_image_for_story(self, story_number: int) -> Path:
        """Find image for a story by number."""
        image_path = self.images_dir / f"{story_number}.png"
        if image_path.exists():
            return image_path

        image_path = self.images_dir / f"{story_number}.jpg"
        if image_path.exists():
            return image_path

        return None

    def validate_image_exists(self, story_number: int) -> bool:
        """Check if image exists for story (required for video creation)."""
        image = self.find_image_for_story(story_number)
        return image is not None

    def create_video_with_audio(self, story_number: int):
        """Create video with embedded audio for a specific story."""
        # Load the story info
        input_reader = InputReader("input/0_input_all_stories.txt")
        stories = input_reader.read_stories()

        story_info = None
        for story in stories:
            if int(story["numbering"]) == story_number:
                story_info = story
                break

        if not story_info:
            self.logger.error(f"Story #{story_number} not found in input file")
            return False

        story_name = story_info["story_name"]
        numbering = story_info["numbering"]

        # Find audio and image files
        audio_file = self.output_dir / f"{numbering}_{story_name}.mp3"
        image_file = self.find_image_for_story(story_number)

        if not audio_file.exists():
            self.logger.error(f"Audio file not found: {audio_file}")
            return False

        if not image_file:
            self.logger.error(f"[X] CANNOT CREATE VIDEO: Image file not found for story #{story_number}")
            self.logger.error(f"    Required: images/{story_number}.jpg or images/{story_number}.png")
            self.logger.error(f"    Videos require images. Add image file and retry.")
            return False

        self.logger.info(f"\n{'=' * 60}")
        self.logger.info(f"Creating Video with Audio for Story #{numbering}: {story_name}")
        self.logger.info(f"{'=' * 60}")
        self.logger.info(f"Image: {image_file}")
        self.logger.info(f"Audio: {audio_file}")

        try:
            # Get video settings from config
            video_config = self.config["video_creation"]
            width = video_config["width"]
            height = video_config["height"]
            fps = video_config["fps"]
            bitrate = video_config["bitrate"]

            output_file = self.output_dir / f"{numbering}_{story_name}_video.mp4"
            temp_video = self.output_dir / f"{numbering}_{story_name}_temp.mp4"

            self.logger.info(f"Creating video ({width}x{height})...")

            # Build ffmpeg command to create video with audio
            # Using image as input, looping it for the duration of the audio
            ffmpeg_path = r"C:\ffmpeg\bin\ffmpeg.exe"
            cmd = [
                ffmpeg_path,
                "-loop", "1",
                "-i", str(image_file),
                "-i", str(audio_file),
                "-c:v", "libx264",
                "-c:a", "aac",
                "-b:v", bitrate,
                "-pix_fmt", "yuv420p",
                "-s", f"{width}x{height}",
                "-r", str(fps),
                "-shortest",
                "-y",
                str(output_file)
            ]

            self.logger.info("Running ffmpeg to create video with audio...")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

            if result.returncode != 0:
                self.logger.error(f"ffmpeg error: {result.stderr}")
                return False

            self.logger.info(f"[+] Video with audio created: {output_file.name}")

            # Mark video as processed in input file
            input_reader = InputReader("input/0_input_all_stories.txt")
            input_reader.update_status(story_name, "X", status_field="status_video")
            self.logger.info(f"[+] Status updated: video marked as processed")

            # Move picture to 1_pic_used folder
            try:
                pic_used_dir = self.images_dir / "1_pic_used"
                pic_used_dir.mkdir(parents=True, exist_ok=True)

                # Move the image file
                import shutil
                destination = pic_used_dir / image_file.name
                shutil.move(str(image_file), str(destination))
                self.logger.info(f"[+] Picture moved to: {pic_used_dir.name}/{image_file.name}")
            except Exception as e:
                self.logger.warning(f"[!] Could not move picture: {e}")

            # Move JSON and audio files to 1_insta_post_X folder (but keep video in output)
            try:
                import shutil
                insta_post_dir = self.output_dir / "1_insta_post_X"
                insta_post_dir.mkdir(parents=True, exist_ok=True)

                # Move JSON file
                json_file = self.output_dir / f"{numbering}_{story_name}.json"
                if json_file.exists():
                    destination = insta_post_dir / json_file.name
                    shutil.move(str(json_file), str(destination))
                    self.logger.info(f"[+] JSON file moved to: 1_insta_post_X/{json_file.name}")

                # Move audio file
                if audio_file.exists():
                    destination = insta_post_dir / audio_file.name
                    shutil.move(str(audio_file), str(destination))
                    self.logger.info(f"[+] Audio file moved to: 1_insta_post_X/{audio_file.name}")

                # Video file STAYS in output folder (not moved)
                self.logger.info(f"[+] Video file kept in: output/{output_file.name}")

            except Exception as e:
                self.logger.warning(f"[!] Could not move files to 1_insta_post_X: {e}")

            return True

        except FileNotFoundError:
            self.logger.error("ffmpeg not found. Please install ffmpeg.")
            self.logger.error("Windows: Download from https://ffmpeg.org/download.html")
            return False
        except Exception as e:
            self.logger.error(f"[-] Failed to create video: {e}", exc_info=True)
            return False

    def create_all_videos_with_audio(self):
        """Create videos by checking input file: status_audio=X, status_picture=X, status_video=O."""

        # First: Scan for new pictures and update status_picture
        self.logger.info("=" * 60)
        self.logger.info("STEP 1: Scanning for picture files...")
        self.logger.info("=" * 60)

        from input_file_manager import InputFileManager
        manager = InputFileManager()

        # Load via InputFileManager (proper CSV handling)
        stories = manager.read_rows()

        if not stories:
            self.logger.info("No stories found in input file")
            return

        # Find all image files
        image_files = list(self.images_dir.glob("*.*"))
        image_extensions = {".jpg", ".jpeg", ".png", ".gif"}
        image_by_number = {}

        for img in image_files:
            if img.suffix.lower() in image_extensions:
                # Extract numbering from filename (e.g., "13.png" → 13, "13_name.png" → 13)
                stem = img.stem
                try:
                    num_str = stem.split("_")[0]
                    story_num = int(num_str)
                    image_by_number[story_num] = img
                    self.logger.info(f"[*] Found image for story #{story_num}: {img.name}")
                except (ValueError, IndexError):
                    pass

        self.logger.info(f"[*] Total images found: {len(image_by_number)}")

        # Update status_picture for stories with images (SAVE IMMEDIATELY FOR EACH)
        for story in stories:
            numbering = story.get("numbering")

            try:
                story_num = int(numbering)
                if story_num in image_by_number:
                    # Picture exists - set status_picture=X and save immediately
                    story["status_picture"] = "X"
                    self.logger.info(f"[+] Story #{numbering}: Picture {story_num} found, setting status_picture=X")
                    # IMPORTANT: Save immediately after each story
                    try:
                        save_result = manager.save_rows(stories, f"Picture found for story #{numbering}")
                        if save_result:
                            self.logger.info(f"[+] Story #{numbering}: Input file and dashboard UPDATED")
                        else:
                            self.logger.error(f"[-] Story #{numbering}: FAILED to save - dashboard NOT updated!")
                    except Exception as e:
                        self.logger.error(f"[-] Story #{numbering}: Save error: {e}")
            except ValueError:
                pass

        self.logger.info(f"[+] Picture scan complete")

        # Second: Create videos
        self.logger.info("=" * 60)
        self.logger.info("STEP 2: Creating videos...")
        self.logger.info("=" * 60)

        created_count = 0
        skipped_count = 0
        error_count = 0

        # Check each story line by line
        for story in stories:
            numbering = story.get("numbering")
            story_name = story.get("story_name")
            status_audio = story.get("status_audio", "O")
            status_picture = story.get("status_picture", "O")
            status_video = story.get("status_video", "O")

            story_number = int(numbering)

            # Check all three conditions
            if status_audio != "X":
                self.logger.info(f"[-] Story #{numbering}: Audio missing (status_audio={status_audio})")
                skipped_count += 1
                continue

            if status_picture != "X":
                self.logger.info(f"[-] Story #{numbering}: Picture missing (status_picture={status_picture})")
                skipped_count += 1
                continue

            if status_video != "O":
                self.logger.info(f"[*] Story #{numbering}: Video already exists (status_video={status_video})")
                skipped_count += 1
                continue

            # All conditions met - create video
            self.logger.info(f"[+] Story #{numbering}: Creating video (audio=X, picture=X, video=O)")
            success = self.create_video_with_audio(story_number)

            if success:
                created_count += 1
            else:
                error_count += 1

        self.logger.info(f"\nVideo creation summary:")
        self.logger.info(f"  Created: {created_count}")
        self.logger.info(f"  Skipped: {skipped_count}")
        self.logger.info(f"  Errors:  {error_count}")

        self.logger.info(f"\n{'=' * 60}")
        self.logger.info("Video creation complete!")
        self.logger.info(f"{'=' * 60}")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate video files with embedded audio")
    parser.add_argument(
        "--story",
        type=int,
        help="Story number (e.g., 1 for story #1)",
    )
    parser.add_argument(
        "--config",
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)",
    )
    parser.add_argument(
        "--output",
        default="./output",
        help="Output directory (default: ./output)",
    )
    parser.add_argument(
        "--images",
        default="./images",
        help="Images directory (default: ./images)",
    )

    args = parser.parse_args()

    try:
        creator = VideoCreatorWithAudio(
            config_path=args.config,
            output_dir=args.output,
            images_dir=args.images
        )

        if args.story:
            success = creator.create_video_with_audio(args.story)
            if not success:
                sys.exit(1)
        else:
            creator.create_all_videos_with_audio()

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
