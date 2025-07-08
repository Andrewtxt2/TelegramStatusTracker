#!/usr/bin/env python3
"""
Тест роботи Telegram бота
"""

import asyncio
import aiohttp
from config import Config

async def test_telegram_bot():
    """Тест бота"""
    config = Config()
    bot_token = config.bot_token
    admin_ids = config.admin_user_ids
    
    if not bot_token:
        print("❌ Токен бота не знайдено")
        return
    
    print(f"🤖 Тестування бота...")
    
    # Отримання інформації про бота
    async with aiohttp.ClientSession() as session:
        try:
            # Інформація про бота
            url = f"https://api.telegram.org/bot{bot_token}/getMe"
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data['ok']:
                        bot_info = data['result']
                        print(f"✅ Бот активний: @{bot_info['username']}")
                        print(f"📱 Посилання: https://t.me/{bot_info['username']}")
                        print(f"🆔 ID: {bot_info['id']}")
                    else:
                        print(f"❌ Помилка API: {data}")
                        return
                else:
                    print(f"❌ HTTP помилка: {resp.status}")
                    return
        except Exception as e:
            print(f"❌ Помилка підключення: {e}")
            return
    
    # Тест відправки повідомлень
    print(f"\n📨 Тестування відправки повідомлень адміністраторам...")
    
    test_message = """
🔄 **ТЕСТ СИСТЕМИ АВТОМАТИЧНОГО МОНІТОРИНГУ**

Це тестове повідомлення для перевірки роботи системи.

✅ Якщо ви отримали це повідомлення, значить:
- Бот працює правильно
- Ваш чат з ботом налаштовано
- Автоматичний моніторинг активний

🔧 **Наступні кроки:**
1. Система автоматично моніторить групу переїзду
2. При появі нових повідомлень ви отримаєте сповіщення
3. Можете схвалювати або відхиляти повідомлення

⚡ _Це автоматичне тестове повідомлення_
"""

    success_count = 0
    async with aiohttp.ClientSession() as session:
        for admin_id in admin_ids:
            try:
                url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                payload = {
                    'chat_id': admin_id,
                    'text': test_message,
                    'parse_mode': 'Markdown'
                }
                
                async with session.post(url, json=payload) as resp:
                    response_data = await resp.json()
                    
                    if resp.status == 200 and response_data['ok']:
                        print(f"✅ Успішно відправлено адміністратору {admin_id}")
                        success_count += 1
                    else:
                        error_desc = response_data.get('description', 'Unknown error')
                        print(f"❌ Помилка для адміністратора {admin_id}: {error_desc}")
                        
                        if 'bot can\'t initiate conversation' in error_desc:
                            print(f"   💡 Рішення: Адміністратор {admin_id} має написати боту /start")
                        elif 'chat not found' in error_desc:
                            print(f"   💡 Рішення: Перевірте правильність ID {admin_id}")
                        
            except Exception as e:
                print(f"❌ Помилка відправки {admin_id}: {e}")
    
    print(f"\n📊 Результат: {success_count}/{len(admin_ids)} адміністраторів отримали повідомлення")
    
    if success_count == 0:
        print("⚠️  Жоден адміністратор не отримав повідомлення")
    elif success_count < len(admin_ids):
        print("⚠️  Не всі адміністратори отримали повідомлення")
        print("💡 Незналажені адміністратори повинні написати боту /start")
    else:
        print("✅ Всі адміністратори налаштовані правильно")

if __name__ == "__main__":
    asyncio.run(test_telegram_bot())