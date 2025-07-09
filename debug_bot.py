#!/usr/bin/env python3
"""
Debug bot commands
"""

import asyncio
from config import Config
from telegram import Bot

async def debug_bot():
    """Debug bot status"""
    config = Config()
    bot = Bot(token=config.bot_token)
    
    print("Getting bot info...")
    try:
        me = await bot.get_me()
        print(f"Bot username: @{me.username}")
        print(f"Bot ID: {me.id}")
        print(f"Bot name: {me.first_name}")
        
        # Check webhook
        webhook_info = await bot.get_webhook_info()
        print(f"Webhook URL: {webhook_info.url}")
        print(f"Webhook pending updates: {webhook_info.pending_update_count}")
        
        # Try to get updates
        updates = await bot.get_updates()
        print(f"Recent updates: {len(updates)}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(debug_bot())