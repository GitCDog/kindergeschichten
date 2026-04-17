#!/usr/bin/env python3
"""Generate audio files for stories."""

import os
import sys
import json
import logging
from pathlib import Path
import yaml
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from project_2_tts_voice_generator.src.elevenlabs_client import ElevenLabsClient
from project_2_tts_voice_generator.src.audio_processor import AudioProcessor
from input_reader import InputReader


class AudioGenerator:
    """Generate audio files for stories."""

    def __init__(self, config_path: str = "config.yaml", output_dir: str = "output"):
        """Initialize audio generator."""
        self.config = self._load_config(config_path)
        self.logger = self._setup_logging()
        self.output_dir = Path(output_dir)
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

    def _get_audio_duration(self, audio_file: Path) -> int:
        """Get audio duration in seconds from MP3 file."""
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_mp3(str(audio_file))
            duration_seconds = int(len(audio) / 1000)  # Convert milliseconds to seconds
            return duration_seconds
        except Exception as e:
            self.logger.warning(f"Could not get audio duration: {e}")
            return 0

    def generate_audio(self, story_number: int):
        """Generate audio for a specific story by number."""
        # Load the story JSON
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

        # Load the story JSON
        json_file = self.output_dir / f"{numbering}_{story_name}.json"
        if not json_file.exists():
            self.logger.error(f"Story JSON not found: {json_file}")
            return False

        with open(json_file, "r", encoding="utf-8") as f:
            story_data = json.load(f)

        story_text = story_data["text"]

        self.logger.info(f"\n{'=' * 60}")
        self.logger.info(f"Generating Audio for Story #{numbering}: {story_name}")
        self.logger.info(f"{'=' * 60}")

        try:
            # Initialize TTS client
            api_key = os.getenv("ELEVENLABS_API_KEY")
            if not api_key:
                self.logger.error("ELEVENLABS_API_KEY environment variable not set")
                return False

            voice_preset = self.config["text_to_speech"]["voice_preset"]
            self.logger.info(f"Using voice: {voice_preset}")

            # Generate audio
            client = ElevenLabsClient(api_key=api_key)
            audio_data = client.generate_audio(
                text=story_text,
                voice_preset=voice_preset
            )

            if not audio_data:
                self.logger.error("Failed to generate audio")
                return False

            # Save audio file
            audio_file = self.output_dir / f"{numbering}_{story_name}.mp3"
            with open(audio_file, "wb") as f:
                f.write(audio_data)

            self.logger.info(f"[+] Audio saved: {audio_file.name}")

            # Get audio duration in seconds
            duration_seconds = self._get_audio_duration(audio_file)

            # Mark audio as processed in input file
            input_reader = InputReader("input/0_input_all_stories.txt")
            input_reader.update_status(story_name, "X", status_field="status_audio")
            self.logger.info(f"[+] Status updated: audio marked as processed")

            # Update seconds column with actual audio duration
            if duration_seconds > 0:
                input_reader.update_status(story_name, str(duration_seconds), status_field="seconds")
                self.logger.info(f"[+] Duration updated: {duration_seconds} seconds")

            return True

        except Exception as e:
            self.logger.error(f"[-] Failed to generate audio: {e}", exc_info=True)
            return False


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate audio files for stories")
    parser.add_argument(
        "--story",
        type=int,
        help="Story number to generate audio for (e.g., 1 for story #1)",
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

    args = parser.parse_args()

    try:
        generator = AudioGenerator(config_path=args.config, output_dir=args.output)

        if args.story:
            # Generate audio for specific story
            success = generator.generate_audio(args.story)
            if not success:
                sys.exit(1)
        else:
            print("Usage: python generate_audio.py --story <number>")
            print("Example: python generate_audio.py --story 1")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
