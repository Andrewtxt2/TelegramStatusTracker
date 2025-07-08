#!/usr/bin/env python3
"""
Швидка автентифікація для нової сесії
"""
import asyncio
import os
from telethon import TelegramClient

async def quick_auth():
    """Швидка автентифікація"""
    try:
        api_id = int(os.getenv('TELEGRAM_API_ID'))
        api_hash = os.getenv('TELEGRAM_API_HASH')
        
        print("🔑 Створення нової сесії...")
        
        # Створюємо нову сесію
        client = TelegramClient('session', api_id, api_hash)
        
        # Підключаємося
        await client.start()
        
        # Перевіряємо підключення
        me = await client.get_me()
        print(f"✅ Підключено як: {me.first_name}")
        
        # Перевіряємо доступ до групи
        try:
            entity = await client.get_entity('pereizdvyshneve')
            print(f"✅ Група знайдена: {entity.title}")
        except Exception as e:
            print(f"❌ Помилка доступу до групи: {e}")
        
        await client.disconnect()
        print("✅ Сесія створена успішно!")
        
    except Exception as e:
        print(f"❌ Помилка: {e}")

if __name__ == "__main__":
    asyncio.run(quick_auth())