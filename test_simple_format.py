#!/usr/bin/env python3
"""
Тест простого формату без посилання
"""

import asyncio
from datetime import datetime
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from config import Config

async def test_simple_format():
    """Тест простого формату: тільки статус + час"""
    config = Config()
    bot = Bot(token=config.bot_token)
    admin_id = 6395626140
    
    test_message = """
🔄 **ПРОСТИЙ ФОРМАТ**

👤 **Від:** Тест користувач  
🤖 **AI Аналіз:** ⚪ НЕВІДОМО

📝 **Текст повідомлення:**
Переїзд зараз закритий на ремонт

⚡ **Після натискання кнопки в канал піде ТІЛЬКИ:**
❌ Закрито
🕓 11:07

**Без посилань та додаткового тексту**
"""

    # Кнопки
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ ВІДКРИТО", callback_data="approve_open_111111"),
            InlineKeyboardButton("❌ ЗАКРИТО", callback_data="approve_closed_111111")
        ],
        [
            InlineKeyboardButton("🗑 ВІДХИЛИТИ", callback_data="reject_111111")
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
        
        print(f"✅ Тест простого формату відправлено")
        print(f"📱 Message ID: {message.message_id}")
        
        # Створюємо тестові дані
        import json
        import os
        
        callback_dir = "callback_data"
        if not os.path.exists(callback_dir):
            os.makedirs(callback_dir)
            
        test_data = {
            "original_message_id": 999,
            "text": "Переїзд зараз закритий на ремонт",
            "sender_name": "Тест користувач",
            "sender_username": "testuser",
            "status": "невідомо",
            "timestamp": datetime.now().isoformat()
        }
        
        with open(f"{callback_dir}/111111.json", "w", encoding="utf-8") as f:
            json.dump(test_data, f, ensure_ascii=False, indent=2)
            
        print("✅ Дані збережено")
        print("💡 Натисніть кнопку - в канал піде ТІЛЬКИ статус + час")
        
    except Exception as e:
        print(f"❌ Помилка: {e}")

if __name__ == "__main__":
    asyncio.run(test_simple_format())