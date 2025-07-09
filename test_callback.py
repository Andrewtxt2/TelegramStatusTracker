#!/usr/bin/env python3
"""
Тест кнопок callback
"""

import asyncio
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from config import Config

async def test_callback_buttons():
    """Тест відправки повідомлення з кнопками"""
    config = Config()
    bot = Bot(token=config.bot_token)
    admin_id = 6395626140  # Основний адміністратор
    
    test_message = """
🔄 **ТЕСТ КНОПОК СХВАЛЕННЯ**

👤 **Від:** Тест користувач
🕐 **Час:** 2025-07-08 11:00:00
🤖 **AI Аналіз:** ⚪ НЕВІДОМО

📝 **Текст:**
Тестове повідомлення для перевірки кнопок схвалення

⚡ _Натисніть одну з кнопок нижче_
"""

    # Створюємо кнопки
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ ВІДКРИТО", callback_data="approve_open_123456"),
            InlineKeyboardButton("❌ ЗАКРИТО", callback_data="approve_closed_123456")
        ],
        [
            InlineKeyboardButton("🗑 ВІДХИЛИТИ", callback_data="reject_123456")
        ]
    ])
    
    try:
        # Відправляємо повідомлення з кнопками
        message = await bot.send_message(
            chat_id=admin_id,
            text=test_message,
            parse_mode='Markdown',
            reply_markup=keyboard
        )
        
        print(f"✅ Тестове повідомлення з кнопками відправлено адміністратору {admin_id}")
        print(f"📱 Message ID: {message.message_id}")
        
        # Створюємо тестові дані для callback
        import json
        import os
        
        callback_dir = "callback_data"
        if not os.path.exists(callback_dir):
            os.makedirs(callback_dir)
            
        test_data = {
            "original_message_id": 999,
            "text": "Тестове повідомлення про стан переїзду",
            "sender_name": "Тест користувач",
            "sender_username": "testuser",
            "status": "невідомо",
            "timestamp": "2025-07-08T11:00:00"
        }
        
        with open(f"{callback_dir}/123456.json", "w", encoding="utf-8") as f:
            json.dump(test_data, f, ensure_ascii=False, indent=2)
            
        print("✅ Тестові дані для callback збережено")
        print("💡 Тепер натисніть одну з кнопок у Telegram")
        
    except Exception as e:
        print(f"❌ Помилка: {e}")

if __name__ == "__main__":
    asyncio.run(test_callback_buttons())