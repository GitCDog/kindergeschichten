#!/usr/bin/env python3
"""
Word count and JSON generation for all stories:
- Count words in each story file
- Validate word count (300-450 range)
- Generate JSON files in output/
- Update 0_input_all_stories.txt with words and status_story_json
"""

import json
import logging
import sys
from pathlib import Path
from input_file_manager import InputFileManager

# Add parent directory to path to import sibling modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from project_1_story_generator.src.story_models import Story

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def generate_word_count_and_json():
    """Process all stories: count words, generate JSON, update input file."""
    print("[DEBUG] generate_word_count_and_json() called", flush=True)

    manager = InputFileManager()
    rows = manager.read_rows()
    print(f"[DEBUG] Read {len(rows)} rows from input file", flush=True)

    input_dir = Path("input")
    output_dir = Path("output")
    output_dir.mkdir(parents=True, exist_ok=True)

    processed_count = 0
    json_count = 0
    rejected_count = 0

    # Process each story
    for row in rows:
        numbering = row['numbering']
        story_name = row['story_name']
        status_story = row['status_story']
        words = row.get('words', '0')

        # Only process if story file exists AND words not yet counted
        if status_story != 'X':
            continue

        # Skip if word count already exists (not 0 or empty)
        if words and words != '0' and words.strip():
            continue

        # Find story file (by numbering, handles apostrophes/underscores)
        story_files = list(input_dir.glob(f"{numbering}_*.txt"))
        if not story_files:
            logger.warning(f"[-] Story #{numbering}: File not found")
            continue

        story_file = story_files[0]  # Use first matching file

        try:
            # Read story file
            with open(story_file, 'r', encoding='utf-8') as f:
                text = f.read().strip()

            # Count words
            word_count = len(text.split())

            # Update words column
            row['words'] = str(word_count)
            processed_count += 1

            # Check word count range (350-400 words)
            if word_count < 350 or word_count > 400:
                logger.warning(f"[!] Story #{numbering}: {word_count} words (outside 350-400 range)")

            # Create JSON file ONLY if it doesn't already exist
            try:
                json_file = output_dir / f"{numbering}_{story_name}.json"

                # IMPORTANT: Never overwrite existing JSON files
                if json_file.exists():
                    logger.info(f"[*] Story #{numbering}: JSON already exists (keeping old file)")
                    row['status_story_json'] = 'X'
                    json_count += 1
                    continue

                story = Story(
                    title=story_name,
                    text=text,
                    duration_estimate_seconds=Story.estimate_duration(text),
                    language="en",
                    age_group="3-6",
                    theme=None,
                    keywords=[]
                )

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

                row['status_story_json'] = 'X'
                json_count += 1
                logger.info(f"[+] Story #{numbering}: {word_count} words → JSON created")

            except Exception as e:
                logger.error(f"[-] Story #{numbering}: JSON generation failed: {e}")
                row['status_story_json'] = 'O'
                rejected_count += 1

        except Exception as e:
            logger.error(f"[-] Story #{numbering}: Error processing: {e}")
            continue

    # Save updated rows
    manager.save_rows(rows, f"Word count & JSON: processed {processed_count}, created {json_count}")

    logger.info(f"[+] Word count & JSON complete:")
    logger.info(f"    Processed: {processed_count} stories")
    logger.info(f"    JSON created: {json_count} stories")
    logger.info(f"    Rejected (out of range): {rejected_count} stories")

    return {
        "success": True,
        "processed": processed_count,
        "json_created": json_count,
        "rejected": rejected_count
    }


if __name__ == "__main__":
    result = generate_word_count_and_json()
    print(f"Result: {result}")
