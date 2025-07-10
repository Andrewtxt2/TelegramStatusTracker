#!/usr/bin/env python3
"""
Interactive authentication for new account
"""

import asyncio
import os
from telethon import TelegramClient

# New account credentials
API_ID = 29299324
API_HASH = 'c262483dda2739c72637661b537dccac'
PHONE = '+380633952873'

async def interactive_auth():
    """Interactive authentication with step-by-step process"""
    session_name = 'new_auth_session'
    
    print(f"🔐 Starting authentication for {PHONE}...")
    
    # Create client
    client = TelegramClient(session_name, API_ID, API_HASH)
    
    try:
        # Connect
        await client.connect()
        print("✅ Connected to Telegram")
        
        # Check if already authorized
        if await client.is_user_authorized():
            print("✅ Already authorized!")
            me = await client.get_me()
            print(f"👤 Logged in as: {me.first_name} {me.last_name or ''}")
            return True
        
        # Send code request
        print(f"📱 Sending code to {PHONE}...")
        code_request = await client.send_code_request(PHONE)
        print(f"✅ Code sent! Check your phone {PHONE}")
        
        # Instructions for user
        print("\n" + "="*50)
        print("🔍 NEXT STEPS:")
        print("1. Check your phone for the Telegram code")
        print("2. Create a file called 'auth_code.txt' with the code")
        print("3. Run: python3 enter_new_code.py")
        print("="*50)
        
        return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
        
    finally:
        await client.disconnect()
        print("🔌 Disconnected")

if __name__ == "__main__":
    asyncio.run(interactive_auth())