# Instagram Automation Implementation Checklist

## ✅ Implementation Complete

### Phase 1: Core Script
- [x] `instagram_auto_poster.py` created
  - [x] InstagramAutoPoser class
  - [x] `get_next_video_from_cloudinary()` - Fetches unposted videos
  - [x] `generate_dynamic_caption()` - Creates captions with story title + keywords
  - [x] `post_to_instagram()` - Two-step Instagram Graph API posting
  - [x] `log_posted_video()` - Tracks posted videos in JSON
  - [x] `run_daily_post()` - Main daily execution method
  - [x] Random time picker (18:00-20:00 CET)
  - [x] Error handling and logging

### Phase 2: Configuration
- [x] `orchestrator/.env` updated with placeholders for:
  - [x] CLOUDINARY_CLOUD_NAME
  - [x] CLOUDINARY_API_KEY
  - [x] CLOUDINARY_API_SECRET
  - [x] INSTAGRAM_BUSINESS_ACCOUNT_ID
  - [x] INSTAGRAM_ACCESS_TOKEN

### Phase 3: Dependencies
- [x] `requirements.txt` updated with `cloudinary>=1.30.0`
- [x] `posted_videos.json` created for tracking

### Phase 4: Logging
- [x] `logs/` directory created
- [x] Logging configured in instagram_auto_poster.py
- [x] Log file: `orchestrator/logs/instagram_auto_poster.log`

### Phase 5: Documentation
- [x] `INSTAGRAM_SETUP.md` - Complete setup guide
- [x] `CLAUDE.md` - Updated with Instagram info
- [x] This checklist

---

## 🔧 User Setup Required

### Before First Run:

1. **Cloudinary Setup**
   - [ ] Create Cloudinary account at https://cloudinary.com
   - [ ] Get Cloud Name, API Key, API Secret
   - [ ] Create `kindergeschichten/` folder in Cloudinary
   - [ ] Upload videos with naming: `{number}_{story_name}.mp4`

2. **Instagram Business Account Setup**
   - [ ] Have Facebook Page connected to Instagram
   - [ ] Create Meta App at https://developers.facebook.com
   - [ ] Get Instagram Business Account ID
   - [ ] Generate long-lived Access Token (expires ~60 days)

3. **Update .env**
   - [ ] Edit `orchestrator/.env`
   - [ ] Add real Cloudinary credentials
   - [ ] Add real Instagram credentials

4. **Install Dependencies**
   ```bash
   cd orchestrator/
   pip install -r requirements.txt
   ```
   - [ ] cloudinary>=1.30.0
   - [ ] requests (already installed)
   - [ ] python-dotenv (already installed)

5. **Test Manually**
   ```bash
   cd orchestrator/
   python instagram_auto_poster.py
   ```
   - [ ] Script runs without errors
   - [ ] Connects to Cloudinary
   - [ ] Selects video
   - [ ] Generates caption
   - [ ] Calculates posting time
   - [ ] Waits and posts to Instagram

6. **Verify on Instagram**
   - [ ] Check Business Account
   - [ ] New post appears
   - [ ] Caption is correct

7. **Set Up Claude Routines**
   - [ ] Go to https://claude.ai/routines
   - [ ] Create routine "Daily Instagram Story Post"
   - [ ] Schedule: Every day at 17:55 CET
   - [ ] Task: `python instagram_auto_poster.py` in orchestrator/
   - [ ] Enable retry on failure

8. **Monitor First Runs**
   - [ ] Check log: `orchestrator/logs/instagram_auto_poster.log`
   - [ ] Verify posts appear daily 18:00-20:00
   - [ ] Confirm no videos are reposted

---

## 📝 Implementation Details

### File Structure
```
orchestrator/
├── instagram_auto_poster.py        # Main script (NEW)
├── posted_videos.json              # Posted video tracker (NEW)
├── INSTAGRAM_SETUP.md              # Setup guide (NEW)
├── logs/                           # Logging directory (NEW)
│   └── instagram_auto_poster.log   # Daily logs
└── .env                            # API credentials (UPDATED)
```

### Key Features Implemented

**Cloudinary Integration:**
- Lists videos from `kindergeschichten/` folder
- Filters out already-posted videos
- Extracts story metadata from filename
- Returns random unposted video

