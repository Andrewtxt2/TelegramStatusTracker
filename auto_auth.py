#!/usr/bin/env python3
"""
Auto authentication script for Telegram bot
Creates fresh session automatically
"""

import os
import sys
import asyncio
import time
from telethon import TelegramClient

# API credentials
API_ID = 26886585
API_HASH = "166e3719a0d93c12bf76af43fe91425f"
PHONE = "+380 68 685 01 66"

async def auto_auth():
    """Create fresh authentication session automatically"""
    
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
            try:
                os.remove(session_file)
                print(f"🗑️ Removed old session: {session_file}")
            except:
                pass
    
    # Create new session with unique name
    session_name = f'auto_auth_session_{int(time.time())}'
    
    print(f"📱 Creating new session: {session_name}")
    
    # Create client
    client = TelegramClient(session_name, API_ID, API_HASH)
    
    try:
        await client.connect()
        
        if not await client.is_user_authorized():
            print(f"📞 Requesting code for: {PHONE}")
            
            try:
                await client.send_code_request(PHONE)
                print("📨 Code request sent successfully!")
                
                # Since we can't get interactive input, we'll create a temporary session
                # and notify the user to provide authentication through a different method
                print("\n🔐 AUTHENTICATION REQUIRED")
                print("A code has been sent to your phone.")
                print("Please check your messages and provide the code.")
                
                # For now, we'll disconnect and let the user handle authentication
                await client.disconnect()
                
                # Create notification
                from telegram import Bot
                bot = Bot(token="8189087426:AAF2XtTEwDRbwvWny-Hi2BPz_0ZeJHh9DEc")
                
                # Notify all admins
                admin_ids = [6395626140, 7766810783, 564704015]
                for admin_id in admin_ids:
                    try:
                        await bot.send_message(
                            chat_id=admin_id,
                            text="🔐 ПОТРІБНА АВТЕНТИФІКАЦІЯ\n\n"
                                 "Система потребує повторної автентифікації.\n"
                                 "Код відправлено на номер +380 68 685 01 66\n\n"
                                 "Будь ласка, повідомте код через команду /auth <код>"
                        )
                    except Exception as e:
                        print(f"Failed to notify admin {admin_id}: {e}")
                
                return session_name
                
            except Exception as e:
                print(f"❌ Failed to request code: {e}")
                return None
        else:
            # Already authorized
            me = await client.get_me()
            print(f"👤 Already logged in as: {me.first_name}")
            
            # Create a copy as auth_session.session for bot to use
            await client.disconnect()
            
            # Copy session file
            import shutil
            shutil.copy(f'{session_name}.session', 'auth_session.session')
            print("✅ Session copied to auth_session.session")
            
            print("\n🎉 Auto authentication complete!")
            return session_name
            
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return None

if __name__ == "__main__":
    result = asyncio.run(auto_auth())
    if result:
        print(f"✅ Session created: {result}")
    else:
        print("❌ Authentication failed")