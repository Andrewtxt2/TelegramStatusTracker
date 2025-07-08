#!/usr/bin/env python3
"""
Тест формату публікації в канал
"""

import asyncio
from datetime import datetime
from telegram import Bot
from config import Config

async def test_channel_format():
    """Тест публікації в канал з правильним форматом"""
    config = Config()
    bot = Bot(token=config.bot_token)
    
    # Тестовий формат - тільки статус і час
    current_time = datetime.now().strftime('%H:%M')
    
    # Тест відкрито
    open_message = f"""✅ Відкрито
🕓 {current_time}"""
    
    # Тест закрито
    closed_message = f"""❌ Закрито
🕓 {current_time}"""
    
    try:
        # Відправляємо тестові повідомлення в канал
        print(f"Відправка тестових повідомлень в канал @kryuvysh...")
        
        # Спочатку "відкрито"
        await bot.send_message(
            chat_id="@kryuvysh",
            text=open_message
        )
        print(f"✅ Відправлено: {open_message}")
        
        # Через 2 секунди "закрито"
        await asyncio.sleep(2)
        
        current_time = datetime.now().strftime('%H:%M')
        closed_message = f"""❌ Закрито
🕓 {current_time}"""
        
        await bot.send_message(
            chat_id="@kryuvysh",
            text=closed_message
        )
        print(f"✅ Відправлено: {closed_message}")
        
        print("✅ Тест формату публікації завершено")
        
    except Exception as e:
        print(f"❌ Помилка: {e}")

if __name__ == "__main__":
    asyncio.run(test_channel_format())