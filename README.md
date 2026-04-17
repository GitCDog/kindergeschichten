================================================================================
KINDERGESCHICHTEN AUTOMATION - COMPLETE DOCUMENTATION
================================================================================

This file contains the full technical documentation. See CLAUDE.md for
critical rules that override everything below.

================================================================================
PROJECT OVERVIEW
================================================================================

Automated pipeline for generating children's stories, converting to audio
with professional voices, creating AI-generated book covers, making Instagram
Reels, and publishing them.

The workflow is managed through a web-based dashboard at http://localhost:9000

================================================================================
COMPLETE STORY LIFECYCLE (7 PHASES)
================================================================================

PHASE 1: Story Created
━━━━━━━━━━━━━━━━━━━━━━━━
User adds row to 0_input_all_stories.txt with keywords:
  50,magic,forest,adventure,The Enchanted Forest,O,O,O,O,O,O,0,0,O

PHASE 2: Scan for New Files (🔄 Button)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Script: detect_register_generate.py
- Detects if story file exists in input/50_*.txt
- Auto-generates story name if missing
- Updates dashboard

PHASE 3: Word Count & JSON (📝 Button)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Script: word_count_and_json.py
- Reads story text from input/{numbering}_{story_name}.txt
- Validates word count (350-400 words)
- Generates output/{numbering}_{story_name}.json
- Updates status_story_json=X, words column

PHASE 4: Generate Audio (🎵 Button)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Script: audio_generator.py
- Reads story text
- Sends to ElevenLabs API (voice: tomasz_z)
- Creates output/{numbering}_{story_name}.mp3
- Extracts duration with ffprobe
- Updates status_audio=X, seconds column

PHASE 5: Generate Pictures (🖼️ Button)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Script: generate_pictures.py
- User enters: "49" or "55-60"
- Sends to OpenAI GPT Image API
- Generates images/{numbering}.png (1024x1536)
- Updates status_picture=X

PHASE 6: Generate Videos (🎬 Button)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Script: generate_videos_with_audio.py
- Requires: status_audio=X, status_picture=X, status_video=O
- Creates output/{numbering}_{story_name}_video.mp4 with ffmpeg
- AUTOMATICALLY archives:
  * output/{numbering}_{story_name}.json → 1_insta_post_X/
  * output/{numbering}_{story_name}.mp3 → 1_insta_post_X/
- Keeps video in output/
- Updates status_video=X

PHASE 7: Post to Instagram (Post Button)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Handler: dashboard_api.py handle_insta_post_update()
- User clicks "Post" on dashboard
- Sets insta_post=X
- Moves video to 1_insta_post_X/
- All files now in 1_insta_post_X/ (ready for upload)

================================================================================
DETAILED API INTEGRATION
================================================================================

OPENAI GPT IMAGE API (Book Covers)
═══════════════════════════════════

File: orchestrator/generate_pictures.py

Endpoint: https://api.openai.com/v1/images/generations

Request Payload:
{
  "model": "gpt-image-1",
  "prompt": "Create a creative Instagram image for kid bedtime stories...",
  "size": "1024x1536",              # Vertical Instagram format
  "quality": "medium",               # low/medium/high
  "n": 1                             # Images per request
}

Terminal Logging:
[API REQUEST]
  URL: https://api.openai.com/v1/images/generations
  Model: gpt-image-1
  Size: 1024x1536
  Quality: medium
  Prompt: [first 100 chars of prompt]...
  Auth: Bearer sk-...

Output: images/{numbering}.png (1024x1536 pixels)
Cost: ~$0.04-0.08 per image (depends on quality)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ELEVENLABS TTS API (Audio Generation)
═════════════════════════════════════

File: orchestrator/audio_generator.py

Voice Preset: tomasz_z (Expressive & Deep)

Other Available Voices:
- friendly_child (warm young female)
- storyteller (classic narrator)
- playful (fun & energetic)

