#!/usr/bin/env python3
"""
Complete automated workflow for new stories:
1. Detect new story files in input/ folder
2. Register with status_story=X
3. Count and update words
4. Generate JSON metadata
5. Update dashboard
"""

import csv
import json
import subprocess
import logging
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from input_file_manager import InputFileManager

from project_1_story_generator.src.story_models import Story
from input_reader import InputReader


class AutomatedStoryWorkflow:
    """Complete workflow: detect → register → count → generate JSON → dashboard."""

    def __init__(self):
        self.logger = self._setup_logging()
        self.input_dir = Path("input")
        self.input_file = self.input_dir / "0_input_all_stories.txt"
        self.output_dir = Path("output")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _setup_logging(self):
        """Setup logging."""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[logging.StreamHandler()],
        )
        return logging.getLogger(__name__)

    def detect_new_stories(self):
        """Detect new story files not yet registered."""
        # Read existing stories
        existing_stories = {}
        if self.input_file.exists():
            with open(self.input_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    existing_stories[row['numbering']] = row['story_name']

        # Get all story files
        story_files = sorted(self.input_dir.glob("*.txt"))
        story_files = [f for f in story_files if f.name != "0_input_all_stories.txt"]

        new_stories = []

        for story_file in story_files:
            # Skip utility files
            if (story_file.stem.startswith("00_") or
                "dump" in story_file.stem.lower() or
                "simplified" in story_file.stem.lower()):
                continue

            # Extract numbering
            parts = story_file.stem.split("_", 1)
            if not parts[0].isdigit():
                continue

            numbering = parts[0]

            # Check if NEW (not in input file)
            if numbering not in existing_stories:
                with open(story_file, 'r', encoding='utf-8') as f:
                    text = f.read().strip()

                word_count = len(text.split())

                # Validate word count (300-450 range)
                is_compliant = 300 <= word_count <= 450

                new_stories.append({
                    'numbering': numbering,
                    'filename': story_file.name,
                    'story_name': story_file.stem,
                    'text': text,
                    'word_count': word_count,
                    'is_compliant': is_compliant
                })

        return new_stories

    def register_story(self, numbering, story_name, word_count):
        """Register new story in input file with status_story=X."""
        rows = []
        fieldnames = None

        if self.input_file.exists():
            with open(self.input_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                fieldnames = reader.fieldnames
                rows = list(reader)

        if fieldnames is None:
            fieldnames = [
                'numbering', 'keyword1', 'keyword2', 'keyword3', 'story_name',
                'status_story', 'words', 'status_story_json', 'status_audio',
                'seconds', 'status_picture', 'status_video', 'status_caption', 'insta_post'
            ]

        # Create new row
        new_row = {
            'numbering': numbering,
            'keyword1': '',
            'keyword2': '',
            'keyword3': '',
            'story_name': story_name,
            'status_story': 'X',  # File exists
            'words': str(word_count),
            'status_story_json': 'O',  # Will be set to X after JSON generation
            'status_audio': 'O',
            'seconds': '0',
            'status_picture': 'O',
            'status_video': 'O',
            'status_caption': 'O',
            'insta_post': 'O'
        }

        rows.append(new_row)

        # Write back
        with open(self.input_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        self.logger.info(f"[+] Story #{numbering}: Registered with {word_count} words")

    def generate_json_for_story(self, numbering, story_name, story_text):
        """Generate JSON metadata for story."""
        try:
            # Create story object
            story = Story(
                title=story_name,
                text=story_text,
                duration_estimate_seconds=Story.estimate_duration(story_text),
                language="en",
                age_group="3-6",
                theme=None,
                keywords=[]
            )

            # Save JSON
            json_file = self.output_dir / f"{numbering}_{story_name}.json"

            story_dict = {
                'numbering': numbering,
                'title': story.title,
                'text': story.text,
                'duration_estimate_seconds': story.duration_estimate_seconds,
                'language': story.language,
                'age_group': story.age_group,
                'theme': story.theme,
                'keywords': story.keywords or [],
            }

            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(story_dict, f, indent=2, ensure_ascii=False)

            self.logger.info(f"[+] Story #{numbering}: JSON generated")

            # Update status in input file
            input_reader = InputReader(str(self.input_file))
            input_reader.update_status(story_name, "X", status_field="status_story_json")

            return True

        except Exception as e:
            self.logger.error(f"[-] Failed to generate JSON for story #{numbering}: {e}")
            return False

    def process_existing_stories_for_json(self):
        """
        REMEDIATION: Process existing stories that have words but missing JSON.

        Finds stories where:
        - status_story=X (text file exists)
        - 300 <= words <= 450 (compliant)
        - status_story_json=O (JSON not yet generated)

        Auto-generates JSON for all such stories.
        """
        rows = []
        if self.input_file.exists():
            with open(self.input_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)

        if not rows:
            return 0

        remediated_count = 0
        manager = InputFileManager()

        for row in rows:
            story_name = row.get('story_name')
            status_story = row.get('status_story')
            status_story_json = row.get('status_story_json')
            words_str = row.get('words', '0')

            try:
                word_count = int(words_str)
            except (ValueError, TypeError):
                word_count = 0

            # Check if needs remediation: story exists, words compliant, but JSON missing
            if (status_story == 'X' and
                300 <= word_count <= 450 and
                status_story_json == 'O'):

                self.logger.info(f"[*] Remediating story '{story_name}': words={word_count}, generating JSON...")

                if manager.process_words_and_generate_json(story_name, word_count):
                    remediated_count += 1
                    self.logger.info(f"[+] Remediated story '{story_name}'")
                else:
                    self.logger.warning(f"[-] Failed to remediate story '{story_name}'")

        return remediated_count

    def update_dashboard(self):
        """Update dashboard data and regenerate HTML."""
        try:
            # Read input file
            with open(self.input_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            # Write dashboard data
            with open('dashboard_data.json', 'w', encoding='utf-8') as f:
                json.dump(rows, f, indent=2, ensure_ascii=False)

            # Regenerate dashboard
            result = subprocess.run(
                ['python', 'generate_dashboard.py'],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                self.logger.info("[+] Dashboard updated")
            else:
                self.logger.warning("[!] Dashboard update had issues")

        except Exception as e:
            self.logger.error(f"[-] Failed to update dashboard: {e}")

    def run_complete_workflow(self):
        """Run complete workflow: detect → register → count → JSON → dashboard."""
        self.logger.info("=" * 60)
        self.logger.info("Complete Story Workflow: Detect → Register → JSON → Dashboard")
        self.logger.info("=" * 60)

        processed_count = 0

        # Step 1: REMEDIATION - Process existing stories with words but missing JSON
        self.logger.info("\n[STEP 1] Checking existing stories for missing JSON...")
        remediated_count = self.process_existing_stories_for_json()
        if remediated_count > 0:
            self.logger.info(f"[+] Remediated {remediated_count} existing stories")
            processed_count += remediated_count

        # Step 2: DETECTION - Find and process new stories
        self.logger.info("\n[STEP 2] Detecting new stories...")
        new_stories = self.detect_new_stories()

        if not new_stories:
            self.logger.info("No new stories detected")
        else:
            self.logger.info(f"Found {len(new_stories)} new stories\n")

            for story in new_stories:
                numbering = story['numbering']
                story_name = story['story_name']
                word_count = story['word_count']
                text = story['text']
                is_compliant = story['is_compliant']

                # Register with status_story=X and word count
                self.register_story(numbering, story_name, word_count)

                # RULE - When words are populated, auto-generate JSON if compliant
                # Use InputFileManager to enforce this rule
                manager = InputFileManager()
                if manager.process_words_and_generate_json(story_name, word_count):
                    processed_count += 1
                else:
                    self.logger.warning(f"[-] Story #{numbering}: Non-compliant word count")

        self.logger.info("=" * 60)

        if processed_count > 0:
            self.logger.info(f"[+] Successfully processed {processed_count} stories (remediated + new)")
            self.logger.info("Updating dashboard...")
            self.update_dashboard()
        else:
            self.logger.info("No stories were successfully processed")

        self.logger.info("=" * 60)
        return processed_count


def main():
    """Main entry point."""
    workflow = AutomatedStoryWorkflow()
    workflow.run_complete_workflow()


if __name__ == "__main__":
    main()
