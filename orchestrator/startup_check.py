#!/usr/bin/env python3
"""
Startup workflow - run this at the beginning of every session:
1. Check and archive newly posted stories
2. Review current status
3. Check for new story files
"""

import sys
import subprocess
from pathlib import Path


def run_startup_checks():
    """Run all startup checks."""
    print("\n" + "=" * 60)
    print("KINDERGESCHICHTEN AUTOMATION - STARTUP CHECKS")
    print("=" * 60 + "\n")

    # Step 1: Validate all status fields
    print("[1/4] Validating status fields against actual files...")
    print("-" * 60)
    result = subprocess.run(
        [sys.executable, "validate_and_fix_status.py"],
        capture_output=False
    )
    if result.returncode != 0:
        print("[!] Warning: Status validation had issues")

    # Step 2: Complete new story workflow (detect > register > JSON > dashboard)
    print("\n[2/4] Processing new stories (Detect > Register > Generate JSON)...")
    print("-" * 60)
    result = subprocess.run(
        [sys.executable, "detect_register_generate.py"],
        capture_output=False
    )
    if result.returncode != 0:
        print("[!] Warning: Story workflow had issues")

    # Step 3: Archive posted stories
    print("\n[3/4] Checking for newly posted stories...")
    print("-" * 60)
    result = subprocess.run(
        [sys.executable, "check_and_archive_posted.py"],
        capture_output=False
    )
    if result.returncode != 0:
        print("[!] Warning: Archive check had issues")

    # Step 4: Show current status
    print("\n[4/4] Current workflow status:")
    print("-" * 60)
    result = subprocess.run(
        [sys.executable, "-c", """
import csv
from pathlib import Path

input_file = "input/0_input_all_stories.txt"

with open(input_file, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

text_count = sum(1 for r in rows if r['status_story']=='X')
json_count = sum(1 for r in rows if r['status_story_json']=='X')
audio_count = sum(1 for r in rows if r['status_audio']=='X')
picture_count = sum(1 for r in rows if r['status_picture']=='X')
video_count = sum(1 for r in rows if r['status_video']=='X')
insta_count = sum(1 for r in rows if r['insta_post']=='X')

total = len(rows)
progress = (text_count + json_count + audio_count + video_count) / (total * 4) * 100

print(f"Text:     {text_count:2d}/99 | JSON:     {json_count:2d}/99 | Audio:    {audio_count:2d}/99 | Picture: {picture_count:2d}/99")
print(f"Video:    {video_count:2d}/99 | Instagram: {insta_count:2d}/99 | Overall Progress: {progress:.0f}%")
"""],
        capture_output=False
    )

    print("\n" + "=" * 60)
    print("Startup checks complete. Ready to proceed.")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    run_startup_checks()
