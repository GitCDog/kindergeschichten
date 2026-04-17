#!/usr/bin/env python3
"""Test OpenAI image generation with DALL-E"""

import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Get API key
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    print("[-] ERROR: OPENAI_API_KEY not found in .env file")
    exit(1)

print(f"[+] Found OpenAI API key: {api_key[:20]}...{api_key[-10:]}")

# Test image generation
try:
    from openai import OpenAI

    client = OpenAI(api_key=api_key)

    print("[*] Generating image with DALL-E...")

    prompt = """Create a creative Instagram image for kid bedtime stories with the title "Zebra's Sunny Striped Day".

    Follow the design style of the example:
    - Ornate golden borders with decorative patterns
    - Night sky with moon and stars in the background
    - A magical zebra character with glowing golden stripes
    - A small child character interacting with the zebra
    - Beautiful landscape with meadows and trees
    - Warm, cozy fantasy illustration style
    - Gold/yellow text styling for the title
    - "Bedtime Favourite" theme
    - Size: 720 x 1280 pixels (vertical format)
    - High quality, detailed illustration suitable for children's book covers
    """

    response = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1024x1792",  # Closest to 720x1280 (16:9 aspect ratio)
        quality="hd",
        n=1
    )

    image_url = response.data[0].url
    print(f"[+] SUCCESS! Image generated!")
    print(f"[+] Image URL: {image_url}")
    print(f"[+] The image has been generated and is available at the URL above")

    # Optional: Save the image
    import requests
    from pathlib import Path

    print("[*] Downloading image...")
    img_data = requests.get(image_url).content
    output_file = Path("images") / "49_Zebra_s_Sunny_Striped_Day.png"

    with open(output_file, 'wb') as f:
        f.write(img_data)

    print(f"[+] Image saved to: {output_file}")

except ImportError:
    print("[-] Required libraries not installed. Install with:")
    print("    pip install openai requests")
except Exception as e:
    print(f"[-] ERROR: {e}")
    if "insufficient_quota" in str(e):
        print("[-] Your OpenAI account has insufficient credits/quota")
        print("[-] Please add credits at: https://platform.openai.com/account/billing/overview")
