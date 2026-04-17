# Automatic Instagram Video Posting Setup Guide

This guide explains how to set up automatic daily posting of kindergeschichten videos from Cloudinary to Instagram.

## Overview

**What it does:**
- Fetches unposted videos from Cloudinary (kindergeschichten folder)
- Generates dynamic Instagram captions with story title and keywords
- Posts video at random time between 18:00-20:00 CET daily
- Tracks posted videos to prevent duplicates
- Logs all activity for monitoring

**How it works:**
1. Claude Routine triggers script daily at 17:55 CET
2. Script picks random unposted video from Cloudinary
3. Generates caption from story metadata
4. Calculates random posting time (18:00-20:00)
5. Waits until posting time, then posts to Instagram
6. Records posted video in `posted_videos.json`

---

## Required Setup

### 1. Cloudinary Account

**Get credentials:**
1. Go to https://cloudinary.com/console
2. Under "Account Details", find:
   - Cloud Name
   - API Key
   - API Secret

**Organize videos:**
- Upload all kindergeschichten videos to folder: `kindergeschichten/`
- Naming convention: `{numbering}_{story_name}.mp4`
  - Example: `1_brave_knight.mp4`, `2_magic_forest.mp4`

### 2. Instagram Business Account

**Prerequisites:**
- Facebook Page connected to Instagram
- Instagram Business Account (not Creator Account)
- Must be able to create app on facebook.com/developers

**Get credentials:**
1. Create Meta App at https://developers.facebook.com/
2. Add "Instagram Graph API" product
3. Generate long-lived Access Token
   - Go to App → Settings → Basic → Show
   - Note: Expires after ~60 days, needs refresh mechanism
4. Find your Instagram Business Account ID
   - Go to IG Account Settings → Settings → Basic Info
   - Note the "Instagram Business Account ID"

### 3. Update .env File

Edit `orchestrator/.env`:

```bash
# Cloudinary Configuration
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret

# Instagram Configuration
INSTAGRAM_ACCESS_TOKEN=your_long_lived_access_token
INSTAGRAM_BUSINESS_ACCOUNT_ID=12345678900123456
```

### 4. Install Dependencies

```bash
cd orchestrator/
pip install -r requirements.txt
```

Required packages:
- `cloudinary>=1.30.0` (Cloudinary SDK)
- `requests>=2.28.0` (HTTP client)
- `python-dotenv>=0.19.0` (Environment variables)

---

## Testing

### Manual Test (Before Scheduling)

```bash
cd orchestrator/
python instagram_auto_poster.py
```

**Expected output:**
```
[+] InstagramAutoPoser initialized successfully
[STEP 1] Fetching next video from Cloudinary...
[*] Found X videos in Cloudinary
[+] Selected video: 1_brave_knight
[STEP 2] Generating Instagram caption...
[+] Caption: Brave Knight...
[STEP 3] Calculating posting time...
[*] Scheduled posting for 18:45 CET (~50 minutes from now)
[STEP 4] Waiting...
[STEP 5] Posting to Instagram...
[+] Published to Instagram: 12345678
[+] Logged posted video: Brave Knight
[SUCCESS] Posted 'Brave Knight' to Instagram
```

Check logs: `orchestrator/logs/instagram_auto_poster.log`

### Verify on Instagram

1. Go to your Instagram Business Account
2. Check Feed or Reels for new post
3. Verify caption is correct

---

## Claude Routines Setup (NEW)

Claude Routines is the new automation feature. Set up daily posting:

### Option 1: Using Claude Routines UI (Recommended)

1. Go to https://claude.ai/routines
2. Click "Create Routine"
3. Configure:
   - **Name:** "Daily Instagram Story Post"
   - **Schedule:** Every day at 17:55 CET
   - **Task:** Execute `python instagram_auto_poster.py` in orchestrator/
   - **Retry:** 3 times with 5-minute backoff on failure
   - **Notifications:** On success and failure

4. Click "Save Routine"

### Option 2: GitHub Auto-Sync (Optional - Recommended)

