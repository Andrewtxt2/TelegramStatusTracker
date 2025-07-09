#!/usr/bin/env python3
"""
Фінальний тест кнопок з правильним форматом
"""

import asyncio
from datetime import datetime
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from config import Config

async def test_final_callback():
    """Тест кнопок з новим форматом"""
    config = Config()
    bot = Bot(token=config.bot_token)
    admin_id = 6395626140
    
    test_message = """
🔄 **ТЕСТ НОВОГО ФОРМАТУ**

👤 **Від:** Тест користувач  
🤖 **AI Аналіз:** ⚪ НЕВІДОМО

📝 **Текст повідомлення:**
Переїзд працює, можна проїжджати

⚡ **Після натискання кнопки в канал піде тільки:**
✅ Відкрито
🕓 11:02

**БЕЗ тексту повідомлення**
"""

    # Кнопки
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ ВІДКРИТО", callback_data="approve_open_789012"),
            InlineKeyboardButton("❌ ЗАКРИТО", callback_data="approve_closed_789012")
        ],
        [
            InlineKeyboardButton("🗑 ВІДХИЛИТИ", callback_data="reject_789012")
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
        
        print(f"✅ Тест з новим форматом відправлено адміністратору")
        print(f"📱 Message ID: {message.message_id}")
        
        # Створюємо тестові дані
        import json
        import os
        
        callback_dir = "callback_data"
        if not os.path.exists(callback_dir):
            os.makedirs(callback_dir)
            
        test_data = {
            "original_message_id": 999,
            "text": "Переїзд працює, можна проїжджати",
            "sender_name": "Тест користувач",
            "sender_username": "testuser",
            "status": "невідомо",
            "timestamp": datetime.now().isoformat()
        }
        
        with open(f"{callback_dir}/789012.json", "w", encoding="utf-8") as f:
            json.dump(test_data, f, ensure_ascii=False, indent=2)
            
        print("✅ Дані збережено")
        print("💡 Натисніть кнопку - в канал піде тільки статус і час")
        print("🔧 Щоб канал працював, додайте бота @Pereyizd_bot як адміністратора в @kryuvysh")
        
    except Exception as e:
        print(f"❌ Помилка: {e}")

if __name__ == "__main__":
    asyncio.run(test_final_callback())