#!/usr/bin/env python3
"""
Фінальний тест формату з посиланням на групу
"""

import asyncio
from datetime import datetime
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from config import Config

async def test_channel_final():
    """Тест фінального формату з посиланням"""
    config = Config()
    bot = Bot(token=config.bot_token)
    admin_id = 6395626140
    
    test_message = """
🔄 **ФІНАЛЬНИЙ ТЕСТ ФОРМАТУ**

👤 **Від:** Тест користувач  
🤖 **AI Аналіз:** ⚪ НЕВІДОМО

📝 **Текст повідомлення:**
Переїзд зараз працює нормально

⚡ **Після натискання кнопки в канал піде:**
✅ Відкрито
🕓 11:05

🔗 https://t.me/pereizdvyshneve

**Формат: статус + час + посилання на групу**
"""

    # Кнопки
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ ВІДКРИТО", callback_data="approve_open_999999"),
            InlineKeyboardButton("❌ ЗАКРИТО", callback_data="approve_closed_999999")
        ],
        [
            InlineKeyboardButton("🗑 ВІДХИЛИТИ", callback_data="reject_999999")
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
        
        print(f"✅ Фінальний тест відправлено адміністратору")
        print(f"📱 Message ID: {message.message_id}")
        
        # Створюємо тестові дані
        import json
        import os
        
        callback_dir = "callback_data"
        if not os.path.exists(callback_dir):
            os.makedirs(callback_dir)
            
        test_data = {
            "original_message_id": 999,
            "text": "Переїзд зараз працює нормально",
            "sender_name": "Тест користувач",
            "sender_username": "testuser",
            "status": "невідомо",
            "timestamp": datetime.now().isoformat()
        }
        
        with open(f"{callback_dir}/999999.json", "w", encoding="utf-8") as f:
            json.dump(test_data, f, ensure_ascii=False, indent=2)
            
        print("✅ Дані збережено")
        print("💡 Натисніть кнопку - в канал піде статус + час + посилання")
        print("🔧 Після додавання бота до каналу все буде працювати автоматично")
        
    except Exception as e:
        print(f"❌ Помилка: {e}")

if __name__ == "__main__":
    asyncio.run(test_channel_final())