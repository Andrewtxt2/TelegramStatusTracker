#!/usr/bin/env python3
"""
Автентифікація для production bot
"""

import asyncio
import os
from telethon import TelegramClient

async def authenticate():
    api_id = int(os.getenv('TELEGRAM_API_ID', '0'))
    api_hash = os.getenv('TELEGRAM_API_HASH', '')
    
    client = TelegramClient('session', api_id, api_hash)
    
    print("📱 Введіть номер телефону: +380686850166")
    
    try:
        await client.start(
            phone='+380686850166',
            code_callback=lambda: input('🔢 Введіть код з SMS: ')
        )
        
        me = await client.get_me()
        print(f"✅ Автентифікація успішна: {me.first_name}")
        
    except Exception as e:
        print(f"❌ Помилка: {e}")
        
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(authenticate())