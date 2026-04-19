#!/usr/bin/env python3
"""Sync dashboard_data.json from GitHub before starting the dashboard."""

import requests
import json
import csv
import io
import os
from dotenv import load_dotenv

load_dotenv()

github_token = os.getenv("GITHUB_TOKEN")
github_repo = os.getenv("GITHUB_REPO")

url = f"https://api.github.com/repos/{github_repo}/contents/orchestrator/input/0_input_all_stories.txt"
headers = {"Authorization": f"token {github_token}", "Accept": "application/vnd.github.v3.raw"}

print("[*] Syncing from GitHub...")
response = requests.get(url, headers=headers, timeout=10)

if response.status_code != 200:
    print(f"[-] Failed to fetch from GitHub: {response.status_code}")
    exit(1)

rows = list(csv.DictReader(io.StringIO(response.text)))

# Update local input file
with open("input/0_input_all_stories.txt", "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

# Update dashboard_data.json
with open("dashboard_data.json", "w", encoding="utf-8") as f:
    json.dump(rows, f, indent=2, ensure_ascii=False)

posted = [r for r in rows if r.get("insta_post") == "X"]
pending = [r for r in rows if r.get("insta_post") == "O"]
print(f"[+] Synced: {len(rows)} stories | {len(posted)} posted | {len(pending)} pending")
if pending:
    print(f"[+] Next to post: #{pending[0]['numbering']} - {pending[0]['story_name']}")

# Regenerate dashboard.html
import subprocess
result = subprocess.run(["python", "generate_dashboard.py"], capture_output=True, text=True)
if result.returncode == 0:
    print("[+] Dashboard regenerated!")
else:
    print(f"[-] Dashboard regeneration failed: {result.stderr}")
