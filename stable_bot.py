#!/usr/bin/env python3
"""
Стабільна версія бота без конфліктів
"""

import asyncio
import signal
import sys
import os
import json
from datetime import datetime, timezone, timedelta
from aiohttp import web
from telethon import TelegramClient, events
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from config import Config
from logger import setup_logger

class StableBot:
    def __init__(self):
        self.logger = setup_logger("stable_bot")
        self.config = Config()
        
        # API credentials
        self.api_id = int(os.getenv('TELEGRAM_API_ID'))
        self.api_hash = os.getenv('TELEGRAM_API_HASH')
        self.phone = os.getenv('TELEGRAM_PHONE')
        
        # Bot setup
        self.bot_token = self.config.bot_token
        self.bot = Bot(token=self.bot_token)
        
        # Telegram client
        self.client = TelegramClient('session', self.api_id, self.api_hash)
        
        # State
        self.running = False
        self.start_time = datetime.now(timezone.utc)
        self.recent_messages = []
        self.message_history_file = "recent_messages.json"
        
        # Web server
        self.web_app = None
        self.runner = None
        self.site = None
        
    async def load_recent_messages(self):
        """Load recent messages"""
        try:
            if os.path.exists(self.message_history_file):
                with open(self.message_history_file, 'r', encoding='utf-8') as f:
                    self.recent_messages = json.load(f)
                self.logger.info(f"Завантажено {len(self.recent_messages)} повідомлень")
        except Exception as e:
            self.logger.error(f"Помилка завантаження: {e}")
            self.recent_messages = []
            
    async def save_recent_messages(self):
        """Save recent messages"""
        try:
            with open(self.message_history_file, 'w', encoding='utf-8') as f:
                json.dump(self.recent_messages, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"Помилка збереження: {e}")
            
    async def setup_web_server(self):
        """Setup web server"""
        self.web_app = web.Application()
        
        self.web_app.router.add_get('/', self.root_endpoint)
        self.web_app.router.add_get('/health', self.health_endpoint)
        self.web_app.router.add_get('/status', self.status_endpoint)
        
        self.runner = web.AppRunner(self.web_app)
        await self.runner.setup()
        
        port = int(os.getenv('PORT', 80))
        self.site = web.TCPSite(self.runner, '0.0.0.0', port)
        await self.site.start()
        
        self.logger.info(f"Web server started on port {port}")
        
    async def root_endpoint(self, request):
        """Root endpoint"""
        return web.Response(text="Stable Telegram Bot is running")
        
    async def health_endpoint(self, request):
        """Health endpoint"""
        uptime = (datetime.now(timezone.utc) - self.start_time).total_seconds()
        
        health_data = {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "uptime": uptime,
            "bot_running": self.running,
            "service": "stable-telegram-bot",
            "version": "1.0.0"
        }
        
        return web.Response(
            text=json.dumps(health_data, indent=2),
            headers={'Content-Type': 'application/json'}
        )
        
    async def status_endpoint(self, request):
        """Status endpoint"""
        uptime = (datetime.now(timezone.utc) - self.start_time).total_seconds()
        
        status_data = {
            "service": "Stable Telegram Bot",
            "version": "1.0.0",
            "uptime": uptime,
            "bot_running": self.running,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "messages_count": len(self.recent_messages)
        }
        
        return web.Response(
            text=json.dumps(status_data, indent=2),
            headers={'Content-Type': 'application/json'}
        )
        
    async def setup_telegram_client(self):
        """Setup Telegram client"""
        await self.client.connect()
        
        if not await self.client.is_user_authorized():
            self.logger.error("Не авторизований")
            return False
            
        me = await self.client.get_me()
        self.logger.info(f"Авторизований як: {me.first_name}")
        
        # Setup message handler
        @self.client.on(events.NewMessage(chats='@pereizdvyshneve'))
        async def handle_message(event):
            await self.process_message(event)
            
        return True
        
    async def process_message(self, event):
        """Process new message"""
        try:
            message_text = event.message.text
            if not message_text:
                return
                
            sender = await event.get_sender()
            sender_name = sender.first_name if sender else "Unknown"
            
            self.logger.info(f"Нове повідомлення від {sender_name}: {message_text[:50]}...")
            
            # Store message
            message_data = {
                "id": event.message.id,
                "text": message_text,
                "from_user": sender_name,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            self.recent_messages.append(message_data)
            if len(self.recent_messages) > 14:
                self.recent_messages.pop(0)
                
            await self.save_recent_messages()
            
            # Send to admins
            await self.send_to_admins(message_data)
            
        except Exception as e:
            self.logger.error(f"Помилка обробки повідомлення: {e}")
            
    async def send_to_admins(self, message_data):
        """Send message to admins"""
        try:
            keyboard = [
                [
                    InlineKeyboardButton("✅ ВІДКРИТО", callback_data=f"approve_open_{message_data['id']}"),
                    InlineKeyboardButton("❌ ЗАКРИТО", callback_data=f"approve_closed_{message_data['id']}")
                ],
                [
                    InlineKeyboardButton("🗑️ ВІДХИЛИТИ", callback_data=f"reject_{message_data['id']}")
                ]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Recent messages context
            recent_context = "\n".join([
                f"• {msg['from_user']}: {msg['text'][:50]}..." 
                for msg in self.recent_messages[-5:]
            ])
            
            admin_text = f"""
📝 Нове повідомлення

👤 Від: {message_data['from_user']}
📄 Текст: {message_data['text']}

📋 Останні повідомлення:
{recent_context}
            """
            
            admin_ids = self.config.admin_user_ids
            sent_count = 0
            
            for admin_id in admin_ids:
                try:
                    await self.bot.send_message(
                        chat_id=admin_id,
                        text=admin_text,
                        reply_markup=reply_markup
                    )
                    sent_count += 1
                    self.logger.info(f"Відправлено адміністратору {admin_id}")
                except Exception as e:
                    self.logger.error(f"Помилка відправки {admin_id}: {e}")
                    
            self.logger.info(f"Відправлено {sent_count} з {len(admin_ids)} адміністраторів")
            
        except Exception as e:
            self.logger.error(f"Помилка відправки адмінам: {e}")
            
    async def start(self):
        """Start the bot"""
        try:
            self.logger.info("Запуск стабільного бота...")
            
            # Load messages
            await self.load_recent_messages()
            
            # Setup web server
            await self.setup_web_server()
            
            # Setup Telegram client
            if not await self.setup_telegram_client():
                raise Exception("Не вдалося налаштувати Telegram client")
                
            self.running = True
            self.logger.info("Стабільний бот запущено успішно!")
            
            # Keep running
            while self.running:
                await asyncio.sleep(1)
                
        except Exception as e:
            self.logger.error(f"Помилка запуску: {e}")
            await self.stop()
            raise
            
    async def stop(self):
        """Stop the bot"""
        try:
            self.logger.info("Зупинка бота...")
            self.running = False
            
            if self.client:
                await self.client.disconnect()
                
            if self.site:
                await self.site.stop()
            if self.runner:
                await self.runner.cleanup()
                
            self.logger.info("Бот зупинено")
            
        except Exception as e:
            self.logger.error(f"Помилка зупинки: {e}")
            
    def signal_handler(self, signum, frame):
        """Handle signals"""
        self.logger.info(f"Отримано сигнал {signum}")
        asyncio.create_task(self.stop())
        sys.exit(0)

async def main():
    """Main function"""
    bot = StableBot()
    
    signal.signal(signal.SIGINT, bot.signal_handler)
    signal.signal(signal.SIGTERM, bot.signal_handler)
    
    try:
        await bot.start()
    except KeyboardInterrupt:
        await bot.stop()
    except Exception as e:
        bot.logger.error(f"Критична помилка: {e}")
        await bot.stop()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())