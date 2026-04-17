#!/usr/bin/env python3
"""
Generate stories only (JSON files) from input.txt
Skips audio/video/upload - just creates story JSON files
"""

import os
import sys
import json
import logging
from pathlib import Path
import yaml

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from project_1_story_generator.src.generators.claude_generator import ClaudeGenerator
from project_1_story_generator.src.generators.template_generator import TemplateGenerator
from project_1_story_generator.src.story_models import Story
from input_reader import InputReader


class StoryGenerator:
    """Generate stories only (JSON files)."""

    def __init__(self, config_path: str = "config.yaml", output_dir: str = "./output"):
        """
        Initialize story generator.

        Args:
            config_path: Path to configuration file
            output_dir: Output directory for JSON files (default: ./output)
        """
        self.config = self._load_config(config_path)
        self.logger = self._setup_logging()
        # JSON/MP3/MP4 go to output/ folder
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        # Story text files go to input/ folder
        self.input_dir = Path("input")
        self.input_dir.mkdir(parents=True, exist_ok=True)
        self.input_reader = InputReader("input/0_input_all_stories.txt")

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

    def generate_all_stories(self):
        """Generate all pending stories from input.txt"""
        stories = self.input_reader.read_stories()

        if not stories:
            self.logger.info("No stories found in input.txt")
            return

        for story_info in stories:
            self.logger.info(f"\n{'=' * 60}")
            self.logger.info(f"Processing Story #{story_info['numbering']}: {story_info['story_name']}")
            self.logger.info(f"Keywords: {', '.join(story_info['keywords'])}")
            self.logger.info(f"{'=' * 60}")

            try:
                # CRITICAL: Skip if JSON already generated (never regenerate)
                # Status codes: X=processed, O=pending
                if story_info.get("status_story_json") == "X":
                    self.logger.info(f"[O] Skipping (JSON already generated): {story_info['story_name']}")
                    continue

                # Check if story text file exists before creating JSON
                if story_info.get("status_story") == "O":
                    self.logger.info(f"[!] Skipping (story text file pending): {story_info['story_name']}")
                    self.logger.info(f"    Use extract_stories.py to add story from dump file")
                    continue

                # Check if story file already exists
                story_text = self._check_existing_story(story_info)

                if story_text:
                    self.logger.info(f"[+] Story file found, using existing story")
                    # Create story object with existing text
                    story = Story(
                        title=story_info["story_name"],
                        text=story_text,
                        duration_estimate_seconds=Story.estimate_duration(story_text),
                        language="en",
                        age_group="3-6",
                        theme=None,
                        keywords=story_info["keywords"],
                    )
                else:
                    if story_info["status_story_json"] == "X":
                        self.logger.info(f"[O] Skipping (already processed): {story_info['story_name']}")
                        continue

                    self.logger.info(f"-> No story file found, but status_story says it should exist!")
                    self.logger.info(f"    Skipping to avoid auto-generation")
                    continue

                # Save JSON
                self._save_story(story, story_info)

                # Mark story_json as processed
                self.input_reader.update_status(story_info["story_name"], "X", status_field="status_story_json")

                self.logger.info(f"[+] Story saved: {story_info['numbering']}_{story_info['story_name']}.json")

            except Exception as e:
                self.logger.error(f"[-] Failed to process story: {e}", exc_info=True)
                continue

        self.logger.info(f"\n{'=' * 60}")
        self.logger.info("All stories processed!")
        self.logger.info(f"{'=' * 60}")

    def _check_existing_story(self, story_info: dict) -> str:
        """Check if story file already exists in input folder.

        Args:
            story_info: Story info from input.txt

        Returns:
            Story text if file exists, None otherwise
        """
        numbering = story_info["numbering"]
        story_name = story_info["story_name"]

        # Check for story file: {numbering}_{story_name}.txt in input/ folder
        story_file = self.input_dir / f"{numbering}_{story_name}.txt"

        if story_file.exists():
            try:
                with open(story_file, "r", encoding="utf-8") as f:
                    return f.read().strip()
            except Exception as e:
                self.logger.warning(f"Failed to read story file {story_file}: {e}")
                return None

        return None

    def _generate_story(self, keywords: list) -> object:
        """Generate a children's story.

        Args:
            keywords: List of keywords to guide story generation

        Returns:
            Story object
        """
        generator_type = self.config["story_generation"]["generator_type"]
        theme = self.config["story_generation"].get("theme")
        duration = self.config["story_generation"]["target_duration_seconds"]

        # Try Claude first if configured
        if generator_type in ["claude", "both"]:
            try:
                self.logger.info("  Using Claude API...")
                generator = ClaudeGenerator()
                return generator.generate(theme=theme, keywords=keywords, duration_seconds=duration)
            except Exception as e:
                self.logger.warning(f"  Claude generation failed: {e}")
                if generator_type == "claude":
                    raise
                self.logger.info("  Fallback to template generator...")

        # Use template generator
        self.logger.info("  Using template generator...")
        generator = TemplateGenerator()
        return generator.generate(theme=theme, keywords=keywords, duration_seconds=duration)

    def _save_story(self, story, story_info: dict) -> None:
        """Save story as JSON file and text file.

        Args:
            story: Story object
            story_info: Story info from input.txt
        """
        numbering = story_info["numbering"]
        story_name = story_info["story_name"]

        # Save story text to input/ folder as {numbering}_{story_name}.txt
        # ONLY if it doesn't already exist (never overwrite)
        text_filename = f"{numbering}_{story_name}.txt"
        text_filepath = self.input_dir / text_filename
        if not text_filepath.exists():
            with open(text_filepath, "w", encoding="utf-8") as f:
                f.write(story.text)
        else:
            self.logger.info(f"  Preserving existing story file: {text_filename}")

        # Save JSON to output/ folder as {numbering}_{story_name}.json
        json_filename = f"{numbering}_{story_name}.json"
        json_filepath = self.output_dir / json_filename
        with open(json_filepath, "w", encoding="utf-8") as f:
            json.dump(story.to_dict(), f, indent=2, ensure_ascii=False)


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate stories only (JSON files)")
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
        "--single",
        action="store_true",
        help="Generate only the next pending story (default: generate all)",
    )

    args = parser.parse_args()

    try:
        generator = StoryGenerator(config_path=args.config, output_dir=args.output)

        if args.single:
            # Generate only the next pending story
            story_info = generator.input_reader.get_next_pending_story()
            if not story_info:
                print("[+] No pending stories in input.txt")
                return

            print(f"\nGenerating Story #{story_info['numbering']}: {story_info['story_name']}")
            print(f"Keywords: {', '.join(story_info['keywords'])}\n")

            try:
                story = generator._generate_story(story_info["keywords"])
                story.title = story_info["story_name"]
                generator._save_story(story, story_info)
                generator.input_reader.update_status(story_info["story_name"], "X", status_field="status_story_json")
                print(f"[+] Story saved: {story_info['numbering']}_{story_info['story_name']}.json")
            except Exception as e:
                print(f"[-] Failed to generate story: {e}")
                sys.exit(1)
        else:
            # Generate all pending stories
            generator.generate_all_stories()

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
