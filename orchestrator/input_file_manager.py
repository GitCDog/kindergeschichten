#!/usr/bin/env python3
"""
Centralized input file manager.
RULE: Dashboard always reads from GitHub input file to stay synced with automation.
"""

import csv
import json
import subprocess
import logging
from pathlib import Path
from dotenv import load_dotenv
import os
import requests

load_dotenv()


class InputFileManager:
    """Manages 0_input_all_stories.txt - reads from GitHub, writes to both local and GitHub."""

    def __init__(self):
        self.input_file = Path("input/0_input_all_stories.txt")
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.github_repo = os.getenv("GITHUB_REPO")
        self.logger = self._setup_logging()

    def _setup_logging(self):
        """Setup logging."""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[logging.StreamHandler()],
        )
        return logging.getLogger(__name__)

    def save_rows(self, rows, description=""):
        """
        Save rows to input file AND sync to GitHub.

        RULE: Input file changes → GitHub syncs → Dashboard updates
        """
        if not rows:
            self.logger.error("Cannot save empty rows")
            return False

        try:
            # Step 1: Write to local file
            with open(self.input_file, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)

            self.logger.info(f"[+] Input file updated locally{': ' + description if description else ''}")

            # Step 2: Sync to GitHub
            if self.github_token and self.github_repo:
                self._sync_to_github(rows, description)

            # Step 3: Update dashboard
            self._update_dashboard_cascade()
            return True

        except Exception as e:
            self.logger.error(f"[-] Failed to save input file: {e}")
            return False

    def _sync_to_github(self, rows, description=""):
        """Sync input file changes to GitHub."""
        try:
            import base64

            # Generate CSV content
            output = []
            if rows:
                fieldnames = rows[0].keys()
                output.append(','.join(fieldnames))
                for row in rows:
                    output.append(','.join(str(row.get(f, '')) for f in fieldnames))

            content = '\n'.join(output) + '\n'
            content_b64 = base64.b64encode(content.encode()).decode()

            # Get current file SHA
            url = f"https://api.github.com/repos/{self.github_repo}/contents/orchestrator/input/0_input_all_stories.txt"
            headers = {
                "Authorization": f"token {self.github_token}",
                "Accept": "application/vnd.github.v3+json"
            }

            get_response = requests.get(url, headers=headers, timeout=10)
            if get_response.status_code != 200:
                self.logger.warning(f"[-] Could not get GitHub file SHA: {get_response.status_code}")
                return

            sha = get_response.json()['sha']

            # Update file on GitHub
            commit_msg = f"[DASHBOARD] {description}" if description else "[DASHBOARD] Update input file"
            update_data = {
                "message": commit_msg,
                "content": content_b64,
                "sha": sha
            }

            update_response = requests.put(url, json=update_data, headers=headers, timeout=10)
            if update_response.status_code == 200:
                self.logger.info(f"[+] GitHub synced")
            else:
                self.logger.warning(f"[-] GitHub sync failed: {update_response.status_code}")

        except Exception as e:
            self.logger.warning(f"[-] GitHub sync error: {e}")

    def _update_dashboard_cascade(self):
        """
        Automatic dashboard update cascade:
        1. Update dashboard_data.json
        2. Regenerate dashboard.html
        """
        try:
            # Step 1: Update dashboard_data.json
            with open(self.input_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            with open('dashboard_data.json', 'w', encoding='utf-8') as f:
                json.dump(rows, f, indent=2, ensure_ascii=False)

            self.logger.info("[+] dashboard_data.json updated")

            # Step 2: Regenerate dashboard.html
            result = subprocess.run(
                ['python', 'generate_dashboard.py'],
                capture_output=True,
                text=True,
                timeout=30,
                cwd='.'
            )

            if result.returncode == 0:
                self.logger.info("[+] dashboard.html regenerated")
            else:
                self.logger.error(f"[-] Dashboard regeneration FAILED with code {result.returncode}")
                if result.stdout:
                    self.logger.error(f"    stdout: {result.stdout}")
                if result.stderr:
                    self.logger.error(f"    stderr: {result.stderr}")

        except subprocess.TimeoutExpired:
            self.logger.error("[-] Dashboard update timeout (30s)")
        except Exception as e:
            self.logger.error(f"[-] Dashboard update failed: {e}")

    def read_rows(self):
        """Read rows from GitHub input file (always current)."""
        if self.github_token and self.github_repo:
            return self._read_rows_from_github()
        else:
            return self._read_rows_from_local()

    def _read_rows_from_github(self):
        """Read input file from GitHub."""
        try:
            url = f"https://api.github.com/repos/{self.github_repo}/contents/orchestrator/input/0_input_all_stories.txt"
            headers = {
                "Authorization": f"token {self.github_token}",
                "Accept": "application/vnd.github.v3.raw"
            }
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                reader = csv.DictReader(response.text.split('\n'))
                return list(reader)
            else:
                self.logger.warning(f"[-] Failed to read from GitHub ({response.status_code}), falling back to local")
                return self._read_rows_from_local()
        except Exception as e:
            self.logger.warning(f"[-] GitHub read failed: {e}, falling back to local")
            return self._read_rows_from_local()

    def _read_rows_from_local(self):
        """Read rows from local input file (fallback)."""
        try:
            with open(self.input_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                return list(reader)
        except Exception as e:
            self.logger.error(f"[-] Failed to read local input file: {e}")
            return []

    def update_cell(self, story_name, column, value):
        """
        Update a single cell and AUTOMATICALLY update dashboard.

        Args:
            story_name: Name of story to update
            column: Column name to update
            value: New value
        """
        rows = self.read_rows()
        if not rows:
            return False

        updated = False
        for row in rows:
            if row.get('story_name') == story_name:
                row[column] = value
                updated = True
                self.logger.info(f"[+] Story '{story_name}': {column}={value}")
                break

        if updated:
            return self.save_rows(rows, f"update: {story_name}")
        else:
            self.logger.warning(f"[-] Story '{story_name}' not found")
            return False

    def add_row(self, new_row):
        """
        Add new story row and AUTOMATICALLY update dashboard.
        """
        rows = self.read_rows()
        if not rows:
            return False

        rows.append(new_row)
        return self.save_rows(rows, f"added story #{new_row.get('numbering')}")

    def process_words_and_generate_json(self, story_name, word_count):
        """
        RULE: When words are populated, auto-generate JSON if compliant (300-450).

        Args:
            story_name: Name of story
            word_count: Word count (int)

        Returns:
            True if JSON generated, False if rejected
        """
        # Validate word count
        is_compliant = 300 <= word_count <= 450

        if not is_compliant:
            if word_count < 300:
                self.logger.warning(
                    f"[-] Story '{story_name}': REJECTED - Too short ({word_count} words, need 300-450)"
                )
            else:
                self.logger.warning(
                    f"[-] Story '{story_name}': REJECTED - Too long ({word_count} words, need 300-450)"
                )
            return False

        # Compliant: Generate JSON automatically
        self.logger.info(f"[+] Story '{story_name}': {word_count} words - COMPLIANT")
        self.logger.info("[+] Auto-triggering JSON generation...")

        # Import here to avoid circular dependency
        try:
            from detect_register_generate import AutomatedStoryWorkflow

            # Get story text
            rows = self.read_rows()
            story_row = next((r for r in rows if r['story_name'] == story_name), None)
            if not story_row:
                self.logger.error(f"[-] Story '{story_name}' not found in input file")
                return False

            numbering = story_row['numbering']
            story_file = Path("input") / f"{numbering}_{story_name}.txt"

            if not story_file.exists():
                self.logger.error(f"[-] Story file not found: {story_file}")
                return False

            # Read story text
            with open(story_file, 'r', encoding='utf-8') as f:
                story_text = f.read().strip()

            # Generate JSON
            workflow = AutomatedStoryWorkflow()
            if workflow.generate_json_for_story(numbering, story_name, story_text):
                self.logger.info(f"[+] JSON generated for story #{numbering}")

                # Update status in input file
                for row in rows:
                    if row['story_name'] == story_name:
                        row['status_story_json'] = 'X'
                        break

                # Save and auto-update dashboard
                self.save_rows(rows, f"JSON generated for {story_name}")
                return True
            else:
                self.logger.error(f"[-] Failed to generate JSON for '{story_name}'")
                return False

        except Exception as e:
            self.logger.error(f"[-] Error generating JSON: {e}")
            return False

    def verify_sync(self):
        """
        Verify that input file and dashboard are in sync.
        Returns True if everything matches, False if out of sync.
        """
        try:
            # Read input file
            with open(self.input_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                input_rows = list(reader)

            # Read dashboard data
            with open('dashboard_data.json', 'r', encoding='utf-8') as f:
                dashboard_data = json.load(f)

            # Compare
            if len(input_rows) != len(dashboard_data):
                self.logger.warning("[!] Row count mismatch")
                return False

            # Check if data matches
            for i, (input_row, dash_row) in enumerate(zip(input_rows, dashboard_data)):
                if input_row != dash_row:
                    self.logger.warning(f"[!] Row {i} mismatch")
                    return False

            self.logger.info("[+] Input file and dashboard are in SYNC")
            return True

        except Exception as e:
            self.logger.error(f"[-] Sync verification failed: {e}")
            return False


if __name__ == "__main__":
    manager = InputFileManager()
    manager.verify_sync()
