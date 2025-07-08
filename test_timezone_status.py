#!/usr/bin/env python3
"""
Тест GMT+2 часу і статусу від кнопки
"""

import asyncio
from datetime import datetime, timezone, timedelta
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from config import Config

async def test_timezone_status():
    """Тест GMT+2 часу і статусу залежно від кнопки"""
    config = Config()
    bot = Bot(token=config.bot_token)
    admin_id = 6395626140
    
    # Показуємо поточний час GMT+2
    gmt_plus_2 = timezone(timedelta(hours=2))
    current_time = datetime.now(gmt_plus_2).strftime('%H:%M')
    
    test_message = f"""
🔄 **ТЕСТ GMT+2 ЧАСУ**

👤 **Від:** Тест користувач  
🤖 **AI Аналіз:** ⚪ НЕВІДОМО

📝 **Текст повідомлення:**
Чи працює зараз переїзд?

⚡ **Час GMT+2:** {current_time}
⚡ **Статус залежить ТІЛЬКИ від кнопки що натиснете:**
- ✅ ВІДКРИТО → "✅ Відкрито 🕓 {current_time}"
- ❌ ЗАКРИТО → "❌ Закрито 🕓 {current_time}"
"""

    # Кнопки
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ ВІДКРИТО", callback_data="approve_open_222222"),
            InlineKeyboardButton("❌ ЗАКРИТО", callback_data="approve_closed_222222")
        ],
        [
            InlineKeyboardButton("🗑 ВІДХИЛИТИ", callback_data="reject_222222")
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
        
        print(f"✅ Тест GMT+2 часу відправлено")
        print(f"📱 Message ID: {message.message_id}")
        print(f"🕓 Поточний час GMT+2: {current_time}")
        
        # Створюємо тестові дані
        import json
        import os
        
        callback_dir = "callback_data"
        if not os.path.exists(callback_dir):
            os.makedirs(callback_dir)
            
        test_data = {
            "original_message_id": 999,
            "text": "Чи працює зараз переїзд?",
            "sender_name": "Тест користувач",
            "sender_username": "testuser",
            "status": "невідомо",
            "timestamp": datetime.now(gmt_plus_2).isoformat()
        }
        
        with open(f"{callback_dir}/222222.json", "w", encoding="utf-8") as f:
            json.dump(test_data, f, ensure_ascii=False, indent=2)
            
        print("✅ Дані збережено")
        print("💡 Натисніть кнопку - статус залежить тільки від вашого вибору")
        
    except Exception as e:
        print(f"❌ Помилка: {e}")

if __name__ == "__main__":
    asyncio.run(test_timezone_status())