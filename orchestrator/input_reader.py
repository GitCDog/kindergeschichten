"""Input file reader for story definitions."""

from pathlib import Path
from typing import Optional, List, Dict


class InputReader:
    """Read and manage story definitions from input.txt file."""

    def __init__(self, input_file: str = "input/0_input_all_stories.txt"):
        """
        Initialize input reader.

        Args:
            input_file: Path to input file (default: input/0_input_all_stories.txt)
        """
        self.input_file = Path(input_file)

    def read_stories(self) -> List[Dict]:
        """
        Parse input.txt and return story definitions.

        Returns:
            List of story dicts with keys: numbering, keywords, story_name, status_story, status_story_json,
            status_audio, status_video, status_caption, status_picture, words, seconds, insta_post, line_number
        """
        stories = []

        if not self.input_file.exists():
            return stories

        with open(self.input_file, "r") as f:
            lines = f.readlines()

        for i, line in enumerate(lines[1:], start=1):  # Skip header
            line = line.strip()
            if not line:
                continue

            parts = [p.strip() for p in line.split(",")]

            if len(parts) < 6:
                continue

            # Current format: numbering,keyword1,keyword2,keyword3,story_name,status_story,words,
            #                 status_story_json,status_audio,seconds,status_video,status_picture,status_caption,insta_post
            # Status codes: X=processed, O=pending
            numbering = parts[0]
            keywords = [parts[1], parts[2], parts[3]]
            story_name = parts[4]
            status_story = parts[5] if len(parts) > 5 else "O"
            words = int(parts[6]) if len(parts) > 6 and parts[6].isdigit() else 0
            status_story_json = parts[7] if len(parts) > 7 else "O"
            status_audio = parts[8] if len(parts) > 8 else "O"
            seconds = int(parts[9]) if len(parts) > 9 and parts[9].isdigit() else 0
            status_video = parts[10] if len(parts) > 10 else "O"
            status_picture = parts[11] if len(parts) > 11 else "O"
            status_caption = parts[12] if len(parts) > 12 else "O"
            insta_post = parts[13] if len(parts) > 13 else "O"

            stories.append(
                {
                    "numbering": numbering,
                    "keywords": keywords,
                    "story_name": story_name,
                    "status_story": status_story,
                    "status_story_json": status_story_json,
                    "status_audio": status_audio,
                    "status_video": status_video,
                    "status_caption": status_caption,
                    "status_picture": status_picture,
                    "words": words,
                    "seconds": seconds,
                    "insta_post": insta_post,
                    "line_number": i,
                }
            )

        return stories

    def get_next_pending_story(self) -> Optional[Dict]:
        """
        Find and return the first story with status_story_json='pending'.

        Returns:
            Story dict or None if no pending stories
        """
        stories = self.read_stories()

        for story in stories:
            if story["status_story_json"] == "pending":
                return story

        return None

    def update_status(self, story_name: str, new_status: str, status_field: str = "status_story_json") -> bool:
        """
        Update status for a story in input.txt.

        IMPORTANT: This uses InputFileManager to ensure automatic dashboard sync.

        Args:
            story_name: Name of the story to update
            new_status: New status value (e.g., "X", "O")
            status_field: Which status field to update: "status_story", "status_story_json", "status_audio",
                         "status_video", "status_caption", "status_picture", "insta_post", "seconds", "words"

        Returns:
            True if updated successfully, False if story not found
        """
        # Import here to avoid circular dependency
        from input_file_manager import InputFileManager

        manager = InputFileManager()
        return manager.update_cell(story_name, status_field, new_status)