**Instagram Graph API Integration:**
- Creates media container (Step 1)
- Publishes container (Step 2)
- Handles errors gracefully
- Returns post ID for tracking

**Caption Generation:**
- Story title + story keywords
- Hashtags: #kindergeschichten #kinderbücher #einschlafgeschichte...
- Example: "The Brave Knight\n\nStichpunkte: adventure · courage\n\n#kindergeschichten..."

**Posting Schedule:**
- Runs daily at 17:55 CET (Claude Routine trigger)
- Calculates random time 18:00-20:00 CET
- Waits until calculated time
- Posts video at random time

**Video Tracking:**
- Stores in `posted_videos.json`
- Fields: numbering, story_name, post_id, date_posted, cloudinary_url
- Prevents duplicate posting

**Error Handling:**
- Validates API credentials at startup
- Handles missing videos gracefully
- Logs all operations
- Retry mechanism available

---

## 🧪 Test Commands

**Syntax check:**
```bash
python -m py_compile instagram_auto_poster.py
```

**Manual test (will post immediately):**
```bash
cd orchestrator/
python instagram_auto_poster.py
```

**View logs:**
```bash
tail -f logs/instagram_auto_poster.log
```

**View posted videos:**
```bash
cat posted_videos.json
```

---

## 🚨 Important Notes

**Credentials:**
- Never commit `.env` to git
- Store credentials securely
- Access tokens expire every ~60 days
- Refresh token before expiration

**Video Format:**
- Must be MP4 with H.264 codec
- Max 4GB
- Duration: 3 seconds to 60 minutes
- Aspect: 4:5 (portrait) or 9:16 (Reel)

**Cloudinary:**
- Free tier: 25 monthly uploads
- Videos stored in `kindergeschichten/` folder
- Naming: `{number}_{story_name}.mp4` (important!)

**Instagram:**
- Business Account required (not Creator Account)
- Must verify Meta Business
- Long-lived token refresh mechanism available

---

## 📊 What Gets Tracked

**In posted_videos.json:**
```json
{
  "numbering": 1,
  "story_name": "The Brave Knight",
  "post_id": "12345678",
  "date_posted": "2026-04-07T19:23:45",
  "cloudinary_url": "https://res.cloudinary.com/..."
}
```

**In logs:**
- When routine executes
- Video selection from Cloudinary
- Caption generation
- Posting time calculation
- Instagram API calls
- Success/failure status
- Any errors encountered

---

## ⏰ Execution Timeline

**Daily at 17:55 CET (Claude Routine trigger):**
1. Load credentials from .env
2. Connect to Cloudinary (5-10 sec)
3. Fetch video list (3-5 sec)
4. Select random unposted video
5. Get story metadata from CSV
6. Generate caption (1 sec)
7. Calculate random time 18:00-20:00
8. **Wait** until calculated time (5-120 minutes)
9. Post to Instagram (5-10 sec)
10. Log result to JSON and file
11. Exit

**Total execution time:** Variable (depends on posting time)
- If posting at 18:00 → routine runs until ~18:05
- If posting at 19:30 → routine runs until ~19:35
- If posting at 20:00 → routine runs until ~20:05

---

## 🆘 Troubleshooting

If automatic posting fails:

1. **Check credentials:**
   ```bash
   grep CLOUDINARY orchestrator/.env
   grep INSTAGRAM orchestrator/.env
   ```

2. **Check logs:**
   ```bash
   tail -50 orchestrator/logs/instagram_auto_poster.log
   ```

3. **Test manually:**
   ```bash
   cd orchestrator/
   python instagram_auto_poster.py
   ```

4. **Verify Cloudinary:**
   - Videos in `kindergeschichten/` folder?
   - Correct filename format: `{number}_{story_name}.mp4`?

5. **Verify Instagram:**
   - Business Account verified?
   - Access token still valid (not expired)?
   - Token needs refresh every ~60 days

---

## ✨ Success Criteria

- [x] Script created and syntax valid
- [x] Dependencies added to requirements.txt
- [x] Configuration template in .env
- [x] Logging infrastructure set up
- [ ] User completes Cloudinary setup
- [ ] User completes Instagram setup
- [ ] User fills in .env credentials
- [ ] Manual test successful
- [ ] Claude Routine created
- [ ] First daily posting succeeds
- [ ] Subsequent posts continue without duplicates

---

