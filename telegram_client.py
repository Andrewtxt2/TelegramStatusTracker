"""
Telegram Client for direct group monitoring using MTProto API
Monitors source group and forwards messages to bot for processing
"""

import asyncio
import os
from typing import Optional, Dict, Any
from telethon import TelegramClient, events
from telethon.tl.types import Message
from datetime import datetime, timezone
import aiohttp
import json
from logger import setup_logger
from config import Config

class TelegramGroupMonitor:
    def __init__(self, config: Config):
        self.config = config
        self.logger = setup_logger("telegram_client")
        
        # API credentials from environment
        api_id_str = os.getenv('TELEGRAM_API_ID')
        api_hash_str = os.getenv('TELEGRAM_API_HASH')
        phone_str = os.getenv('TELEGRAM_PHONE')
        
        if not api_id_str or not api_hash_str or not phone_str:
            self.logger.error("Missing required environment variables: TELEGRAM_API_ID, TELEGRAM_API_HASH, or TELEGRAM_PHONE")
            raise ValueError("Missing required API credentials")
            
        self.api_id = int(api_id_str)
        self.api_hash = api_hash_str
        self.phone = phone_str
        
        # Bot token for sending processed messages
        self.bot_token = config.bot_token
        
        # Initialize client
        self.client = TelegramClient('session', self.api_id, self.api_hash)
        self.running = False
        
    async def start(self):
        """Start the Telegram client and begin monitoring"""
        try:
            self.logger.info("Starting Telegram client...")
            
            # Connect and authenticate
            await self.client.start(phone=self.phone)
            
            if not await self.client.is_user_authorized():
                self.logger.error("User not authorized. Please run authorization first.")
                return False
                
            me = await self.client.get_me()
            self.logger.info(f"Authorized as: {me.first_name}")
            
            # Register event handlers
            await self.register_handlers()
            
            self.running = True
            self.logger.info("Telegram client started and monitoring...")
            
            # Keep running
            await self.client.run_until_disconnected()
            
        except Exception as e:
            self.logger.error(f"Error starting Telegram client: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False
            
    async def register_handlers(self):
        """Register message handlers for the source group"""
        source_group = self.config.source_group_id
        
        # Try different ways to identify the source group
        if isinstance(source_group, str) and source_group.startswith('@'):
            source_entity = source_group
        elif isinstance(source_group, str) and 'pereizdvyshneve' in source_group:
            source_entity = 'pereizdvyshneve'
        elif isinstance(source_group, str) and 't.me' in source_group:
            # Extract username from t.me link
            source_entity = source_group.split('/')[-1]
        else:
            source_entity = 'pereizdvyshneve'  # Default username
            
        self.logger.info(f"Monitoring group: {source_entity}")
        
        @self.client.on(events.NewMessage(chats=[source_entity]))
        async def handle_new_message(event):
            await self.process_group_message(event)
            
    async def process_group_message(self, event):
        """Process new message from the monitored group"""
        try:
            message = event.message
            
            if not message.text:
                return
                
            self.logger.info(f"New message from group: {message.id}")
            
            # Prepare message data
            sender = await message.get_sender()
            sender_username = getattr(sender, 'username', '') or ''
            sender_name = getattr(sender, 'first_name', '') or ''
            
            message_data = {
                'message_id': message.id,
                'chat_id': message.chat_id,
                'user_id': message.sender_id,
                'username': sender_username,
                'first_name': sender_name,
                'text': message.text,
                'timestamp': message.date.isoformat(),
                'source': 'telegram_api'
            }
            
            # Send to bot for processing
            await self.send_to_bot(message_data)
            
        except Exception as e:
            self.logger.error(f"Error processing group message: {e}")
            
    async def send_to_bot(self, message_data: Dict[str, Any]):
        """Send message data to the bot for analysis and forwarding"""
        try:
            # Send via Telegram Bot API to admin group
            admin_group_id = self.config.admin_group_id
            
            if not admin_group_id or admin_group_id == 0:
                self.logger.warning("Admin group not configured")
                return
                
            # Format message for admin group
            formatted_text = f"""
🔄 **Нове повідомлення з групи переїзду**

👤 **Від:** {message_data.get('first_name', '')} (@{message_data.get('username', 'Unknown')})
🕐 **Час:** {message_data['timestamp']}

📝 **Текст:**
{message_data['text']}

_Автоматично переслано через API моніторинг_
"""

            # Send via bot API
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            payload = {
                'chat_id': admin_group_id,
                'text': formatted_text,
                'parse_mode': 'Markdown'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        self.logger.info("Message sent to admin group successfully")
                    else:
                        error_text = await response.text()
                        self.logger.error(f"Failed to send message to admin group: {error_text}")
                        
            # Also trigger bot analysis
            await self.trigger_bot_analysis(message_data)
                        
        except Exception as e:
            self.logger.error(f"Error sending to bot: {e}")
            
    async def trigger_bot_analysis(self, message_data: Dict[str, Any]):
        """Trigger bot analysis by sending message to bot directly"""
        try:
            # Send message to one of the admin users to trigger processing
            admin_ids = self.config.admin_user_ids
            
            if not admin_ids:
                return
                
            primary_admin = admin_ids[0]
            
            # Format message to send to admin
            message_text = f"📨 Автоматичне повідомлення з групи:\n\n{message_data['text']}"
            
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            payload = {
                'chat_id': primary_admin,
                'text': message_text
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        self.logger.info("Analysis triggered successfully")
                    else:
                        self.logger.error(f"Failed to trigger analysis: {await response.text()}")
                        
        except Exception as e:
            self.logger.error(f"Error triggering bot analysis: {e}")
            
    async def stop(self):
        """Stop the Telegram client"""
        self.logger.info("Stopping Telegram client...")
        self.running = False
        if self.client.is_connected():
            await self.client.disconnect()
        self.logger.info("Telegram client stopped")

async def main():
    """Main function for standalone client operation"""
    config = Config()
    monitor = TelegramGroupMonitor(config)
    
    try:
        await monitor.start()
    except KeyboardInterrupt:
        await monitor.stop()
    except Exception as e:
        monitor.logger.critical(f"Critical error in Telegram client: {e}")

if __name__ == "__main__":
    asyncio.run(main())