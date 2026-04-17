#!/usr/bin/env python3
"""
Automatic daily Instagram video poster using Cloudinary and Instagram Graph API.
Posts kindergeschichten videos daily at random time 18:00-20:00 CET.

Schedule: Daily at 17:55 CET using Claude Routines
"""

import os
import json
import csv
import io
import random
import logging
import requests
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv
import cloudinary
import cloudinary.api

# Optional GitHub integration
try:
    from github import Github
    GITHUB_AVAILABLE = True
except ImportError:
    GITHUB_AVAILABLE = False

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/instagram_auto_poster.log", encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# Ensure logs directory exists
Path("logs").mkdir(exist_ok=True)


class InstagramAutoPoser:
    """Automatically post kindergeschichten videos to Instagram."""

    def __init__(self):
        """Initialize with API credentials from .env"""
        # Cloudinary config
        self.cloudinary_cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME")
        self.cloudinary_api_key = os.getenv("CLOUDINARY_API_KEY")
        self.cloudinary_api_secret = os.getenv("CLOUDINARY_API_SECRET")

        # Instagram/Meta config
        self.instagram_recipient_id = os.getenv("INSTAGRAM_RECIPIENT_ID")
        self.instagram_access_token = os.getenv("INSTAGRAM_ACCESS_TOKEN")

        # GitHub config (optional)
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.github_repo = os.getenv("GITHUB_REPO")
        self.use_github = GITHUB_AVAILABLE and self.github_token and self.github_repo
        self.github = None

        # Validate credentials
        if not self.cloudinary_cloud_name:
            raise ValueError("CLOUDINARY_CLOUD_NAME not found in .env")
        if not self.instagram_recipient_id:
            raise ValueError("INSTAGRAM_RECIPIENT_ID not found in .env")
        if not self.instagram_access_token:
            raise ValueError("INSTAGRAM_ACCESS_TOKEN not found in .env")

        # Configure Cloudinary
        cloudinary.config(
            cloud_name=self.cloudinary_cloud_name,
            api_key=self.cloudinary_api_key,
            api_secret=self.cloudinary_api_secret
        )

        # Configure GitHub if available
        if self.use_github:
            try:
                self.github = Github(self.github_token)
                repo = self.github.get_repo(self.github_repo)
                logger.info(f"[+] GitHub integration enabled: {self.github_repo}")
            except Exception as e:
                logger.warning(f"[!] GitHub initialization failed: {e}")
                self.use_github = False
        else:
            raise ValueError("GitHub integration is REQUIRED for cloud execution. Set GITHUB_TOKEN and GITHUB_REPO in .env")

        logger.info("[+] InstagramAutoPoser initialized successfully")

    def _read_input_file_from_github(self):
        """
        Read input file from GitHub and parse CSV rows.
        Returns list of dictionaries with row data, or empty list on error.
        """
        try:
            if not self.github:
                logger.error("[-] GitHub not initialized")
                return []

            logger.info("[*] Reading input file from GitHub...")
            repo = self.github.get_repo(self.github_repo)

            file_path = "orchestrator/input/0_input_all_stories.txt"
            file = repo.get_contents(file_path)
            content = file.decoded_content.decode('utf-8')

            # Parse CSV
            reader = csv.DictReader(io.StringIO(content))
            rows = list(reader)

            logger.info(f"[+] Read {len(rows)} rows from GitHub")
            return rows

        except Exception as e:
            logger.error(f"[-] Error reading input file from GitHub: {e}")
            return []

    def get_next_video_from_cloudinary(self):
        """
        Get NEXT unposted video in sequential order from input file.
        Returns: {
            'story_name': 'Story Name',
            'numbering': 1,
            'keywords': ['keyword1', 'keyword2', 'keyword3'],
            'url': 'https://...',
            'public_id': 'kindergeschichten/1_story_name'
        }
        """
        try:
            logger.info("[*] Reading input file to find next unposted video...")

            # Read input file from GitHub to get sequential order
            rows = self._read_input_file_from_github()
            if not rows:
                logger.warning("[-] No stories in input file on GitHub")
                return None

            # Find FIRST story with insta_post=O (in sequence)
            next_story = None
            for row in rows:
                if row.get("insta_post") == "O":
                    next_story = row
                    break

            if not next_story:
                logger.warning("[-] No unposted videos in input file (all have insta_post=X)")
                return None

            numbering = next_story.get("numbering")
            story_name = next_story.get("story_name")

            logger.info(f"[+] Next video to post (in sequence): #{numbering} - {story_name}")

            # Now find this video on Cloudinary
            logger.info("[*] Finding video on Cloudinary...")

            # Search in both kindergeschichten/ folder and root
            all_videos = []
            try:
                result = cloudinary.api.resources(
                    type="upload",
                    prefix="kindergeschichten/",
                    resource_type="video",
                    max_results=500
                )
                all_videos.extend(result.get("resources", []))
            except:
                pass

            try:
                result_root = cloudinary.api.resources(
                    type="upload",
                    resource_type="video",
                    max_results=500
                )
                root_videos = [v for v in result_root.get("resources", []) if "/" not in v.get("public_id", "")]
                all_videos.extend(root_videos)
            except:
                pass

            if not all_videos:
                logger.error(f"[-] No videos found on Cloudinary")
                return None

            # Find matching video by numbering
            video_url = None
            public_id = None
            for video in all_videos:
                pid = video.get("public_id", "")
                filename = pid.split("/")[-1]

                # Try to extract numbering from filename
                try:
                    num_str = filename.split("_")[0]
                    num = int(num_str)

                    if num == int(numbering):
                        video_url = video.get("secure_url", video.get("url", ""))
                        public_id = pid
                        logger.info(f"[+] Found on Cloudinary: {pid}")
                        break
                except:
                    pass

            if not video_url:
                logger.error(f"[-] Video #{numbering} not found on Cloudinary")
                return None

            # Prepare response
            selected = {
                "numbering": int(numbering),
                "story_name": story_name,
                "public_id": public_id,
                "url": video_url,
                "keywords": [
                    next_story.get("keyword1", ""),
                    next_story.get("keyword2", ""),
                    next_story.get("keyword3", "")
                ]
            }
            selected["keywords"] = [k for k in selected["keywords"] if k]

            return selected

        except Exception as e:
            logger.error(f"[-] Error getting next video: {e}")
            import traceback
            traceback.print_exc()
            return None

    def generate_dynamic_caption(self, story_info):
        """
        Generate sweet invitation caption for kids to listen to the story.
        Format: Sweet invitation + story_name + 5 hashtags (in English)
        """
        try:
            story_name = story_info.get("story_name", "Unknown Story")

            # Sweet invitations in English (rotate through different ones)
            invitations = [
                f"Want to hear the story '{story_name}'?\nA wonderful adventure awaits you! 🌙",
                f"Join us on a journey into the world of '{story_name}'!\nA story full of magic and surprises... ✨",
                f"The story '{story_name}' is calling you!\nGet ready for an exciting adventure... 🎭",
                f"Ready for '{story_name}'?\nA wonderful story to dream about... 💫",
                f"'{story_name}' is waiting for you!\nLet's experience an adventure together... 🌟"
            ]

            # Pick a random invitation
            caption = random.choice(invitations)

            # Add newline before hashtags
            caption += "\n\n"

            # 5 relevant hashtags (in English)
            hashtags = "#bedtimestories #kidsbooks #sleepystories #childrensaudio #bedtimeadventure"
            caption += hashtags

            logger.info(f"[+] Caption generated ({len(caption)} chars)")
            return caption

        except Exception as e:
            logger.error(f"[-] Error generating caption: {e}")
            return f"Come and listen to the story!\n\n#bedtimestories #kidsbooks #sleepystories #childrensaudio #bedtimeadventure"

    def post_to_instagram(self, video_url, caption):
        """
        Post video to Instagram using Graph API v18.0.
        Two-step process:
        1. POST /ig_business_account_id/media (create container)
        2. POST /ig_business_account_id/media_publish (publish container)
        """
        try:
            logger.info("[*] Creating Instagram media container...")

            # Step 1: Create container
            container_url = f"https://graph.instagram.com/v18.0/{self.instagram_recipient_id}/media"

            container_payload = {
                "access_token": self.instagram_access_token,
                "media_type": "REELS",
                "video_url": video_url,
                "caption": caption
            }

            container_response = requests.post(container_url, json=container_payload, timeout=30)

            if container_response.status_code != 200:
                logger.error(f"[-] Container creation failed: {container_response.status_code}")
                logger.error(f"[-] Response: {container_response.text}")
                return None

            container_data = container_response.json()
            creation_id = container_data.get("id")

            if not creation_id:
                logger.error(f"[-] No creation_id in response: {container_data}")
                return None

            logger.info(f"[+] Container created: {creation_id}")

            # Step 2: Poll media status until FINISHED
            logger.info("[*] Polling media status (waiting for Instagram to process video)...")
            import time
            max_attempts = 12  # 12 * 10 seconds = 120 seconds max wait
            attempt = 0

            while attempt < max_attempts:
                time.sleep(10)
                attempt += 1

                status_url = f"https://graph.instagram.com/v18.0/{creation_id}"
                status_response = requests.get(status_url, params={"fields": "status", "access_token": self.instagram_access_token}, timeout=30)

                if status_response.status_code == 200:
                    status_data = status_response.json()
                    media_status = status_data.get("status")
                    logger.info(f"[*] Status: {media_status} (attempt {attempt}/{max_attempts})")

                    if media_status == "FINISHED":
                        logger.info(f"[+] Media processing complete!")
                        break
                else:
                    logger.warning(f"[!] Could not check status: {status_response.text}")

            # Step 3: Publish container
            logger.info("[*] Publishing media to Instagram...")
            publish_url = f"https://graph.instagram.com/v18.0/{self.instagram_recipient_id}/media_publish"

            publish_payload = {
                "access_token": self.instagram_access_token,
                "creation_id": creation_id
            }

            publish_response = requests.post(publish_url, json=publish_payload, timeout=30)

            if publish_response.status_code != 200:
                logger.error(f"[-] Publishing failed: {publish_response.status_code}")
                logger.error(f"[-] Response: {publish_response.text}")
                return None

            publish_data = publish_response.json()
            post_id = publish_data.get("id")

            if not post_id:
                logger.error(f"[-] No post_id in response: {publish_data}")
                return None

            logger.info(f"[+] Published to Instagram: {post_id}")
            return post_id

        except requests.Timeout:
            logger.error("[-] Request timeout while posting to Instagram")
            return None
        except Exception as e:
            logger.error(f"[-] Error posting to Instagram: {e}")
            return None

    def log_posted_video(self, story_info, post_id):
        """
        Record posted video and update GitHub files.
        Everything syncs to GitHub for cloud execution.
        """
        try:
            story_name = story_info.get("story_name")

            # 1. Read current posted_videos.json from GitHub
            logger.info("[*] Reading posted_videos.json from GitHub...")
            repo = self.github.get_repo(self.github_repo)

            file_path = "orchestrator/posted_videos.json"
            try:
                file = repo.get_contents(file_path)
                data = json.loads(file.decoded_content.decode('utf-8'))
            except:
                data = {"videos": []}

            # 2. Add new entry
            new_entry = {
                "numbering": story_info.get("numbering"),
                "story_name": story_name,
                "post_id": post_id,
                "date_posted": datetime.now().isoformat(),
                "cloudinary_url": story_info.get("url")
            }
            data["videos"].append(new_entry)
            logger.info(f"[+] Posted video logged: {story_name}")

            # 3. Update GitHub files
            self._update_github_input_file(story_info)
            self._update_github_posted_videos(data)

        except Exception as e:
            logger.error(f"[-] Error logging posted video: {e}")

    def _update_github_input_file(self, story_info):
        """Update input file on GitHub to mark video as posted."""
        try:
            if not self.github:
                return

            logger.info("[*] Updating input file on GitHub...")
            repo = self.github.get_repo(self.github_repo)

            # Get file from GitHub
            file_path = "orchestrator/input/0_input_all_stories.txt"
            try:
                file = repo.get_contents(file_path)
                content = file.decoded_content.decode('utf-8')
            except Exception as e:
                logger.warning(f"[!] Could not read {file_path} from GitHub: {e}")
                return

            # Parse CSV and update
            import csv
            import io

            lines = content.split('\n')
            if not lines:
                return

            # Parse CSV
            reader = csv.DictReader(io.StringIO(content))
            rows = list(reader)

            # Find and update the row
            updated = False
            for row in rows:
                if row.get('story_name') == story_info.get('story_name'):
                    row['insta_post'] = 'X'
                    updated = True
                    break

            if not updated:
                logger.warning(f"[!] Could not find story in CSV: {story_info.get('story_name')}")
                return

            # Write CSV back
            output = io.StringIO()
            if rows:
                fieldnames = rows[0].keys()
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
                new_content = output.getvalue()

                # Push to GitHub
                commit_message = f"[AUTO] Posted story #{story_info.get('numbering')} \"{story_info.get('story_name')}\" to Instagram"
                repo.update_file(file_path, commit_message, new_content, file.sha)
                logger.info(f"[+] Updated GitHub: {file_path}")

        except Exception as e:
            logger.error(f"[-] Error updating GitHub input file: {e}")

    def _update_github_posted_videos(self, data):
        """Update posted_videos.json on GitHub."""
        try:
            if not self.github:
                return

            logger.info("[*] Syncing posted_videos.json to GitHub...")
            repo = self.github.get_repo(self.github_repo)

            file_path = "orchestrator/posted_videos.json"
            content = json.dumps(data, indent=2, ensure_ascii=False)

            try:
                file = repo.get_contents(file_path)
                repo.update_file(file_path, "[AUTO] Updated posted videos tracker", content, file.sha)
                logger.info(f"[+] Updated GitHub: {file_path}")
            except:
                # File doesn't exist, create it
                repo.create_file(file_path, "[AUTO] Create posted videos tracker", content)
                logger.info(f"[+] Created GitHub: {file_path}")

        except Exception as e:
            logger.error(f"[-] Error updating GitHub posted_videos: {e}")


    def get_random_posting_time(self):
        """
        Calculate random time between 18:00-20:00 CET for today.
        Returns seconds to wait.
        """
        now = datetime.now()

        # Random hour between 18 and 20, random minute
        hour = random.randint(18, 19)  # 18:00-19:59
        minute = random.randint(0, 59)

        post_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

        # If time has already passed today, use tomorrow
        if post_time <= now:
            post_time += timedelta(days=1)

        wait_seconds = (post_time - now).total_seconds()
        wait_minutes = wait_seconds / 60

        logger.info(f"[*] Scheduled posting for {post_time.strftime('%H:%M')} CET (~{wait_minutes:.1f} minutes from now)")

        return wait_seconds, post_time

    def run_daily_post(self):
        """
        Main entry point: Fetch, generate caption, post to Instagram.
        Called daily by Claude Routine at 17:55 CET.
        """
        logger.info("=" * 60)
        logger.info("DAILY INSTAGRAM POST ROUTINE STARTED")
        logger.info("=" * 60)

        try:
            # Step 1: Get next video from Cloudinary
            logger.info("\n[STEP 1] Fetching next video from Cloudinary...")
            story_info = self.get_next_video_from_cloudinary()

            if not story_info:
                logger.warning("[!] No video available to post today. Skipping.")
                return False

            # Step 2: Generate caption
            logger.info("\n[STEP 2] Generating Instagram caption...")
            caption = self.generate_dynamic_caption(story_info)
            logger.info(f"[+] Caption:\n{caption}\n")

            # Step 3: Calculate posting time
            logger.info("\n[STEP 3] Calculating posting time...")
            wait_seconds, post_time = self.get_random_posting_time()

            # Step 4: Wait until posting time
            logger.info(f"\n[STEP 4] Waiting {int(wait_seconds)} seconds until {post_time.strftime('%H:%M')}...")
            import time
            time.sleep(wait_seconds)

            # Step 5: Post to Instagram
            logger.info("\n[STEP 5] Posting to Instagram...")
            post_id = self.post_to_instagram(story_info["url"], caption)

            if not post_id:
                logger.error("[-] Failed to post to Instagram")
                return False

            # Step 6: Log success
            logger.info("\n[STEP 6] Logging posted video...")
            self.log_posted_video(story_info, post_id)

            logger.info("\n" + "=" * 60)
            logger.info(f"[SUCCESS] Posted '{story_info['story_name']}' to Instagram")
            logger.info(f"[SUCCESS] Post ID: {post_id}")
            logger.info("=" * 60 + "\n")

            return True

        except Exception as e:
            logger.error(f"\n[-] FATAL ERROR in daily post routine: {e}")
            logger.exception("Full traceback:")
            return False


def main():
    """Entry point for manual testing or routine execution."""
    try:
        poster = InstagramAutoPoser()
        success = poster.run_daily_post()
        exit(0 if success else 1)
    except Exception as e:
        logger.error(f"[-] Fatal error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)


if __name__ == "__main__":
    main()
