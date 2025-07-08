#!/usr/bin/env python3
"""
Скрипт для налаштування автентифікації Telegram API
Запустіть цей скрипт один раз для авторизації
"""

import asyncio
import os
from telethon import TelegramClient

async def setup_authentication():
    """Налаштування автентифікації"""
    
    api_id = os.getenv('TELEGRAM_API_ID')
    api_hash = os.getenv('TELEGRAM_API_HASH')
    phone = os.getenv('TELEGRAM_PHONE')
    
    if not all([api_id, api_hash, phone]):
        print("❌ Відсутні необхідні змінні середовища!")
        print("Потрібні: TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_PHONE")
        return False
        
    try:
        api_id = int(api_id)
    except ValueError:
        print("❌ Невірний формат API_ID")
        return False
    
    print(f"📱 Налаштування автентифікації для {phone}")
    print(f"🔑 API ID: {api_id}")
    
    client = TelegramClient('auto_session', api_id, api_hash)
    
    try:
        print("🔄 Підключення до Telegram...")
        await client.start(phone=phone)
        
        if await client.is_user_authorized():
            me = await client.get_me()
            print(f"✅ Успішно авторизовано як: {me.first_name}")
            
            # Перевірка доступу до групи
            try:
                entity = await client.get_entity('pereizdvyshneve')
                print(f"✅ Доступ до групи підтверджено: {entity.title}")
            except Exception as e:
                print(f"⚠️ Не вдалося отримати доступ до групи: {e}")
                print("Переконайтеся, що ви є учасником групи https://t.me/pereizdvyshneve")
                
            return True
        else:
            print("❌ Автентифікація не вдалася")
            return False
            
    except Exception as e:
        print(f"❌ Помилка під час автентифікації: {e}")
        return False
    finally:
        await client.disconnect()

if __name__ == "__main__":
    success = asyncio.run(setup_authentication())
    if success:
        print("\n🎉 Автентифікація налаштована успішно!")
        print("Тепер можна запускати автоматичний моніторинг командою:")
        print("python auto_monitor.py")
    else:
        print("\n❌ Налаштування автентифікації не вдалося!")