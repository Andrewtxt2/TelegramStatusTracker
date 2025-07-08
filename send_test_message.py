
#!/usr/bin/env python3
"""
Відправка простого тестового повідомлення
"""

import asyncio
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from config import Config

async def send_simple_test():
    """Відправити просте тестове повідомлення"""
    config = Config()
    bot = Bot(token=config.bot_token)
    
    # Адміністратори
    admin_ids = [537827257, 6395626140, 564704015, 7766810783]
    
    # Простий текст без складного форматування
    test_message = """🔄 ТЕСТ СИСТЕМИ

👤 Від: Тест користувач
🕐 Час: зараз
🤖 Статус: відкрито

📝 Текст: Тестове повідомлення для перевірки

Натисніть кнопку для тесту:"""

    # Кнопки
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ ВІДКРИТО", callback_data="approve_open_test123"),
            InlineKeyboardButton("❌ ЗАКРИТО", callback_data="approve_closed_test123")
        ],
        [
            InlineKeyboardButton("🗑 ВІДХИЛИТИ", callback_data="reject_test123")
        ]
    ])
    
    success_count = 0
    for admin_id in admin_ids:
        try:
            await bot.send_message(
                chat_id=admin_id,
                text=test_message,
                reply_markup=keyboard
            )
            print(f"✅ Відправлено адміністратору {admin_id}")
            success_count += 1
        except Exception as e:
            print(f"❌ Помилка для {admin_id}: {e}")
    
    print(f"\n✅ Успішно відправлено {success_count} з {len(admin_ids)} адміністраторів")

if __name__ == "__main__":
    asyncio.run(send_simple_test())
