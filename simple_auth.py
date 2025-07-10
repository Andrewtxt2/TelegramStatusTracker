#!/usr/bin/env python3
"""
Simple authentication - just request code
"""

import asyncio
import os
from telethon import TelegramClient

# API credentials
API_ID = 29299324
API_HASH = "c262483dda2739c72637661b537dccac"
PHONE = "+380633952873"

async def request_new_code():
    """Request new authentication code"""
    
    print(f"🔄 Requesting new code for {PHONE}...")
    
    # Clean up old sessions
    if os.path.exists('auth_session.session'):
        os.remove('auth_session.session')
    if os.path.exists('new_account.session'):
        os.remove('new_account.session')
    
    # Create new session
    session_name = 'auth_session'
    client = TelegramClient(session_name, API_ID, API_HASH)
    
    try:
        await client.connect()
        
        # Request code
        print("📨 Sending new code...")
        sent_code = await client.send_code_request(PHONE)
        print(f"✅ New code sent!")
        print(f"📱 Check SMS on {PHONE}")
        
        # Save the phone_code_hash for later use
        with open('code_hash.txt', 'w') as f:
            f.write(sent_code.phone_code_hash)
        
        print(f"✅ Code hash saved: {sent_code.phone_code_hash}")
        
        # Notify admins
        from telegram import Bot
        bot = Bot(token="8189087426:AAF2XtTEwDRbwvWny-Hi2BPz_0ZeJHh9DEc")
        admin_ids = [6395626140, 7766810783, 564704015]
        
        message = (
            f"📨 НОВИЙ КОД ВІДПРАВЛЕНО\n\n"
            f"📱 Номер: {PHONE}\n"
            f"🔐 Перевірте SMS та надайте новий код\n\n"
            f"Після отримання коду система буде готова до запуску з усіма функціями."
        )
        
        for admin_id in admin_ids:
            try:
                await bot.send_message(chat_id=admin_id, text=message)
            except:
                pass
        
        await client.disconnect()
        
        print("✅ New code requested successfully")
        print("📱 Check your SMS and provide the new code")
        return True
        
    except Exception as e:
        print(f"❌ Code request failed: {e}")
        await client.disconnect()
        return False

if __name__ == "__main__":
    success = asyncio.run(request_new_code())
    if success:
        print("\n📨 New code sent!")
        print("Please provide the new SMS code when received")
    else:
        print("\n❌ Failed to send new code")