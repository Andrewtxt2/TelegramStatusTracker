#!/usr/bin/env python3
"""
Setup script for Telegram MTProto API authentication
Run this once to authenticate your account
"""

import os
import asyncio
from telethon import TelegramClient

async def setup_auth():
    """Setup authentication for Telegram API"""
    
    # Get credentials from environment
    api_id = os.getenv('TELEGRAM_API_ID')
    api_hash = os.getenv('TELEGRAM_API_HASH')
    phone = os.getenv('TELEGRAM_PHONE')
    
    if not all([api_id, api_hash, phone]):
        print("Missing required environment variables!")
        return False
    
    api_id = int(api_id)
    
    print(f"Setting up authentication for {phone}")
    print(f"API ID: {api_id}")
    
    client = TelegramClient('session', api_id, api_hash)
    
    try:
        await client.start(phone=phone)
        
        if await client.is_user_authorized():
            me = await client.get_me()
            print(f"✅ Successfully authenticated as: {me.first_name}")
            
            # Test access to the source group
            try:
                entity = await client.get_entity('pereizdvyshneve')
                print(f"✅ Successfully found source group: {entity.title}")
            except Exception as e:
                print(f"❌ Could not access source group: {e}")
                
            return True
        else:
            print("❌ Authentication failed")
            return False
            
    except Exception as e:
        print(f"❌ Error during authentication: {e}")
        return False
    finally:
        await client.disconnect()

if __name__ == "__main__":
    success = asyncio.run(setup_auth())
    if success:
        print("✅ Authentication setup complete!")
    else:
        print("❌ Authentication setup failed!")