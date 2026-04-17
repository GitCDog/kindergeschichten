# GitHub Integration Setup Guide

Automatic syncing of your input file to GitHub so the Instagram posting script can update it 24/7.

## Overview

**Problem:** Computer is off, but script needs to update `0_input_all_stories.txt`

**Solution:** Store files on GitHub, script commits updates automatically

**Result:** 
- Script posts video at 18:00-20:00 CET
- Updates input file on GitHub immediately
- Computer syncs via `git pull` when back on

---

## Step 1: Create GitHub Repository

1. Go to https://github.com/new
2. Create new repository:
   - **Name:** `kindergeschichten-automation` (or your choice)
   - **Visibility:** Private (recommended) or Public
   - **Initialize:** Don't initialize (we'll push existing code)
   - Click "Create repository"

3. Note the repository URL:
   ```
   https://github.com/YOUR_USERNAME/kindergeschichten-automation.git
   ```

---

## Step 2: Create GitHub Personal Access Token

1. Go to https://github.com/settings/tokens
2. Click "Generate new token" → "Generate new token (classic)"
3. Configure token:
   - **Token name:** `kindergeschichten-posting`
   - **Expiration:** 90 days (refresh before expiration)
   - **Scopes:** Check `repo` (full control of private/public repos)
   - Click "Generate token"

