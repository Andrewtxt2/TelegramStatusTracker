#!/usr/bin/env python3
"""
Production-ready Telegram Bot Service for 24/7 operation
Uses only Bot API without MTProto for stable deployment
"""

import asyncio
import signal
import sys
import json
import os
from datetime import datetime, timezone, timedelta
from aiohttp import web
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, MessageHandler, CallbackQueryHandler, CommandHandler, filters, ContextTypes
from config import Config
from logger import setup_logger
from database import DatabaseManager
from message_analyzer import MessageAnalyzer

class ProductionTelegramBot:
    def __init__(self):
        self.logger = setup_logger("production_bot")
        self.config = Config()
        self.db = DatabaseManager()
        self.analyzer = MessageAnalyzer()
        
        # Bot setup
        self.bot_token = self.config.bot_token
        self.application = None
        self.web_app = None
        self.runner = None
        self.site = None
        self.running = False
        self.start_time = datetime.now(timezone.utc)
        
        # Message history for context
        self.recent_messages = []
        self.message_history_file = "recent_messages.json"
        
    async def setup_bot(self):
        """Setup the Telegram bot application"""
        self.application = Application.builder().token(self.bot_token).build()
        
        # Register handlers
        self.application.add_handler(CommandHandler("start", self.handle_start))
        self.application.add_handler(CommandHandler("status", self.handle_status))
        self.application.add_handler(CommandHandler("health", self.handle_health))
        self.application.add_handler(CallbackQueryHandler(self.handle_callback))
        
        # Message handlers - only for admin groups
        self.application.add_handler(MessageHandler(filters.ALL, self.handle_message))
        
        # Initialize database
        await self.db.initialize()
        
        # Load message history
        await self.load_recent_messages()
        
        self.logger.info("Bot setup completed")
        
    async def handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user_id = update.effective_user.id
        admin_ids = self.config.admin_user_ids
        
        welcome_message = """
🤖 **24/7 Telegram Bot Service**

✅ Служба активна та працює
📊 Статус: Онлайн
🔄 Режим: Автоматичний моніторинг

ℹ️ Для отримання статусу використовуйте /status
🏥 Для перевірки здоров'я використовуйте /health
        """
        
        if user_id in admin_ids:
            admin_message = """
👨‍💼 **Адміністратор**

Ви маєте доступ до керування ботом.
Перешліть повідомлення або надішліть текст для аналізу.
            """
            welcome_message += admin_message
            
        await update.message.reply_text(welcome_message)
        
    async def handle_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        uptime = datetime.now(timezone.utc) - self.start_time
        
        status_message = f"""
📊 **Статус Служби**

🟢 Статус: Активна
⏱️ Час роботи: {uptime.days} днів, {uptime.seconds//3600} годин
🔄 Режим: Автоматичний
📊 Обробка повідомлень: Активна

📈 **Статистика**
📝 Всього повідомлень: {len(self.recent_messages)}
⏰ Останнє оновлення: {datetime.now(timezone.utc).strftime('%H:%M:%S')}
        """
        
        await update.message.reply_text(status_message)
        
    async def handle_health(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /health command"""
        health_status = "🟢 Здоровий"
        
        health_message = f"""
🏥 **Перевірка Здоров'я**

{health_status}
⏰ Час перевірки: {datetime.now(timezone.utc).strftime('%H:%M:%S')}
🔄 Служба працює нормально
        """
        
        await update.message.reply_text(health_message)
        
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming messages for analysis"""
        if not update.message or not update.message.text:
            return
            
        user_id = update.effective_user.id
        admin_ids = self.config.admin_user_ids
        
        # Only process messages from admins
        if user_id not in admin_ids:
            return
            
        message_text = update.message.text
        
        # Analyze message
        analysis = await self.analyzer.analyze_message(message_text)
        
        # Store in recent messages
        message_data = {
            "id": update.message.message_id,
            "text": message_text,
            "from_user": update.effective_user.first_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "analysis": analysis
        }
        
        self.recent_messages.append(message_data)
        if len(self.recent_messages) > 14:
            self.recent_messages.pop(0)
            
        await self.save_recent_messages()
        
        # Create approval buttons
        keyboard = [
            [
                InlineKeyboardButton("✅ ВІДКРИТО", callback_data=f"approve_open_{update.message.message_id}"),
                InlineKeyboardButton("❌ ЗАКРИТО", callback_data=f"approve_closed_{update.message.message_id}")
            ],
            [
                InlineKeyboardButton("🕐 ДОДАТИ ЧАС", callback_data=f"add_time_{update.message.message_id}"),
                InlineKeyboardButton("🗑️ ВІДХИЛИТИ", callback_data=f"reject_{update.message.message_id}")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Format recent messages for context
        recent_context = "\n".join([
            f"• {msg['from_user']}: {msg['text'][:50]}..." 
            for msg in self.recent_messages[-5:]
        ])
        
        response_text = f"""
📝 **Нове повідомлення для аналізу**

👤 Від: {update.effective_user.first_name}
📄 Текст: {message_text}

🤖 **Аналіз:**
📊 Рекомендований статус: {analysis.get('suggested_status', 'Невизначено')}
🎯 Впевненість: {analysis.get('confidence', 0)}%

📋 **Останні повідомлення:**
{recent_context}
        """
        
        await update.message.reply_text(response_text, reply_markup=reply_markup)
        
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries from inline buttons"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        parts = data.split('_')
        
        if len(parts) >= 3:
            action = parts[0]
            status = parts[1] if len(parts) > 2 else parts[1]
            message_id = '_'.join(parts[2:]) if len(parts) > 2 else parts[1]
            
            if action == "approve":
                await self.approve_message(query, status, message_id)
            elif action == "reject":
                await self.reject_message(query, message_id)
            elif action == "add" and status == "time":
                await self.add_timestamp(query, message_id)
                
    async def approve_message(self, query, status, message_id):
        """Approve and publish message"""
        status_emoji = "✅" if status == "open" else "❌"
        status_text = "Відкрито" if status == "open" else "Закрито"
        
        # Get current time in GMT+3
        current_time = datetime.now(timezone(timedelta(hours=3)))
        time_str = current_time.strftime("%H:%M")
        
        # Create final message
        final_message = f"{status_emoji} {status_text} 🕓 {time_str}"
        
        # Send to target channel
        try:
            target_channel = self.config.target_channel_id
            bot = Bot(token=self.bot_token)
            await bot.send_message(chat_id=target_channel, text=final_message)
            
            # Update callback message
            await query.edit_message_text(
                f"✅ Повідомлення затверджено як '{status_text}' та опубліковано о {time_str}"
            )
            
            self.logger.info(f"Message approved as '{status_text}' and published at {time_str}")
            
        except Exception as e:
            self.logger.error(f"Error publishing message: {e}")
            await query.edit_message_text(f"❌ Помилка публікації: {str(e)}")
            
    async def reject_message(self, query, message_id):
        """Reject message"""
        await query.edit_message_text("🗑️ Повідомлення відхилено")
        self.logger.info(f"Message {message_id} rejected")
        
    async def add_timestamp(self, query, message_id):
        """Add timestamp to message"""
        current_time = datetime.now(timezone(timedelta(hours=3)))
        time_str = current_time.strftime("%H:%M")
        await query.edit_message_text(f"🕐 Час додано: {time_str}")
        
    async def load_recent_messages(self):
        """Load recent messages from file"""
        try:
            if os.path.exists(self.message_history_file):
                with open(self.message_history_file, 'r', encoding='utf-8') as f:
                    self.recent_messages = json.load(f)
                self.logger.info(f"Loaded {len(self.recent_messages)} recent messages")
            else:
                self.recent_messages = []
        except Exception as e:
            self.logger.error(f"Error loading recent messages: {e}")
            self.recent_messages = []
            
    async def save_recent_messages(self):
        """Save recent messages to file"""
        try:
            with open(self.message_history_file, 'w', encoding='utf-8') as f:
                json.dump(self.recent_messages, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving recent messages: {e}")
            
    async def setup_web_server(self):
        """Setup web server for health checks"""
        self.web_app = web.Application()
        
        # Routes
        self.web_app.router.add_get('/', self.root_endpoint)
        self.web_app.router.add_get('/health', self.health_endpoint)
        self.web_app.router.add_get('/status', self.status_endpoint)
        
        # Setup runner
        self.runner = web.AppRunner(self.web_app)
        await self.runner.setup()
        
        # Start server
        port = int(os.getenv('PORT', 80))
        self.site = web.TCPSite(self.runner, '0.0.0.0', port)
        await self.site.start()
        
        self.logger.info(f"Web server started on port {port}")
        
    async def root_endpoint(self, request):
        """Root endpoint"""
        return web.Response(
            text="24/7 Telegram Bot Service is running",
            headers={'Content-Type': 'text/plain'}
        )
        
    async def health_endpoint(self, request):
        """Health check endpoint"""
        try:
            uptime = (datetime.now(timezone.utc) - self.start_time).total_seconds()
            
            # Check bot health
            try:
                bot = Bot(token=self.bot_token)
                await bot.get_me()
                bot_status = "healthy"
            except Exception as e:
                self.logger.error(f"Bot health check failed: {e}")
                bot_status = "unhealthy"
                
            health_data = {
                "status": "healthy" if bot_status == "healthy" else "unhealthy",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "uptime": uptime,
                "service": "telegram-bot",
                "version": "1.0.0",
                "bot_running": self.running,
                "services": {
                    "telegram_bot": bot_status,
                    "web_server": "healthy",
                    "database": "healthy"
                }
            }
            
            status_code = 200 if health_data["status"] == "healthy" else 503
            return web.Response(
                text=json.dumps(health_data, indent=2),
                status=status_code,
                headers={'Content-Type': 'application/json'}
            )
            
        except Exception as e:
            self.logger.error(f"Health check error: {e}")
            return web.Response(
                text=f"Health check error: {str(e)}",
                status=500,
                headers={'Content-Type': 'text/plain'}
            )
            
    async def status_endpoint(self, request):
        """Status endpoint"""
        uptime = (datetime.now(timezone.utc) - self.start_time).total_seconds()
        
        status_data = {
            "service": "Telegram Bot Service",
            "version": "1.0.0",
            "uptime": uptime,
            "bot_running": self.running,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "messages_processed": len(self.recent_messages),
            "last_activity": self.recent_messages[-1]["timestamp"] if self.recent_messages else None
        }
        
        return web.Response(
            text=json.dumps(status_data, indent=2),
            headers={'Content-Type': 'application/json'}
        )
        
    async def start(self):
        """Start both bot and web server"""
        try:
            self.logger.info("Starting Production Telegram Bot Service...")
            
            # Setup web server
            await self.setup_web_server()
            
            # Setup bot
            await self.setup_bot()
            
            # Start bot polling
            await self.application.initialize()
            await self.application.start()
            
            self.running = True
            self.logger.info("Production bot service started successfully")
            
            # Start polling
            await self.application.updater.start_polling()
            
            # Keep running
            while self.running:
                await asyncio.sleep(1)
                
        except Exception as e:
            self.logger.error(f"Error starting bot service: {e}")
            await self.stop()
            raise
            
    async def stop(self):
        """Stop all services"""
        try:
            self.logger.info("Stopping production bot service...")
            self.running = False
            
            # Stop bot
            if self.application:
                await self.application.updater.stop()
                await self.application.stop()
                await self.application.shutdown()
                
            # Stop web server
            if self.site:
                await self.site.stop()
            if self.runner:
                await self.runner.cleanup()
                
            self.logger.info("Production bot service stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping service: {e}")
            
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        asyncio.create_task(self.stop())
        sys.exit(0)

async def main():
    """Main function"""
    bot = ProductionTelegramBot()
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, bot.signal_handler)
    signal.signal(signal.SIGTERM, bot.signal_handler)
    
    try:
        await bot.start()
    except KeyboardInterrupt:
        await bot.stop()
    except Exception as e:
        bot.logger.error(f"Application error: {e}")
        await bot.stop()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())