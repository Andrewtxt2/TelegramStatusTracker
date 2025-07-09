#!/usr/bin/env python3
"""
Check bot status and send test message
"""

import asyncio
from config import Config
from telegram import Bot

async def check_bot():
    """Check bot status"""
    config = Config()
    bot = Bot(token=config.bot_token)
    
    try:
        me = await bot.get_me()
        print(f"✅ Bot active: @{me.username} ({me.first_name})")
        
        # Check webhook status
        webhook_info = await bot.get_webhook_info()
        print(f"Webhook URL: {webhook_info.url or 'None (polling mode)'}")
        
        # Test sending message to bot creator
        try:
            await bot.send_message(
                chat_id=6395626140,  # Admin that worked before
                text="🔧 Bot Status Check\n\nBot is running and ready to receive commands!\n\nTry:\n/start\n/status\n/health"
            )
            print("✅ Test message sent to admin")
        except Exception as e:
            print(f"❌ Failed to send test message: {e}")
            
    except Exception as e:
        print(f"❌ Bot check failed: {e}")

if __name__ == "__main__":
    asyncio.run(check_bot())