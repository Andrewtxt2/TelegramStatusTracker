#!/usr/bin/env python3
"""
Enter authentication code for new account
"""

import asyncio
import os
from telethon import TelegramClient

# New account credentials
API_ID = 29299324
API_HASH = 'c262483dda2739c72637661b537dccac'
PHONE = '+380633952873'

async def enter_code():
    """Enter authentication code"""
    session_name = 'new_auth_session'
    
    # Read code from file
    if os.path.exists('auth_code.txt'):
        with open('auth_code.txt', 'r') as f:
            code = f.read().strip()
        print(f"📱 Using code: {code}")
    else:
        print("❌ File 'auth_code.txt' not found")
        print("Create the file with your authentication code")
        return False
    
    # Create client
    client = TelegramClient(session_name, API_ID, API_HASH)
    
    try:
        # Connect
        await client.connect()
        print("✅ Connected to Telegram")
        
        # Sign in with code
        try:
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
            
            # Remove code file
            os.remove('auth_code.txt')
            print("🗑️ Removed auth_code.txt")
            
            return True
            
        except Exception as e:
            print(f"❌ Authentication failed: {e}")
            
            # Try 2FA if needed
            if "Two-step verification" in str(e):
                if os.path.exists('2fa_password.txt'):
                    with open('2fa_password.txt', 'r') as f:
                        password = f.read().strip()
                    
                    await client.sign_in(password=password)
                    print("✅ 2FA authentication successful!")
                    
                    # Get user info
                    me = await client.get_me()
                    print(f"👤 Logged in as: {me.first_name} {me.last_name or ''}")
                    
                    # Remove password file
                    os.remove('2fa_password.txt')
                    print("🗑️ Removed 2fa_password.txt")
                    
                    return True
                else:
                    print("❌ 2FA required. Create '2fa_password.txt' with your password")
                    return False
            
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
        
    finally:
        await client.disconnect()
        print("🔌 Disconnected")

if __name__ == "__main__":
    asyncio.run(enter_code())