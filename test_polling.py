#!/usr/bin/env python3
"""
Test polling system by sending a message to the group
"""

import asyncio
from telethon import TelegramClient
import os
from datetime import datetime

async def test_polling():
    # Use environment variables
    api_id = int(os.getenv('TELEGRAM_API_ID', '0'))
    api_hash = os.getenv('TELEGRAM_API_HASH', '')
    
    client = TelegramClient('test_polling_session', api_id, api_hash)
    
    try:
        await client.start()
        
        # Get the target group
        entity = await client.get_entity('https://t.me/pereizdvyshneve')
        print(f"✅ Group: {entity.title} (ID: {entity.id})")
        
        # Current time
        now = datetime.now()
        time_str = now.strftime('%H:%M')
        
        # Send a test message
        test_message = f"🔄 Тест polling системи - переїзд закрито {time_str}"
        
        message = await client.send_message(entity, test_message)
        print(f"✅ Test message sent: ID {message.id}")
        print(f"📝 Message: {test_message}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(test_polling())