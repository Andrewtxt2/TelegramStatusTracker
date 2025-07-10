#!/usr/bin/env python3
"""
New account authentication setup
Creates fresh session with new Telegram account
"""

import asyncio
import os
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError

# API credentials (same API app, different user account)
API_ID = 26886585
API_HASH = "166e3719a0d93c12bf76af43fe91425f"

async def setup_new_account():
    """Setup authentication with new account"""
    
    print("🔄 Setting up new account authentication...")
    
    # Clean up old sessions
    old_sessions = [
        'auth_session.session',
        'new_account.session',
        'fresh_session.session'
    ]
    
    for session_file in old_sessions:
        if os.path.exists(session_file):
            os.remove(session_file)
            print(f"🗑️ Removed old session: {session_file}")
    
    # Get new phone number
    phone = input("📞 Enter new phone number (with country code, e.g., +380123456789): ")
    
    # Create new session
    session_name = 'new_account'
    client = TelegramClient(session_name, API_ID, API_HASH)
    
    try:
        await client.connect()
        
        print(f"📨 Sending code to {phone}...")
        await client.send_code_request(phone)
        
        # Get code from user
        code = input("Enter the code you received: ")
        
        try:
            await client.sign_in(phone, code)
            print("✅ Authentication successful!")
            
        except SessionPasswordNeededError:
            password = input("🔒 Enter your 2FA password: ")
            await client.sign_in(password=password)
            print("✅ Authentication with 2FA successful!")
        
        # Test the new account
        me = await client.get_me()
        print(f"👤 Logged in as: {me.first_name}")
        
        # Create auth_session.session for bot
        await client.disconnect()
        
        # Copy to main session file
        import shutil
        shutil.copy('new_account.session', 'auth_session.session')
        print("✅ Session saved as auth_session.session")
        
        # Update config with new phone
        import json
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
            
            config['mtproto_settings']['phone'] = phone
            
            with open('config.json', 'w') as f:
                json.dump(config, f, indent=2)
            
            print("✅ Config updated with new phone number")
            
        except Exception as e:
            print(f"⚠️ Config update failed: {e}")
        
        print("\n🎉 New account setup complete!")
        print("You can now restart the bot with the new account.")
        
        return True
        
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 New Account Authentication Setup")
    print("This will create a fresh session with a new Telegram account.")
    print("Make sure you have access to the new phone number.")
    print()
    
    try:
        success = asyncio.run(setup_new_account())
        if success:
            print("\n✅ Setup completed successfully!")
            print("Run: python3 main.py to start the bot")
        else:
            print("\n❌ Setup failed")
    except KeyboardInterrupt:
        print("\n❌ Setup cancelled by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")