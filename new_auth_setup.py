#!/usr/bin/env python3
"""
Setup authentication for new account
API ID: 29299324
Phone: +380633952873
"""

import asyncio
import os
from telethon import TelegramClient

# New account credentials
API_ID = 29299324
API_HASH = 'c262483dda2739c72637661b537dccac'
PHONE = '+380633952873'

async def setup_new_auth():
    """Setup authentication for new account"""
    session_name = 'new_auth_session'
    
    print(f"🔐 Setting up authentication for {PHONE}...")
    
    # Create client
    client = TelegramClient(session_name, API_ID, API_HASH)
    
    try:
        # Connect
        await client.connect()
        
        # Send code request
        if not await client.is_user_authorized():
            await client.send_code_request(PHONE)
            print(f"📱 Code sent to {PHONE}")
            
            # Get code from user
            code = input("Enter the code you received: ")
            
            try:
                # Sign in
                await client.sign_in(PHONE, code)
                print("✅ Authentication successful!")
                
                # Get user info
                me = await client.get_me()
                print(f"👤 Logged in as: {me.first_name} {me.last_name or ''}")
                
                # Test connection
                print("🧪 Testing connection...")
                dialogs = await client.get_dialogs(limit=5)
                print(f"📋 Found {len(dialogs)} dialogs")
                
                print(f"💾 Session saved as: {session_name}.session")
                
            except Exception as e:
                print(f"❌ Authentication failed: {e}")
                
                # Try 2FA if needed
                if "Two-step verification" in str(e):
                    password = input("Enter your 2FA password: ")
                    await client.sign_in(password=password)
                    print("✅ 2FA authentication successful!")
                    
                    # Get user info
                    me = await client.get_me()
                    print(f"👤 Logged in as: {me.first_name} {me.last_name or ''}")
                    
        else:
            print("✅ Already authenticated")
            me = await client.get_me()
            print(f"👤 Logged in as: {me.first_name} {me.last_name or ''}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        
    finally:
        await client.disconnect()
        print("🔌 Disconnected")

if __name__ == "__main__":
    asyncio.run(setup_new_auth())