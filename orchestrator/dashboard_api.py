#!/usr/bin/env python3
"""
Dashboard Server - Serves dashboard.html and handles button clicks.
Open: http://localhost:8000
"""

import json
import logging
import threading
import os
from dotenv import load_dotenv
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from input_file_manager import InputFileManager

# Load .env file
load_dotenv()


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Global progress tracking
scan_progress = {"status": "idle", "percent": 0, "message": ""}
word_count_progress = {"status": "idle", "percent": 0, "message": ""}
audio_progress = {"status": "idle", "percent": 0, "message": ""}
video_progress = {"status": "idle", "percent": 0, "message": ""}
pic_progress = {"status": "idle", "percent": 0, "message": ""}


class DashboardHandler(BaseHTTPRequestHandler):
    """Handle HTTP requests."""

    def log_message(self, format, *args):
        """Print all requests to console."""
        print(f"[HTTP] {format % args}", flush=True)

    def do_GET(self):
        """Serve dashboard.html on GET requests."""
        if self.path in ['/', '/dashboard.html']:
            try:
                with open('dashboard.html', 'r', encoding='utf-8') as f:
                    content = f.read()

                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Content-Length', str(len(content.encode('utf-8'))))
                self.end_headers()
                self.wfile.write(content.encode('utf-8'))
                return
            except FileNotFoundError:
                self.send_error(404, 'dashboard.html not found')
                return

        elif self.path == '/api/scan-progress':
            self.send_json(200, scan_progress)
            return

        elif self.path == '/api/word-count-progress':
            self.send_json(200, word_count_progress)
            return

        elif self.path == '/api/audio-progress':
            self.send_json(200, audio_progress)
            return

        elif self.path == '/api/video-progress':
            self.send_json(200, video_progress)
            return

        elif self.path == '/api/pic-progress':
            self.send_json(200, pic_progress)
            return

        self.send_error(404, 'Not found')

    def do_POST(self):
        """Handle POST requests for API calls."""
        try:
            import sys
            print(f"[POST] Received request to: {self.path}", file=sys.stderr, flush=True)
            print(f"[POST] Received request to: {self.path}", flush=True)
            sys.stdout.flush()
            sys.stderr.flush()

            if self.path == '/api/update-insta-post':
                self.handle_insta_post_update()
            elif self.path == '/api/scan-new-files':
                self.handle_scan_new_files()
            elif self.path == '/api/word-count-json':
                self.handle_word_count_json()
            elif self.path == '/api/audio-generation':
                self.handle_audio_generation()
            elif self.path == '/api/video-generation':
                self.handle_video_generation()
            elif self.path == '/api/generate-pictures':
                self.handle_generate_pictures()
            else:
                print(f"[POST] Unknown path: {self.path}", file=sys.stderr, flush=True)
                self.send_error(404, 'Not found')
        except Exception as e:
            print(f"[POST ERROR] {e}", file=sys.stderr, flush=True)
            import traceback
            traceback.print_exc()

    def handle_insta_post_update(self):
        """Handle insta_post status update and move files to 1_insta_post_X."""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body.decode('utf-8'))

            story_name = data.get('story_name')
            if not story_name:
                self.send_json(400, {"success": False, "error": "Missing story_name"})
                return

            manager = InputFileManager()

            # First, get story info to find numbering
            rows = manager.read_rows()
            story_row = None
            for row in rows:
                if row.get('story_name') == story_name:
                    story_row = row
                    break

            if not story_row:
                self.send_json(400, {"success": False, "error": "Story not found"})
                return

            numbering = story_row.get('numbering')

            # Update insta_post status
            success = manager.update_cell(story_name, 'insta_post', 'X')

            if success:
                logger.info(f"[+] Updated insta_post for: {story_name}")

                # Move video file to 1_insta_post_X (JSON and audio already moved during video generation)
                try:
                    import shutil
                    from pathlib import Path

                    output_dir = Path("output")
                    insta_post_dir = output_dir / "1_insta_post_X"
                    insta_post_dir.mkdir(parents=True, exist_ok=True)

                    # Move video file
                    video_file = output_dir / f"{numbering}_{story_name}_video.mp4"
                    if video_file.exists():
                        destination = insta_post_dir / video_file.name
                        shutil.move(str(video_file), str(destination))
                        logger.info(f"[+] Video file moved to: 1_insta_post_X/{video_file.name}")

                except Exception as e:
                    logger.warning(f"[!] Could not move video file: {e}")

                self.send_json(200, {"success": True})
            else:
                self.send_json(400, {"success": False, "error": "Failed to update status"})

        except Exception as e:
            logger.error(f"[-] Error: {e}")
            self.send_json(500, {"success": False, "error": str(e)})

    def handle_scan_new_files(self):
        """Handle scan for new files (stories, images, audio)."""
        global scan_progress

        # Start scan in background thread
        scan_thread = threading.Thread(target=self._run_scan_background)
        scan_thread.daemon = True
        scan_thread.start()

        # Return immediately
        self.send_json(200, {"success": True, "message": "Scan started"})

    def handle_word_count_json(self):
        """Handle word count and JSON generation."""
        global word_count_progress

        # Reset progress state
        word_count_progress["status"] = "scanning"
        word_count_progress["percent"] = 0
        word_count_progress["message"] = "Starting..."

        # Start processing in background thread
        process_thread = threading.Thread(target=self._run_word_count_background)
        process_thread.daemon = True
        process_thread.start()

        # Return immediately
        self.send_json(200, {"success": True, "message": "Word count processing started"})

    def handle_audio_generation(self):
        """Handle audio file generation."""
        global audio_progress

        # Reset progress state
        audio_progress["status"] = "scanning"
        audio_progress["percent"] = 0
        audio_progress["message"] = "Starting..."

        # Start processing in background thread
        audio_thread = threading.Thread(target=self._run_audio_background)
        audio_thread.daemon = True
        audio_thread.start()

        # Return immediately
        self.send_json(200, {"success": True, "message": "Audio generation started"})

    def handle_generate_pictures(self):
        """Handle picture generation."""
        global pic_progress

        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body.decode('utf-8'))

            story_input = data.get('story_input', '')
            if not story_input:
                self.send_json(400, {"success": False, "error": "Missing story_input"})
                return

            # Reset progress state
            pic_progress["status"] = "scanning"
            pic_progress["percent"] = 0
            pic_progress["message"] = "Starting..."
            pic_progress["story_input"] = story_input

            # Start processing in background thread
            pic_thread = threading.Thread(target=self._run_picture_background, args=(story_input,))
            pic_thread.daemon = True
            pic_thread.start()

            # Return immediately
            self.send_json(200, {"success": True, "message": "Picture generation started"})

        except Exception as e:
            logger.error(f"[-] Error: {e}")
            self.send_json(500, {"success": False, "error": str(e)})

    def handle_video_generation(self):
        """Handle video file generation."""
        global video_progress

        # Reset progress state
        video_progress["status"] = "scanning"
        video_progress["percent"] = 0
        video_progress["message"] = "Starting..."

        # Start processing in background thread
        video_thread = threading.Thread(target=self._run_video_background)
        video_thread.daemon = True
        video_thread.start()

        # Return immediately
        self.send_json(200, {"success": True, "message": "Video generation started"})

    def _run_picture_background(self, story_input):
        """Run picture generation in background with progress updates."""
        global pic_progress

        print("[THREAD] _run_picture_background() started", flush=True)

        try:
            import subprocess
            import sys

            pic_progress["status"] = "generating"
            pic_progress["percent"] = 20
            pic_progress["message"] = f"Generating pictures for: {story_input}..."

            # Run generate_pictures.py script
            result = subprocess.run(
                [sys.executable, "generate_pictures.py", story_input],
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )

            pic_progress["percent"] = 90

            if result.returncode == 0:
                pic_progress["message"] = "Picture generation complete"
                logger.info(f"[+] Picture generation successful for: {story_input}")
                pic_progress["percent"] = 100
                pic_progress["status"] = "complete"
            else:
                error_msg = result.stderr if result.stderr else result.stdout
                pic_progress["status"] = "error"
                pic_progress["message"] = f"Error: {error_msg[:100]}"
                logger.error(f"[-] Picture generation error: {error_msg}")

        except subprocess.TimeoutExpired:
            pic_progress["status"] = "error"
            pic_progress["message"] = "Generation timeout (5 minutes exceeded)"
            logger.error("[-] Picture generation timeout")
        except Exception as e:
            logger.error(f"[-] Picture generation error: {e}")
            pic_progress["status"] = "error"
            pic_progress["message"] = f"Error: {str(e)}"

    def _run_video_background(self):
        """Run video generation in background with progress updates."""
        global video_progress

        print("[THREAD] _run_video_background() started", flush=True)

        try:
            print("[THREAD] Importing VideoCreatorWithAudio...", flush=True)
            from generate_videos_with_audio import VideoCreatorWithAudio
            print("[THREAD] Import successful", flush=True)

            video_progress["status"] = "scanning"
            video_progress["percent"] = 10
            video_progress["message"] = "Starting video generation..."

            video_progress["percent"] = 30
            video_progress["message"] = "Initializing video creator..."

            video_progress["percent"] = 50
            video_progress["message"] = "Creating videos with audio..."

            # Create videos using the existing script
            video_creator = VideoCreatorWithAudio()
            video_creator.create_all_videos_with_audio()

            video_progress["percent"] = 95
            message = "Video generation complete"
            video_progress["message"] = message

            logger.info(f"[+] {message}")

            video_progress["percent"] = 100
            video_progress["status"] = "complete"

        except Exception as e:
            logger.error(f"[-] Video generation error: {e}")
            video_progress["status"] = "error"
            video_progress["message"] = f"Error: {str(e)}"

    def _run_audio_background(self):
        """Run audio generation in background with progress updates."""
        global audio_progress

        print("[THREAD] _run_audio_background() started", flush=True)

        try:
            print("[THREAD] Importing generate_audio_files...", flush=True)
            from audio_generator import generate_audio_files
            print("[THREAD] Import successful", flush=True)

            audio_progress["status"] = "scanning"
            audio_progress["percent"] = 10
            audio_progress["message"] = "Starting audio generation..."

            audio_progress["percent"] = 30
            audio_progress["message"] = "Initializing TTS..."

            audio_progress["percent"] = 50
            audio_progress["message"] = "Generating audio files..."

            result = generate_audio_files()

            generated = result.get("generated", 0)
            skipped = result.get("skipped", 0)
            error = result.get("error", 0)

            audio_progress["percent"] = 85
            message = f"Generated: {generated} | Skipped: {skipped} | Error: {error}"
            audio_progress["message"] = message

            logger.info(f"[+] Audio generation complete: {message}")

            # Extract duration for audio files with status_audio=X but seconds=0
            audio_progress["percent"] = 90
            audio_progress["message"] = "Extracting audio duration..."

            print("[THREAD] Importing scan_and_update_audio...", flush=True)
            from scan_audio_files import scan_and_update_audio
            print("[THREAD] Running audio duration extraction...", flush=True)

            duration_result = scan_and_update_audio()
            duration_updated = duration_result.get("updated", 0)

            logger.info(f"[+] Audio duration extraction complete: {duration_updated} stories updated")

            audio_progress["percent"] = 100
            audio_progress["status"] = "complete"

        except Exception as e:
            logger.error(f"[-] Audio generation error: {e}")
            audio_progress["status"] = "error"
            audio_progress["message"] = f"Error: {str(e)}"

    def _run_word_count_background(self):
        """Run word count and JSON generation in background with progress updates."""
        global word_count_progress

        print("[THREAD] _run_word_count_background() started", flush=True)

        try:
            print("[THREAD] Importing generate_word_count_and_json...", flush=True)
            from word_count_and_json import generate_word_count_and_json
            print("[THREAD] Import successful", flush=True)

            word_count_progress["status"] = "scanning"
            word_count_progress["percent"] = 10
            word_count_progress["message"] = "Starting word count..."

            word_count_progress["percent"] = 30
            word_count_progress["message"] = "Counting words in stories..."

            word_count_progress["percent"] = 60
            word_count_progress["message"] = "Generating JSON files..."

            result = generate_word_count_and_json()

            processed = result.get("processed", 0)
            created = result.get("json_created", 0)
            rejected = result.get("rejected", 0)

            word_count_progress["percent"] = 95
            message = f"Processed: {processed} | JSON: {created} | Rejected: {rejected}"
            word_count_progress["message"] = message

            logger.info(f"[+] Word count complete: {message}")

            word_count_progress["percent"] = 100
            word_count_progress["status"] = "complete"

        except Exception as e:
            logger.error(f"[-] Word count error: {e}")
            word_count_progress["status"] = "error"
            word_count_progress["message"] = f"Error: {str(e)}"

    def _run_scan_background(self):
        """Run comprehensive scan in background with progress updates."""
        global scan_progress

        try:
            from comprehensive_scan import scan_and_update

            scan_progress["status"] = "scanning"
            scan_progress["percent"] = 10
            scan_progress["message"] = "Scanning input folder..."

            # Run comprehensive scan
            scan_progress["percent"] = 30
            scan_progress["message"] = "Checking story files..."

            scan_progress["percent"] = 50
            scan_progress["message"] = "Checking image files..."

            scan_progress["percent"] = 70
            scan_progress["message"] = "Checking audio files..."

            result = scan_and_update()

            scan_progress["percent"] = 95
            stories = result.get("stories", 0)
            images = result.get("images", 0)
            audio = result.get("audio", 0)
            updated = result.get("updated", 0)

            message = f"Stories: {stories} | Images: {images} | Audio: {audio} | Updated: {updated}"
            scan_progress["message"] = message

            logger.info(f"[+] Comprehensive scan complete: {message}")

            scan_progress["percent"] = 100
            scan_progress["status"] = "complete"

        except Exception as e:
            logger.error(f"[-] Scan error: {e}")
            scan_progress["status"] = "error"
            scan_progress["message"] = f"Error: {str(e)}"

    def send_json(self, status, data):
        """Send JSON response."""
        content = json.dumps(data).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Length', str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, format, *args):
        """Suppress default logging."""
        return


if __name__ == '__main__':
    port = 9000
    server = HTTPServer(('', port), DashboardHandler)

    print("=" * 60)
    print("Dashboard Server")
    print("=" * 60)
    print(f"[+] Open: http://localhost:{port}")
    print("[+] Press Ctrl+C to stop")
    print("=" * 60)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[+] Server stopped")
        server.server_close()
