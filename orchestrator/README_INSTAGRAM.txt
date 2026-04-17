================================================================================
AUTOMATIC INSTAGRAM VIDEO POSTING
================================================================================

NEW FEATURE: Automatically post kindergeschichten videos to Instagram daily!

📖 SETUP GUIDE
================================================================================

See: orchestrator/INSTAGRAM_SETUP.md

This guide explains:
  - Cloudinary account setup
  - Instagram Business Account setup
  - API credentials configuration
  - Testing the script manually
  - Setting up Claude Routines for daily posting
  - Monitoring and troubleshooting

✅ IMPLEMENTATION CHECKLIST
================================================================================

See: orchestrator/INSTAGRAM_IMPLEMENTATION_CHECKLIST.md

Step-by-step checklist for:
  - Required user setup
  - Testing before running
  - Claude Routine configuration
  - Monitoring first executions

🚀 QUICK START
================================================================================

1. Fill in credentials in orchestrator/.env:
   CLOUDINARY_CLOUD_NAME=...
   CLOUDINARY_API_KEY=...
   CLOUDINARY_API_SECRET=...
   INSTAGRAM_BUSINESS_ACCOUNT_ID=...
   INSTAGRAM_ACCESS_TOKEN=...

2. Upload videos to Cloudinary:
   Folder: kindergeschichten/
   Files: 1_story_name.mp4, 2_another_story.mp4, ...

3. Test manually:
   cd orchestrator/
   python instagram_auto_poster.py

4. Set up Claude Routine:
   - Schedule: Daily at 17:55 CET
   - Task: python instagram_auto_poster.py
   - Go to: https://claude.ai/routines

✨ WHAT IT DOES
================================================================================

✓ Fetches unposted videos from Cloudinary
✓ Generates dynamic captions (story title + keywords)
✓ Posts daily at random time 18:00-20:00 CET
✓ Tracks posted videos (no duplicates)
✓ Logs all activity for monitoring
✓ Handles errors gracefully

📂 FILES CREATED
================================================================================

instagram_auto_poster.py              - Main automation script
posted_videos.json                    - Tracks posted videos
INSTAGRAM_SETUP.md                    - Complete setup guide
INSTAGRAM_IMPLEMENTATION_CHECKLIST.md - Step-by-step checklist
logs/instagram_auto_poster.log        - Daily execution logs

📝 API CREDENTIALS NEEDED
================================================================================

Cloudinary (https://cloudinary.com):
  - Cloud Name
  - API Key
  - API Secret

Instagram/Meta (https://developers.facebook.com):
  - Business Account ID
  - Long-lived Access Token (expires every ~60 days)

🧪 TESTING
================================================================================

Manual test (posts immediately):
  cd orchestrator/
  python instagram_auto_poster.py

View logs:
  tail -f orchestrator/logs/instagram_auto_poster.log

View posted videos:
  cat orchestrator/posted_videos.json

🚨 IMPORTANT
================================================================================

- Never commit .env file (contains API keys!)
- Access tokens expire every ~60 days - refresh before expiration
- Videos must be in Cloudinary: kindergeschichten/{number}_{name}.mp4
- Instagram Business Account required (not Creator Account)
- First test should be manual to verify all APIs work

📖 FULL DOCUMENTATION
================================================================================

INSTAGRAM_SETUP.md
  ├─ Cloudinary account setup
  ├─ Instagram Business Account setup
  ├─ Environment variable configuration
  ├─ Manual testing
  ├─ Claude Routine setup
  ├─ Monitoring and logs
  ├─ Caption format
  ├─ Troubleshooting
  └─ API costs and requirements

INSTAGRAM_IMPLEMENTATION_CHECKLIST.md
  ├─ Implementation status (✅ complete)
  ├─ User setup checklist (⬜ TODO)
  ├─ File structure
  ├─ Key features
  ├─ Test commands
  ├─ Important notes
  └─ Success criteria

================================================================================
Questions? Check the guides above or review instagram_auto_poster.py source.
================================================================================