Process:
1. Reads story text from input/{numbering}_{story_name}.txt
2. Calls tts.generate_audio(text, voice_preset="tomasz_z")
3. Saves to output/{numbering}_{story_name}.mp3
4. Extracts duration with ffprobe
5. Updates seconds column in input file

Output: output/{numbering}_{story_name}.mp3
Cost: ~$0.30 per 1M characters (~$0.01-0.05 per story)

================================================================================
FILE NAMING CONVENTIONS
================================================================================

Input File: 0_input_all_stories.txt

14-column CSV:
numbering,keyword1,keyword2,keyword3,story_name,status_story,status_story_json,status_audio,status_picture,status_video,status_caption,words,seconds,insta_post

Example:
50,magic,forest,adventure,The Enchanted Forest,X,X,X,X,X,O,385,210,O

Columns:
1.  numbering          (1-99)
2.  keyword1           (user-supplied)
3.  keyword2           (user-supplied)
4.  keyword3           (user-supplied)
5.  story_name         (auto-generated or user-supplied)
6.  status_story       (story text file exists: X/O)
7.  status_story_json  (JSON metadata generated: X/O)
8.  status_audio       (MP3 audio file: X/O)
9.  status_picture     (PNG book cover: X/O)
10. status_video       (MP4 video file: X/O)
11. status_caption     (caption text created: X/O)
12. words              (word count, target: 350-400)
13. seconds            (audio duration in seconds)
14. insta_post         (posted to Instagram: X/O)

Status Codes:
X = Processed/Completed ✓
O = Pending/Waiting ○

Output Files:
- Story text: input/{numbering}_{story_name}.txt
- JSON metadata: output/{numbering}_{story_name}.json
- Audio: output/{numbering}_{story_name}.mp3
- Video: output/{numbering}_{story_name}_video.mp4

================================================================================
CONFIGURATION
================================================================================

Environment Variables (.env):
OPENAI_API_KEY=sk-...                   # OpenAI GPT Image
ELEVENLABS_API_KEY=sk_...               # ElevenLabs TTS
ANTHROPIC_API_KEY=sk-ant-...            # Legacy (not used)

config.yaml:
story_generation:
  generator_type: "claude"              # Story generation (legacy)
  target_duration_seconds: 300

text_to_speech:
  voice_preset: "tomasz_z"              # Current voice

video_creation:
  width: 1080
  height: 1920                          # Vertical Instagram Reel
  fps: 24
  bitrate: "2000k"

================================================================================
TROUBLESHOOTING
================================================================================

Server Not Starting
═══════════════════
$ netstat -an | grep 9000
$ taskkill /F /IM python.exe
$ cd orchestrator && python dashboard_api.py

