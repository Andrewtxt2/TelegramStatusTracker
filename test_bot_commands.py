#!/usr/bin/env python3
"""
Test bot commands
"""

import asyncio
from config import Config
from telegram import Bot

async def test_commands():
    """Test bot commands"""
    config = Config()
    bot = Bot(token=config.bot_token)
    
    # Test with different admins
    admin_ids = config.admin_user_ids
    print(f"Available admins: {admin_ids}")
    
    admin_id = admin_ids[1]  # Try second admin
    
    print(f"Testing commands with admin {admin_id}")
    
    try:
        # Test /start command
        await bot.send_message(admin_id, "/start")
        print("✅ Sent /start command")
        
        await asyncio.sleep(2)
        
        # Test /status command  
        await bot.send_message(admin_id, "/status")
        print("✅ Sent /status command")
        
        await asyncio.sleep(2)
        
        # Test /health command
        await bot.send_message(admin_id, "/health")
        print("✅ Sent /health command")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_commands())