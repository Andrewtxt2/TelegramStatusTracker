#!/usr/bin/env python3
"""
Fresh authentication script for Telegram bot
Run this to create a new session without IP conflicts
"""

import os
import sys
import asyncio
from telethon import TelegramClient

# API credentials
API_ID = 26886585
API_HASH = "166e3719a0d93c12bf76af43fe91425f"
PHONE = "+380 68 685 01 66"

async def fresh_auth():
    """Create fresh authentication session"""
    
    print("🔄 Creating fresh authentication session...")
    
    # Remove all existing sessions to avoid conflicts
    session_files = [
        'auth_session.session',
        'simple_render_bot.session',
        'working_session.session',
        'render_session.session',
        'render_no_auth_bot.session'
    ]
    
    for session_file in session_files:
        if os.path.exists(session_file):
            os.remove(session_file)
            print(f"🗑️ Removed old session: {session_file}")
    
    # Create new session
    import time
    session_name = f'fresh_auth_session_{int(time.time())}'
    
    print(f"📱 Creating new session: {session_name}")
    
    # Create client
    client = TelegramClient(session_name, API_ID, API_HASH)
    
    try:
        await client.connect()
        
        if not await client.is_user_authorized():
            print(f"📞 Sending code to: {PHONE}")
            await client.send_code_request(PHONE)
            
            # Get code from user
            code = input("📨 Enter the code you received: ")
            
            try:
                await client.sign_in(PHONE, code)
                print("✅ Authentication successful!")
            except Exception as e:
                if "two-step verification" in str(e).lower():
                    password = input("🔒 Enter your 2FA password: ")
                    await client.sign_in(password=password)
                    print("✅ Authentication with 2FA successful!")
                else:
                    raise e
        
        # Test connection
        me = await client.get_me()
        print(f"👤 Logged in as: {me.first_name}")
        
        # Create a copy as auth_session.session for bot to use
        await client.disconnect()
        
        # Copy session file
        import shutil
        shutil.copy(f'{session_name}.session', 'auth_session.session')
        print("✅ Session copied to auth_session.session")
        
        print("\n🎉 Fresh authentication complete!")
        print("Now you can restart the bot and it will use the new session.")
        
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 Fresh Authentication Script")
    print("This will create a new authentication session for the bot.")
    print("Make sure to close any other running instances of the bot first.")
    print()
    
    confirm = input("Continue? (y/n): ")
    if confirm.lower() != 'y':
        print("Cancelled.")
        sys.exit(0)
    
    asyncio.run(fresh_auth())