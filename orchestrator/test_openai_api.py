#!/usr/bin/env python3
"""Test OpenAI API key"""

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

# Test the API
try:
    from openai import OpenAI

    client = OpenAI(api_key=api_key)

    print("[*] Testing OpenAI API connection...")

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": "Say 'hello' in one word"}
        ],
        max_tokens=10
    )

    print(f"[+] SUCCESS! API works!")
    print(f"[+] Response: {response.choices[0].message.content}")
    print(f"[+] Model: {response.model}")
    print(f"[+] Tokens used: {response.usage.total_tokens}")

except ImportError:
    print("[-] OpenAI library not installed. Install with: pip install openai")
except Exception as e:
    print(f"[-] ERROR: {e}")
    print(f"[-] API key might be invalid or account has no credits")
