#!/usr/bin/env python3
"""
Check for newly posted stories (insta_post=X) and automatically archive their files.
This should be called at the start of every session to keep archives up-to-date.
"""

import csv
import shutil
import logging
from pathlib import Path
from input_reader import InputReader


class PostedStoriesArchiver:
    """Archive files for stories marked as insta_post=X."""

    def __init__(self):
        self.logger = self._setup_logging()
        self.output_dir = Path("output")
        self.archive_dir = self.output_dir / "1_insta_post_X"
        self.archive_dir.mkdir(parents=True, exist_ok=True)

    def _setup_logging(self):
        """Setup logging."""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[logging.StreamHandler()],
        )
        return logging.getLogger(__name__)

    def check_and_archive_posted_stories(self):
        """Check for newly posted stories and archive their files."""
        input_reader = InputReader("input/0_input_all_stories.txt")
        stories = input_reader.read_stories()

        # Find all stories marked as insta_post=X
        posted_stories = [s for s in stories if s["insta_post"] == "X"]

        if not posted_stories:
            self.logger.info("No stories marked as insta_post=X")
            return

        self.logger.info(f"Found {len(posted_stories)} stories marked as insta_post=X")
        self.logger.info("=" * 60)

        archived_count = 0
        files_moved = 0

        for story in posted_stories:
            numbering = story["numbering"]
            story_name = story["story_name"]

            # Files to check and archive
            files_to_archive = [
                self.output_dir / f"{numbering}_{story_name}.json",
                self.output_dir / f"{numbering}_{story_name}.mp3",
                self.output_dir / f"{numbering}_{story_name}_video.mp4",
            ]

            # Archive files that exist in main output folder (not already archived)
            for file_path in files_to_archive:
                if file_path.exists() and file_path.parent == self.output_dir:
                    dest_path = self.archive_dir / file_path.name
                    if not dest_path.exists():
                        shutil.move(str(file_path), str(dest_path))
                        self.logger.info(f"[+] Archived: {file_path.name}")
                        files_moved += 1
                    else:
                        # Already archived
                        self.logger.info(f"[O] Already archived: {file_path.name}")

            if files_moved > 0:
                archived_count += 1

        self.logger.info("=" * 60)
        if files_moved > 0:
            self.logger.info(f"[+] Archived {files_moved} files for {archived_count} stories")
        else:
            self.logger.info("All posted stories already archived or files missing")


def main():
    """Main entry point."""
    archiver = PostedStoriesArchiver()
    archiver.check_and_archive_posted_stories()


if __name__ == "__main__":
    main()
