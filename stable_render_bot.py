#!/usr/bin/env python3
"""
Stable Render Bot - Concurrent MTProto monitoring and Bot API polling
Guarantees continuous operation without blocking
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
API_ID = int(os.getenv('TELEGRAM_API_ID', '29299324'))
API_HASH = os.getenv('TELEGRAM_API_HASH', 'c262483dda2739c72637661b537dccac')
BOT_TOKEN = os.getenv('BOT_TOKEN', '8189087426:AAF2XtTEwDRbwvWny-Hi2BPz_0ZeJHh9DEc')
ADMIN_IDS = [int(x) for x in os.getenv('ADMIN_IDS', '6395626140,7766810783,564704015').split(',')]
SOURCE_GROUP = os.getenv('SOURCE_GROUP', 'https://t.me/pereizdvyshneve')
TARGET_CHANNEL = os.getenv('TARGET_CHANNEL', '@kryuvysh')
PORT = int(os.getenv('PORT', '5000'))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('stable_render_bot.log')
    ]
)
logger = logging.getLogger('stable_render_bot')

class StableRenderBot:
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
        self.last_message_time = datetime.now()
        
    async def start(self):
        """Start the stable render bot"""
        logger.info("🚀 Starting Stable Render Bot...")
        
        try:
            # Start web server first
            await self.start_web_server()
            
            # Initialize MTProto client
            session_files = [
                'auth_session.session',
                'new_auth_session.session',
                'simple_render_bot.session',
                'working_session.session',
                'render_session.session'
            ]
            
            session_used = None
            for session_file in session_files:
                if os.path.exists(session_file):
                    session_used = session_file
                    logger.info(f"📱 Using existing session: {session_file}")
                    break
            
            if not session_used:
                logger.error("❌ No existing session found!")
                return
            
            # Initialize MTProto client
            self.client = TelegramClient(session_used.replace('.session', ''), API_ID, API_HASH)
            await self.client.connect()
            
            if not await self.client.is_user_authorized():
                logger.error("❌ Session not authorized!")
                return
                
            me = await self.client.get_me()
            logger.info(f"✅ MTProto connected: {me.first_name}")
            
            # Get target group
            logger.info("🔍 Searching for target group...")
            if SOURCE_GROUP.startswith('https://t.me/'):
                group_username = SOURCE_GROUP.split('/')[-1]
            else:
                group_username = SOURCE_GROUP
            
            self.target_entity = await self.client.get_entity(group_username)
            logger.info(f"✅ Group found: {self.target_entity.title} (ID: {self.target_entity.id})")
            
            # Initialize Bot API
            self.bot = TelegramBot(token=BOT_TOKEN)
            logger.info("✅ Bot API connected")
            
            # Start concurrent tasks
            tasks = [
                asyncio.create_task(self.start_message_monitoring()),
                asyncio.create_task(self.start_bot_polling()),
                asyncio.create_task(self.health_check_loop())
            ]
            
            # Notify admins
            await self.notify_admins(
                "🚀 Stable Render Bot STARTED!\n\n"
                "✅ MTProto моніторинг активний\n"
                "✅ Bot API polling запущен\n"
                "✅ Web server працює\n"
                "✅ Кнопки схвалення працюють\n\n"
                f"📋 Група: {self.target_entity.title}\n"
                f"📢 Канал: {TARGET_CHANNEL}\n"
                f"🌐 Порт: {PORT}"
            )
            
            logger.info("🔄 All systems running...")
            
            # Wait for all tasks
            await asyncio.gather(*tasks)
            
        except Exception as e:
            logger.error(f"❌ Startup error: {e}")
            logger.error(traceback.format_exc())
            
    async def start_message_monitoring(self):
        """Start MTProto message monitoring"""
        logger.info("🔍 Starting message monitoring...")
        
        try:
            # Register message handler
            @self.client.on(events.NewMessage(chats=self.target_entity))
            async def handle_group_message(event):
                try:
                    message = event.message
                    logger.info(f"📨 New message from {self.target_entity.title}: ID {message.id}")
                    await self.process_group_message(message)
                except Exception as e:
                    logger.error(f"❌ Message processing error: {e}")
                    
            # Start continuous monitoring
            logger.info("✅ Message handler registered")
            
            # Keep monitoring alive
            while self.running:
                try:
                    await asyncio.sleep(5)
                    
                    # Check connection
                    if not self.client.is_connected():
                        logger.warning("⚠️ MTProto disconnected, reconnecting...")
                        await self.client.connect()
                        
                except Exception as e:
                    logger.error(f"❌ Monitoring error: {e}")
                    await asyncio.sleep(10)
                    
        except Exception as e:
            logger.error(f"❌ Message monitoring error: {e}")
            
    async def start_bot_polling(self):
        """Start Bot API polling using manual approach"""
        logger.info("🔄 Starting Bot API polling...")
        
        try:
            # Create application
            self.app = Application.builder().token(BOT_TOKEN).build()
            
            # Add handlers
            self.app.add_handler(CallbackQueryHandler(self.handle_callback))
            self.app.add_handler(CommandHandler("start", self.handle_start))
            self.app.add_handler(CommandHandler("status", self.handle_status_command))
            
            # Initialize and start
            await self.app.initialize()
            await self.app.start()
            
            logger.info("✅ Bot API initialized")
            
            # Manual polling loop to avoid AttributeError
            offset = 0
            while self.running:
                try:
                    # Get updates manually
                    updates = await self.app.bot.get_updates(
                        offset=offset,
                        timeout=10,
                        allowed_updates=["callback_query", "message"]
                    )
                    
                    # Process each update
                    for update in updates:
                        try:
                            await self.app.process_update(update)
                            offset = update.update_id + 1
                        except Exception as process_error:
                            logger.error(f"❌ Update processing error: {process_error}")
                    
                    # Small delay between polling
                    await asyncio.sleep(1)
                    
                except Exception as poll_error:
                    logger.error(f"❌ Polling error: {poll_error}")
                    await asyncio.sleep(5)
                    
            logger.info("✅ Bot API polling started")
                
        except Exception as e:
            logger.error(f"❌ Bot polling error: {e}")
            
    async def health_check_loop(self):
        """Health check loop"""
        logger.info("🏥 Starting health check loop...")
        
        while self.running:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes
                
                # Check MTProto connection
                if not self.client.is_connected():
                    logger.warning("⚠️ MTProto disconnected")
                    await self.client.connect()
                    
                # Check message processing
                time_since_last = (datetime.now() - self.last_message_time).total_seconds()
                if time_since_last > 3600:  # 1 hour without messages
                    logger.info(f"ℹ️ No messages for {time_since_last/60:.1f} minutes")
                    
                logger.info("✅ Health check passed")
                
            except Exception as e:
                logger.error(f"❌ Health check error: {e}")
                
    async def process_group_message(self, message):
        """Process message from target group"""
        try:
            self.last_message_time = datetime.now()
            
            # Skip non-text messages
            if not message.text:
                logger.info(f"⏩ Skipping non-text message {message.id}")
                return
                
            # Skip old messages (more than 1 hour)
            # Convert to UTC for comparison
            from datetime import timezone
            now_utc = datetime.now(timezone.utc)
            if message.date < now_utc - timedelta(hours=1):
                logger.info(f"⏩ Skipping old message {message.id}")
                return
                
            logger.info(f"📝 Processing message {message.id}: {message.text[:50]}...")
            
            # Analyze message
            analysis = await self.analyze_message(message.text)
            
            # Store message
            self.message_store[message.id] = {
                'text': message.text,
                'date': message.date,
                'status': analysis['status'],
                'confidence': analysis['confidence']
            }
            
            # Add to recent messages
            self.recent_messages.append({
                'id': message.id,
                'text': message.text,
                'date': message.date
            })
            
            # Keep only last 10 messages
            if len(self.recent_messages) > 10:
                self.recent_messages = self.recent_messages[-10:]
                
            logger.info(f"🤖 Analysis: {analysis['status']} ({analysis['confidence']:.0%})")
            
            # Send to admins
            await self.send_to_admins(message)
            
        except Exception as e:
            logger.error(f"❌ Message processing error: {e}")
            
    async def analyze_message(self, text):
        """Analyze message text"""
        text_lower = text.lower()
        
        # Keywords for closed status
        closed_keywords = ['закрит', 'закрыт', 'закрыто', 'closed', 'close', 'перекрыт', 'перекрыто', 'заблокиров']
        
        # Keywords for open status  
        open_keywords = ['открыт', 'відкрит', 'открыто', 'open', 'opened', 'разблокиров', 'проезд']
        
        closed_score = sum(1 for keyword in closed_keywords if keyword in text_lower)
        open_score = sum(1 for keyword in open_keywords if keyword in text_lower)
        
        if closed_score > open_score:
            return {'status': 'closed', 'confidence': min(0.8, 0.6 + closed_score * 0.1)}
        elif open_score > closed_score:
            return {'status': 'open', 'confidence': min(0.8, 0.6 + open_score * 0.1)}
        else:
            return {'status': 'unknown', 'confidence': 0.5}
            
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
            user_id = query.from_user.id
            data = query.data
            
            logger.info(f"🎯 Callback from user {user_id}: {data}")
            
            # Check if user is admin
            if user_id not in ADMIN_IDS:
                logger.warning(f"⚠️ Non-admin user {user_id} tried to use callback")
                await query.answer("❌ Доступ заборонено", show_alert=True)
                return
            
            # Answer callback query immediately
            await query.answer("🔄 Обробка...")
            
            if data.startswith("approve_"):
                action_parts = data.split("_")
                if len(action_parts) >= 3:
                    status = action_parts[1]
                    message_id = int(action_parts[2])
                    
                    logger.info(f"✅ Processing approve: {status} for message {message_id}")
                    await self.approve_message(query, message_id, status)
                    
            elif data.startswith("reject_"):
                parts = data.split("_")
                if len(parts) >= 2:
                    message_id = int(parts[1])
                    logger.info(f"🚫 Processing reject for message {message_id}")
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
            logger.info(f"📢 Sending to channel: {TARGET_CHANNEL}")
            await self.bot.send_message(
                chat_id=TARGET_CHANNEL,
                text=channel_text
            )
            logger.info(f"✅ Successfully sent to channel")
            
            # Update admin
            await query.edit_message_text(
                f"✅ Повідомлення схвалено!\n\n📢 Канал: {TARGET_CHANNEL}\n📝 Статус: {status}\n🕓 Час: {time_str}"
            )
            
            logger.info(f"✅ Message {message_id} fully processed")
            
        except Exception as e:
            logger.error(f"❌ Approve error: {e}")
            
    async def reject_message(self, query, message_id: int):
        """Reject message"""
        try:
            logger.info(f"🚫 Rejecting message {message_id}")
            await query.edit_message_text("🚫 Повідомлення відхилено")
        except Exception as e:
            logger.error(f"❌ Reject error: {e}")
            
    async def start_web_server(self):
        """Start web server"""
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
        return Response(text="Stable Render Bot is running! 🤖", status=200)
        
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
            "bot_name": "Stable Render Bot",
            "version": "1.0.0",
            "group": self.target_entity.title if self.target_entity else "Not connected",
            "channel": TARGET_CHANNEL,
            "admins": len(ADMIN_IDS),
            "recent_messages": len(self.recent_messages),
            "stored_messages": len(self.message_store),
            "last_message": self.last_message_time.isoformat(),
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
                "🤖 Stable Render Bot активний!\n\n"
                "✅ MTProto моніторинг\n"
                "✅ Bot API polling\n"
                "✅ Web server\n\n"
                "Команди: /status"
            )
        except Exception as e:
            logger.error(f"❌ Start command error: {e}")
            
    async def handle_status_command(self, update, context):
        """Handle /status command"""
        try:
            uptime = datetime.now() - self.startup_time
            time_since_last = (datetime.now() - self.last_message_time).total_seconds()
            
            text = (
                f"📊 Stable Render Bot Status\n\n"
                f"✅ Uptime: {uptime}\n"
                f"📋 Група: {self.target_entity.title if self.target_entity else 'N/A'}\n"
                f"📢 Канал: {TARGET_CHANNEL}\n"
                f"💬 Повідомлення: {len(self.recent_messages)}\n"
                f"🕓 Останнє: {time_since_last/60:.1f} хв назад\n"
                f"🔗 MTProto: {'✅' if self.client and self.client.is_connected() else '❌'}\n"
                f"🤖 Bot API: {'✅' if self.bot else '❌'}\n"
                f"🌐 Web: {'✅' if self.web_app else '❌'}"
            )
            await update.message.reply_text(text)
        except Exception as e:
            logger.error(f"❌ Status command error: {e}")
            
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
    bot = StableRenderBot()
    await bot.start()

if __name__ == "__main__":
    asyncio.run(main())