#!/usr/bin/env python3
"""
Quick authentication using telethon's built-in start() method
"""

import asyncio
import os
from telethon import TelegramClient

# API credentials
API_ID = 29299324
API_HASH = "c262483dda2739c72637661b537dccac"
PHONE = "+380633952873"

async def quick_auth():
    """Quick authentication using start() method"""
    
    print(f"🔄 Quick authentication for {PHONE}...")
    
    # Clean up old sessions
    if os.path.exists('auth_session.session'):
        os.remove('auth_session.session')
    
    # Create new session
    session_name = 'auth_session'
    client = TelegramClient(session_name, API_ID, API_HASH)
    
    try:
        # This will automatically handle the authentication flow
        await client.start(phone=PHONE)
        
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
            f"📱 Номер: {PHONE}\n\n"
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
        
        print("✅ Authentication completed successfully")
        print("✅ Session saved as auth_session.session")
        
        return True
        
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        await client.disconnect()
        return False

if __name__ == "__main__":
    success = asyncio.run(quick_auth())
    if success:
        print("\n🎉 Authentication complete!")
        print("Ready to start bot with: python3 main.py")
    else:
        print("\n❌ Authentication failed")