#!/usr/bin/env python3
"""
Production-ready bot for 24/7 monitoring with no conflicts
Single instance with MTProto monitoring and Bot API callbacks
"""

import asyncio
import os
import time
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
from telethon import TelegramClient, events
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, ContextTypes
from telegram.error import NetworkError, TimedOut, TelegramError
from config import Config
from aiohttp import web
import signal

# Налаштування логування
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('production_bot.log'),
        logging.StreamHandler()
    ]
)

class ProductionBot:
    def __init__(self):
        self.logger = logging.getLogger("production_bot")
        self.config = Config()
        
        # MTProto credentials
        mtproto_config = self.config.get('mtproto_settings', {})
        self.api_id = int(mtproto_config.get('api_id', '0'))
        self.api_hash = mtproto_config.get('api_hash', '')
        
        # Telegram clients
        self.client = TelegramClient('session', self.api_id, self.api_hash)
        
        # Bot only for callbacks (no polling)
        self.bot = Bot(token=self.config.bot_token)
        
        # State
        self.running = False
        self.start_time = time.time()
        self.message_storage = {}
        self.recent_messages = []
        self.shutdown_event = asyncio.Event()
        
        # HTTP server
        self.app = web.Application()
        self.setup_routes()
        
        # Graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
    def _signal_handler(self, signum, frame):
        """Signal handler for graceful shutdown"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.shutdown_event.set()
        
    def setup_routes(self):
        """Setup HTTP routes"""
        self.app.router.add_get('/', self.handle_root)
        self.app.router.add_get('/health', self.handle_health)
        self.app.router.add_get('/status', self.handle_status)
        self.app.router.add_post('/webhook', self.handle_webhook)
        
    async def handle_root(self, request):
        """Root endpoint"""
        return web.Response(text="Production Bot is running", content_type='text/plain')
        
    async def handle_health(self, request):
        """Health check endpoint"""
        try:
            health_data = {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "uptime": time.time() - self.start_time,
                "service": "production-bot",
                "version": "1.0.0",
                "mtproto_connected": self.client.is_connected(),
                "messages_processed": len(self.message_storage)
            }
            return web.json_response(health_data)
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return web.json_response({"status": "unhealthy", "error": str(e)}, status=500)
            
    async def handle_status(self, request):
        """Status endpoint"""
        try:
            status_data = {
                "service": "Production Bot",
                "status": "running",
                "uptime_seconds": time.time() - self.start_time,
                "mtproto_connected": self.client.is_connected(),
                "config_loaded": bool(self.config.bot_token),
                "recent_messages": len(self.recent_messages),
                "stored_messages": len(self.message_storage)
            }
            return web.json_response(status_data)
        except Exception as e:
            self.logger.error(f"Status check failed: {e}")
            return web.json_response({"status": "error", "error": str(e)}, status=500)
            
    async def handle_webhook(self, request):
        """Handle Telegram webhook for callbacks"""
        try:
            data = await request.json()
            if 'callback_query' in data:
                await self.handle_callback_query(data['callback_query'])
            return web.json_response({"ok": True})
        except Exception as e:
            self.logger.error(f"Webhook error: {e}")
            return web.json_response({"ok": False, "error": str(e)}, status=500)
            
    async def handle_callback_query(self, callback_data):
        """Handle callback query from webhook"""
        try:
            query_id = callback_data['id']
            data = callback_data['data']
            message = callback_data['message']
            
            # Process callback
            if data.startswith('approve_'):
                action, status, message_id = data.split('_', 2)
                await self.approve_message(query_id, status, message_id)
            elif data.startswith('reject_'):
                action, message_id = data.split('_', 1)
                await self.reject_message(query_id, message_id)
                
            # Answer callback query
            await self.bot.answer_callback_query(query_id)
            
        except Exception as e:
            self.logger.error(f"Callback processing error: {e}")
            
    async def start(self):
        """Start the production bot"""
        try:
            self.logger.info("🚀 Starting Production Bot...")
            
            # Start MTProto client
            await self.client.start()
            me = await self.client.get_me()
            self.logger.info(f"✅ MTProto connected: {me.first_name}")
            
            # Get target group
            entity = await self.client.get_entity('https://t.me/pereizdvyshneve')
            self.logger.info(f"✅ Group found: {entity.title}")
            self.logger.info(f"✅ Group ID: {entity.id}")
            self.target_group_id = entity.id
            
            # Setup message handler
            @self.client.on(events.NewMessage(chats=entity))
            async def handle_message(event):
                # Log every message attempt
                self.logger.info(f"🔍 Message received from chat ID: {event.chat_id}")
                await self.process_message(event)
                
            # Start HTTP server
            runner = web.AppRunner(self.app)
            await runner.setup()
            site = web.TCPSite(runner, '0.0.0.0', 80)
            await site.start()
            self.logger.info("✅ HTTP server started on port 80")
            
            # Set webhook for callbacks
            webhook_url = f"https://{os.getenv('REPLIT_DOMAINS', 'localhost')}/webhook"
            try:
                await self.bot.set_webhook(webhook_url)
                self.logger.info(f"✅ Webhook set: {webhook_url}")
            except Exception as e:
                self.logger.warning(f"Webhook setup failed: {e}")
            
            # Notify admins
            await self.notify_startup()
            
            self.running = True
            self.logger.info("✅ Production Bot is active and ready!")
            
            # Main loop
            while not self.shutdown_event.is_set():
                await asyncio.sleep(1)
                
        except Exception as e:
            self.logger.error(f"Critical error: {e}")
            raise
            
    async def process_message(self, event):
        """Process new message from monitored group"""
        try:
            message_id = event.message.id
            message_text = event.message.message or ""
            chat_id = event.chat_id
            
            self.logger.info(f"📨 New message ID {message_id} from chat {chat_id}")
            self.logger.info(f"📝 Text: {message_text[:50]}...")
            
            # Verify this is from target group
            if hasattr(self, 'target_group_id') and chat_id != self.target_group_id:
                self.logger.warning(f"⚠️ Message from wrong chat: {chat_id} != {self.target_group_id}")
                return
            
            # Analyze message
            analysis = self.analyze_message(message_text)
            self.logger.info(f"🤖 Analysis: {analysis['status']} ({analysis['confidence']}%)")
            
            # Store message
            message_data = {
                'id': message_id,
                'text': message_text,
                'analysis': analysis,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'sender': event.message.sender_id
            }
            
            self.message_storage[message_id] = message_data
            self.recent_messages.append(message_data)
            if len(self.recent_messages) > 14:
                self.recent_messages.pop(0)
            
            # Send to admins
            await self.send_to_admins(message_text, analysis, message_id)
            
        except Exception as e:
            self.logger.error(f"Message processing error: {e}")
            
    def analyze_message(self, text):
        """Analyze message for relocation status"""
        text_lower = text.lower()
        
        # Status keywords
        open_keywords = ['відкрито', 'відчинено', 'проїзд', 'можна', 'працює', 'open']
        closed_keywords = ['закрито', 'зачинено', 'немає', 'не працює', 'closed']
        
        open_count = sum(1 for keyword in open_keywords if keyword in text_lower)
        closed_count = sum(1 for keyword in closed_keywords if keyword in text_lower)
        
        if open_count > closed_count:
            return {"status": "відкрито", "confidence": min(60 + open_count * 20, 95)}
        elif closed_count > open_count:
            return {"status": "закрито", "confidence": min(60 + closed_count * 20, 95)}
        else:
            return {"status": "невизначено", "confidence": 30}
            
    async def send_to_admins(self, message_text, analysis, message_id):
        """Send message to administrators with approval buttons"""
        try:
            # Recent messages context
            recent_text = "📜 Останні повідомлення:\n"
            for msg in self.recent_messages[-5:]:
                recent_text += f"• {msg['text'][:50]}...\n"
                
            # Main message
            text = f"📨 Нове повідомлення з групи:\n\n{message_text}\n\n"
            text += f"🤖 Статус: {analysis['status']} ({analysis['confidence']}%)\n\n"
            text += recent_text
            
            # Buttons
            keyboard = [
                [
                    InlineKeyboardButton("✅ Відкрито", callback_data=f"approve_open_{message_id}"),
                    InlineKeyboardButton("❌ Закрито", callback_data=f"approve_closed_{message_id}")
                ],
                [
                    InlineKeyboardButton("🗑 Відхилити", callback_data=f"reject_{message_id}")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Send to each admin
            successful_sends = 0
            for admin_id in self.config.admin_user_ids:
                try:
                    await self.bot.send_message(
                        chat_id=admin_id,
                        text=text,
                        reply_markup=reply_markup
                    )
                    successful_sends += 1
                    self.logger.info(f"✅ Sent to admin {admin_id}")
                except Exception as e:
                    self.logger.warning(f"Failed to send to admin {admin_id}: {e}")
                    
            self.logger.info(f"📤 Message sent to {successful_sends}/{len(self.config.admin_user_ids)} admins")
            
        except Exception as e:
            self.logger.error(f"Admin notification error: {e}")
            
    async def approve_message(self, query_id, status, message_id):
        """Approve and publish message"""
        try:
            # Get current time in GMT+3
            kiev_time = datetime.now(timezone(timedelta(hours=3)))
            time_str = kiev_time.strftime("%H:%M")
            
            # Format message
            status_emoji = "✅" if status == "open" else "❌"
            status_text = "Відкрито" if status == "open" else "Закрито"
            
            final_message = f"{status_emoji} {status_text} 🕓 {time_str}"
            
            # Publish to channel
            await self.bot.send_message(
                chat_id=self.config.target_channel_id,
                text=final_message
            )
            
            self.logger.info(f"✅ Published to channel: {final_message}")
            
        except Exception as e:
            self.logger.error(f"Publishing error: {e}")
            
    async def reject_message(self, query_id, message_id):
        """Reject message"""
        try:
            self.logger.info(f"🗑 Message {message_id} rejected")
        except Exception as e:
            self.logger.error(f"Rejection error: {e}")
            
    async def notify_startup(self):
        """Notify admins about startup"""
        try:
            startup_message = f"🚀 Production Bot запущено!\n\n"
            startup_message += f"📅 Час: {datetime.now().strftime('%H:%M:%S')}\n"
            startup_message += f"🔗 Моніторинг: https://t.me/pereizdvyshneve\n"
            startup_message += f"📤 Публікація: {self.config.target_channel_id}\n\n"
            startup_message += f"✅ Система готова до роботи!"
            
            for admin_id in self.config.admin_user_ids:
                try:
                    await self.bot.send_message(chat_id=admin_id, text=startup_message)
                except Exception as e:
                    self.logger.warning(f"Startup notification failed for {admin_id}: {e}")
                    
        except Exception as e:
            self.logger.error(f"Startup notification error: {e}")

async def main():
    """Main function"""
    bot = ProductionBot()
    await bot.start()

if __name__ == "__main__":
    asyncio.run(main())