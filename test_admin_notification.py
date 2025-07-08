#!/usr/bin/env python3
"""
Тест відправки повідомлень адміністраторам
"""

import asyncio
import aiohttp
from config import Config

async def test_admin_notification():
    """Тест відправки повідомлень адміністраторам"""
    config = Config()
    
    bot_token = config.bot_token
    admin_ids = config.admin_user_ids
    
    print(f"Bot token: {bot_token[:10]}..." if bot_token else "Bot token відсутній")
    print(f"Admin IDs: {admin_ids}")
    
    test_message = """
🔄 **ТЕСТ АВТОМАТИЧНОГО МОНІТОРИНГУ**

👤 **Від:** Тест користувач
🕐 **Час:** 2025-07-08 10:50:00
🤖 **Статус:** 🟢 ВІДКРИТО

📝 **Текст:**
Тестове повідомлення для перевірки роботи автоматичного моніторингу

⚡ _Це тестове повідомлення_
"""

    async with aiohttp.ClientSession() as session:
        for admin_id in admin_ids:
            try:
                url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                payload = {
                    'chat_id': admin_id,
                    'text': test_message,
                    'parse_mode': 'Markdown'
                }
                
                print(f"Відправка тестового повідомлення адміністратору {admin_id}...")
                
                async with session.post(url, json=payload) as resp:
                    response_text = await resp.text()
                    
                    if resp.status == 200:
                        print(f"✅ Успішно відправлено {admin_id}")
                    else:
                        print(f"❌ Помилка {admin_id}: {resp.status}")
                        print(f"Відповідь: {response_text}")
                        
            except Exception as e:
                print(f"❌ Помилка відправки {admin_id}: {e}")

if __name__ == "__main__":
    asyncio.run(test_admin_notification())