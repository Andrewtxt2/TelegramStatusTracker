#!/usr/bin/env python3
"""
Test script to send a message to the monitored group
"""

import asyncio
from telethon import TelegramClient
from config import Config

async def send_test_message():
    config = Config()
    mtproto_config = config.get('mtproto_settings', {})
    api_id = int(mtproto_config.get('api_id', '0'))
    api_hash = mtproto_config.get('api_hash', '')
    
    client = TelegramClient('test_session', api_id, api_hash)
    await client.start()
    
    try:
        # Get the target group
        entity = await client.get_entity('https://t.me/pereizdvyshneve')
        print(f"Found group: {entity.title} (ID: {entity.id})")
        
        # Send a test message
        test_message = "🔄 Тест моніторингу переїзду - 9:15"
        
        message = await client.send_message(entity, test_message)
        print(f"✅ Test message sent: {message.id}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(send_test_message())