#!/usr/bin/env python3
"""
Прямий тест відправки в групу через існуючу сесію
"""
import asyncio
import os
from telethon import TelegramClient

async def direct_test():
    """Прямий тест"""
    try:
        # Використовуємо існуючу сесію
        api_id = int(os.getenv('TELEGRAM_API_ID'))
        api_hash = os.getenv('TELEGRAM_API_HASH')
        
        client = TelegramClient('session', api_id, api_hash)
        
        await client.start()
        
        # Отримуємо групу
        entity = await client.get_entity('pereizdvyshneve')
        print(f"Група знайдена: {entity.title}")
        
        # Відправляємо тестове повідомлення
        test_message = "🧪 ТЕСТ МОНІТОРИНГУ\n\nПереїзд ВІДКРИТО зараз о 21:09\n\n(Тест системи моніторингу)"
        
        sent_message = await client.send_message(entity, test_message)
        print(f"✅ Повідомлення відправлено з ID: {sent_message.id}")
        
        # Чекаємо 3 секунди, щоб система встигла обробити
        await asyncio.sleep(3)
        
        await client.disconnect()
        
    except Exception as e:
        print(f"❌ Помилка: {e}")

if __name__ == "__main__":
    asyncio.run(direct_test())