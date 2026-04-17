#!/usr/bin/env python3
"""Generate dashboard HTML with embedded data."""

import json
from pathlib import Path

# Read JSON data
with open('dashboard_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Total stories from input file
total_stories = len(data)

# Calculate stats
text_done = sum(1 for r in data if r['status_story'] == 'X')
json_done = sum(1 for r in data if r['status_story_json'] == 'X')
audio_done = sum(1 for r in data if r['status_audio'] == 'X')
pictures_done = sum(1 for r in data if r['status_picture'] == 'X')
video_done = sum(1 for r in data if r['status_video'] == 'X')
posted_done = sum(1 for r in data if r['insta_post'] == 'X')

total_done = text_done + json_done + audio_done + video_done
percent = round((total_done / (len(data) * 4)) * 100)

# Build table rows
rows_html = ""
for row in data:
    def get_checkmark(status):
        return "✓" if status == 'X' else "○"

    def get_color(status):
        return 'color: #28a745;' if status == 'X' else 'color: #ccc;'

    insta_active = 'active' if row['insta_post'] == 'X' else ''
    insta_label = "✓ Posted" if row['insta_post'] == 'X' else "Post"

    rows_html += f"""                    <tr>
                        <td class="num">{row['numbering']}</td>
                        <td class="name">{row['story_name']}</td>
                        <td class="keywords">{row['keyword1']}, {row['keyword2']}, {row['keyword3']}</td>
                        <td class="status-cell" style="{get_color(row['status_story'])}">{get_checkmark(row['status_story'])}</td>
                        <td class="center">{row['words']}</td>
                        <td class="status-cell" style="{get_color(row['status_story_json'])}">{get_checkmark(row['status_story_json'])}</td>
                        <td class="status-cell" style="{get_color(row['status_audio'])}">{get_checkmark(row['status_audio'])}</td>
                        <td class="center">{row['seconds']}</td>
                        <td class="status-cell" style="{get_color(row['status_picture'])}">{get_checkmark(row['status_picture'])}</td>
                        <td class="status-cell" style="{get_color(row['status_video'])}">{get_checkmark(row['status_video'])}</td>
                        <td class="status-cell" style="{get_color(row['status_caption'])}">{get_checkmark(row['status_caption'])}</td>
                        <td class="center"><button class="insta-button {insta_active}" data-story="{row['story_name']}" onclick="toggleInstaPost(this)" {'' if row['status_video'] == 'X' else 'disabled'}>{insta_label}</button></td>
                    </tr>
"""

html_template = f'''<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kindergeschichten Dashboard</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}

        .container {{
            max-width: 1600px;
            margin: 0 auto;
        }}

        .header {{
            background: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}

        h1 {{
            color: #333;
            margin-bottom: 10px;
            font-size: 28px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 20px;
        }}

        .refresh-btn {{
            background: #667eea;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            transition: all 0.3s ease;
        }}

        .refresh-btn:hover {{
            background: #5568d3;
            transform: scale(1.05);
        }}

        .refresh-btn:active {{
            transform: scale(0.95);
        }}

        .refresh-btn.scanning {{
            opacity: 0.7;
            cursor: not-allowed;
        }}

        .scan-progress {{
            display: none;
            margin-top: 20px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
        }}

        .scan-progress.visible {{
            display: block;
        }}

        .progress-bar-scan {{
            background: #e9ecef;
            border-radius: 4px;
            height: 30px;
            overflow: hidden;
            margin: 10px 0;
        }}

        .progress-fill-scan {{
            background: linear-gradient(90deg, #667eea, #764ba2);
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            transition: width 0.3s ease;
            width: 0%;
        }}

        .scan-message {{
            font-size: 14px;
            color: #666;
            margin-top: 10px;
            text-align: center;
        }}

        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }}

        .stat-box {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }}

        .stat-box h3 {{
            font-size: 11px;
            color: #666;
            margin-bottom: 8px;
            text-transform: uppercase;
            font-weight: 600;
        }}

        .stat-box .value {{
            font-size: 28px;
            font-weight: bold;
            color: #28a745;
        }}

        .progress-section {{
            margin-top: 20px;
        }}

        .progress-bar {{
            background: #e9ecef;
            border-radius: 4px;
            height: 30px;
            overflow: hidden;
            display: flex;
            align-items: center;
            margin-top: 10px;
        }}

        .progress-fill {{
            background: linear-gradient(90deg, #28a745, #20c997);
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            width: {percent}%;
        }}

        .table-container {{
            background: white;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            overflow: hidden;
            height: 750px;
            display: flex;
            flex-direction: column;
        }}

        .table-scroll {{
            overflow-y: auto;
            flex: 1;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
        }}

        thead {{
            background: #667eea;
            color: white;
            position: sticky;
            top: 0;
            z-index: 10;
        }}

        th {{
            padding: 12px 8px;
            text-align: left;
            font-weight: 600;
            white-space: nowrap;
        }}

        td {{
            padding: 10px 8px;
            border-bottom: 1px solid #eee;
        }}

        tr:hover {{
            background: #f8f9fa;
        }}

        .num {{
            font-weight: bold;
            color: #667eea;
            width: 35px;
            text-align: center;
        }}

        .name {{
            min-width: 250px;
            font-weight: 500;
        }}

        .keywords {{
            min-width: 200px;
            font-size: 12px;
            color: #666;
        }}

        .status-cell {{
            text-align: center;
            width: 35px;
            font-size: 18px;
            font-weight: bold;
        }}

        .insta-button {{
            background: #e9ecef;
            border: none;
            padding: 6px 12px;
            border-radius: 4px;
            cursor: pointer;
            font-weight: bold;
            transition: all 0.3s ease;
            color: #666;
        }}

        .insta-button:hover {{
            background: #dee2e6;
        }}

        .insta-button.active {{
            background: #28a745;
            color: white;
        }}

        .insta-button:disabled {{
            opacity: 0.6;
            cursor: not-allowed;
        }}

        .center {{
            text-align: center;
        }}

        ::-webkit-scrollbar {{
            width: 8px;
        }}

        ::-webkit-scrollbar-track {{
            background: #f1f1f1;
        }}

        ::-webkit-scrollbar-thumb {{
            background: #667eea;
            border-radius: 4px;
        }}

        ::-webkit-scrollbar-thumb:hover {{
            background: #555;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>
                <span>📚 Kindergeschichten Automation Dashboard</span>
                <div style="display: flex; gap: 10px;">
                    <button class="refresh-btn" onclick="scanForNewFiles()" id="scanBtn">🔄 Scan for New Files</button>
                    <button class="refresh-btn" onclick="wordCountAndJson()" id="wordBtn">📝 Word Count & JSON</button>
                    <button class="refresh-btn" onclick="generateAudio()" id="audioBtn">🎵 Generate Audio</button>
                    <button class="refresh-btn" onclick="generatePictures()" id="picBtn">🖼️ Generate Pics</button>
                    <button class="refresh-btn" onclick="generateVideo()" id="videoBtn">🎬 Generate Videos</button>
                </div>
            </h1>
            <div class="stats">
                <div class="stat-box">
                    <h3>Total Stories</h3>
                    <div class="value">{total_stories}</div>
                </div>
                <div class="stat-box">
                    <h3>Text Files ✓</h3>
                    <div class="value">{text_done}/99</div>
                </div>
                <div class="stat-box">
                    <h3>JSON Files ✓</h3>
                    <div class="value">{json_done}/99</div>
                </div>
                <div class="stat-box">
                    <h3>Audio Files ✓</h3>
                    <div class="value">{audio_done}/99</div>
                </div>
                <div class="stat-box">
                    <h3>Pictures ✓</h3>
                    <div class="value">{pictures_done}/99</div>
                </div>
                <div class="stat-box">
                    <h3>Video Files ✓</h3>
                    <div class="value">{video_done}/99</div>
                </div>
                <div class="stat-box">
                    <h3>Posted ✓</h3>
                    <div class="value">{posted_done}/99</div>
                </div>
            </div>
            <div class="progress-section">
                <h3>Overall Progress ({percent}%)</h3>
                <div class="progress-bar">
                    <div class="progress-fill">{percent}%</div>
                </div>
            </div>

            <div style="margin-top: 20px; padding: 15px; background: #f8f9fa; border-radius: 8px; display: none;" id="picInputDiv">
                <label style="display: block; margin-bottom: 10px; font-weight: 600;">Enter Story Numbers:</label>
                <input type="text" id="picStoryInput" placeholder="e.g., 49 or 55-60" style="width: 200px; padding: 8px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px;">
                <button onclick="startGeneratePictures()" style="margin-left: 10px; padding: 8px 15px; background: #667eea; color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: bold;">Generate</button>
            </div>

            <div class="scan-progress" id="scanProgress">
                <h3>Scanning for New Files</h3>
                <div class="progress-bar-scan">
                    <div class="progress-fill-scan" id="scanProgressBar">0%</div>
                </div>
                <div class="scan-message" id="scanMessage">Starting...</div>
            </div>
        </div>

        <div class="table-container">
            <div class="table-scroll">
                <table>
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>Story Name</th>
                            <th>Keywords</th>
                            <th title="Text File">Text</th>
                            <th>Words</th>
                            <th title="JSON">JSON</th>
                            <th title="Audio">Audio</th>
                            <th>Sec</th>
                            <th title="Picture">Pic</th>
                            <th title="Video">Video</th>
                            <th title="Caption">Cap</th>
                            <th title="Posted">Post</th>
                        </tr>
                    </thead>
                    <tbody>
{rows_html}                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
        async function toggleInstaPost(button) {{
            if (button.classList.contains('active')) {{
                return;
            }}

            const storyName = button.getAttribute('data-story');
            button.disabled = true;
            button.textContent = 'Updating...';

            try {{
                const response = await fetch('/api/update-insta-post', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{story_name: storyName}})
                }});

                const result = await response.json();

                if (response.ok && result.success) {{
                    button.classList.add('active');
                    button.textContent = '✓ Posted';
                }} else {{
                    button.textContent = 'Error';
                    button.disabled = false;
                    setTimeout(() => button.textContent = 'Post', 2000);
                }}
            }} catch (error) {{
                console.error('Error:', error);
                button.textContent = 'Failed';
                button.disabled = false;
                setTimeout(() => button.textContent = 'Post', 2000);
            }}
        }}

        let progressInterval = null;

        async function scanForNewFiles() {{
            const btn = document.getElementById('scanBtn');
            const progressDiv = document.getElementById('scanProgress');

            btn.classList.add('scanning');
            btn.disabled = true;
            btn.textContent = '⏳ Scanning...';
            progressDiv.classList.add('visible');

            try {{
                const response = await fetch('/api/scan-new-files', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}}
                }});

                if (response.ok) {{
                    // Start polling for progress
                    pollScanProgress(btn, progressDiv);
                }} else {{
                    btn.textContent = '🔄 Scan for New Files';
                    btn.disabled = false;
                    btn.classList.remove('scanning');
                    progressDiv.classList.remove('visible');
                }}
            }} catch (error) {{
                console.error('Error:', error);
                btn.textContent = '🔄 Scan for New Files';
                btn.disabled = false;
                btn.classList.remove('scanning');
                progressDiv.classList.remove('visible');
            }}
        }}

        async function pollScanProgress(btn, progressDiv) {{
            progressInterval = setInterval(async () => {{
                try {{
                    const response = await fetch('/api/scan-progress');
                    const progress = await response.json();

                    const progressBar = document.getElementById('scanProgressBar');
                    const message = document.getElementById('scanMessage');

                    progressBar.style.width = progress.percent + '%';
                    progressBar.textContent = progress.percent + '%';
                    message.textContent = progress.message;

                    if (progress.status === 'complete' || progress.status === 'error') {{
                        clearInterval(progressInterval);

                        if (progress.status === 'complete') {{
                            btn.textContent = '✓ Done! Refreshing...';
                            setTimeout(() => location.reload(), 2000);
                        }} else {{
                            btn.textContent = '🔄 Scan for New Files';
                            btn.disabled = false;
                            btn.classList.remove('scanning');
                            setTimeout(() => progressDiv.classList.remove('visible'), 2000);
                        }}
                    }}
                }} catch (error) {{
                    console.error('Error polling progress:', error);
                }}
            }}, 300);
        }}

        async function wordCountAndJson() {{
            const btn = document.getElementById('wordBtn');
            const progressDiv = document.getElementById('scanProgress');

            btn.classList.add('scanning');
            btn.disabled = true;
            btn.textContent = '⏳ Processing...';
            progressDiv.classList.add('visible');

            try {{
                const response = await fetch('/api/word-count-json', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}}
                }});

                if (response.ok) {{
                    pollWordCountProgress(btn, progressDiv);
                }} else {{
                    btn.textContent = '📝 Word Count & JSON';
                    btn.disabled = false;
                    btn.classList.remove('scanning');
                    progressDiv.classList.remove('visible');
                }}
            }} catch (error) {{
                console.error('Error:', error);
                btn.textContent = '📝 Word Count & JSON';
                btn.disabled = false;
                btn.classList.remove('scanning');
                progressDiv.classList.remove('visible');
            }}
        }}

        async function pollWordCountProgress(btn, progressDiv) {{
            let pollInterval = setInterval(async () => {{
                try {{
                    const response = await fetch('/api/word-count-progress');
                    const progress = await response.json();

                    const progressBar = document.getElementById('scanProgressBar');
                    const message = document.getElementById('scanMessage');

                    progressBar.style.width = progress.percent + '%';
                    progressBar.textContent = progress.percent + '%';
                    message.textContent = progress.message;

                    if (progress.status === 'complete' || progress.status === 'error') {{
                        clearInterval(pollInterval);

                        if (progress.status === 'complete') {{
                            btn.textContent = '✓ Done! Refreshing...';
                            setTimeout(() => location.reload(), 2000);
                        }} else {{
                            btn.textContent = '📝 Word Count & JSON';
                            btn.disabled = false;
                            btn.classList.remove('scanning');
                            setTimeout(() => progressDiv.classList.remove('visible'), 2000);
                        }}
                    }}
                }} catch (error) {{
                    console.error('Error polling:', error);
                }}
            }}, 300);
        }}

        async function generateAudio() {{
            const btn = document.getElementById('audioBtn');
            const progressDiv = document.getElementById('scanProgress');

            btn.classList.add('scanning');
            btn.disabled = true;
            btn.textContent = '⏳ Processing...';
            progressDiv.classList.add('visible');

            try {{
                const response = await fetch('/api/audio-generation', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}}
                }});

                if (response.ok) {{
                    pollAudioProgress(btn, progressDiv);
                }} else {{
                    btn.textContent = '🎵 Generate Audio';
                    btn.disabled = false;
                    btn.classList.remove('scanning');
                    progressDiv.classList.remove('visible');
                }}
            }} catch (error) {{
                console.error('Error:', error);
                btn.textContent = '🎵 Generate Audio';
                btn.disabled = false;
                btn.classList.remove('scanning');
                progressDiv.classList.remove('visible');
            }}
        }}

        async function pollAudioProgress(btn, progressDiv) {{
            let pollInterval = setInterval(async () => {{
                try {{
                    const response = await fetch('/api/audio-progress');
                    const progress = await response.json();

                    const progressBar = document.getElementById('scanProgressBar');
                    const message = document.getElementById('scanMessage');

                    progressBar.style.width = progress.percent + '%';
                    progressBar.textContent = progress.percent + '%';
                    message.textContent = progress.message;

                    if (progress.status === 'complete' || progress.status === 'error') {{
                        clearInterval(pollInterval);

                        if (progress.status === 'complete') {{
                            btn.textContent = '✓ Done! Refreshing...';
                            setTimeout(() => location.reload(), 2000);
                        }} else {{
                            btn.textContent = '🎵 Generate Audio';
                            btn.disabled = false;
                            btn.classList.remove('scanning');
                            setTimeout(() => progressDiv.classList.remove('visible'), 2000);
                        }}
                    }}
                }} catch (error) {{
                    console.error('Error polling:', error);
                }}
            }}, 300);
        }}

        async function generatePictures() {{
            const picInputDiv = document.getElementById('picInputDiv');
            if (picInputDiv.style.display === 'none' || picInputDiv.style.display === '') {{
                picInputDiv.style.display = 'block';
                document.getElementById('picStoryInput').focus();
            }} else {{
                picInputDiv.style.display = 'none';
            }}
        }}

        async function startGeneratePictures() {{
            const inputField = document.getElementById('picStoryInput');
            const storyInput = inputField.value.trim();

            if (!storyInput) {{
                alert('Please enter a story number or range (e.g., "49" or "55-60")');
                return;
            }}

            const btn = document.getElementById('picBtn');
            const progressDiv = document.getElementById('scanProgress');

            btn.classList.add('scanning');
            btn.disabled = true;
            btn.textContent = '⏳ Generating...';
            progressDiv.classList.add('visible');
            document.getElementById('picInputDiv').style.display = 'none';

            try {{
                const response = await fetch('/api/generate-pictures', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{story_input: storyInput}})
                }});

                if (response.ok) {{
                    pollPicProgress(btn, progressDiv, storyInput);
                }} else {{
                    btn.textContent = '🖼️ Generate Pics';
                    btn.disabled = false;
                    btn.classList.remove('scanning');
                    progressDiv.classList.remove('visible');
                    document.getElementById('picInputDiv').style.display = 'block';
                }}
            }} catch (error) {{
                console.error('Error:', error);
                btn.textContent = '🖼️ Generate Pics';
                btn.disabled = false;
                btn.classList.remove('scanning');
                progressDiv.classList.remove('visible');
                document.getElementById('picInputDiv').style.display = 'block';
            }}
        }}

        async function pollPicProgress(btn, progressDiv, storyInput) {{
            let pollInterval = setInterval(async () => {{
                try {{
                    const response = await fetch('/api/pic-progress');
                    const progress = await response.json();

                    const progressBar = document.getElementById('scanProgressBar');
                    const message = document.getElementById('scanMessage');

                    progressBar.style.width = progress.percent + '%';
                    progressBar.textContent = progress.percent + '%';
                    message.textContent = progress.message;

                    if (progress.status === 'complete' || progress.status === 'error') {{
                        clearInterval(pollInterval);

                        if (progress.status === 'complete') {{
                            btn.textContent = '✓ Done! Refreshing...';
                            setTimeout(() => location.reload(), 2000);
                        }} else {{
                            btn.textContent = '🖼️ Generate Pics';
                            btn.disabled = false;
                            btn.classList.remove('scanning');
                            document.getElementById('picInputDiv').style.display = 'block';
                            setTimeout(() => progressDiv.classList.remove('visible'), 2000);
                        }}
                    }}
                }} catch (error) {{
                    console.error('Error polling:', error);
                }}
            }}, 300);
        }}

        async function generateVideo() {{
            const btn = document.getElementById('videoBtn');
            const progressDiv = document.getElementById('scanProgress');

            btn.classList.add('scanning');
            btn.disabled = true;
            btn.textContent = '⏳ Processing...';
            progressDiv.classList.add('visible');

            try {{
                const response = await fetch('/api/video-generation', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}}
                }});

                if (response.ok) {{
                    pollVideoProgress(btn, progressDiv);
                }} else {{
                    btn.textContent = '🎬 Generate Videos';
                    btn.disabled = false;
                    btn.classList.remove('scanning');
                    progressDiv.classList.remove('visible');
                }}
            }} catch (error) {{
                console.error('Error:', error);
                btn.textContent = '🎬 Generate Videos';
                btn.disabled = false;
                btn.classList.remove('scanning');
                progressDiv.classList.remove('visible');
            }}
        }}

        async function pollVideoProgress(btn, progressDiv) {{
            let pollInterval = setInterval(async () => {{
                try {{
                    const response = await fetch('/api/video-progress');
                    const progress = await response.json();

                    const progressBar = document.getElementById('scanProgressBar');
                    const message = document.getElementById('scanMessage');

                    progressBar.style.width = progress.percent + '%';
                    progressBar.textContent = progress.percent + '%';
                    message.textContent = progress.message;

                    if (progress.status === 'complete' || progress.status === 'error') {{
                        clearInterval(pollInterval);

                        if (progress.status === 'complete') {{
                            btn.textContent = '✓ Done! Refreshing...';
                            setTimeout(() => location.reload(), 2000);
                        }} else {{
                            btn.textContent = '🎬 Generate Videos';
                            btn.disabled = false;
                            btn.classList.remove('scanning');
                            setTimeout(() => progressDiv.classList.remove('visible'), 2000);
                        }}
                    }}
                }} catch (error) {{
                    console.error('Error polling:', error);
                }}
            }}, 300);
        }}
    </script>
</body>
</html>'''

with open('dashboard.html', 'w', encoding='utf-8') as f:
    f.write(html_template)

print("[+] Dashboard generated successfully!")
print(f"[+] Text: {text_done}/99 | JSON: {json_done}/99 | Audio: {audio_done}/99 | Pictures: {pictures_done}/99 | Video: {video_done}/99 | Posted: {posted_done}/99")
print(f"[+] Overall Progress: {percent}%")
print(f"[+] Open: dashboard.html")
