#!/usr/bin/env python3
import csv, json

with open('input/0_input_all_stories.txt', encoding='utf-8') as f:
    rows = list(csv.DictReader(f))

with open('dashboard_data.json', 'w', encoding='utf-8') as f:
    json.dump(rows, f, indent=2, ensure_ascii=False)

print(f'dashboard_data.json updated: {len(rows)} stories')
