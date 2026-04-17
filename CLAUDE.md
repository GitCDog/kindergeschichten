# Kindergeschichten Automation

Automated pipeline for generating children's stories, audio, book covers, and Instagram Reels.
**Managed via web-based Dashboard** at `http://localhost:9000`

**→ Full documentation in `README.txt`**

## 🚀 Quick Start

### Manual Dashboard
```bash
cd orchestrator/
python dashboard_api.py
# Open http://localhost:9000
```

### Automatic Instagram Posting (GitHub Actions)
**Posts automatically every 3 days at 15:30 CET**

Setup already configured in `.github/workflows/instagram-poster.yml`:
- GitHub Actions triggers every 3 days
- Reads input file from GitHub
- Posts next unposted video to Instagram
- Updates GitHub tracking automatically
- Deletes video from Cloudinary after posting

Credentials stored in **GitHub Secrets** (not .env)

## 🚨 CRITICAL RULES (NON-NEGOTIABLE)

### 1️⃣ FILE LOCATIONS ARE IMMUTABLE
```
During generation → output/ folder
After video creation → JSON & Audio auto-move to 1_insta_post_X/
After user posts → Video moves to 1_insta_post_X/
Video NEVER moved automatically - only when user clicks "Post"
```

### 2️⃣ VIDEO WORKFLOW SEQUENCE
```
1. Generate video → saves to output/{numbering}_{story_name}_video.mp4
2. Auto-move JSON → 1_insta_post_X/
3. Auto-move Audio → 1_insta_post_X/
4. Video stays in output/ (waiting for Post button)
5. Click Post → video moves to 1_insta_post_X/
```

### 3️⃣ CSV STRUCTURE IS LOCKED
- **Always 14 columns** - never add/remove/rename columns
- **First 5 columns:** numbering, keyword1, keyword2, keyword3, story_name
- **Status columns:** status_story, status_story_json, status_audio, status_picture, status_video, status_caption
- **Metadata columns:** words, seconds, insta_post
- Status codes: `X`=done, `O`=pending

### 4️⃣ STATUS UPDATES ARE CRITICAL
Every script must update the CSV after generating files:
- After video generation → auto-archive JSON & audio
- After user clicks Post → move video
- Always update status fields (`X` = processed, `O` = pending)

### 5️⃣ API KEYS REQUIRED

**Dashboard (.env file locally):**
```bash
OPENAI_API_KEY=sk-...                    # GPT Image (book covers)
ELEVENLABS_API_KEY=sk_...                # ElevenLabs TTS (audio)
```

**Automatic Instagram (GitHub Secrets - cloud only):**
```
CLOUDINARY_CLOUD_NAME=...                # Cloudinary account
CLOUDINARY_API_KEY=...
CLOUDINARY_API_SECRET=...
INSTAGRAM_RECIPIENT_ID=...               # Instagram Business Account ID
INSTAGRAM_ACCESS_TOKEN=...               # Long-lived access token
GITHUB_TOKEN=...                         # for GitHub API access
GITHUB_REPO=...                          # your-org/your-repo
```
**Note:** Credentials set in GitHub Settings → Secrets, not in local .env

## 📊 Dashboard Buttons
| Button | Script | Does |
|--------|--------|------|
| 🔄 Scan | `detect_register_generate.py` | Auto-detect new stories |
| 📝 Word Count & JSON | `word_count_and_json.py` | Create JSON metadata |
| 🎵 Generate Audio | `audio_generator.py` | Create MP3 with TTS |
| 🖼️ Generate Pics | `generate_pictures.py` | Create PNG book covers |
| 🎬 Generate Videos | `generate_videos_with_audio.py` | Create MP4, auto-archive JSON & audio |
| ✓ Post | `dashboard_api.py` | Move video to 1_insta_post_X/ |

## 📁 Folder Structure
```
orchestrator/
├── input/              (0_input_all_stories.txt + story .txt files)
├── output/             (generated .json, .mp3, .mp4 files)
│   └── 1_insta_post_X/ (archived files after posting)
├── images/             (AI-generated .png book covers)
├── dashboard.html      (web interface)
└── dashboard_api.py    (HTTP server on port 9000)
```

## 📖 Additional Documentation

**Manual Dashboard Generation:**
- README.txt - Complete story lifecycle, API docs, troubleshooting

**Automatic Instagram Posting:**
- orchestrator/INSTAGRAM_SETUP.md - Full setup and configuration guide