4. **Copy the token immediately** (won't be shown again!)
   - Example: `ghp_1234567890abcdefghijklmnopqrstuvwxyz`

---

## Step 3: Initialize Git & Push to GitHub

**In your project folder:**

```bash
# Navigate to project
cd c:\Users\slawa\Desktop\claude\5_kindergeschichten-automation

# Initialize git (if not already done)
git init

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit: kindergeschichten automation with Instagram posting"

# Add GitHub as remote
git remote add origin https://github.com/YOUR_USERNAME/kindergeschichten-automation.git

# Push to GitHub
git push -u origin main
```

If `main` branch doesn't exist:
```bash
git branch -M main
git push -u origin main
```

---

## Step 4: Update .env with GitHub Credentials

Edit `orchestrator/.env`:

```bash
# GitHub Configuration
GITHUB_TOKEN=ghp_your_token_here
GITHUB_REPO=YOUR_USERNAME/kindergeschichten-automation
```

**Example:**
```bash
GITHUB_TOKEN=ghp_1234567890abcdefghijklmnopqrstuvwxyz
GITHUB_REPO=slawa/kindergeschichten-automation
```

---

## Step 5: Install Dependencies

```bash
cd orchestrator/
pip install -r requirements.txt
```

This installs:
- `PyGithub>=2.0.0` - GitHub API integration
- Plus all other dependencies

---

## Step 6: Test GitHub Integration

**Manual test:**
```bash
cd orchestrator/
python instagram_auto_poster.py
```

**Expected output:**
```
[+] GitHub integration enabled: slawa/kindergeschichten-automation
[*] Updating input file on GitHub...
[+] Updated GitHub: orchestrator/input/0_input_all_stories.txt
[+] Syncing posted_videos.json to GitHub...
[+] Updated GitHub: orchestrator/posted_videos.json
[SUCCESS] Posted 'Story Name' to Instagram
```

**Verify on GitHub:**
1. Go to your GitHub repo
2. Check `orchestrator/input/0_input_all_stories.txt`
3. Look for the insta_post column - should show `X` for posted story
4. Check commit history - should see auto-commit message

---

## Step 7: Set Up Git Sync on Your Computer

When your computer is back on, sync latest changes:

```bash
cd c:\Users\slawa\Desktop\claude\5_kindergeschichten-automation
git pull origin main
```

**Or set up automatic sync:**

### Option A: Windows Task Scheduler (Auto-sync)
```bash
# Create a batch file: sync_github.bat
@echo off
cd c:\Users\slawa\Desktop\claude\5_kindergeschichten-automation
git pull origin main
```

Then schedule it in Task Scheduler:
- Trigger: Every 30 minutes
- Action: Run sync_github.bat

### Option B: Manual Sync Before Using Dashboard
Just remember to `git pull` before starting the dashboard:
```bash
git pull origin main
```

---

## How It Works

### Daily Posting Workflow

1. **17:55 CET** - Claude Routine triggers Instagram script
2. **Script execution:**
   - Fetches video from Cloudinary
   - Generates caption
   - Waits until 18:00-20:00 time
   - Posts to Instagram
   - **Updates `0_input_all_stories.txt` on GitHub** ✓
   - Sets `insta_post=X` for that story
   - **Commits change to GitHub** with message:
     ```
     [AUTO] Posted story #25 "Owl's Starry Night Library" to Instagram
     ```

3. **Your computer** (whenever back on):
   - `git pull` to get latest file
   - Local file automatically updated

---

## Monitoring

### Check GitHub Commits

```bash
# See commit history
git log --oneline

# See recent changes
git diff HEAD~1 HEAD
```

### Check Logs

```bash
# View script logs
tail -f orchestrator/logs/instagram_auto_poster.log

# Search for GitHub updates
grep "GitHub" orchestrator/logs/instagram_auto_poster.log
```

### View Posted Videos

```bash
# Locally
cat orchestrator/posted_videos.json

# On GitHub
https://github.com/YOUR_USERNAME/kindergeschichten-automation/blob/main/orchestrator/posted_videos.json
```

---

## .gitignore (Important!)

Make sure `.env` is NOT committed (contains API keys):

**Create `.gitignore` in project root:**
```
.env
*.log
__pycache__/
.venv/
venv/
*.pyc
.DS_Store
```

Verify .env is ignored:
```bash
git status  # Should NOT show .env
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "fatal: repository not found" | Check GITHUB_REPO format: `username/repo-name` |
| "401 Unauthorized" | Invalid GitHub token, regenerate at github.com/settings/tokens |
| Token expired | Regenerate personal access token |
| "File not found on GitHub" | Make sure files are pushed: `git push origin main` |
| Merge conflicts | Pull latest before pushing: `git pull origin main` |

### Regenerate Token (If Expired)

1. Go to https://github.com/settings/tokens
2. Delete old token (if needed)
3. Generate new token
4. Update `.env` with new token
5. Test: `python instagram_auto_poster.py`

---

## Git Commands Reference

```bash
# Check status
git status

# See what changed
git diff

# Pull latest from GitHub
git pull origin main

# Push local changes (if any)
git push origin main

# See commit history
git log --oneline -10

# View a specific commit
git show <commit-hash>
```

---

## Security Notes

⚠️ **Important:**

1. **Never commit .env** (contains API keys)
   - Make sure it's in `.gitignore`
   - Verify with: `git status`

2. **GitHub token security:**
   - Personal Access Token = password equivalent
   - Keep it secret, never share
   - Store in `.env` only (not in code)
   - Can regenerate anytime

3. **Public vs Private Repository:**
   - **Recommended:** Private (story files are private)
   - Public is fine if you don't mind sharing stories

4. **Token expiration:**
   - Default: 90 days
   - Set reminder to refresh before expiration
   - Can change in token settings

---

## What Gets Synced to GitHub

**Uploaded to GitHub:**
- ✅ `orchestrator/` - All Python scripts
- ✅ `orchestrator/input/0_input_all_stories.txt` - Input file (updated automatically)
- ✅ `orchestrator/posted_videos.json` - Posted video tracker
- ✅ `.gitignore` - Ignore patterns
- ✅ `CLAUDE.md`, `README.txt`, etc.

**NOT synced (ignored):**
- ❌ `.env` - API credentials (stays local)
- ❌ `orchestrator/logs/` - Log files (stays local)
- ❌ `orchestrator/output/` - Generated files (stays local)
- ❌ `orchestrator/images/` - Generated images (stays local)
- ❌ `venv/` - Python virtual env

---

## Success Checklist

- [ ] GitHub repository created
- [ ] Personal Access Token generated
- [ ] Project pushed to GitHub
- [ ] `.env` has GITHUB_TOKEN and GITHUB_REPO
- [ ] `.gitignore` prevents .env from being committed
- [ ] Dependencies installed: `pip install -r requirements.txt`
- [ ] Manual test successful: `python instagram_auto_poster.py`
- [ ] Verify update on GitHub (check commit history)
- [ ] Set up automatic sync or remember to `git pull`

---

## Next Steps

1. ✅ Create GitHub repo
2. ✅ Generate personal access token
3. ✅ Push project to GitHub
4. ✅ Update .env
5. ✅ Install PyGithub
6. ✅ Test manually
7. ✅ Set up Claude Routine for daily posting at 17:55 CET
8. ✅ Monitor first execution
9. ✅ Sync computer with `git pull` when back on

---

