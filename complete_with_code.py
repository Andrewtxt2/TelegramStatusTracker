#!/usr/bin/env python3
"""
Complete authentication with provided code
"""

import asyncio
import os
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError

# API credentials
API_ID = 29299324
API_HASH = "c262483dda2739c72637661b537dccac"
CODE = "81638"

async def complete_auth():
    """Complete authentication with code"""
    
    print(f"🔄 Completing authentication with code: {CODE}")
    
    # Load saved state
    try:
        with open('auth_state.txt', 'r') as f:
            lines = f.read().strip().split('\n')
            phone = lines[0]
            phone_code_hash = lines[1]
        print(f"✅ Using saved state: {phone}")
    except:
        print("❌ No saved authentication state")
        return False
    
    # Use existing session
    session_name = 'auth_session'
    client = TelegramClient(session_name, API_ID, API_HASH)
    
    try:
        await client.connect()
        
        # Sign in with code
        print(f"🔐 Signing in...")
        await client.sign_in(phone, CODE, phone_code_hash=phone_code_hash)
        
        # Test connection
        me = await client.get_me()
        print(f"✅ Successfully authenticated as: {me.first_name}")
        
        # Notify admins
        from telegram import Bot
        bot = Bot(token="8189087426:AAF2XtTEwDRbwvWny-Hi2BPz_0ZeJHh9DEc")
        admin_ids = [6395626140, 7766810783, 564704015]
        
        message = (
            f"🎉 АВТЕНТИФІКАЦІЯ ЗАВЕРШЕНА\n\n"
            f"👤 Акаунт: {me.first_name}\n"
            f"📱 Номер: {phone}\n\n"
            f"✅ Сесія створена: auth_session.session\n"
            f"✅ Система готова до запуску\n\n"
            f"Бот зараз буде запущений з усіма функціями!"
        )
        
        for admin_id in admin_ids:
            try:
                await bot.send_message(chat_id=admin_id, text=message)
            except:
                pass
        
        await client.disconnect()
        
        # Clean up
        if os.path.exists('auth_state.txt'):
            os.remove('auth_state.txt')
        if os.path.exists('code_hash.txt'):
            os.remove('code_hash.txt')
        
        print("✅ Authentication completed successfully")
        return True
        
    except SessionPasswordNeededError:
        print("❌ 2FA password required")
        return False
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(complete_auth())
    if success:
        print("\n🎉 Authentication complete!")
        print("Starting bot now...")
    else:
        print("\n❌ Authentication failed")