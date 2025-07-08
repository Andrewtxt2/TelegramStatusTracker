#!/usr/bin/env python3
"""
Тест GMT+3 часу і показу останніх повідомлень
"""

import asyncio
from datetime import datetime, timezone, timedelta
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from config import Config

async def test_timezone_recent():
    """Тест GMT+3 часу"""
    config = Config()
    bot = Bot(token=config.bot_token)
    admin_id = 6395626140
    
    # Показуємо поточний час GMT+3
    gmt_plus_3 = timezone(timedelta(hours=3))
    current_time = datetime.now(gmt_plus_3).strftime('%H:%M')
    
    test_message = f"""
🔄 **ТЕСТ GMT+3 ЧАСУ І ОСТАННІХ ПОВІДОМЛЕНЬ**

👤 **Від:** Тест користувач  
🤖 **AI Аналіз:** ⚪ НЕВІДОМО

📝 **Текст повідомлення:**
Чи працює зараз переїзд? Треба перевірити

⚡ **Поточний час GMT+3:** {current_time}

📊 **Тепер система показує останні 14 повідомлень разом з новим**

⚡ **Статус залежить ТІЛЬКИ від кнопки:**
- ✅ ВІДКРИТО → "✅ Відкрито 🕓 {current_time}"
- ❌ ЗАКРИТО → "❌ Закрито 🕓 {current_time}"
"""

    # Кнопки
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ ВІДКРИТО", callback_data="approve_open_333333"),
            InlineKeyboardButton("❌ ЗАКРИТО", callback_data="approve_closed_333333")
        ],
        [
            InlineKeyboardButton("🗑 ВІДХИЛИТИ", callback_data="reject_333333")
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
        
        print(f"✅ Тест GMT+3 часу і останніх повідомлень відправлено")
        print(f"📱 Message ID: {message.message_id}")
        print(f"🕓 Поточний час GMT+3: {current_time}")
        
        # Створюємо тестові дані
        import json
        import os
        
        callback_dir = "callback_data"
        if not os.path.exists(callback_dir):
            os.makedirs(callback_dir)
            
        test_data = {
            "original_message_id": 999,
            "text": "Чи працює зараз переїзд? Треба перевірити",
            "sender_name": "Тест користувач",
            "sender_username": "testuser",
            "status": "невідомо",
            "timestamp": datetime.now(gmt_plus_3).isoformat()
        }
        
        with open(f"{callback_dir}/333333.json", "w", encoding="utf-8") as f:
            json.dump(test_data, f, ensure_ascii=False, indent=2)
            
        print("✅ Дані збережено")
        print("💡 Тепер система показує останні 14 повідомлень + використовує GMT+3")
        
    except Exception as e:
        print(f"❌ Помилка: {e}")

if __name__ == "__main__":
    asyncio.run(test_timezone_recent())