For automatic input file updates while computer is off:
1. See **orchestrator/GITHUB_SETUP.md** for complete guide
2. Enables script to update your CSV on GitHub automatically
3. Sync back to local computer with `git pull`

### Option 3: Command Line (If available)

```bash
cd orchestrator/
claude routine create --name "Daily Instagram Post" \
  --schedule "0 17:55 * * *" \
  --command "python instagram_auto_poster.py"
```

### Option 4: Manual Cron (Fallback)

If Claude Routines unavailable:

**Linux/Mac:**
```bash
# Edit crontab
crontab -e

# Add line (runs daily at 17:55 CET)
55 17 * * * cd /path/to/orchestrator && python instagram_auto_poster.py >> logs/instagram_auto_poster.log 2>&1
```

**Windows (Task Scheduler):**
1. Open Task Scheduler
2. Create Basic Task
3. Set trigger: Daily at 17:55
4. Set action: Run `python instagram_auto_poster.py` from orchestrator folder

---

## Monitoring

### Check Logs

```bash
# Real-time log tail
tail -f orchestrator/logs/instagram_auto_poster.log

# Today's posts
grep "SUCCESS" orchestrator/logs/instagram_auto_poster.log
```

### View Posted Videos

```bash
# See all posted videos
cat orchestrator/posted_videos.json
```

Example:
```json
{
  "videos": [
    {
      "numbering": 1,
      "story_name": "The Brave Knight",
      "post_id": "12345678",
      "date_posted": "2026-04-07T19:23:45.123456",
      "cloudinary_url": "https://res.cloudinary.com/..."
    }
  ]
}
```

---

## Caption Format

**Generated caption example:**

```
The Brave Knight

Stichpunkte: adventure · courage · friendship

#kindergeschichten #kinderbücher #einschlafgeschichte #gutenachtgeschichte #kindergarten #vorlesegeschichte #gutenacht #schlafen
```

**Customization:**

To change hashtags, edit in `instagram_auto_poster.py`, line ~160 in `generate_dynamic_caption()`:

```python
hashtags = "#kindergeschichten #kinderbücher #einschlafgeschichte..."
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "CLOUDINARY_CLOUD_NAME not found" | Update .env with Cloudinary credentials |
| "No videos found in Cloudinary" | Upload videos to `kindergeschichten/` folder in Cloudinary |
| "No unposted videos available" | All videos already posted, or folder empty |
| "Container creation failed: 401" | Invalid Instagram access token, refresh it |
| "Publishing failed: 400" | Video format issue - check MP4 codec, size, duration |
| Token expired | Refresh long-lived token from Meta Developer Dashboard |

### Video Requirements

Instagram requires:
- **Format:** MP4 with H.264 codec
- **Max size:** 4GB
- **Duration:** 3 seconds to 60 minutes
- **Aspect ratio:** 4:5 (portrait) or 9:16 (Reel)
- **Framerate:** 23-60 fps

---

## API Costs

**Cloudinary:**
- Free tier: 25 monthly uploads
- Paid: Variable based on storage/bandwidth

**Instagram/Meta:**
- Free: Using business access token
- No per-post charge, but account must be Meta Business verified

**OpenAI (caption generation - optional):**
- Not used by default (uses story metadata)
- Could add in future for AI captions

---

## Next Steps

1. ✅ Create Cloudinary account and organize videos
2. ✅ Create Instagram Business Account and get credentials
3. ✅ Update .env with credentials
4. ✅ Test manually: `python instagram_auto_poster.py`
5. ✅ Set up Claude Routine for daily 17:55 CET
6. ✅ Monitor first 3-5 executions
7. ✅ Adjust caption format if needed

---

## Support

**Check logs for errors:**
```bash
tail -n 50 orchestrator/logs/instagram_auto_poster.log
```

**Manual test with verbose output:**
```bash
cd orchestrator/
python -u instagram_auto_poster.py 2>&1 | tee test_output.log
```

---

## Security Notes

⚠️ **Important:**
- Never commit `.env` file to git (it contains API keys)
- Access tokens expire - set up refresh mechanism
- Long-lived tokens: ~60 days before expiration
- Refresh token: Go to Meta Developer Dashboard before expiration

---

