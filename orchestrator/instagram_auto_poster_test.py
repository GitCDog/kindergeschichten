#!/usr/bin/env python3
"""
TEST MODE: Simulate Instagram posting WITHOUT actually posting to Instagram.
Use this to verify the automation works before posting for real.
"""

import os
import json
import csv
import io
import logging
import requests
from datetime import datetime
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

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


class InstagramAutoPoserTest:
    """Test mode: simulate posting without actually sending to Instagram."""

    def __init__(self):
        """Initialize with API credentials."""
        self.cloudinary_cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME")
        self.cloudinary_api_key = os.getenv("CLOUDINARY_API_KEY")
        self.cloudinary_api_secret = os.getenv("CLOUDINARY_API_SECRET")
        self.instagram_recipient_id = os.getenv("INSTAGRAM_RECIPIENT_ID")
        self.instagram_access_token = os.getenv("INSTAGRAM_ACCESS_TOKEN")

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
            api_secret=self.cloudinary_api_secret,
            secure=True
        )

        # Configure GitHub if available
        if self.use_github:
            try:
                self.github = Github(self.github_token, verify=False)
                repo = self.github.get_repo(self.github_repo)
                logger.info(f"[+] GitHub integration enabled: {self.github_repo}")
            except Exception as e:
                logger.warning(f"[!] GitHub initialization failed: {e}")
                self.use_github = False

        logger.info("[+] InstagramAutoPoser TEST MODE initialized")

    def _read_input_file_from_github(self):
        """Read input file from GitHub and parse CSV rows."""
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
        """Get NEXT unposted video in sequential order from input file."""
        try:
            logger.info("[*] Reading input file to find next unposted video...")

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
            return None

    def generate_dynamic_caption(self, story_info):
        """Generate Instagram caption from story metadata."""
        try:
            story_name = story_info.get("story_name", "Story")
            keywords = story_info.get("keywords", [])

            # Format story name (replace underscores with spaces)
            formatted_name = story_name.replace("_", " ")

            # Build caption
            caption = f"Ready for '{formatted_name}'?\nA wonderful story to dream about... 💭\n\n"
            caption += "#bedtimestories #kidsbooks #sleepystories #childrensaudio #bedtimeadventure"

            logger.info(f"[+] Caption generated ({len(caption)} chars)")
            logger.info(f"[+] Caption:\n{caption}")

            return caption

        except Exception as e:
            logger.error(f"[-] Error generating caption: {e}")
            return None

    def simulate_instagram_post(self, video_url, caption):
        """SIMULATE Instagram posting without actually posting."""
        try:
            logger.info("\n" + "="*60)
            logger.info("[TEST MODE] WOULD POST TO INSTAGRAM:")
            logger.info("="*60)
            logger.info(f"Video URL: {video_url}")
            logger.info(f"Caption: {caption}")
            logger.info(f"Account ID: {self.instagram_recipient_id}")
            logger.info(f"Timestamp: {datetime.now().isoformat()}")
            logger.info("="*60)
            logger.info("[TEST MODE] NO VIDEO WAS SENT - THIS IS A TEST")
            logger.info("="*60 + "\n")

            return "test-post-id-12345"

        except Exception as e:
            logger.error(f"[-] Error in test simulation: {e}")
            return None

    def run_test(self):
        """Run test simulation."""
        logger.info("="*60)
        logger.info("INSTAGRAM AUTO-POSTER - TEST MODE")
        logger.info("="*60)

        try:
            # Step 1: Get next video
            logger.info("\n[STEP 1] Fetching next video from Cloudinary...")
            story_info = self.get_next_video_from_cloudinary()

            if not story_info:
                logger.warning("[-] No video to post")
                return False

            # Step 2: Generate caption
            logger.info("\n[STEP 2] Generating Instagram caption...")
            caption = self.generate_dynamic_caption(story_info)

            if not caption:
                logger.error("[-] Failed to generate caption")
                return False

            # Step 3: Simulate posting
            logger.info("\n[STEP 3] Simulating Instagram post...")
            post_id = self.simulate_instagram_post(story_info.get("url"), caption)

            if not post_id:
                logger.error("[-] Simulation failed")
                return False

            logger.info("\n" + "="*60)
            logger.info("TEST SIMULATION COMPLETE - ALL STEPS PASSED")
            logger.info("="*60)
            logger.info("In production, the video would now be:")
            logger.info("  1. Posted to Instagram")
            logger.info("  2. Tracked in posted_videos.json on GitHub")
            logger.info("  3. Marked as insta_post=X in input file on GitHub")
            logger.info("  4. Deleted from Cloudinary")
            logger.info("="*60 + "\n")

            return True

        except Exception as e:
            logger.error(f"[-] Test failed: {e}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == "__main__":
    try:
        tester = InstagramAutoPoserTest()
        success = tester.run_test()
        exit(0 if success else 1)
    except Exception as e:
        logger.error(f"[-] Fatal error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
