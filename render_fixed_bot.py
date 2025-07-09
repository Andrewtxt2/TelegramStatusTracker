#!/usr/bin/env python3
"""
Render Fixed Bot - Eliminates session conflicts for deployment
"""

import asyncio
import json
import logging
import os
import sys
import time
import traceback
from datetime import datetime, timedelta
from telethon import TelegramClient, events
from telegram.ext import Application, CallbackQueryHandler, CommandHandler
from telegram import Bot as TelegramBot, InlineKeyboardButton, InlineKeyboardMarkup
from aiohttp import web
from aiohttp.web import Request, Response

# Configuration
API_ID = int(os.getenv('TELEGRAM_API_ID', '26886585'))
API_HASH = os.getenv('TELEGRAM_API_HASH', '166e3719a0d93c12bf76af43fe91425f')
BOT_TOKEN = os.getenv('BOT_TOKEN', '8189087426:AAF2XtTEwDRbwvWny-Hi2BPz_0ZeJHh9DEc')
ADMIN_IDS = [int(x) for x in os.getenv('ADMIN_IDS', '6395626140,7766810783').split(',')]
SOURCE_GROUP = os.getenv('SOURCE_GROUP', 'https://t.me/pereizdvyshneve')
TARGET_CHANNEL = os.getenv('TARGET_CHANNEL', '@kryuvysh')
PORT = int(os.getenv('PORT', '5000'))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('render_fixed_bot.log')
    ]
)
logger = logging.getLogger('render_fixed_bot')

