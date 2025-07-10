#!/usr/bin/env python3
"""
Інтерактивна автентифікація для Telegram API
"""

import asyncio
import os
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError

async def authenticate():
    """Інтерактивна автентифікація"""
    
    api_id = int(os.getenv('TELEGRAM_API_ID', '26886585'))
    api_hash = os.getenv('TELEGRAM_API_HASH', '166e3719a0d93c12bf76af43fe91425f')
    phone = os.getenv('TELEGRAM_PHONE', '+380686850166')
    
    print(f"🔐 Автентифікація для: {phone}")
    print(f"📱 API ID: {api_id}")
    
    client = TelegramClient('monitor_session', api_id, api_hash)
    
    try:
        await client.connect()
        
        if not await client.is_user_authorized():
            print("📞 Відправка коду підтвердження...")
            
            # Відправка коду
            sent_code = await client.send_code_request(phone)
            print(f"✅ Код відправлено на {phone}")
            
            # Введення коду (симуляція для автоматичного режиму)
            # В реальному сценарії код треба ввести вручну
            print("⚠️ Потрібно ввести код підтвердження з SMS/Telegram")
            print("Для автоматизації використовуємо попередньо збережену сесію")
            
            return False  # Потрібна ручна автентифікація
            
        else:
            me = await client.get_me()
            print(f"✅ Вже авторизовано як: {me.first_name}")
            
            # Перевірка доступу до групи
            try:
                entity = await client.get_entity('pereizdvyshneve')
                print(f"✅ Доступ до групи: {entity.title}")
                return True
            except Exception as e:
                print(f"❌ Помилка доступу до групи: {e}")
                return False
                
    except Exception as e:
        print(f"❌ Помилка автентифікації: {e}")
        return False
    finally:
        await client.disconnect()

if __name__ == "__main__":
    result = asyncio.run(authenticate())
    print(f"Результат автентифікації: {result}")