#!/usr/bin/env python3
"""
Простий тест відправки повідомлення в групу
"""
import asyncio
import os
from telethon import TelegramClient

async def send_simple_test():
    """Відправити просте тестове повідомлення"""
    try:
        # Ініціалізація клієнта з новою сесією
        api_id = int(os.getenv('TELEGRAM_API_ID'))
        api_hash = os.getenv('TELEGRAM_API_HASH')
        
        client = TelegramClient('test_session', api_id, api_hash)
        
        await client.start()
        
        # Відправляємо тестове повідомлення
        entity = await client.get_entity('pereizdvyshneve')
        
        test_message = "🧪 ТЕСТ СИСТЕМИ\n\nПереїзд ВІДКРИТО зараз\n\n(Тест 21:09)"
        
        await client.send_message(entity, test_message)
        print("✅ Тестове повідомлення відправлено")
        
        await client.disconnect()
        
    except Exception as e:
        print(f"❌ Помилка: {e}")

if __name__ == "__main__":
    asyncio.run(send_simple_test())