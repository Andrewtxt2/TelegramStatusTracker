#!/usr/bin/env python3
"""
Quick authentication setup for bot
This will create a new session that doesn't require interactive input
"""

import asyncio
import os
from telethon import TelegramClient
from config import Config

async def setup_auth():
    """Setup authentication"""
    config = Config()
    
    api_id = int(os.getenv('TELEGRAM_API_ID', '0'))
    api_hash = os.getenv('TELEGRAM_API_HASH', '')
    phone = os.getenv('TELEGRAM_PHONE', '+380686850166')
    
    print(f"Setting up authentication...")
    print(f"API ID: {api_id}")
    print(f"Phone: {phone}")
    
    # Create new session
    client = TelegramClient('working_session', api_id, api_hash)
    
    try:
        await client.start(phone=phone)
        
        # Test connection
        me = await client.get_me()
        print(f"✅ Successfully authenticated as: {me.first_name}")
        
        # Test group access
        group_link = config.source_group_id
        if group_link.startswith('https://t.me/'):
            group_username = group_link.split('/')[-1]
            target_entity = await client.get_entity(group_username)
        else:
            target_entity = await client.get_entity(group_link)
        
        print(f"✅ Can access group: {target_entity.title}")
        
        await client.disconnect()
        print("✅ Authentication setup complete! Session saved as 'working_session.session'")
        
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(setup_auth())