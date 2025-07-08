"""
Core Telegram Bot Service for 24/7 operation
Handles message monitoring, forwarding, and admin workflows
"""

import asyncio
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import re
from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, MessageHandler, CallbackQueryHandler, CommandHandler, filters, ContextTypes
from telegram.error import TelegramError, NetworkError, TimedOut, RetryAfter

from database import DatabaseManager
from message_analyzer import MessageAnalyzer
from config import Config
from logger import setup_logger

class TelegramBotService:
    def __init__(self, config: Config):
        self.config = config
        self.logger = setup_logger()
        self.db = DatabaseManager()
        self.analyzer = MessageAnalyzer()
        self.application: Optional[Application] = None
        self.bot: Optional[Bot] = None
        self.running = False
        self.last_health_check = time.time()
        self.error_count = 0
        self.max_errors = 10
        
    async def start(self):
        """Start the bot service with continuous monitoring"""
        try:
            # Initialize bot application
            self.application = Application.builder().token(self.config.bot_token).build()
            self.bot = self.application.bot
            
            # Register handlers
            self.register_handlers()
            
            # Start the application
            await self.application.initialize()
            await self.application.start()
            
            # Start polling with error handling
            await self.start_polling()
            
            self.running = True
            self.logger.info("Bot service started and polling...")
            
        except Exception as e:
            self.logger.error(f"Failed to start bot service: {e}")
            raise
            
    async def start_polling(self):
        """Start continuous polling with error recovery"""
        while True:
            try:
                await self.application.updater.start_polling(
                    drop_pending_updates=True,
                    allowed_updates=["message", "callback_query"]
                )
                break
            except (NetworkError, TimedOut) as e:
                self.logger.warning(f"Network error during polling start: {e}")
                await asyncio.sleep(5)
                continue
            except RetryAfter as e:
                self.logger.warning(f"Rate limited, waiting {e.retry_after} seconds")
                await asyncio.sleep(e.retry_after)
                continue
            except Exception as e:
                self.logger.error(f"Unexpected error during polling start: {e}")
                await asyncio.sleep(10)
                continue
                
    def register_handlers(self):
        """Register all bot handlers"""
        # Message handler for source group or forwarded messages
        source_chat_id = self.config.source_group_id
        admin_ids = self.config.admin_user_ids
        
        if source_chat_id and source_chat_id != 0:
            # Direct monitoring of source group (if bot is member)
            message_handler = MessageHandler(
                filters.Chat(chat_id=source_chat_id) & filters.TEXT,
                self.handle_source_message
            )
            self.application.add_handler(message_handler)
        
        # Handle forwarded messages from admins
        if admin_ids:
            forwarded_handler = MessageHandler(
                filters.User(user_id=admin_ids) & filters.FORWARDED & filters.TEXT,
                self.handle_forwarded_message
            )
            self.application.add_handler(forwarded_handler)
        
        # Handle direct messages from admins with specific commands
        direct_handler = MessageHandler(
            filters.User(user_id=admin_ids) & filters.TEXT & ~filters.COMMAND & ~filters.FORWARDED,
            self.handle_direct_message
        )
        self.application.add_handler(direct_handler)
        
        # Callback query handler for admin buttons
        callback_handler = CallbackQueryHandler(self.handle_admin_callback)
        self.application.add_handler(callback_handler)
        
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.handle_start))
        self.application.add_handler(CommandHandler("status", self.handle_status))
        self.application.add_handler(CommandHandler("health", self.handle_health))
        
        # Error handler
        self.application.add_error_handler(self.handle_error)
        
    async def handle_source_message(self, update: Update, context):
        """Handle messages from source group"""
        try:
            message = update.message
            if not message or not message.text:
                return
                
            self.logger.info(f"Received message from source group: {message.message_id}")
            
            # Analyze message for status
            analysis = await self.analyzer.analyze_message(message.text)
            
            # Store message in database
            message_data = {
                'message_id': message.message_id,
                'chat_id': message.chat_id,
                'user_id': message.from_user.id,
                'username': message.from_user.username or '',
                'text': message.text,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'analysis': analysis,
                'status': 'pending'
            }
            
            await self.db.store_message(message_data)
            
            # Forward to admin group with buttons
            await self.forward_to_admin(message, analysis)
            
        except Exception as e:
            self.logger.error(f"Error handling source message: {e}")
            await self.handle_error(None, context, e)
    
    async def handle_forwarded_message(self, update: Update, context):
        """Handle forwarded messages from admins"""
        try:
            message = update.message
            if not message or not message.text:
                return
                
            self.logger.info(f"Received forwarded message from admin: {message.from_user.id}")
            
            # Check if message was forwarded from the source group
            if message.forward_from_chat:
                forward_from = message.forward_from_chat.username or str(message.forward_from_chat.id)
                source_group = str(self.config.source_group_id).replace('@', '')
                
                if source_group in forward_from or 'pereizdvyshneve' in forward_from:
                    # This is a forwarded message from our source group
                    await self.process_relocation_message(message)
                    return
            
            # Reply with instructions
            await message.reply_text(
                "📝 **Як пересилати повідомлення:**\n\n"
                "1. Перешліть повідомлення з групи переїзду сюди\n"
                "2. Або напишіть текст про статус переїзду\n"
                "3. Бот автоматично проаналізує та надішле в адмін групу\n\n"
                "Підтримувані слова: відкрито, закрито, працює, не працює",
                parse_mode='Markdown'
            )
            
        except Exception as e:
            self.logger.error(f"Error handling forwarded message: {e}")
            
    async def handle_direct_message(self, update: Update, context):
        """Handle direct messages from admins"""
        try:
            message = update.message
            if not message or not message.text:
                return
                
            self.logger.info(f"Received direct message from admin: {message.from_user.id}")
            
            # Process as potential relocation status update
            await self.process_relocation_message(message)
            
        except Exception as e:
            self.logger.error(f"Error handling direct message: {e}")
            
    async def process_relocation_message(self, message):
        """Process message as potential relocation status update"""
        try:
            # Analyze message for status
            analysis = await self.analyzer.analyze_message(message.text)
            
            # Store message in database
            message_data = {
                'message_id': message.message_id,
                'chat_id': message.chat_id,
                'user_id': message.from_user.id,
                'username': message.from_user.username or '',
                'text': message.text,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'analysis': analysis,
                'status': 'pending',
                'source': 'forwarded' if message.forward_from_chat else 'direct'
            }
            
            await self.db.store_message(message_data)
            
            # Forward to admin group with buttons
            await self.forward_to_admin(message, analysis)
            
            # Confirm receipt to the admin who sent it
            await message.reply_text(
                f"✅ **Повідомлення отримано і проаналізовано**\n\n"
                f"🤖 Аналіз: {analysis['suggested_status'].upper()}\n"
                f"📊 Впевненість: {analysis['confidence']:.1%}\n\n"
                f"Відправлено в адмін групу для затвердження.",
                parse_mode='Markdown'
            )
            
        except Exception as e:
            self.logger.error(f"Error processing relocation message: {e}")
            await message.reply_text(f"❌ Помилка обробки повідомлення: {e}")
            
    async def forward_to_admin(self, message, analysis: Dict[str, Any]):
        """Forward message to admin group with inline buttons"""
        try:
            # Prepare message text
            original_text = message.text
            user_info = f"From: @{message.from_user.username or 'Unknown'}"
            timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            
            # AI analysis info
            suggested_status = analysis.get('suggested_status', 'unknown')
            confidence = analysis.get('confidence', 0)
            
            admin_text = f"""
📍 **New Relocation Status Message**

{original_text}

👤 {user_info}
🕐 {timestamp}

🤖 **AI Analysis:**
Suggested Status: {suggested_status.upper()}
Confidence: {confidence:.2%}

Please review and approve:
"""
            
            # Create inline keyboard
            keyboard = [
                [
                    InlineKeyboardButton("✅ OPEN", callback_data=f"approve_open_{message.message_id}"),
                    InlineKeyboardButton("❌ CLOSED", callback_data=f"approve_closed_{message.message_id}")
                ],
                [
                    InlineKeyboardButton("⏰ Add Timestamp", callback_data=f"timestamp_{message.message_id}"),
                    InlineKeyboardButton("🚫 Reject", callback_data=f"reject_{message.message_id}")
                ]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Send to admin group
            await self.bot.send_message(
                chat_id=self.config.admin_group_id,
                text=admin_text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
            # Send notification to admin
            await self.notify_admin(f"New message requiring review: {suggested_status.upper()}")
            
        except Exception as e:
            self.logger.error(f"Error forwarding to admin: {e}")
            raise
            
    async def handle_admin_callback(self, update: Update, context):
        """Handle admin button callbacks"""
        try:
            query = update.callback_query
            await query.answer()
            
            callback_data = query.data
            self.logger.info(f"Admin callback: {callback_data}")
            
            # Parse callback data
            action, message_id = callback_data.rsplit('_', 1)
            message_id = int(message_id)
            
            # Get message from database
            message_data = await self.db.get_message(message_id)
            if not message_data:
                await query.edit_message_text("❌ Message not found in database")
                return
                
            if action.startswith('approve_'):
                status = action.replace('approve_', '')
                await self.approve_message(query, message_data, status)
                
            elif action == 'timestamp':
                await self.add_timestamp(query, message_data)
                
            elif action == 'reject':
                await self.reject_message(query, message_data)
                
        except Exception as e:
            self.logger.error(f"Error handling admin callback: {e}")
            await query.edit_message_text(f"❌ Error processing request: {e}")
            
    async def approve_message(self, query, message_data: Dict, status: str):
        """Approve and forward message to target channel"""
        try:
            # Update message status in database
            await self.db.update_message_status(message_data['message_id'], 'approved', status)
            
            # Prepare message for target channel
            timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            status_emoji = "✅" if status == "open" else "❌"
            
            channel_text = f"""
{status_emoji} **STATUS: {status.upper()}**

{message_data['text']}

🕐 Approved: {timestamp}
👤 From: @{message_data['username']}
"""
            
            # Send to target channel
            await self.bot.send_message(
                chat_id=self.config.target_channel_id,
                text=channel_text,
                parse_mode='Markdown'
            )
            
            # Update admin message
            await query.edit_message_text(
                f"✅ **APPROVED: {status.upper()}**\n\n"
                f"Message forwarded to channel at {timestamp}"
            )
            
            # Send notifications
            await self.notify_users(f"Status update: {status.upper()}")
            await self.notify_admin(f"Message approved and forwarded: {status.upper()}")
            
            self.logger.info(f"Message {message_data['message_id']} approved as {status}")
            
        except Exception as e:
            self.logger.error(f"Error approving message: {e}")
            await query.edit_message_text(f"❌ Error approving message: {e}")
            
    async def add_timestamp(self, query, message_data: Dict):
        """Add timestamp to message"""
        try:
            timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            
            # Update keyboard with timestamp
            keyboard = [
                [
                    InlineKeyboardButton("✅ OPEN", callback_data=f"approve_open_{message_data['message_id']}"),
                    InlineKeyboardButton("❌ CLOSED", callback_data=f"approve_closed_{message_data['message_id']}")
                ],
                [
                    InlineKeyboardButton("🚫 Reject", callback_data=f"reject_{message_data['message_id']}")
                ]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            updated_text = query.message.text + f"\n\n⏰ **Timestamp Added:** {timestamp}"
            
            await query.edit_message_text(
                text=updated_text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            self.logger.error(f"Error adding timestamp: {e}")
            await query.edit_message_text(f"❌ Error adding timestamp: {e}")
            
    async def reject_message(self, query, message_data: Dict):
        """Reject message"""
        try:
            # Update message status in database
            await self.db.update_message_status(message_data['message_id'], 'rejected')
            
            # Update admin message
            await query.edit_message_text(
                f"🚫 **REJECTED**\n\n"
                f"Message from @{message_data['username']} rejected at "
                f"{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}"
            )
            
            self.logger.info(f"Message {message_data['message_id']} rejected")
            
        except Exception as e:
            self.logger.error(f"Error rejecting message: {e}")
            await query.edit_message_text(f"❌ Error rejecting message: {e}")
            
    async def notify_admin(self, message: str):
        """Send notification to admin(s)"""
        admin_ids = self.config.admin_user_ids
        for admin_id in admin_ids:
            try:
                await self.bot.send_message(
                    chat_id=admin_id,
                    text=f"🔔 **Admin Notification**\n\n{message}",
                    parse_mode='Markdown'
                )
            except Exception as e:
                self.logger.error(f"Error sending admin notification to {admin_id}: {e}")
            
    async def notify_users(self, message: str):
        """Send notification to users"""
        try:
            # Send to admin group
            await self.bot.send_message(
                chat_id=self.config.admin_group_id,
                text=f"📢 **Status Update**\n\n{message}",
                parse_mode='Markdown'
            )
        except Exception as e:
            self.logger.error(f"Error sending user notification: {e}")
            
    async def handle_start(self, update: Update, context):
        """Handle /start command"""
        user_id = update.message.from_user.id
        admin_ids = self.config.admin_user_ids
        
        if user_id in admin_ids:
            await update.message.reply_text(
                "🤖 **24/7 Relocation Status Bot**\n\n"
                "✅ Ви адміністратор цього бота!\n\n"
                "📝 **Як користуватися:**\n"
                "• Перешліть повідомлення з групи переїзду сюди\n"
                "• Або напишіть текст про статус переїзду\n"
                "• Бот проаналізує та надішле в адмін групу\n"
                "• Затвердіть статус кнопками ✅ ВІДКРИТО / ❌ ЗАКРИТО\n\n"
                "🔄 Бот працює 24/7 та готовий обробляти повідомлення!",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                "🤖 **24/7 Relocation Status Bot**\n\n"
                "Цей бот моніторить статуси переїзду.\n"
                "Працює безперервно для адміністраторів.",
                parse_mode='Markdown'
            )
        
    async def handle_status(self, update: Update, context):
        """Handle /status command"""
        uptime = time.time() - self.last_health_check
        message_count = await self.db.get_message_count()
        
        status_text = f"""
🤖 **Bot Status**

🟢 Status: Running
⏰ Uptime: {uptime:.0f} seconds
📊 Messages processed: {message_count}
🚨 Error count: {self.error_count}

Last health check: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}
"""
        
        await update.message.reply_text(status_text, parse_mode='Markdown')
        
    async def handle_health(self, update: Update, context):
        """Handle /health command"""
        self.last_health_check = time.time()
        await update.message.reply_text("✅ Bot is healthy and running")
        
    async def handle_error(self, update: Update, context, error: Exception = None):
        """Handle errors with recovery"""
        if error is None:
            error = context.error
            
        self.error_count += 1
        self.logger.error(f"Bot error #{self.error_count}: {error}")
        
        if self.error_count >= self.max_errors:
            self.logger.critical("Too many errors, requiring restart")
            await self.stop()
            raise Exception("Too many errors, bot restart required")
            
        # Handle specific error types
        if isinstance(error, (NetworkError, TimedOut)):
            self.logger.warning("Network error, will retry automatically")
            await asyncio.sleep(5)
            
        elif isinstance(error, RetryAfter):
            self.logger.warning(f"Rate limited, waiting {error.retry_after} seconds")
            await asyncio.sleep(error.retry_after)
            
        else:
            self.logger.error(f"Unexpected error: {error}")
            await asyncio.sleep(10)
            
    async def stop(self):
        """Stop the bot service"""
        self.logger.info("Stopping bot service...")
        self.running = False
        
        if self.application:
            await self.application.stop()
            await self.application.shutdown()
            
        self.logger.info("Bot service stopped")
