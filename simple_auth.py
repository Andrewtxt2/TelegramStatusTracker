#!/usr/bin/env python3
"""
Проста автентифікація з номером телефону
"""
import asyncio
import os
from telethon import TelegramClient

async def simple_auth():
    """Проста автентифікація"""
    try:
        api_id = int(os.getenv('TELEGRAM_API_ID'))
        api_hash = os.getenv('TELEGRAM_API_HASH')
        phone = '+380633952873'  # Номер телефону з попередньої автентифікації
        
        print("🔑 Автентифікація...")
        
        client = TelegramClient('session', api_id, api_hash)
        
        # Підключаємось з номером телефону
        await client.start(phone=phone)
        
        # Перевіряємо підключення
        me = await client.get_me()
        print(f"✅ Підключено як: {me.first_name}")
        
        # Перевіряємо доступ до групи
        entity = await client.get_entity('pereizdvyshneve')
        print(f"✅ Група знайдена: {entity.title}")
        
        await client.disconnect()
        print("✅ Автентифікація успішна!")
        
    except Exception as e:
        print(f"❌ Помилка: {e}")

if __name__ == "__main__":
    asyncio.run(simple_auth())