#!/usr/bin/env python3
"""
Validate and auto-fix status fields in 0_input_all_stories.txt
Checks if actual files match their status_story/status_audio/status_video values
"""

import csv
import json
import subprocess
import logging
from pathlib import Path


class StatusValidator:
    """Validate and fix status fields."""

    def __init__(self):
        self.logger = self._setup_logging()
        self.input_file = Path("input/0_input_all_stories.txt")
        self.output_dir = Path("output")
        self.archive_dir = self.output_dir / "1_insta_post_X"

    def _setup_logging(self):
        """Setup logging."""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[logging.StreamHandler()],
        )
        return logging.getLogger(__name__)

    def check_file_exists(self, numbering, story_name, file_type):
        """Check if a file exists for a story."""
        if file_type == "story":
            # Check in input/ folder
            path = Path("input") / f"{numbering}_{story_name}.txt"
            return path.exists()

        elif file_type == "json":
            # Check in output/ folder
            path = self.output_dir / f"{numbering}_{story_name}.json"
            return path.exists()

        elif file_type == "audio":
            # Check in output/ or archive/ folder
            path1 = self.output_dir / f"{numbering}_{story_name}.mp3"
            path2 = self.archive_dir / f"{numbering}_{story_name}.mp3"
            return path1.exists() or path2.exists()

        elif file_type == "video":
            # Check in output/ or archive/ folder
            path1 = self.output_dir / f"{numbering}_{story_name}_video.mp4"
            path2 = self.archive_dir / f"{numbering}_{story_name}_video.mp4"
            return path1.exists() or path2.exists()

        return False

    def validate_and_fix_all_statuses(self):
        """Validate all status fields and auto-fix mismatches."""
        # Read input file
        with open(self.input_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        self.logger.info("=" * 60)
        self.logger.info("Validating Status Fields")
        self.logger.info("=" * 60)

        fixed_count = 0
        issues = []

        for row in rows:
            numbering = row['numbering']
            story_name = row['story_name']
            status_story = row['status_story']

            # RULE: If status_story=X, MUST have words > 0
            if status_story == 'X':
                try:
                    word_count = int(row.get('words', '0'))
                    if word_count == 0:
                        # File exists but no word count - count it now
                        story_file = Path("input") / f"{numbering}_{story_name}.txt"
                        if story_file.exists():
                            with open(story_file, 'r', encoding='utf-8') as f:
                                text = f.read().strip()
                            word_count = len(text.split())
                            row['words'] = str(word_count)
                            fixed_count += 1
                            self.logger.info(
                                f"[+] Story #{numbering}: words updated to {word_count}"
                            )
                except ValueError:
                    pass

            # RULE: status_story_json=X only if JSON file exists
            # If status_story=X but status_story_json=O, that's OK - just pending JSON generation

            # Check status_story (story text file)
            # RULE: Status=X never reverts to O (marks completed work)
            actual_story_exists = self.check_file_exists(numbering, story_name, "story")
            current_status_story = row['status_story']

            if current_status_story == 'X' and not actual_story_exists:
                # File is missing but status=X (work was completed)
                # Keep X - never revert! Just log warning
                self.logger.warning(
                    f"[!] Story #{numbering}: status_story=X but file missing (archived?)"
                )
            elif current_status_story == 'O' and actual_story_exists:
                # File exists but status=O - should be X
                row['status_story'] = 'X'
                fixed_count += 1
                self.logger.info(
                    f"[+] Story #{numbering}: status_story O -> X"
                )

            # Check status_story_json (story JSON metadata)
            # RULE: Status=X never reverts to O
            actual_json_exists = self.check_file_exists(numbering, story_name, "json")
            current_status_json = row['status_story_json']

            if current_status_json == 'X' and not actual_json_exists:
                # File missing but status=X - work was done, never revert
                self.logger.warning(
                    f"[!] Story #{numbering}: status_story_json=X but file missing (archived?)"
                )
            elif current_status_json == 'O' and actual_json_exists:
                # File exists but status=O - should be X
                row['status_story_json'] = 'X'
                fixed_count += 1
                self.logger.info(
                    f"[+] Story #{numbering}: status_story_json O -> X"
                )

            # Check status_audio (audio MP3 file)
            # RULE: Status=X never reverts to O
            actual_audio_exists = self.check_file_exists(numbering, story_name, "audio")
            current_status_audio = row['status_audio']

            if current_status_audio == 'X' and not actual_audio_exists:
                # File missing but status=X - work was done, never revert
                self.logger.warning(
                    f"[!] Story #{numbering}: status_audio=X but file missing (archived?)"
                )
            elif current_status_audio == 'O' and actual_audio_exists:
                # File exists but status=O - should be X
                row['status_audio'] = 'X'
                fixed_count += 1
                self.logger.info(
                    f"[+] Story #{numbering}: status_audio O -> X"
                )

            # Check status_video (video MP4 file)
            # RULE: Status=X never reverts to O
            actual_video_exists = self.check_file_exists(numbering, story_name, "video")
            current_status_video = row['status_video']

            if current_status_video == 'X' and not actual_video_exists:
                # File missing but status=X - work was done, never revert
                self.logger.warning(
                    f"[!] Story #{numbering}: status_video=X but file missing (archived?)"
                )
            elif current_status_video == 'O' and actual_video_exists:
                # File exists but status=O - should be X
                row['status_video'] = 'X'
                fixed_count += 1
                self.logger.info(
                    f"[+] Story #{numbering}: status_video O -> X"
                )

        # Write back if changes made
        if fixed_count > 0:
            with open(self.input_file, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)

            self.logger.info("=" * 60)
            self.logger.info(f"[+] Fixed {fixed_count} status fields")
            self.logger.info("Updating dashboard...")

            # Update dashboard
            self.update_dashboard()
        else:
            self.logger.info("=" * 60)
            self.logger.info("All status fields are correct!")

        return fixed_count, issues

    def update_dashboard(self):
        """Update dashboard data and regenerate HTML."""
        try:
            # Read input file and create dashboard_data.json
            with open(self.input_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            # Write dashboard data
            with open('dashboard_data.json', 'w', encoding='utf-8') as f:
                json.dump(rows, f, indent=2, ensure_ascii=False)

            # Regenerate dashboard HTML
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


def main():
    """Main entry point."""
    validator = StatusValidator()
    fixed_count, issues = validator.validate_and_fix_all_statuses()


if __name__ == "__main__":
    main()
