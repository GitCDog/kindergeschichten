#!/usr/bin/env python3
"""Generate book covers using GPT Image model - supports single story or range"""

import os
import csv
import json
import base64
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Get API key
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    print("[-] ERROR: OPENAI_API_KEY not found in .env file")
    exit(1)

def parse_story_input(input_str):
    """Parse input like '49' or '55-60' and return list of story numbers"""
    input_str = input_str.strip()

    if '-' in input_str:
        # Range format: "55-60"
        try:
            parts = input_str.split('-')
            start = int(parts[0].strip())
            end = int(parts[1].strip())
            return list(range(start, end + 1))
        except:
            print(f"[-] ERROR: Invalid range format '{input_str}'. Use format: '55-60'")
            return []
    else:
        # Single story format: "49"
        try:
            return [int(input_str)]
        except:
            print(f"[-] ERROR: Invalid story number '{input_str}'. Use format: '49' or '55-60'")
            return []

def read_story_by_number(numbering):
    """Read story name from input file by numbering"""
    input_file = Path("input/0_input_all_stories.txt")

    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader, start=1):
            if idx == numbering:
                return row.get('story_name')

    return None

def generate_image(numbering, story_name):
    """Generate a single image for a story"""
    try:
        import requests

        print(f"\n[*] Generating image for Story #{numbering}: {story_name}...")

        # Dynamic prompt with story_name variable
        prompt = f"""Create a creative Instagram image for kid bedtime stories with the title "{story_name}". A whimsical, cozy children's bedtime image illustration in a dreamy fairytale style. Vertical composition (portrait), sized for Instagram (672x1010). Title at the top in large, elegant, glowing golden serif lettering: {story_name}. Frame the entire image with an ornate decorative border featuring swirls, stars, and storybook-style embellishments similar to classic children's book covers.

Color palette: warm golds, soft yellows, teal, and deep blues. Lighting is soft, glowing, and magical with sparkles throughout. Highly detailed, painterly, smooth textures, storybook illustration style, comforting and enchanting atmosphere."""

        # Direct API call to OpenAI Images endpoint
        url = "https://api.openai.com/v1/images/generations"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "gpt-image-1",
            "prompt": prompt,
            "size": "1024x1536",
            "quality": "medium",
            "n": 1
        }

        # Log the full API request
        print(f"\n[API REQUEST]")
        print(f"  URL: {url}")
        print(f"  Model: {payload['model']}")
        print(f"  Size: {payload['size']}")
        print(f"  Quality: {payload['quality']}")
        print(f"  Prompt: {payload['prompt'][:100]}..." if len(payload['prompt']) > 100 else f"  Prompt: {payload['prompt']}")
        print(f"  Auth: Bearer {api_key[:20]}...")

        response = requests.post(url, headers=headers, json=payload)

        if response.status_code != 200:
            print(f"[-] ERROR {response.status_code}: {response.text}")
            return False

        data = response.json()

        if "data" not in data or len(data["data"]) == 0:
            print(f"[-] ERROR: No image data in response")
            return False

        image_item = data["data"][0]

        if "b64_json" in image_item:
            img_data = base64.b64decode(image_item["b64_json"])
        elif "url" in image_item:
            img_data = requests.get(image_item["url"]).content
        else:
            print(f"[-] ERROR: No image data in response")
            return False

        # Save image
        output_file = Path("images") / f"{numbering}.png"
        with open(output_file, 'wb') as f:
            f.write(img_data)

        print(f"[+] Image saved: {output_file} ({len(img_data)} bytes)")
        return True

    except Exception as e:
        print(f"[-] ERROR generating image: {e}")
        import traceback
        traceback.print_exc()
        return False

def main(story_input):
    """Main function - process input and generate images"""

    print(f"[+] Found OpenAI API key")

    # Parse input
    story_numbers = parse_story_input(story_input)

    if not story_numbers:
        print("[-] No valid story numbers to process")
        return False

    print(f"[*] Will generate images for: {story_numbers}")

    success_count = 0
    failed_count = 0

    # Generate images for each story
    for numbering in story_numbers:
        story_name = read_story_by_number(numbering)

        if not story_name:
            print(f"[-] ERROR: Could not find story #{numbering}")
            failed_count += 1
            continue

        if generate_image(numbering, story_name):
            success_count += 1
        else:
            failed_count += 1

    # Summary
    print(f"\n{'='*60}")
    print(f"[+] Generated: {success_count} images")
    if failed_count > 0:
        print(f"[-] Failed: {failed_count} images")
    print(f"{'='*60}")

    return failed_count == 0

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python generate_pictures.py <story_number_or_range>")
        print("  Example: python generate_pictures.py 49")
        print("  Example: python generate_pictures.py 55-60")
        exit(1)

    story_input = sys.argv[1]
    success = main(story_input)
    exit(0 if success else 1)
