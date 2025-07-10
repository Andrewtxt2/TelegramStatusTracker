#!/usr/bin/env python3
"""
Create new session for local testing to avoid IP conflicts with Render
"""

import asyncio
import os
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError

# API credentials
API_ID = 26886585
API_HASH = "166e3719a0d93c12bf76af43fe91425f"
PHONE = "+380686850166"

async def create_local_session():
    """Create new session for local testing"""
    
    # Create session with timestamp to avoid conflicts
    session_name = f"local_test_session_{int(asyncio.get_event_loop().time())}"
    
    print(f"🔑 Creating new session: {session_name}")
    
    client = TelegramClient(session_name, API_ID, API_HASH)
    
    try:
        await client.connect()
        
        if not await client.is_user_authorized():
            print("📞 Sending code request...")
            await client.send_code_request(PHONE)
            
            code = input("Enter the code you received: ")
            
            try:
                await client.sign_in(PHONE, code)
                print("✅ Successfully signed in!")
                
            except SessionPasswordNeededError:
                password = input("Enter your 2FA password: ")
                await client.sign_in(password=password)
                print("✅ Successfully signed in with 2FA!")
        
        me = await client.get_me()
        print(f"✅ Session created for: {me.first_name}")
        print(f"📱 Session file: {session_name}.session")
        
        return session_name
        
    except Exception as e:
        print(f"❌ Error creating session: {e}")
        return None
    
    finally:
        await client.disconnect()

if __name__ == "__main__":
    session_name = asyncio.run(create_local_session())
    if session_name:
        print(f"\n🎉 Session created successfully: {session_name}.session")
        print("This session can now be used for local testing without IP conflicts!")
    else:
        print("\n❌ Failed to create session")