#!/usr/bin/env python3
"""
Quick new account setup
Creates session ready for new account authentication
"""

import asyncio
import os
from telethon import TelegramClient
from telegram import Bot

# API credentials
API_ID = 26886585
API_HASH = "166e3719a0d93c12bf76af43fe91425f"
BOT_TOKEN = "8189087426:AAF2XtTEwDRbwvWny-Hi2BPz_0ZeJHh9DEc"

async def setup_new_account():
    """Setup for new account authentication"""
    
    print("🔄 Preparing new account setup...")
    
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
    
    # Notify admins about new account setup needed
    try:
        bot = Bot(token=BOT_TOKEN)
        admin_ids = [6395626140, 7766810783, 564704015]
        
        message = (
            "🔐 НАЛАШТУВАННЯ НОВОГО АКАУНТА\n\n"
            "Система очищена від старих сесій.\n"
            "Для завершення налаштування потрібно:\n\n"
            "1️⃣ Створити новий Telegram акаунт\n"
            "2️⃣ Увійти в нього через @BotFather\n"
            "3️⃣ Додати номер телефону нового акаунта\n\n"
            "Після цього система буде працювати повністю:\n"
            "✅ Моніторинг групи\n"
            "✅ Кнопки схвалення\n"
            "✅ Публікація в канал\n\n"
            "Готові продовжити з новим акаунтом?"
        )
        
        for admin_id in admin_ids:
            try:
                await bot.send_message(chat_id=admin_id, text=message)
                print(f"✅ Notified admin {admin_id}")
            except Exception as e:
                print(f"❌ Failed to notify admin {admin_id}: {e}")
        
        print("\n🎉 Setup prepared successfully!")
        print("✅ Old sessions cleaned")
        print("✅ Admins notified")
        print("✅ Ready for new account authentication")
        
        return True
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(setup_new_account())
    if success:
        print("\n🚀 Ready for new account!")
        print("Please provide the new phone number when ready.")
    else:
        print("\n❌ Setup failed")