class RenderFixedBot:
    def __init__(self):
        self.client = None
        self.bot = None
        self.app = None
        self.web_app = None
        self.target_entity = None
        self.message_store = {}
        self.recent_messages = []
        self.running = True
        self.startup_time = datetime.now()
        
    async def start(self):
        """Start the render fixed bot system"""
        logger.info("🚀 Starting Render Fixed Bot (Session Conflict Solution)...")
        
        try:
            # Create unique session for this deployment
            import uuid
            session_name = f"render_deploy_{uuid.uuid4().hex[:8]}"
            
            logger.info(f"📱 Creating new session: {session_name}")
            self.client = TelegramClient(session_name, API_ID, API_HASH)
            
            # Start with phone authentication
            await self.client.start(phone='+380686850166')
            
            me = await self.client.get_me()
            logger.info(f"✅ MTProto connected: {me.first_name}")
            
            # Get target group
            logger.info("🔍 Searching for target group...")
            if SOURCE_GROUP.startswith('https://t.me/'):
                group_username = SOURCE_GROUP.split('/')[-1]
            else:
                group_username = SOURCE_GROUP
            
            self.target_entity = await self.client.get_entity(group_username)
            logger.info(f"✅ Group found: {self.target_entity.title}")
            
            # Initialize Bot API
            self.bot = TelegramBot(token=BOT_TOKEN)
            logger.info("✅ Bot API connected")
            
            # Setup handlers
            await self.setup_handlers()
            
            # Start web server
            await self.start_web_server()
            
            # Start bot polling
            await self.start_bot_polling()
            
            # Notify admins
            await self.notify_admins(
                "🚀 Render Fixed Bot DEPLOYED!\n\n"
                "✅ Новий сесійний файл створено\n"
                "✅ Конфлікти сесій виправлені\n"
                "✅ Моніторинг групи активний\n"
                "✅ Web server запущений\n\n"
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
            # If authentication fails, try to handle it gracefully
            await self.handle_auth_error(e)
            
    async def handle_auth_error(self, error):
        """Handle authentication errors"""
        if "AuthKeyDuplicatedError" in str(error):
            logger.warning("🔄 AuthKeyDuplicatedError detected, attempting recovery...")
            try:
                # Try with a different session name
                import time
                session_name = f"render_recovery_{int(time.time())}"
                logger.info(f"📱 Trying recovery session: {session_name}")
                
                if self.client:
                    await self.client.disconnect()
                    
                self.client = TelegramClient(session_name, API_ID, API_HASH)
                await self.client.start(phone='+380686850166')
                
                me = await self.client.get_me()
                logger.info(f"✅ Recovery successful: {me.first_name}")
                
                # Continue with setup
                await self.complete_setup()
                
            except Exception as recovery_error:
                logger.error(f"❌ Recovery failed: {recovery_error}")
                # Start web server anyway for health checks
                await self.start_web_server()
                
    async def complete_setup(self):
        """Complete setup after authentication"""
        try:
            # Get target group
            if SOURCE_GROUP.startswith('https://t.me/'):
                group_username = SOURCE_GROUP.split('/')[-1]
            else:
                group_username = SOURCE_GROUP
            
            self.target_entity = await self.client.get_entity(group_username)
            logger.info(f"✅ Group found: {self.target_entity.title}")
            
            # Setup handlers
            await self.setup_handlers()
            
            # Start web server
            await self.start_web_server()
            
            # Start bot polling
            await self.start_bot_polling()
            
            # Notify admins
            await self.notify_admins(
                "🚀 Render Fixed Bot RECOVERED!\n\n"
                "✅ Конфлікти сесій виправлені\n"
                "✅ Система працює нормально\n"
                f"📋 Група: {self.target_entity.title}\n"
                f"📢 Канал: {TARGET_CHANNEL}"
            )
            
        except Exception as e:
            logger.error(f"❌ Complete setup error: {e}")
            
    async def setup_handlers(self):
        """Setup all handlers"""
        logger.info("⚙️ Setting up handlers...")
        
        # MTProto handler for group messages
        @self.client.on(events.NewMessage(chats=self.target_entity))
        async def handle_group_message(event):
            try:
                await self.process_group_message(event.message)
            except Exception as e:
                logger.error(f"❌ Group message error: {e}")
        
        logger.info("✅ Handlers configured")
        
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
            
    async def start_bot_polling(self):
        """Start bot polling for commands"""
        try:
            logger.info("🔄 Starting bot polling...")
            
            # Initialize Bot API
            self.bot = TelegramBot(token=BOT_TOKEN)
            
            # Create application
            self.app = Application.builder().token(BOT_TOKEN).build()
            
            # Add handlers
            self.app.add_handler(CallbackQueryHandler(self.handle_callback))
            self.app.add_handler(CommandHandler("start", self.handle_start))
            self.app.add_handler(CommandHandler("status", self.handle_status_command))
            
            # Initialize and start
            await self.app.initialize()
            await self.app.start()
            
            # Start polling
            await self.app.updater.start_polling(
                drop_pending_updates=True,
                allowed_updates=["callback_query", "message"]
            )
            
            logger.info("✅ Bot polling started")
            
        except Exception as e:
            logger.error(f"❌ Bot polling error: {e}")
            
    async def handle_root(self, request: Request) -> Response:
        """Root endpoint"""
        return Response(text="Render Fixed Bot is running! 🤖", status=200)
        
    async def handle_health(self, request: Request) -> Response:
        """Health check endpoint"""
        health_data = {
            "status": "healthy",
            "uptime": str(datetime.now() - self.startup_time),
            "timestamp": datetime.now().isoformat(),
            "services": {
                "mtproto": self.client and self.client.is_connected() if self.client else False,
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
            "bot_name": "Render Fixed Bot",
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
        
    async def handle_start(self, update, context):
        """Handle /start command"""
        try:
            await update.message.reply_text(
                "🤖 Render Fixed Bot активний!\n\n"
                "✅ Конфлікти сесій виправлені\n"
                "✅ Моніторинг групи\n"
                "✅ Аналіз повідомлень\n"
                "✅ Публікація в канал\n\n"
                "Команда: /status"
            )
        except Exception as e:
            logger.error(f"❌ Start command error: {e}")
            
    async def handle_status_command(self, update, context):
        """Handle /status command"""
        try:
            uptime = datetime.now() - self.startup_time
            text = (
                f"📊 Render Fixed Bot Status\n\n"
                f"✅ Uptime: {uptime}\n"
                f"📋 Група: {self.target_entity.title if self.target_entity else 'N/A'}\n"
                f"📢 Канал: {TARGET_CHANNEL}\n"
                f"💬 Повідомлення: {len(self.recent_messages)}\n"
                f"🔗 MTProto: {'✅' if self.client and self.client.is_connected() else '❌'}\n"
                f"🤖 Bot API: {'✅' if self.bot else '❌'}\n"
                f"🌐 Web: {'✅' if self.web_app else '❌'}"
            )
            await update.message.reply_text(text)
        except Exception as e:
            logger.error(f"❌ Status command error: {e}")
            
    async def process_group_message(self, message):
        """Process group message"""
        try:
            if not message.text or len(message.text.strip()) < 1:
                return
                
            logger.info(f"📝 Processing message {message.id}: {message.text[:50]}...")
            
            # Simple analysis
            text = message.text.lower()
            if any(word in text for word in ['відкрит', 'відкрыт', 'open', '+']):
                status = 'open'
                confidence = 0.8
            elif any(word in text for word in ['закрит', 'закрыт', 'closed', '-']):
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
            
            # Update recent messages
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
            
    async def send_to_admins(self, message):
        """Send message to admins with buttons"""
        try:
            msg_data = self.message_store[message.id]
            time_str = message.date.strftime("%H:%M")
            
            # Build context
            context_text = ""
            if len(self.recent_messages) > 1:
                context_text = "📋 Контекст:\n"
                for i, recent_msg in enumerate(self.recent_messages[:-1]):
                    msg_time = recent_msg['date'].strftime("%H:%M")
                    msg_preview = recent_msg['text'][:50] + "..." if len(recent_msg['text']) > 50 else recent_msg['text']
                    context_text += f"{i+1}. {msg_time}: {msg_preview}\n"
                context_text += "\n"
            
            text = f"📨 Повідомлення о {time_str}\n\n{context_text}💬 НОВЕ: {message.text}\n\n🤖 Аналіз: {msg_data['status']} ({msg_data['confidence']:.0%})\n\nВиберіть дію:"
            
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
            logger.info(f"🎯 Callback: {data}")
            
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
            
    async def approve_message(self, query, message_id: int, status: str):
        """Approve and publish message"""
        try:
            logger.info(f"✅ Approving message {message_id} with status: {status}")
            
            # Get current time (GMT+3)
            current_time = datetime.now() + timedelta(hours=3)
            time_str = current_time.strftime("%H:%M")
            
            # Create channel message
            if status == 'open':
                channel_text = f"✅ Відкрито\n🕓 {time_str}"
            else:
                channel_text = f"❌ Закрито\n🕓 {time_str}"
            
            # Send to channel
            await self.bot.send_message(
                chat_id=TARGET_CHANNEL,
                text=channel_text
            )
            
            # Update admin
            await query.edit_message_text(
                f"✅ Повідомлення схвалено!\n\n📢 Канал: {TARGET_CHANNEL}\n📝 Статус: {status}\n🕓 Час: {time_str}"
            )
            
            logger.info(f"✅ Message {message_id} published")
            
        except Exception as e:
            logger.error(f"❌ Approve error: {e}")
            
    async def reject_message(self, query, message_id: int):
        """Reject message"""
        try:
            logger.info(f"🚫 Rejecting message {message_id}")
            await query.edit_message_text("🚫 Повідомлення відхилено")
        except Exception as e:
            logger.error(f"❌ Reject error: {e}")
            
    async def notify_admins(self, message: str):
        """Send notification to all admins"""
        try:
            for admin_id in ADMIN_IDS:
                try:
                    await self.bot.send_message(chat_id=admin_id, text=message)
                except Exception as e:
                    logger.error(f"❌ Failed to notify admin {admin_id}: {e}")
        except Exception as e:
            logger.error(f"❌ Notify admins error: {e}")

async def main():
    """Main function"""
    bot = RenderFixedBot()
    await bot.start()

if __name__ == "__main__":
    asyncio.run(main())