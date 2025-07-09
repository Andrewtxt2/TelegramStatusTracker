#!/usr/bin/env python3
"""
Simple test to send a command to the bot
"""

import asyncio
from config import Config
from telegram import Bot

async def send_test_command():
    """Send test command to bot"""
    config = Config()
    bot = Bot(token=config.bot_token)
    
    # Use admin that can receive messages
    admin_id = 6395626140  # This admin worked before
    
    print(f"Sending test message to admin {admin_id}")
    
    try:
        # Send a regular message (not command) to avoid conflicts
        await bot.send_message(
            chat_id=admin_id,
            text="🔧 Тест зв'язку з ботом\n\nТепер спробуйте написати боту:\n/start\n/status\n/health"
        )
        print("✅ Test message sent successfully")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(send_test_command())