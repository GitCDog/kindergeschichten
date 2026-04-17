#!/usr/bin/env python3
"""
Extract stories from 00_story_dump.txt and create individual story files
matching the naming convention: {numbering}_{story_name}.txt

After extracting each story, it is removed from the dump file to prevent
re-extraction on subsequent runs.
"""

import re
import sys
from pathlib import Path
from input_reader import InputReader

def count_words(text: str) -> int:
    """Count words in text."""
    return len(text.split())

def extract_stories_from_dump(dump_file: str = "input/00_story_dump.txt", min_words: int = 300, max_words: int = 450):
    """
    Parse the story dump file and extract stories within word count range.
    Format: numbering,"story_text"

    Only extracts stories with word count between min_words and max_words.

    Returns:
        Tuple of (stories dict, all_lines list, skipped_report dict)
        stories: Dict mapping numbering to story text (valid word counts)
        all_lines: List of all lines from dump file (for updating)
        skipped_report: Dict of skipped stories with reasons
    """
    stories = {}
    all_lines = []
    skipped_report = {}

    dump_path = Path(dump_file)
    if not dump_path.exists():
        print(f"[-] Dump file not found: {dump_file}")
        return stories, all_lines, skipped_report

    with open(dump_path, 'r', encoding='utf-8') as f:
        all_lines = f.readlines()

    # Skip header line (numbering,full_story)
    for line in all_lines[1:]:
        line_stripped = line.strip()
        if not line_stripped:
            continue

        # Format: numbering,"story text"
        # Split on the first comma
        parts = line_stripped.split(',', 1)
        if len(parts) == 2:
            numbering = parts[0].strip()
            story_raw = parts[1].strip()

            # Remove surrounding quotes if present
            if story_raw.startswith('"') and story_raw.endswith('"'):
                story_text = story_raw[1:-1]
            else:
                story_text = story_raw

            if numbering.isdigit():
                # Check word count
                word_count = count_words(story_text)

                if word_count < min_words:
                    skipped_report[numbering] = f"Too short ({word_count} words, need {min_words}-{max_words})"
                elif word_count > max_words:
                    skipped_report[numbering] = f"Too long ({word_count} words, need {min_words}-{max_words})"
                else:
                    stories[numbering] = story_text

    return stories, all_lines, skipped_report

def remove_stories_from_dump(dump_file: str, extracted_numbers: set):
    """
    Remove extracted stories from the dump file.
    Handles both numbered story lines and their continuation lines.

    Args:
        dump_file: Path to dump file
        extracted_numbers: Set of story numbers that were extracted
    """
    dump_path = Path(dump_file)

    with open(dump_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    new_lines = [lines[0]]  # Keep header
    skip_until_next_number = False
    current_extracted = False

    for line in lines[1:]:
        line_stripped = line.strip()

        # Check if this line starts with a story number
        if line_stripped and line_stripped[0].isdigit():
            # Extract numbering (everything before the first comma)
            parts = line_stripped.split(',', 1)
            if len(parts) >= 1:
                numbering = parts[0].strip()
                if numbering.isdigit():
                    # Check if this story was extracted
                    if numbering in extracted_numbers:
                        current_extracted = True
                    else:
                        current_extracted = False
                        new_lines.append(line)
                    continue

        # If we're not in an extracted story, keep the line
        # Status codes: X=processed, O=pending
        if not current_extracted:
            new_lines.append(line)

    # Write updated dump file
    with open(dump_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

    # Count remaining stories
    remaining = sum(1 for line in new_lines[1:]
                   if line.strip() and line.strip()[0].isdigit())
    return remaining

def main():
    """Extract stories and create files."""
    print("[*] Extracting stories from dump file (300-450 words requirement)...")

    # Extract stories from dump (300-450 words)
    stories, all_lines, skipped_report = extract_stories_from_dump(min_words=300, max_words=450)

    # Report skipped stories
    if skipped_report:
        print(f"\n[!] SKIPPED {len(skipped_report)} stories (outside word count range):")
        for numbering, reason in sorted(skipped_report.items()):
            print(f"    Story #{numbering}: {reason}")

    if not stories:
        print("[-] No stories found in dump file within word count range (300-400 words)")
        return

    print(f"\n[+] Found {len(stories)} stories in dump file (within range)")

    # Load input file to get story names
    input_reader = InputReader("input/0_input_all_stories.txt")
    all_stories = input_reader.read_stories()

    # Create a mapping of numbering to story_name
    story_names = {story['numbering']: story['story_name'] for story in all_stories}

    # Create story files
    input_dir = Path("input")
    input_dir.mkdir(parents=True, exist_ok=True)

    created_count = 0
    extracted_numbers = set()

    for numbering, story_text in stories.items():
        # Get story name from input file
        if numbering not in story_names:
            print(f"[-] Story #{numbering} not found in input file, skipping")
            continue

        story_name = story_names[numbering]
        filename = f"{numbering}_{story_name}.txt"
        filepath = input_dir / filename

        # Check if file already exists
        if filepath.exists():
            print(f"[O] File already exists: {filename} (will be removed from dump)")
            extracted_numbers.add(numbering)
            continue

        # Write story file
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(story_text)
            print(f"[+] Created: {filename}")
            created_count += 1
            extracted_numbers.add(numbering)
        except Exception as e:
            print(f"[-] Failed to create {filename}: {e}")

    # Remove extracted stories from dump file
    if extracted_numbers:
        print(f"\n[*] Removing {len(extracted_numbers)} stories from dump file...")
        remaining = remove_stories_from_dump("input/00_story_dump.txt", extracted_numbers)
        print(f"[+] Dump file updated ({remaining} stories remain)")

    print(f"\n[+] Successfully created {created_count} story files")

    # Update word counts and other metadata
    if created_count > 0:
        print("\n[*] Updating word counts in input file...")
        from update_columns import ColumnUpdater
        updater = ColumnUpdater()
        updater.update_input_file()
        print("[+] Updated metadata")

if __name__ == "__main__":
    main()
