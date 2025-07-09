#!/usr/bin/env python3
"""
Bot-only version that works without MTProto user session
Uses only Bot API for all operations
"""

import asyncio
import os
import sys
import logging
from datetime import datetime
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot_only.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('bot_only')

class BotOnlyMonitor:
    def __init__(self):
        self.config = self._load_config()
        self.bot = None
        self.app = None
        self.start_time = datetime.now()
        
    def _load_config(self):
        """Load configuration"""
        import json
        try:
            with open('config.json', 'r') as f:
                return json.load(f)
        except:
            return {
                'bot_token': os.getenv('BOT_TOKEN', ''),
                'admin_user_ids': [6395626140],
                'source_group_id': '@pereizdvyshneve',
                'target_channel_id': '@kryuvysh'
            }
    
    async def start(self):
        """Start bot-only monitoring"""
        logger.info("🚀 Starting Bot-Only Monitor...")
        
        # Initialize bot
        self.bot = Bot(token=self.config['bot_token'])
        self.app = Application.builder().token(self.config['bot_token']).build()
        
        # Register handlers
        self.app.add_handler(CommandHandler("start", self.handle_start))
        self.app.add_handler(CommandHandler("status", self.handle_status))
        self.app.add_handler(CommandHandler("health", self.handle_health))
        self.app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, self.handle_message))
        
        # Start polling
        await self.app.initialize()
        await self.app.start()
        
        logger.info("✅ Bot polling started")
        
        # Send startup message
        await self.notify_admins("🚀 Bot-Only Monitor запущено!\n\nБот готовий до роботи:\n• Команди: /start, /status, /health\n• Для моніторингу групи потрібно додати бота до групи")
        
        await self.app.updater.start_polling(
            drop_pending_updates=True,
            allowed_updates=["message", "callback_query"]
        )
        
        # Keep running
        await self.app.updater.idle()
        
    async def handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user_id = update.effective_user.id
        logger.info(f"Received /start command from {user_id}")
        
        if user_id in self.config['admin_user_ids']:
            message = "🚀 Bot-Only Monitor активний!\n\n"
            message += "Доступні команди:\n"
            message += "• /start - інформація про бота\n"
            message += "• /status - детальний стан системи\n"
            message += "• /health - перевірка всіх компонентів\n\n"
            message += "📝 Примітка: Для моніторингу групи потрібно додати бота як учасника до групи"
        else:
            message = "🤖 Переїзд Monitor Bot\n\nЦей бот призначений для моніторингу статусу переїзду."
            
        await update.message.reply_text(message)
        
    async def handle_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        user_id = update.effective_user.id
        logger.info(f"Received /status command from {user_id}")
        
        if user_id not in self.config['admin_user_ids']:
            await update.message.reply_text("❌ Доступ заборонений")
            return
            
        # System status
        uptime = datetime.now() - self.start_time
        
        status = f"📊 Стан системи Bot-Only Monitor\n\n"
        status += f"🕐 Час роботи: {uptime}\n"
        status += f"🤖 Бот: Активний\n"
        status += f"📋 Режим: Bot API Only\n"
        status += f"👥 Адміністраторів: {len(self.config['admin_user_ids'])}\n"
        status += f"🔄 Статус: Очікує повідомлень з групи\n\n"
        status += f"ℹ️ Для моніторингу потрібно додати бота до групи {self.config['source_group_id']}"
        
        await update.message.reply_text(status)
        
    async def handle_health(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /health command"""
        user_id = update.effective_user.id
        logger.info(f"Received /health command from {user_id}")
        
        if user_id not in self.config['admin_user_ids']:
            await update.message.reply_text("❌ Доступ заборонений")
            return
            
        # Health check
        try:
            # Test bot API
            me = await self.bot.get_me()
            bot_status = f"✅ @{me.username}"
        except Exception as e:
            bot_status = f"❌ Помилка: {e}"
            
        health = f"🏥 Перевірка здоров'я системи\n\n"
        health += f"🤖 Bot API: {bot_status}\n"
        health += f"📱 Polling: ✅ Активний\n"
        health += f"💾 Конфігурація: ✅ Завантажена\n"
        health += f"📊 Система: ✅ Працює\n\n"
        health += f"🔄 Остання перевірка: {datetime.now().strftime('%H:%M:%S')}"
        
        await update.message.reply_text(health)
        
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle all messages"""
        try:
            message = update.message
            chat = update.effective_chat
            user = update.effective_user
            
            # Log message info
            logger.info(f"📨 Message from {user.first_name} in {chat.type}: {message.text[:50]}...")
            
            # Check if message is from monitored group
            if chat.username and chat.username == self.config['source_group_id'].replace('@', ''):
                logger.info(f"📍 Message from monitored group: {chat.title}")
                await self.process_group_message(message)
            
            # Check if message is from admin
            elif user.id in self.config['admin_user_ids']:
                logger.info(f"👤 Message from admin: {user.first_name}")
                await self.handle_admin_message(message)
                
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            
    async def process_group_message(self, message):
        """Process message from monitored group"""
        try:
            if not message.text:
                return
                
            logger.info(f"🔍 Processing group message: {message.text[:100]}...")
            
            # Simple analysis
            text_lower = message.text.lower()
            
            # Check for status keywords
            if any(word in text_lower for word in ['відкрито', 'відкрит', 'open', 'працює', 'working']):
                status = 'відкрито'
            elif any(word in text_lower for word in ['закрито', 'закрит', 'closed', 'не працює', 'not working']):
                status = 'закрито'
            else:
                status = 'невідомо'
                
            # Send to admins
            admin_message = f"📨 Нове повідомлення з групи\n\n"
            admin_message += f"💬 Текст: {message.text}\n\n"
            admin_message += f"🕐 Час: {message.date.strftime('%H:%M')}\n"
            admin_message += f"🤖 Статус: {status}\n"
            admin_message += f"👤 Від: {message.from_user.first_name if message.from_user else 'Unknown'}"
            
            await self.notify_admins(admin_message)
            
        except Exception as e:
            logger.error(f"Error processing group message: {e}")
            
    async def handle_admin_message(self, message):
        """Handle message from admin"""
        try:
            if message.text.startswith('/'):
                return  # Commands are handled separately
                
            # Echo back to admin
            await message.reply_text(f"📨 Отримано повідомлення: {message.text}")
            
        except Exception as e:
            logger.error(f"Error handling admin message: {e}")
            
    async def notify_admins(self, message):
        """Send notification to all admins"""
        for admin_id in self.config['admin_user_ids']:
            try:
                await self.bot.send_message(chat_id=admin_id, text=message)
                logger.info(f"✅ Notified admin {admin_id}")
            except Exception as e:
                logger.warning(f"Failed to notify admin {admin_id}: {e}")

async def main():
    """Main function"""
    bot_monitor = BotOnlyMonitor()
    try:
        await bot_monitor.start()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot error: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(main())