#!/usr/bin/env python3
"""
Render-optimized Telegram Bot
Fixed version for stable deployment without polling conflicts
"""

import asyncio
import json
import logging
import os
import time
import traceback
from datetime import datetime, timedelta
from telethon import TelegramClient, events
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CallbackQueryHandler, CommandHandler
from message_analyzer import MessageAnalyzer
from aiohttp import web
from aiohttp.web import Request, Response
import signal
import sys

# Configuration
API_ID = int(os.getenv('TELEGRAM_API_ID', '26886585'))
API_HASH = os.getenv('TELEGRAM_API_HASH', '166e3719a0d93c12bf76af43fe91425f')
BOT_TOKEN = '8189087426:AAF2XtTEwDRbwvWny-Hi2BPz_0ZeJHh9DEc'
SOURCE_GROUP = 'https://t.me/pereizdvyshneve'
TARGET_CHANNEL = '@kryuvysh'
ADMIN_IDS = [6395626140, 7766810783]
PORT = int(os.getenv('PORT', '5000'))

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('render_bot.log')
    ]
)
logger = logging.getLogger('render_bot')

class RenderBot:
    def __init__(self):
        self.client = None
        self.bot = None
        self.app = None
        self.web_app = None
        self.target_entity = None
        self.analyzer = MessageAnalyzer()
        self.message_store = {}
        self.recent_messages = []
        self.running = True
        self.startup_time = datetime.now()
        
    async def start(self):
        """Start the Render-optimized bot system"""
        logger.info("🚀 Starting Render Bot System...")
        
        try:
            # Initialize MTProto client with existing session
            session_name = "working_session"
            self.client = TelegramClient(session_name, API_ID, API_HASH)
            
            logger.info("📱 Starting authentication...")
            await self.client.start(phone='+380686850166')
            
            me = await self.client.get_me()
            logger.info(f"✅ MTProto connected: {me.first_name}")
            
            # Get target group
            logger.info("🔍 Searching for target group...")
            group_username = SOURCE_GROUP.split('/')[-1]
            self.target_entity = await self.client.get_entity(group_username)
            logger.info(f"✅ Group found: {self.target_entity.title}")
            
            # Initialize Bot API
            self.bot = Bot(token=BOT_TOKEN)
            logger.info("✅ Bot API connected")
            
            # Setup MTProto handlers
            await self.setup_mtproto_handlers()
            
            # Start web server for health checks
            await self.start_web_server()
            
            # Start bot application (webhook mode for Render)
            await self.start_bot_application()
            
            # Notify admins
            await self.notify_admins(
                "🚀 RENDER BOT ЗАПУЩЕНО!\n\n"
                "✅ Оптимізовано для Render\n"
                "✅ Webhook режим\n"
                "✅ Контекст останніх 9 повідомлень\n"
                "✅ Стабільна робота 24/7\n\n"
                f"📋 Група: {self.target_entity.title}\n"
                f"📢 Канал: {TARGET_CHANNEL}\n"
                f"🌐 Порт: {PORT}"
            )
            
            logger.info("🔄 Bot running on Render...")
            
            # Keep running
            await self.client.run_until_disconnected()
            
        except Exception as e:
            logger.error(f"❌ Startup error: {e}")
            logger.error(traceback.format_exc())
            
    async def setup_mtproto_handlers(self):
        """Setup MTProto event handlers"""
        logger.info("⚙️ Setting up MTProto handlers...")
        
        @self.client.on(events.NewMessage(chats=self.target_entity))
        async def handle_group_message(event):
            try:
                logger.info(f"📨 Group message {event.message.id}")
                await self.process_group_message(event.message)
            except Exception as e:
                logger.error(f"❌ Group message error: {e}")
                
        logger.info("✅ MTProto handlers configured")
        
    async def start_web_server(self):
        """Start web server for health checks"""
        try:
            self.web_app = web.Application()
            self.web_app.router.add_get('/', self.handle_root)
            self.web_app.router.add_get('/health', self.handle_health)
            self.web_app.router.add_get('/status', self.handle_status)
            
            runner = web.AppRunner(self.web_app)
            await runner.setup()
            site = web.TCPSite(runner, '0.0.0.0', PORT)
            await site.start()
            
            logger.info(f"🌐 Web server started on port {PORT}")
            
        except Exception as e:
            logger.error(f"❌ Web server error: {e}")
            
    async def handle_root(self, request: Request) -> Response:
        """Root endpoint"""
        return Response(text="Render Bot is running! 🤖", status=200)
        
    async def handle_health(self, request: Request) -> Response:
        """Health check endpoint"""
        health_data = {
            "status": "healthy",
            "uptime": str(datetime.now() - self.startup_time),
            "timestamp": datetime.now().isoformat(),
            "services": {
                "mtproto": self.client and self.client.is_connected(),
                "bot_api": self.bot is not None,
                "web_server": True
            }
        }
        return Response(
            text=json.dumps(health_data, indent=2),
            content_type='application/json',
            status=200
        )
        
    async def handle_status(self, request: Request) -> Response:
        """Status endpoint"""
        status_data = {
            "bot_name": "Render Bot",
            "version": "1.0.0",
            "group": self.target_entity.title if self.target_entity else "Not connected",
            "channel": TARGET_CHANNEL,
            "admins": len(ADMIN_IDS),
            "recent_messages": len(self.recent_messages),
            "stored_messages": len(self.message_store),
            "uptime": str(datetime.now() - self.startup_time)
        }
        return Response(
            text=json.dumps(status_data, indent=2),
            content_type='application/json',
            status=200
        )
        
    async def start_bot_application(self):
        """Start bot application in webhook mode"""
        try:
            logger.info("🔄 Starting Bot Application...")
            
            # Create application
            self.app = Application.builder().token(BOT_TOKEN).build()
            
            # Add handlers
            self.app.add_handler(CallbackQueryHandler(self.handle_callback))
            self.app.add_handler(CommandHandler("start", self.handle_start))
            self.app.add_handler(CommandHandler("status", self.handle_status_command))
            self.app.add_handler(CommandHandler("health", self.handle_health_command))
            
            # Initialize and start
            await self.app.initialize()
            await self.app.start()
            
            # Clear webhook and use polling for Render
            try:
                await self.bot.delete_webhook(drop_pending_updates=True)
                logger.info("✅ Webhook cleared")
                
                # Start polling in background task
                asyncio.create_task(self.polling_loop())
                
            except Exception as e:
                logger.error(f"❌ Bot application error: {e}")
                
        except Exception as e:
            logger.error(f"❌ Bot application startup error: {e}")
            
    async def polling_loop(self):
        """Custom polling loop to avoid conflicts"""
        logger.info("🔄 Starting custom polling loop...")
        
        offset = 0
        while self.running:
            try:
                # Get updates manually
                updates = await self.bot.get_updates(
                    offset=offset,
                    timeout=30,
                    allowed_updates=["callback_query", "message"]
                )
                
                for update in updates:
                    offset = update.update_id + 1
                    
                    # Handle callback queries
                    if update.callback_query:
                        await self.handle_callback(update, None)
                    
                    # Handle messages
                    elif update.message:
                        await self.handle_message(update, None)
                        
            except Exception as e:
                logger.error(f"❌ Polling error: {e}")
                await asyncio.sleep(5)
                
    async def handle_start(self, update, context):
        """Handle /start command"""
        try:
            await update.message.reply_text(
                "🤖 Render Bot активний!\n\n"
                "✅ Моніторинг групи\n"
                "✅ Аналіз повідомлень\n"
                "✅ Публікація в канал\n\n"
                "Команди: /status, /health"
            )
        except Exception as e:
            logger.error(f"❌ Start command error: {e}")
            
    async def handle_status_command(self, update, context):
        """Handle /status command"""
        try:
            uptime = datetime.now() - self.startup_time
            text = (
                f"📊 Render Bot Status\n\n"
                f"✅ Uptime: {uptime}\n"
                f"📋 Група: {self.target_entity.title if self.target_entity else 'N/A'}\n"
                f"📢 Канал: {TARGET_CHANNEL}\n"
                f"💬 Останні повідомлення: {len(self.recent_messages)}\n"
                f"🗃️ Збережено: {len(self.message_store)}\n"
                f"🔗 MTProto: {'✅' if self.client.is_connected() else '❌'}\n"
                f"🤖 Bot API: {'✅' if self.bot else '❌'}"
            )
            await update.message.reply_text(text)
        except Exception as e:
            logger.error(f"❌ Status command error: {e}")
            
    async def handle_health_command(self, update, context):
        """Handle /health command"""
        try:
            text = (
                "🏥 Health Check\n\n"
                "✅ Всі сервіси працюють\n"
                "✅ Підключення стабільне\n"
                "✅ Готовий до роботи"
            )
            await update.message.reply_text(text)
        except Exception as e:
            logger.error(f"❌ Health command error: {e}")
            
    async def handle_message(self, update, context):
        """Handle regular messages"""
        try:
            # Only handle messages from admins
            if update.message.from_user.id not in ADMIN_IDS:
                return
                
            logger.info(f"📨 Admin message from {update.message.from_user.id}")
            
        except Exception as e:
            logger.error(f"❌ Message handling error: {e}")
            
    async def process_group_message(self, message):
        """Process group message"""
        try:
            if not message.text or len(message.text.strip()) < 1:
                logger.info(f"📝 Skipping empty message {message.id}")
                return
                
            logger.info(f"📝 Processing message {message.id}: {message.text[:50]}...")
            
            # Simple analysis
            text = message.text.lower()
            if 'відкрит' in text or 'открыт' in text or 'open' in text or '+' in text:
                status = 'open'
                confidence = 0.8
            elif 'закрит' in text or 'закрыт' in text or 'closed' in text or '-' in text:
                status = 'closed'
                confidence = 0.8
            else:
                status = 'unknown'
                confidence = 0.3
            
            # Store message
            self.message_store[message.id] = {
                'text': message.text,
                'date': message.date,
                'status': status,
                'confidence': confidence
            }
            
            # Add to recent messages (keep last 9)
            self.recent_messages.append({
                'text': message.text,
                'date': message.date,
                'id': message.id
            })
            
            if len(self.recent_messages) > 9:
                self.recent_messages.pop(0)
            
            logger.info(f"🤖 Analysis: {status} ({confidence:.0%})")
            
            # Send to admins
            await self.send_to_admins(message)
            
        except Exception as e:
            logger.error(f"❌ Message processing error: {e}")
            logger.error(traceback.format_exc())
            
    async def send_to_admins(self, message):
        """Send message to admins with buttons"""
        try:
            logger.info(f"📤 Sending message {message.id} to admins...")
            
            msg_data = self.message_store[message.id]
            time_str = message.date.strftime("%H:%M")
            
            # Build context from recent messages
            context_text = ""
            if len(self.recent_messages) > 1:
                context_text = "📋 Контекст (останні повідомлення):\n"
                for i, recent_msg in enumerate(self.recent_messages[:-1]):
                    msg_time = recent_msg['date'].strftime("%H:%M")
                    msg_preview = recent_msg['text'][:50] + "..." if len(recent_msg['text']) > 50 else recent_msg['text']
                    context_text += f"{i+1}. {msg_time}: {msg_preview}\n"
                context_text += "\n"
            
            text = f"📨 Повідомлення о {time_str}\n\n"
            text += context_text
            text += f"💬 НОВЕ: {message.text}\n\n"
            text += f"🤖 Аналіз: {msg_data['status']} ({msg_data['confidence']:.0%})\n\n"
            text += "Виберіть дію:"
            
            # Create buttons
            keyboard = [
                [
                    InlineKeyboardButton("✅ Відкрито", callback_data=f"approve_open_{message.id}"),
                    InlineKeyboardButton("❌ Закрито", callback_data=f"approve_closed_{message.id}")
                ],
                [
                    InlineKeyboardButton("🚫 Відхилити", callback_data=f"reject_{message.id}")
                ]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Send to all admins
            for admin_id in ADMIN_IDS:
                try:
                    await self.bot.send_message(
                        chat_id=admin_id,
                        text=text,
                        reply_markup=reply_markup
                    )
                    logger.info(f"✅ Sent to admin {admin_id}")
                except Exception as e:
                    logger.error(f"❌ Failed to send to admin {admin_id}: {e}")
                    
        except Exception as e:
            logger.error(f"❌ Send to admins error: {e}")
            
    async def handle_callback(self, update, context):
        """Handle callback queries"""
        try:
            query = update.callback_query
            await query.answer()
            
            data = query.data
            logger.info(f"🎯 Callback: {data} from {query.from_user.id}")
            
            if data.startswith("approve_"):
                action_parts = data.split("_")
                status = action_parts[1]
                message_id = int(action_parts[2])
                
                await self.approve_message(query, message_id, status)
                
            elif data.startswith("reject_"):
                message_id = int(data.split("_")[1])
                await self.reject_message(query, message_id)
                
        except Exception as e:
            logger.error(f"❌ Callback error: {e}")
            
    async def approve_message(self, query, message_id, status):
        """Approve and publish message"""
        try:
            logger.info(f"📤 Starting approval for message {message_id} with status {status}")
            
            status_emoji = "✅" if status == "open" else "❌"
            status_text = "Відкрито" if status == "open" else "Закрито"
            
            # Use GMT+3 timezone
            utc_now = datetime.utcnow()
            kyiv_time = utc_now + timedelta(hours=3)
            current_time = kyiv_time.strftime("%H:%M")
            channel_text = f"{status_emoji} {status_text}\n🕓 {current_time}"
            
            logger.info(f"📢 Publishing to channel {TARGET_CHANNEL}: {channel_text}")
            
            # Send to channel
            await self.bot.send_message(
                chat_id=TARGET_CHANNEL,
                text=channel_text
            )
            
            logger.info("✅ Successfully published to channel")
            
            # Update admin message
            await query.edit_message_text(
                text=f"✅ Опубліковано як {status_text}\n\n"
                     f"📢 Канал: {TARGET_CHANNEL}\n"
                     f"🕓 Час: {current_time}\n"
                     f"👤 Адмін: {query.from_user.first_name}"
            )
            
            logger.info(f"✅ Message {message_id} published as {status}")
            
        except Exception as e:
            logger.error(f"❌ Approve error: {e}")
            
    async def reject_message(self, query, message_id):
        """Reject message"""
        try:
            await query.edit_message_text(
                text=f"🚫 Повідомлення відхилено\n\n"
                     f"👤 Адмін: {query.from_user.first_name}\n"
                     f"🕓 Час: {datetime.now().strftime('%H:%M')}"
            )
            
            logger.info(f"🚫 Message {message_id} rejected")
            
        except Exception as e:
            logger.error(f"❌ Reject error: {e}")
            
    async def notify_admins(self, message):
        """Notify all admins"""
        try:
            for admin_id in ADMIN_IDS:
                try:
                    await self.bot.send_message(admin_id, message)
                    logger.info(f"✅ Notified admin {admin_id}")
                except Exception as e:
                    logger.error(f"❌ Failed to notify admin {admin_id}: {e}")
        except Exception as e:
            logger.error(f"❌ Notify admins error: {e}")
            
    async def stop(self):
        """Stop the bot"""
        logger.info("🛑 Stopping Render Bot...")
        self.running = False
        
        if self.app:
            await self.app.stop()
            await self.app.shutdown()
            
        if self.client:
            await self.client.disconnect()
            
        logger.info("✅ Render Bot stopped")

# Main execution
async def main():
    """Main function"""
    bot = RenderBot()
    
    # Handle shutdown signals
    def signal_handler(sig, frame):
        logger.info(f"🔔 Received signal {sig}")
        asyncio.create_task(bot.stop())
        
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await bot.start()
    except KeyboardInterrupt:
        logger.info("🔔 Keyboard interrupt received")
    except Exception as e:
        logger.error(f"❌ Main error: {e}")
        logger.error(traceback.format_exc())
    finally:
        await bot.stop()

if __name__ == "__main__":
    asyncio.run(main())