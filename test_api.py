#!/usr/bin/env python3
"""Direct API test - minimal."""
import asyncio
from groq import AsyncGroq
import os

# Load env
from dotenv import load_dotenv
load_dotenv('/home/rushi/vg/.env')

api_key = os.getenv('GROQ_API_KEY')
print(f"API key loaded: {api_key[:15]}...")

async def test():
    client = AsyncGroq(api_key=api_key)
    resp = await client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": "Say hello in one word"}]
    )
    return resp.choices[0].message.content

result = asyncio.run(test())
print(f"Response: {result}")
print("✅ API working!" if result else "❌ API failed")