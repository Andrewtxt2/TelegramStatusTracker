#!/usr/bin/env python3
"""
Відправка тестового повідомлення в групу для перевірки роботи бота
"""
import asyncio
import os
from telethon import TelegramClient

async def send_test_message():
    """Відправити тестове повідомлення в групу"""
    try:
        # Ініціалізація клієнта
        api_id = int(os.getenv('TELEGRAM_API_ID'))
        api_hash = os.getenv('TELEGRAM_API_HASH')
        
        client = TelegramClient('session', api_id, api_hash)
        
        await client.start()
        
        # Відправляємо тестове повідомлення
        entity = await client.get_entity('pereizdvyshneve')
        
        test_message = "🧪 ТЕСТОВЕ ПОВІДОМЛЕННЯ 🧪\n\n✅ Переїзд ВІДКРИТО\n\n⏰ Час: зараз\n\n(Це тестове повідомлення для перевірки роботи бота)"
        
        await client.send_message(entity, test_message)
        print("✅ Тестове повідомлення відправлено")
        
        await client.disconnect()
        
    except Exception as e:
        print(f"❌ Помилка відправки: {e}")

if __name__ == "__main__":
    asyncio.run(send_test_message())