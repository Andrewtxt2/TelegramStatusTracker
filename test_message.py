#!/usr/bin/env python3
"""
Тест для перевірки роботи системи
"""
import asyncio
from telethon import TelegramClient
import os

async def test_message():
    api_id = int(os.getenv('TELEGRAM_API_ID'))
    api_hash = os.getenv('TELEGRAM_API_HASH')
    
    client = TelegramClient('test_session', api_id, api_hash)
    await client.start()
    
    # Перевірка чи є доступ до групи
    try:
        entity = await client.get_entity('pereizdvyshneve')
        print(f"✅ Група знайдена: {entity.title}")
        print(f"ID групи: {entity.id}")
        print(f"Тип: {type(entity)}")
        
        # Отримати останні повідомлення
        messages = await client.get_messages(entity, limit=3)
        print(f"\nОстанні {len(messages)} повідомлень:")
        for msg in messages:
            if msg.text:
                print(f"ID: {msg.id}, Текст: {msg.text[:50]}...")
                
    except Exception as e:
        print(f"Помилка: {e}")
    
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(test_message())