#!/usr/bin/env python3
"""
Standalone Telegram Bot that runs independently
"""

import asyncio
import signal
import sys
import os
import logging
from datetime import datetime
import json
import traceback

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config
from message_analyzer import MessageAnalyzer
from telethon import TelegramClient
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

class StandaloneBot:
    def __init__(self):
        self.config = Config()
        self.analyzer = MessageAnalyzer()
        self.client = None
        self.bot_app = None
        self.running = True
        self.target_entity = None
        self.start_time = datetime.now()
        self.processed_messages = 0
        self.last_message_time = None
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('standalone_bot.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger('standalone_bot')
        
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
        
    async def start(self):
        """Start the standalone bot"""
        # Setup signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        self.logger.info("🚀 Starting Standalone Bot...")
        
        try:
            # Initialize MTProto client
            api_id = int(os.getenv('TELEGRAM_API_ID', '0'))
            api_hash = os.getenv('TELEGRAM_API_HASH', '')
            
            self.client = TelegramClient('session', api_id, api_hash)
            await self.client.start()
            
            me = await self.client.get_me()
            self.logger.info(f"✅ MTProto connected: {me.first_name}")
            
            # Get target group
            group_link = self.config.source_group_id
            if group_link.startswith('https://t.me/'):
                group_username = group_link.split('/')[-1]
                self.target_entity = await self.client.get_entity(group_username)
            elif group_link.startswith('@'):
                self.target_entity = await self.client.get_entity(group_link)
            else:
                try:
                    self.target_entity = await self.client.get_entity(int(group_link))
                except ValueError:
                    self.target_entity = await self.client.get_entity(group_link)
            
            self.logger.info(f"✅ Group found: {self.target_entity.title}")
            
            # Initialize Bot API
            self.bot_app = Application.builder().token(self.config.bot_token).build()
            
            # Register command handlers
            self.bot_app.add_handler(CommandHandler("status", self.handle_status))
            self.bot_app.add_handler(CommandHandler("health", self.handle_health))
            self.bot_app.add_handler(CommandHandler("start", self.handle_start))
            self.bot_app.add_handler(CallbackQueryHandler(self.handle_callback))
            
            # Start bot polling in background
            asyncio.create_task(self.start_bot_polling())
            
            # Start monitoring
            await self.start_monitoring()
            
        except Exception as e:
            self.logger.error(f"Startup error: {e}")
            self.logger.error(traceback.format_exc())
            raise
            
    async def start_monitoring(self):
        """Start message monitoring"""
        last_message_id = None
        
        # Get latest message ID
        try:
            async for message in self.client.iter_messages(self.target_entity, limit=1):
                last_message_id = message.id
                break
        except Exception as e:
            self.logger.error(f"Failed to get initial message ID: {e}")
            return
            
        self.logger.info(f"🔄 Starting monitoring from message ID: {last_message_id}")
        
        # Monitoring loop
        while self.running:
            try:
                # Check connection
                if not self.client.is_connected():
                    self.logger.warning("🔄 Reconnecting...")
                    await self.client.connect()
                
                # Check for new messages
                new_messages = []
                async for message in self.client.iter_messages(self.target_entity, limit=10):
                    if message.id > last_message_id:
                        new_messages.append(message)
                    else:
                        break
                
                # Process new messages
                for message in reversed(new_messages):
                    await self.process_message(message)
                    last_message_id = message.id
                    self.processed_messages += 1
                    self.last_message_time = datetime.now()
                
                # Sleep between checks
                await asyncio.sleep(10)
                
            except Exception as e:
                self.logger.error(f"Monitoring error: {e}")
                await asyncio.sleep(30)
                
    async def process_message(self, message):
        """Process a new message"""
        self.logger.info(f"📨 New message ID {message.id}: {message.text[:50]}...")
        
        try:
            # Analyze message
            analysis = self.analyzer.analyze_message(message.text)
            self.logger.info(f"🤖 Analysis: {analysis['status']} ({analysis['confidence']}%)")
            
            # Send to admins
            await self.send_to_admins(message, analysis)
            
        except Exception as e:
            self.logger.error(f"Error processing message {message.id}: {e}")
            
    async def send_to_admins(self, message, analysis):
        """Send message to administrators"""
        try:
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            
            # Format message
            time_str = message.date.strftime("%H:%M")
            message_text = f"📨 Нове повідомлення о {time_str}\n\n"
            message_text += f"💬 Текст: {message.text}\n\n"
            message_text += f"🤖 Аналіз: {analysis['status']} ({analysis['confidence']}%)"
            
            # Create keyboard
            keyboard = [
                [
                    InlineKeyboardButton("✅ Відкрито", callback_data=f"approve_open_{message.id}"),
                    InlineKeyboardButton("🔴 Закрито", callback_data=f"approve_closed_{message.id}")
                ],
                [
                    InlineKeyboardButton("❌ Відхилити", callback_data=f"reject_{message.id}")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Send to each admin
            bot = Bot(token=self.config.bot_token)
            admin_ids = self.config.admin_user_ids
            
            for admin_id in admin_ids:
                try:
                    await bot.send_message(
                        chat_id=admin_id,
                        text=message_text,
                        reply_markup=reply_markup
                    )
                    self.logger.info(f"✅ Sent to admin {admin_id}")
                except Exception as e:
                    self.logger.warning(f"Failed to send to admin {admin_id}: {e}")
            
        except Exception as e:
            self.logger.error(f"Error sending to admins: {e}")
    
    async def start_bot_polling(self):
        """Start bot polling for commands"""
        try:
            await self.bot_app.initialize()
            await self.bot_app.start()
            await self.bot_app.updater.start_polling()
            self.logger.info("✅ Bot polling started for commands")
        except Exception as e:
            self.logger.error(f"Error starting bot polling: {e}")
    
    async def handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        await update.message.reply_text(
            "🤖 Standalone Bot активний!\n\n"
            "Доступні команди:\n"
            "/status - Стан системи\n"
            "/health - Перевірка здоров'я\n"
        )
    
    async def handle_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        try:
            uptime = datetime.now() - self.start_time
            uptime_str = str(uptime).split('.')[0]
            
            status_text = f"📊 Стан Standalone Bot:\n\n"
            status_text += f"🟢 Статус: Активний\n"
            status_text += f"⏱️ Час роботи: {uptime_str}\n"
            status_text += f"📨 Оброблено повідомлень: {self.processed_messages}\n"
            status_text += f"🔗 Підключено як: Ольга\n"
            status_text += f"👥 Група: {self.target_entity.title if self.target_entity else 'Не підключено'}\n"
            
            if self.last_message_time:
                last_msg_ago = datetime.now() - self.last_message_time
                status_text += f"📝 Останнє повідомлення: {str(last_msg_ago).split('.')[0]} тому\n"
            
            status_text += f"🔄 Моніторинг: {'Активний' if self.running else 'Зупинено'}\n"
            
            await update.message.reply_text(status_text)
            
        except Exception as e:
            self.logger.error(f"Error in status command: {e}")
            await update.message.reply_text("❌ Помилка при отриманні статусу")
    
    async def handle_health(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /health command"""
        try:
            health_checks = []
            
            # Check MTProto connection
            if self.client and self.client.is_connected():
                health_checks.append("✅ MTProto: Підключено")
            else:
                health_checks.append("❌ MTProto: Відключено")
            
            # Check group access
            if self.target_entity:
                health_checks.append(f"✅ Група: {self.target_entity.title}")
            else:
                health_checks.append("❌ Група: Не знайдено")
            
            # Check bot polling
            if self.bot_app and self.bot_app.updater.running:
                health_checks.append("✅ Bot API: Активний")
            else:
                health_checks.append("❌ Bot API: Неактивний")
            
            # Check monitoring
            if self.running:
                health_checks.append("✅ Моніторинг: Працює")
            else:
                health_checks.append("❌ Моніторинг: Зупинено")
            
            health_text = "🏥 Перевірка здоров'я:\n\n" + "\n".join(health_checks)
            await update.message.reply_text(health_text)
            
        except Exception as e:
            self.logger.error(f"Error in health command: {e}")
            await update.message.reply_text("❌ Помилка при перевірці здоров'я")
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries from inline keyboards"""
        query = update.callback_query
        await query.answer()
        
        try:
            data = query.data
            if data.startswith('approve_'):
                status = 'open' if 'open' in data else 'closed'
                message_id = data.split('_')[-1]
                
                # Update message with approval
                status_emoji = "✅" if status == 'open' else "🔴"
                status_text = "Відкрито" if status == 'open' else "Закрито"
                
                await query.edit_message_text(
                    f"{query.message.text}\n\n"
                    f"📝 Схвалено: {status_emoji} {status_text}"
                )
                
                # Here you would typically publish to channel
                self.logger.info(f"Message {message_id} approved as {status}")
                
            elif data.startswith('reject_'):
                message_id = data.split('_')[-1]
                await query.edit_message_text(
                    f"{query.message.text}\n\n"
                    f"❌ Відхилено адміністратором"
                )
                self.logger.info(f"Message {message_id} rejected")
                
        except Exception as e:
            self.logger.error(f"Error handling callback: {e}")
            
    async def stop(self):
        """Stop the bot"""
        self.logger.info("Stopping bot...")
        self.running = False
        
        if self.client:
            await self.client.disconnect()
            
        self.logger.info("Bot stopped")

async def main():
    """Main function"""
    bot = StandaloneBot()
    try:
        await bot.start()
    except KeyboardInterrupt:
        await bot.stop()
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())