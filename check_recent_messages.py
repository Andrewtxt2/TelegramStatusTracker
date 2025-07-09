#!/usr/bin/env python3
"""
Check recent messages from the monitored group
"""

import asyncio
from telethon import TelegramClient
from config import Config
from datetime import datetime, timedelta

async def check_recent_messages():
    config = Config()
    mtproto_config = config.get('mtproto_settings', {})
    api_id = int(mtproto_config.get('api_id', '0'))
    api_hash = mtproto_config.get('api_hash', '')
    
    # Use the same session as production bot
    client = TelegramClient('session', api_id, api_hash)
    await client.start()
    
    try:
        # Get the target group
        entity = await client.get_entity('https://t.me/pereizdvyshneve')
        print(f"✅ Group: {entity.title} (ID: {entity.id})")
        
        # Get recent messages from the last hour
        now = datetime.now()
        since = now - timedelta(hours=1)
        
        messages = []
        async for message in client.iter_messages(entity, limit=20):
            if message.date > since:
                messages.append(message)
        
        print(f"📝 Found {len(messages)} messages in the last hour:")
        for msg in messages:
            time_str = msg.date.strftime('%H:%M:%S')
            text = msg.message[:100] if msg.message else "[No text]"
            print(f"  {time_str} - ID:{msg.id} - {text}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(check_recent_messages())