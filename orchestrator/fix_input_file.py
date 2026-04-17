#!/usr/bin/env python3
"""
Fix corrupted 0_input_all_stories.txt file
Restore proper 14-column format with keyword1, keyword2, keyword3 separate
"""

import csv
from pathlib import Path

input_file = Path("input/0_input_all_stories.txt")
backup_file = Path("input/0_input_all_stories.txt.backup")

# Backup current file
if input_file.exists():
    import shutil
    shutil.copy(input_file, backup_file)
    print(f"[+] Backup created: {backup_file}")

# Read corrupted file
rows = []
with open(input_file, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        rows.append(row)

print(f"[*] Read {len(rows)} rows from corrupted file")

# Fix each row
fixed_rows = []
for row in rows:
    fixed_row = {}

    # Keep basic fields
    fixed_row['numbering'] = row.get('numbering', '')
    fixed_row['story_name'] = row.get('story_name', '')

    # Parse keywords from the corrupted list format
    keywords_str = row.get('keywords', "['', '', '']")
    # Remove brackets and quotes, split by comma
    keywords_str = keywords_str.strip("[]").replace("'", "").replace('"', '')
    keywords = [k.strip() for k in keywords_str.split(',')]

    # Ensure we have 3 keywords
    while len(keywords) < 3:
        keywords.append('')

    fixed_row['keyword1'] = keywords[0] if len(keywords) > 0 else ''
    fixed_row['keyword2'] = keywords[1] if len(keywords) > 1 else ''
    fixed_row['keyword3'] = keywords[2] if len(keywords) > 2 else ''

    # Status fields
    fixed_row['status_story'] = row.get('status_story', 'O')
    fixed_row['words'] = row.get('words', '0')
    fixed_row['status_story_json'] = row.get('status_story_json', 'O')
    fixed_row['status_audio'] = row.get('status_audio', 'O')
    fixed_row['seconds'] = row.get('seconds', '0')
    fixed_row['status_picture'] = row.get('status_picture', 'O')
    fixed_row['status_video'] = row.get('status_video', 'O')
    fixed_row['status_caption'] = row.get('status_caption', 'O')
    fixed_row['insta_post'] = row.get('insta_post', 'O')

    fixed_rows.append(fixed_row)

# Write correct format
fieldnames = ['numbering', 'keyword1', 'keyword2', 'keyword3', 'story_name',
              'status_story', 'words', 'status_story_json', 'status_audio', 'seconds',
              'status_picture', 'status_video', 'status_caption', 'insta_post']

with open(input_file, 'w', encoding='utf-8', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(fixed_rows)

print(f"[+] Fixed file saved with {len(fixed_rows)} rows")
print(f"[+] Columns: {', '.join(fieldnames)}")
print(f"[+] Backup available at: {backup_file}")
