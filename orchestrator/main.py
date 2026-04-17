#!/usr/bin/env python3
"""
Main orchestrator for kindergeschichten-automation workflow.

This script orchestrates the complete pipeline:
1. Generate story (Project 1)
2. Convert to audio (Project 2)
3. Create video (Project 3)
4. Upload to Instagram (Project 4)
"""

import os
import sys
import json
import logging
import argparse
import random
from datetime import datetime
from pathlib import Path
import yaml

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from project_1_story_generator.src.generators.claude_generator import ClaudeGenerator
from project_2_tts_voice_generator.src.elevenlabs_client import ElevenLabsClient
from project_2_tts_voice_generator.src.audio_processor import AudioProcessor
from project_3_video_creator.src.image_processor import ImageProcessor
from project_3_video_creator.src.video_generator import VideoGenerator
from project_4_instagram_uploader.src.instagram_api import InstagramAPI
from input_reader import InputReader


class WorkflowOrchestrator:
    """Orchestrate the complete children's story workflow."""

    def __init__(self, config_path: str = "config.yaml", input_file: str = "input/0_input_all_stories.txt", use_input_file: bool = True):
        """
        Initialize orchestrator.

        Args:
            config_path: Path to configuration file
            input_file: Path to input file (default: input/0_input_all_stories.txt)
            use_input_file: Whether to use input file (default: True)
        """
        self.config = self._load_config(config_path)
        self.logger = self._setup_logging()
        # Save JSON/MP3/MP4 in output/ folder
        self.output_dir = Path("output")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        # Save story text in input/ folder
        self.input_dir = Path("input")
        self.input_dir.mkdir(parents=True, exist_ok=True)

        # Initialize input reader
        self.use_input_file = use_input_file
        self.input_reader = InputReader(input_file) if use_input_file else None
        self.current_story_info = None

    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file."""
        try:
            with open(config_path, "r") as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            raise ValueError(f"Config file not found: {config_path}")

    def _setup_logging(self) -> logging.Logger:
        """Setup logging."""
        log_file = self.config["output"]["log_file"]
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(stream=sys.stdout),
            ],
        )

        return logging.getLogger(__name__)

    def run(self) -> dict:
        """
        Execute the complete workflow.

        Returns:
            Dictionary with workflow results
        """
        try:
            self.logger.info("=" * 60)
            self.logger.info("Starting Kindergeschichten Automation Workflow")
            self.logger.info("=" * 60)

            results = {}

            # Check for pending story in input.txt
            keywords = None
            story_name = None
            if self.use_input_file:
                self.current_story_info = self.input_reader.get_next_pending_story()
                if not self.current_story_info:
                    self.logger.info("[+] No pending stories in input.txt")
                    return {"status": "no_pending_stories"}
                keywords = self.current_story_info.get("keywords")
                story_name = self.current_story_info.get("story_name")
                self.logger.info(f"\n[0/4] Found pending story: '{story_name}'")
                self.logger.info(f"      Keywords: {', '.join(keywords)}")

            # Step 1: Generate story
            self.logger.info("\n[1/4] Generating story...")
            story = self._generate_story(keywords=keywords)
            # Override title with story_name from input.txt
            if story_name:
                story.title = story_name
            results["story"] = story.to_dict()
            self.logger.info(f"[+] Story generated: {story.title}")
            # Save story text to input/ folder and JSON to output/ folder
            numbering = self.current_story_info.get("numbering") if self.current_story_info else "1"
            if story_name:
                self._save_story_text(story.text, numbering, story_name)
                json_filename = f"{numbering}_{story_name}.json"
            else:
                json_filename = "story.json"
            self._save_json(json_filename, story.to_dict())

            # Display story for review
            self.logger.info("\n" + "=" * 60)
            self.logger.info("STORY PREVIEW")
            self.logger.info("=" * 60)
            self.logger.info(f"Title: {story.title}")
            self.logger.info(f"Keywords: {', '.join(keywords) if keywords else 'N/A'}")
            self.logger.info(f"Duration: ~{story.duration_estimate_seconds}s")
            self.logger.info("\nStory Text:")
            self.logger.info("-" * 60)
            self.logger.info(story.text)
            self.logger.info("-" * 60)

            # Ask user for confirmation
            print("\n" + "=" * 60)
            response = input("[+] Continue with audio/video generation? (yes/no): ").strip().lower()
            if response not in ["yes", "y"]:
                self.logger.info("[-] Workflow cancelled by user")
                self.logger.info("Story saved to: story.json")
                return {"status": "cancelled_by_user", "story": story.to_dict()}

            # Step 2: Generate audio
            self.logger.info("\n[2/4] Generating audio...")
            numbering = self.current_story_info.get("numbering") if self.current_story_info else "1"
            audio_path = self._generate_audio(story.text, story_name=story_name, numbering=numbering)
            results["audio_path"] = str(audio_path)
            self.logger.info(f"[+] Audio generated: {audio_path}")

            # Step 3: Create video
            self.logger.info("\n[3/4] Creating video...")
            numbering = self.current_story_info.get("numbering") if self.current_story_info else None
            image_path = self._get_image_by_numbering(numbering) if numbering else self._get_image_for_theme(story.theme, keywords=keywords)
            video_path = self._create_video(image_path, audio_path, story_name=story_name, numbering=numbering)
            results["video_path"] = str(video_path)
            self.logger.info(f"[+] Video created: {video_path}")

            # Step 4: Upload to Instagram
            self.logger.info("\n[4/4] Uploading to Instagram...")
            # Use story_name from input.txt if available, otherwise use generated title
            caption_title = story_name if story_name else story.title
            upload_result = self._upload_to_instagram(video_path, caption_title, keywords=keywords)
            results["instagram"] = upload_result
            self.logger.info(f"[+] Uploaded to Instagram: {upload_result.get('id', 'N/A')}")

            # Mark story as processed in input.txt
            if self.use_input_file and self.current_story_info:
                self.input_reader.update_status(self.current_story_info["story_name"], "processed")
                self.logger.info(f"[+] Story '{self.current_story_info['story_name']}' marked as processed in input.txt")

            self.logger.info("\n" + "=" * 60)
            self.logger.info("[+] Workflow completed successfully!")
            self.logger.info("=" * 60)

            return results

        except Exception as e:
            self.logger.error(f"[-] Workflow failed: {e}", exc_info=True)
            raise

    def _generate_story(self, keywords: list = None) -> object:
        """Generate a children's story using Claude.

        Args:
            keywords: Optional list of keywords to guide story generation

        Returns:
            Story object
        """
        theme = self.config["story_generation"].get("theme")
        duration = self.config["story_generation"]["target_duration_seconds"]

        self.logger.info("  Using Claude API...")
        generator = ClaudeGenerator()
        return generator.generate(theme=theme, keywords=keywords, duration_seconds=duration)

    def _generate_audio(self, text: str, story_name: str = None, numbering: str = None) -> Path:
        """Generate audio from text using TTS.

        Args:
            text: Story text to convert to audio
            story_name: Story name for filename
            numbering: Story numbering for filename

        Returns:
            Path to generated audio file
        """
        try:
            voice_preset = self.config["text_to_speech"]["voice_preset"]
            self.logger.info(f"  Using voice preset: {voice_preset}")

            client = ElevenLabsClient()
            audio_bytes = client.generate_audio(text, voice_preset=voice_preset)

            # Save audio with numbering_story_name format
            if story_name and numbering:
                audio_filename = f"{numbering}_{story_name}.mp3"
            else:
                audio_filename = "story.mp3"
            audio_path = self.output_dir / audio_filename
            AudioProcessor.save_audio(audio_bytes, str(audio_path))

            # Validate audio if configured
            if self.config["text_to_speech"]["validate_audio"]:
                is_valid, details = AudioProcessor.validate_audio_duration(text, audio_bytes)
                if not is_valid:
                    if 'error' in details:
                        self.logger.warning(f"  Audio validation skipped: {details['error']}")
                    else:
                        self.logger.warning(
                            f"  Audio duration validation: "
                            f"expected {details['estimated_duration']:.0f}s, "
                            f"got {details['actual_duration']:.0f}s"
                        )

            return audio_path

        except Exception as e:
            self.logger.error(f"  Audio generation failed: {e}")
            raise

    def _create_video(self, image_path: str, audio_path: str, story_name: str = None, numbering: str = None) -> Path:
        """Create video from image and audio.

        Args:
            image_path: Path to background image
            audio_path: Path to audio file
            story_name: Story name for filename
            numbering: Story numbering for filename

        Returns:
            Path to generated video file
        """
        try:
            # Prepare image
            video_config = self.config["video_creation"]
            target_size = (video_config["width"], video_config["height"])

            processed_image = self.output_dir / "image_processed.jpg"
            ImageProcessor.prepare_image(image_path, str(processed_image), target_size)
            self.logger.info(f"  Image prepared")

            # Generate video with numbering_story_name_video format
            video_generator = VideoGenerator()
            if story_name and numbering:
                video_filename = f"{numbering}_{story_name}_video.mp4"
            else:
                video_filename = "story_video.mp4"
            video_path = self.output_dir / video_filename

            self.logger.info("  Generating video (this may take a few moments)...")
            video_generator.create_video(
                image_path=str(processed_image),
                audio_path=str(audio_path),
                output_path=str(video_path),
            )

            # Delete temporary processed image
            if processed_image.exists():
                processed_image.unlink()
                self.logger.info("  Temporary files cleaned up")

            return video_path

        except Exception as e:
            self.logger.error(f"  Video creation failed: {e}")
            raise

    def _upload_to_instagram(self, video_path: str, story_title: str, keywords: list = None) -> dict:
        """Upload video to Instagram.

        Args:
            video_path: Path to video file
            story_title: Title for the story
            keywords: Optional list of keywords to include

        Returns:
            Upload result dictionary
        """
        try:
            upload_config = self.config["instagram"]

            # Generate caption
            hashtags = " ".join([f"#{tag}" for tag in upload_config["hashtags"]])
            # Add keywords as hashtags if available
            if keywords:
                keyword_hashtags = " ".join([f"#{kw}" for kw in keywords])
                hashtags = keyword_hashtags + " " + hashtags

            caption = upload_config["caption_template"].format(
                title=story_title,
                theme=self.config["story_generation"].get("theme", "adventure"),
                hashtags=hashtags,
            )

            self.logger.info(f"  Caption: {caption[:50]}...")

            # Upload
            api = InstagramAPI()
            result = api.upload_reel(video_path=video_path, caption=caption)

            return result

        except Exception as e:
            self.logger.warning(f"  Instagram upload skipped (test mode): {e}")
            return {"id": "test_mode", "status": "test"}

    def _get_image_by_numbering(self, numbering: str) -> str:
        """Get an image matching the story numbering.

        Args:
            numbering: Story numbering (e.g., "1", "2", "3")

        Returns:
            Path to selected image, or placeholder if not found
        """
        base_image_dir = Path(self.config["video_creation"]["image_directory"])

        if not base_image_dir.exists():
            base_image_dir.mkdir(parents=True, exist_ok=True)

        # Look for images matching the numbering
        # Supports: 1.jpg, 1.png, 1_*.jpg, 1_*.png, etc.
        matching_images = []
        matching_images.extend(base_image_dir.glob(f"{numbering}.jpg"))
        matching_images.extend(base_image_dir.glob(f"{numbering}.png"))
        matching_images.extend(base_image_dir.glob(f"{numbering}_*.jpg"))
        matching_images.extend(base_image_dir.glob(f"{numbering}_*.png"))

        if matching_images:
            selected_image = matching_images[0]
            self.logger.info(f"  Selected image for story #{numbering}: {selected_image.name}")
            return str(selected_image)

        # If not found, log warning and return placeholder
        self.logger.warning(f"  No image found for story #{numbering}")
        self.logger.info(f"  Expected: {base_image_dir}/{numbering}.jpg or {base_image_dir}/{numbering}_*.jpg")
        self.logger.info("  Using default placeholder image...")
        return self._create_placeholder_image()

    def _get_image_for_theme(self, theme: str, keywords: list = None) -> str:
        """Get an image matching the story theme.

        Args:
            theme: Story theme (e.g., 'forest', 'adventure', 'friendship')
            keywords: Optional list of keywords to use as theme fallback

        Returns:
            Path to selected image
        """
        base_image_dir = Path(self.config["video_creation"]["image_directory"])

        # Ensure base directory exists
        base_image_dir.mkdir(parents=True, exist_ok=True)

        # Normalize theme
        theme = theme.lower() if theme else "generic"

        # Try to use first keyword as theme if current theme is generic
        if (theme == "generic" or theme not in ["forest", "adventure", "friendship"]) and keywords:
            first_keyword = keywords[0].lower()
            if first_keyword in ["forest", "adventure", "friendship"]:
                theme = first_keyword

        # Look for theme-specific images first
        theme_dir = base_image_dir / theme
        images = []

        if theme_dir.exists():
            images = list(theme_dir.glob("*.jpg")) + list(theme_dir.glob("*.png"))

        # Fall back to generic images if theme directory is empty or doesn't exist
        if not images:
            if theme != "generic":
                self.logger.info(f"  No images found for theme '{theme}', using generic images...")

            generic_dir = base_image_dir / "generic"
            generic_dir.mkdir(parents=True, exist_ok=True)
            images = list(generic_dir.glob("*.jpg")) + list(generic_dir.glob("*.png"))

        # If still no images, create placeholder
        if not images:
            self.logger.warning(
                f"  No images found in {base_image_dir / theme} or {base_image_dir / 'generic'}"
            )
            self.logger.info("  Add images to orchestrator/images/{forest,adventure,friendship,generic}/")
            self.logger.info("  Using default placeholder image...")
            return self._create_placeholder_image()

        selected_image = random.choice(images)
        self.logger.info(f"  Selected image for theme '{theme}': {selected_image.name}")
        return str(selected_image)

    def _create_placeholder_image(self) -> str:
        """Create a simple placeholder image."""
        from PIL import Image, ImageDraw

        img = Image.new("RGB", (1080, 1920), color=(100, 150, 200))
        draw = ImageDraw.Draw(img)

        # Add text
        text = "Children's Story"
        draw.text((540, 960), text, fill=(255, 255, 255), anchor="mm")

        placeholder_path = self.output_dir / "placeholder.jpg"
        img.save(str(placeholder_path))

        return str(placeholder_path)

    def _save_story_text(self, text: str, numbering: str, story_name: str) -> None:
        """Save raw story text to input folder.

        ONLY saves if file doesn't already exist (never overwrites).

        Args:
            text: Story text
            numbering: Story numbering
            story_name: Story name
        """
        filename = f"{numbering}_{story_name}.txt"
        filepath = self.input_dir / filename
        # Only save if it doesn't already exist (preserve existing stories)
        if not filepath.exists():
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(text)

    def _save_json(self, filename: str, data: dict) -> None:
        """Save data as JSON to output folder."""
        filepath = self.output_dir / filename
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Kindergeschichten Automation Workflow")
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
        "--theme",
        help="Override theme from config",
    )
    parser.add_argument(
        "--input",
        default="input.txt",
        help="Path to input file with story definitions (default: input.txt)",
    )
    parser.add_argument(
        "--no-input",
        action="store_true",
        help="Run without input file (ignore input.txt)",
    )

    args = parser.parse_args()

    try:
        use_input_file = not args.no_input
        orchestrator = WorkflowOrchestrator(
            config_path=args.config,
            input_file=args.input,
            use_input_file=use_input_file
        )

        # Override theme if provided
        if args.theme:
            orchestrator.config["story_generation"]["theme"] = args.theme

        results = orchestrator.run()

        # Print summary
        print("\n" + "=" * 60)
        print("Workflow Results:")
        print("=" * 60)

        if results.get("status") == "no_pending_stories":
            print("[+] No pending stories in input.txt")
        elif results.get("status") == "cancelled_by_user":
            print("[+] Story generated and saved (cancelled before audio generation)")
            print(f"  Story: {results['story']['title']}")
            print(f"  Saved to: orchestrator/output/story.json")
        else:
            print(f"[+] Story: {results['story']['title']}")
            print(f"[+] Audio: {results['audio_path']}")
            print(f"[+] Video: {results['video_path']}")
            print(f"[+] Instagram: {results['instagram']}")

        print("=" * 60)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
