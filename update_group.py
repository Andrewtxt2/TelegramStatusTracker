#!/usr/bin/env python3
"""
Update group monitoring without restart
"""

import asyncio
import os
from telethon import TelegramClient
from telegram import Bot

# Configuration
API_ID = os.getenv('TELEGRAM_API_ID', '26886585')
API_HASH = os.getenv('TELEGRAM_API_HASH', '166e3719a0d93c12bf76af43fe91425f')
BOT_TOKEN = '8189087426:AAF2XtTEwDRbwvWny-Hi2BPz_0ZeJHh9DEc'
ADMIN_IDS = [6395626140, 7766810783]
NEW_SOURCE_GROUP = 'https://t.me/rfsdxv'

async def update_group():
    """Update monitoring group"""
    try:
        # Test new group access
        client = TelegramClient('working_session', API_ID, API_HASH)
        await client.start()
        
        # Get new group
        group_username = NEW_SOURCE_GROUP.split('/')[-1]
        new_group = await client.get_entity(group_username)
        
        print(f"✅ New group found: {new_group.title}")
        print(f"✅ Group ID: {new_group.id}")
        
        # Test message access
        messages = await client.get_messages(new_group, limit=3)
        print(f"✅ Can access messages: {len(messages)} found")
        
        # Notify admins
        bot = Bot(token=BOT_TOKEN)
        notification = (
            f"🔄 ГРУПА МОНІТОРИНГУ ЗМІНЕНА!\n\n"
            f"Нова група: {new_group.title}\n"
            f"Посилання: {NEW_SOURCE_GROUP}\n"
            f"ID: {new_group.id}\n"
            f"Доступ до повідомлень: ✅\n\n"
            f"Перезапускаю систему з новою групою..."
        )
        
        for admin_id in ADMIN_IDS:
            await bot.send_message(chat_id=admin_id, text=notification)
            
        await client.disconnect()
        print("✅ Group update completed")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        
        # Notify about error
        bot = Bot(token=BOT_TOKEN)
        error_msg = f"❌ Помилка зміни групи: {str(e)}\n\nПеревірте доступ до https://t.me/rfsdxv"
        
        for admin_id in ADMIN_IDS:
            await bot.send_message(chat_id=admin_id, text=error_msg)

if __name__ == "__main__":
    asyncio.run(update_group())