Files Not Generating
════════════════════
✓ Check API keys in .env
✓ Check terminal output for error messages
✓ Verify source files exist (story text, images, etc.)
✓ Check status fields (can't generate audio without status_story_json=X)

Videos Not Created
══════════════════
Requirements:
  status_audio=X         (audio file exists)
  status_picture=X       (image file exists)
  status_video=O         (not yet generated)

Verify:
✓ images/{numbering}.png exists
✓ ffmpeg installed: ffmpeg -version
✓ ffmpeg path correct: C:\ffmpeg\bin\ffmpeg.exe

Picture Generation Failing
═══════════════════════════
✓ OPENAI_API_KEY is valid
✓ Check OpenAI quota/billing
✓ images/ directory exists
✓ API endpoint correct: https://api.openai.com/v1/images/generations

Audio Generation Failing
════════════════════════
✓ ELEVENLABS_API_KEY is valid
✓ Check ElevenLabs quota
✓ output/ directory exists
✓ Voice preset correct: tomasz_z (case-sensitive)

Performance Metrics
═══════════════════
Typical generation times per story:
- Picture generation: 20-60 seconds
- Audio generation: 10-30 seconds
- Video creation: 5-15 seconds
- JSON generation: <1 second

Total pipeline: ~2-3 minutes per story

================================================================================
DASHBOARD STATISTICS
================================================================================

Real-time Display:
TOTAL STORIES: 99
├─ Text Files ✓:    99/99
├─ JSON Files ✓:    95/99
├─ Audio Files ✓:   99/99
├─ Pictures ✓:      59/99
├─ Video Files ✓:   48/99
├─ Posted ✓:        11/99
└─ Overall Progress: 86%

Progress Bars:
- Green bar shows workflow progression
- Updates automatically after each button action
- Shows current operation and percentage

================================================================================
STORY TEXT REQUIREMENTS
================================================================================

Stories should include:

Word Count: 350-400 words
- Validated in "Word Count & JSON" step
- Too short/long stories are rejected

Narrative Voice:
- Warm, gentle, intimate
- Old grandpa telling bedtime story to grandkids

Style:
- Include bracketed narration cues [tone], [action], [pause]
- Cozy, dreamy atmosphere
- Suitable for ages 3-6

Bracketed Cue Types:
- Tone: [softly], [sarcastically], [with excitement], [whispering]
- Action: [sighs], [gasps], [giggles], [paces], [shivers]
- Pacing: [beat], [pause], [suddenly], [long moment]

Example:
"The dragon landed with a BOOM. [deep breath] I'd never seen anything so big.
[steps back] 'Hello there, little friend,' it said kindly. [surprisingly gentle voice]
'I'm not here to hurt you. I'm just a lonely old dragon.'"

================================================================================
DATA FLOW
================================================================================

Input CSV → JSON Cache → HTML Dashboard → Browser

0_input_all_stories.txt (user edits)
    ↓
InputFileManager (reads/validates CSV)
    ↓
dashboard_data.json (cached for dashboard)
    ↓
generate_dashboard.py (converts to HTML)
    ↓
dashboard.html (displayed at http://localhost:9000)

Important: Always edit 0_input_all_stories.txt directly.
Dashboard data regenerates automatically when scripts update the CSV.

================================================================================
ARCHIVE STRATEGY
================================================================================

After video generation:

output/
├── {numbering}_{story_name}_video.mp4      (stays here)
│
1_insta_post_X/
├── {numbering}_{story_name}.json           (moved during video generation)
├── {numbering}_{story_name}.mp3            (moved during video generation)
└── {numbering}_{story_name}_video.mp4      (moved when user clicks "Post")

Purpose:
- Working files stay in output/
- Published files move to 1_insta_post_X/
- Clear separation prevents overwrites

================================================================================
CORE SCRIPTS
================================================================================

dashboard_api.py
  Web server (HTTP, port 9000)
  Handles all button clicks
  Manages progress tracking
  Backend for dashboard

generate_dashboard.py
  Generates dashboard.html from CSV data
  Displays statistics and story table
  Called automatically when data changes

generate_pictures.py
  OpenAI GPT Image API integration
  Input: story numbers or ranges (e.g., "49" or "55-60")
  Output: PNG book covers in images/

audio_generator.py
  ElevenLabs TTS integration
  Converts story text to MP3
  Extracts audio duration

generate_videos_with_audio.py
  ffmpeg video creation
  Combines image + audio → MP4
  Auto-archives JSON & audio
  Keeps video in output/

input_file_manager.py
  CSV read/write operations
  Syncs with dashboard_data.json
  Status field updates

word_count_and_json.py
  Word count validation
  JSON metadata generation
  Validates 350-400 word range

detect_register_generate.py
  Auto-detects new story files
  Registers in input file
  Generates story names

================================================================================
GETTING STARTED
================================================================================

1. Start Dashboard Server
   $ cd orchestrator/
   $ python dashboard_api.py

2. Open Browser
   http://localhost:9000

3. Add Stories (Optional)
   Edit 0_input_all_stories.txt manually or use dashboard buttons

4. Process Stories
   Click buttons in order:
   🔄 → 📝 → 🎵 → 🖼️ → 🎬 → ✓

================================================================================
VERSION HISTORY
================================================================================

2026-04-07: Split documentation
- CLAUDE.md: Critical rules only (~90 lines)
- README.txt: Full documentation (this file)

================================================================================
