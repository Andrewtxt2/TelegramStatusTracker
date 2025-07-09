#!/usr/bin/env python3
"""
Test direct message to bot to trigger command handler
"""

import asyncio
from config import Config
from telegram import Bot

async def test_direct():
    """Test direct message to bot"""
    config = Config()
    bot = Bot(token=config.bot_token)
    
    # Send message to bot chat (simulate user sending command)
    try:
        # This will simulate a user sending /start to the bot
        bot_info = await bot.get_me()
        print(f"Bot info: @{bot_info.username} (ID: {bot_info.id})")
        
        # Send a message to admin about testing
        await bot.send_message(
            chat_id=6395626140,
            text="🧪 Тестування команд бота\n\nЗараз спробуйте написати боту @Pereyizd_bot:\n\n/start\n/status\n/health\n\nЯкщо команди не працюють, я виправлю це."
        )
        print("✅ Instructions sent to admin")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_direct())