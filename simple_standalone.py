#!/usr/bin/env python3
"""
Simple standalone bot without interactive authentication
"""

import asyncio
import os
import sys
import logging
from datetime import datetime
from telethon import TelegramClient, events
from telegram import Bot
from config import Config
from message_analyzer import MessageAnalyzer

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('simple_standalone.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('simple_standalone')

async def main():
    """Main function"""
    config = Config()
    analyzer = MessageAnalyzer()
    
    # Use existing session
    api_id = int(os.getenv('TELEGRAM_API_ID', '0'))
    api_hash = os.getenv('TELEGRAM_API_HASH', '')
    
    # Try different session files
    for session_file in ['test_session', 'auth_session', 'session']:
        if os.path.exists(f'{session_file}.session'):
            logger.info(f"Using session: {session_file}")
            client = TelegramClient(session_file, api_id, api_hash)
            break
    else:
        logger.error("No valid session found")
        return
    
    try:
        await client.start()
        me = await client.get_me()
        logger.info(f"✅ Connected as: {me.first_name}")
        
        # Get group
        group_link = config.source_group_id
        if group_link.startswith('https://t.me/'):
            group_username = group_link.split('/')[-1]
            target_entity = await client.get_entity(group_username)
        else:
            target_entity = await client.get_entity(group_link)
        
        logger.info(f"✅ Monitoring group: {target_entity.title}")
        
        # Setup bot for admin messages
        bot = Bot(token=config.bot_token)
        
        # Message handler
        @client.on(events.NewMessage(chats=target_entity))
        async def handle_message(event):
            try:
                if event.message.text:
                    logger.info(f"📨 New message: {event.message.text[:50]}...")
                    
                    # Analyze message
                    analysis = await analyzer.analyze_message(event.message.text)
                    logger.info(f"🤖 Analysis: {analysis['suggested_status']} ({analysis['confidence']:.0%})")
                    
                    # Send to admin
                    admin_message = f"📨 Нове повідомлення\n\n💬 {event.message.text}\n\n🤖 Аналіз: {analysis['suggested_status']} ({analysis['confidence']:.0%})"
                    
                    for admin_id in config.admin_user_ids:
                        try:
                            await bot.send_message(chat_id=admin_id, text=admin_message)
                            logger.info(f"✅ Sent to admin {admin_id}")
                        except Exception as e:
                            logger.error(f"Failed to send to admin {admin_id}: {e}")
                            
            except Exception as e:
                logger.error(f"Error handling message: {e}")
        
        logger.info("🔄 Starting message monitoring...")
        await client.run_until_disconnected()
        
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(main())