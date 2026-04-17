#!/usr/bin/env python3
"""Generate book cover using GPT Image model - Direct API call with requests"""

import os
import csv
import json
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Get API key
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    print("[-] ERROR: OPENAI_API_KEY not found in .env file")
    exit(1)

print(f"[+] Found OpenAI API key")

# Read story name from input file (line 49)
input_file = Path("input/0_input_all_stories.txt")
story_name = None

with open(input_file, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for idx, row in enumerate(reader, start=1):
        if idx == 49:
            story_name = row.get('story_name')
            break

if not story_name:
    print("[-] ERROR: Could not find story at line 49")
    exit(1)

print(f"[+] Found story #49: {story_name}")

# Generate image via direct API call
try:
    import requests

    print(f"\n[*] Generating image for Story #49: {story_name}...")

    # Dynamic prompt with story_name variable
    prompt = f"""Create a creative Instagram image for kid bedtime stories with the title "{story_name}". A whimsical, cozy children's bedtime image illustration in a dreamy fairytale style. Vertical composition (portrait), sized for Instagram (672x1010). Title at the top in large, elegant, glowing golden serif lettering: {story_name}. Frame the entire image with an ornate decorative border featuring swirls, stars, and storybook-style embellishments similar to classic children's book covers.

Color palette: warm golds, soft yellows, teal, and deep blues. Lighting is soft, glowing, and magical with sparkles throughout. Highly detailed, painterly, smooth textures, storybook illustration style, comforting and enchanting atmosphere."""

    print(f"[*] Sending prompt to GPT Image via direct API...")
    print(f"[*] Story name in prompt: {story_name}")

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
        "quality": "high",
        "n": 1
    }

    print(f"[*] POST to: {url}")
    print(f"[*] Model: gpt-image-1")
    print(f"[*] Size: 1024x1536")
    print(f"[*] Quality: high")

    response = requests.post(url, headers=headers, json=payload)

    print(f"[*] Response status: {response.status_code}")

    if response.status_code != 200:
        print(f"[-] ERROR: {response.status_code}")
        print(f"[-] Response: {response.text}")
        exit(1)

    data = response.json()
    print(f"[+] API response received!")

    if "data" not in data or len(data["data"]) == 0:
        print(f"[-] ERROR: No image data in response")
        print(f"[-] Response: {json.dumps(data, indent=2)}")
        exit(1)

    image_item = data["data"][0]

    if "b64_json" in image_item:
        print(f"[+] Image returned as base64 data")
        import base64
        img_data = base64.b64decode(image_item["b64_json"])
    elif "url" in image_item:
        print(f"[+] Image URL: {image_item['url'][:80]}...")
        # Download image
        print(f"[*] Downloading image...")
        img_response = requests.get(image_item["url"])
        img_response.raise_for_status()
        img_data = img_response.content
    else:
        print(f"[-] ERROR: No 'b64_json' or 'url' field in response")
        print(f"[-] Available fields: {image_item.keys()}")
        exit(1)

    # Save as 49.png
    output_file = Path("images") / "49.png"
    with open(output_file, 'wb') as f:
        f.write(img_data)

    print(f"[+] Image saved to: {output_file}")
    print(f"[+] File size: {len(img_data)} bytes")
    print(f"\n[+] SUCCESS! Image 49.png generated with GPT Image for: {story_name}")

except requests.exceptions.RequestException as e:
    print(f"[-] Request ERROR: {e}")
except Exception as e:
    print(f"[-] ERROR: {e}")
    import traceback
    traceback.print_exc()
