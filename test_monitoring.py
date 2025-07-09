#!/usr/bin/env python3
"""
Test monitoring by sending a message to the group
"""

import asyncio
from telethon import TelegramClient
from config import Config
from datetime import datetime

async def test_monitoring():
    config = Config()
    
    # Load MTProto settings from environment
    import os
    api_id = int(os.getenv('TELEGRAM_API_ID', '0'))
    api_hash = os.getenv('TELEGRAM_API_HASH', '')
    
    client = TelegramClient('test_session2', api_id, api_hash)
    await client.start()
    
    try:
        # Get the target group
        entity = await client.get_entity('https://t.me/pereizdvyshneve')
        print(f"✅ Group: {entity.title} (ID: {entity.id})")
        
        # Current time
        now = datetime.now()
        time_str = now.strftime('%H:%M')
        
        # Send a test message
        test_message = f"🔄 Тест моніторингу - переїзд відкрито {time_str}"
        
        message = await client.send_message(entity, test_message)
        print(f"✅ Test message sent: ID {message.id}")
        print(f"📝 Message: {test_message}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(test_monitoring())