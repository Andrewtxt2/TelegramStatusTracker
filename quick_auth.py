#!/usr/bin/env python3
"""
Швидка автентифікація для відновлення сесії
"""
import asyncio
import os
from telethon import TelegramClient

async def quick_auth():
    """Швидка автентифікація"""
    try:
        api_id = int(os.getenv('TELEGRAM_API_ID'))
        api_hash = os.getenv('TELEGRAM_API_HASH')
        
        print("🔐 Створення нової сесії...")
        client = TelegramClient('session', api_id, api_hash)
        
        # Автентифікація
        await client.start(phone='+380633952873')
        
        print("✅ Автентифікація успішна!")
        
        # Тест підключення
        me = await client.get_me()
        print(f"✅ Підключено як: {me.first_name}")
        
        # Тест доступу до групи
        try:
            entity = await client.get_entity('pereizdvyshneve')
            print(f"✅ Доступ до групи: {entity.title}")
        except Exception as e:
            print(f"❌ Помилка доступу до групи: {e}")
        
        await client.disconnect()
        print("✅ Сесія збережена")
        
    except Exception as e:
        print(f"❌ Помилка автентифікації: {e}")

if __name__ == "__main__":
    asyncio.run(quick_auth())