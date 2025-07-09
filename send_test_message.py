#!/usr/bin/env python3
"""
Відправка тестового повідомлення через Bot API
"""
import asyncio
import os
from telegram import Bot

async def send_test_message():
    """Відправка тестового повідомлення через бота"""
    try:
        # Отримання токену з конфігурації
        import json
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not bot_token:
            print("❌ Токен бота не знайдено в змінних середовища")
            return
        
        bot = Bot(token=bot_token)
        
        # Відправка в адмін-групу (симулюючи повідомлення з групи)
        admin_group = os.getenv('TELEGRAM_ADMIN_GROUP', '@pereyizd_bot')
        
        test_message = """🧪 ТЕСТОВЕ ПОВІДОМЛЕННЯ
        
📍 Джерело: Група моніторингу
📝 Текст: Переїзд ВІДКРИТО зараз о 21:53

🤖 Аналіз AI:
✅ Статус: ВІДКРИТО
📊 Упевненість: 95%

Оберіть дію:"""
        
        # Клавіатура для адміністраторів
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        
        keyboard = [
            [
                InlineKeyboardButton("✅ ВІДКРИТО", callback_data="approve_open_test"),
                InlineKeyboardButton("❌ ЗАКРИТО", callback_data="approve_closed_test")
            ],
            [InlineKeyboardButton("🗑 ВІДХИЛИТИ", callback_data="reject_test")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Відправка повідомлення адміністраторам
        admin_ids = [564704015, 7766810783]
        
        for admin_id in admin_ids:
            try:
                await bot.send_message(
                    chat_id=admin_id,
                    text=test_message,
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
                print(f"✅ Тестове повідомлення відправлено адміністратору {admin_id}")
            except Exception as e:
                print(f"❌ Помилка відправки адміністратору {admin_id}: {e}")
        
    except Exception as e:
        print(f"❌ Загальна помилка: {e}")

if __name__ == "__main__":
    asyncio.run(send_test_message())