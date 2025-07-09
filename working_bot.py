#!/usr/bin/env python3
"""
Working Telegram Bot - Simplified stable version
No session conflicts, no dual polling, just working system
"""

import asyncio
import logging
import os
import time
import traceback
from datetime import datetime
import pytz
from telethon import TelegramClient, events
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CallbackQueryHandler
# from message_analyzer import MessageAnalyzer  # Using built-in analysis

# Configuration
API_ID = os.getenv('TELEGRAM_API_ID', '26886585')
API_HASH = os.getenv('TELEGRAM_API_HASH', '166e3719a0d93c12bf76af43fe91425f')
BOT_TOKEN = '8189087426:AAF2XtTEwDRbwvWny-Hi2BPz_0ZeJHh9DEc'
ADMIN_IDS = [6395626140, 7766810783]
SOURCE_GROUP = 'https://t.me/pereizdvyshneve'
TARGET_CHANNEL = '@kryuvysh'

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('working_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('working_bot')

class WorkingBot:
    def __init__(self):
        self.client = None
        self.bot = None
        self.app = None
        self.target_entity = None
        # self.analyzer = MessageAnalyzer()  # Using built-in analysis
        self.message_store = {}
        self.running = True
        
    async def start(self):
        """Start the working bot system"""
        logger.info("🚀 Starting Working Bot System...")
        
        try:
            # Use existing session or create new one
            session_name = "working_session"
            
            # Initialize MTProto client
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
            
            # Start Bot API application in background
            asyncio.create_task(self.start_bot_api())
            
            # Notify admins
            await self.notify_admins(
                "🚀 Working Bot System ЗАПУЩЕНО!\n\n"
                "✅ Стабільна версія без конфліктів\n"
                "✅ Моніторинг групи активний\n"
                "✅ Кнопки працюють\n\n"
                f"📋 Група: {self.target_entity.title}\n"
                f"📢 Канал: {TARGET_CHANNEL}"
            )
            
            logger.info("🔄 Bot running...")
            
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
        
    async def start_bot_api(self):
        """Start Bot API application"""
        try:
            logger.info("🔄 Starting Bot API...")
            
            # Create application
            self.app = Application.builder().token(BOT_TOKEN).build()
            
            # Add callback handler
            self.app.add_handler(CallbackQueryHandler(self.handle_callback))
            
            # Start polling
            await self.app.initialize()
            await self.app.start()
            await self.app.updater.start_polling()
            
            logger.info("✅ Bot API polling started")
            
        except Exception as e:
            logger.error(f"❌ Bot API error: {e}")
            
    async def process_group_message(self, message):
        """Process group message"""
        try:
            if not message.text or len(message.text.strip()) < 1:
                logger.info(f"📝 Skipping empty message {message.id}")
                return
                
            logger.info(f"📝 Processing message {message.id}: {message.text[:50]}...")
            
            # Simple analysis without external analyzer
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
            
            logger.info(f"🤖 Analysis: {status} ({confidence:.0%})")
            
            # Send to admins
            await self.send_to_admins(message)
            
            logger.info(f"✅ Message {message.id} processed successfully")
            
        except Exception as e:
            logger.error(f"❌ Message processing error: {e}")
            logger.error(traceback.format_exc())
            
    async def get_previous_messages(self, current_message_id, limit=9):
        """Get previous messages from group"""
        try:
            messages = await self.client.get_messages(
                self.target_entity,
                min_id=current_message_id - 100,
                max_id=current_message_id - 1,
                limit=limit
            )
            
            # Sort by date (oldest first)
            messages.sort(key=lambda m: m.date)
            
            previous_texts = []
            for msg in messages:
                if msg.text and msg.text.strip():
                    time_str = msg.date.astimezone(pytz.timezone('Europe/Kyiv')).strftime("%H:%M")
                    # Limit message length
                    text = msg.text[:100] + "..." if len(msg.text) > 100 else msg.text
                    previous_texts.append(f"🕐 {time_str}: {text}")
            
            return previous_texts
            
        except Exception as e:
            logger.error(f"❌ Error getting previous messages: {e}")
            return []

    async def send_to_admins(self, message):
        """Send message to admins with buttons and previous messages"""
        try:
            logger.info(f"📤 Sending message {message.id} to admins...")
            
            msg_data = self.message_store[message.id]
            time_str = message.date.astimezone(pytz.timezone('Europe/Kyiv')).strftime("%H:%M")
            
            # Get previous messages
            previous_messages = await self.get_previous_messages(message.id, 9)
            
            text = f"📨 Нове повідомлення о {time_str}\n\n"
            text += f"💬 {message.text}\n\n"
            text += f"🤖 Аналіз: {msg_data['status']} ({msg_data['confidence']:.0%})\n\n"
            
            # Add previous messages if any
            if previous_messages:
                text += "📋 Попередні повідомлення:\n"
                for prev_msg in previous_messages:
                    text += f"{prev_msg}\n"
                text += "\n"
            
            text += "Виберіть дію:"
            
            # Create inline keyboard
            
            keyboard = [
                [
                    InlineKeyboardButton("✅ Відкрито", callback_data=f"approve_open_{message.id}"),
                    InlineKeyboardButton("❌ Закрито", callback_data=f"approve_closed_{message.id}")
                ],
                [
                    InlineKeyboardButton("❌ Відхилити", callback_data=f"reject_{message.id}")
                ]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Send to all admins
            success_count = 0
            for admin_id in ADMIN_IDS:
                try:
                    await self.bot.send_message(
                        chat_id=admin_id,
                        text=text,
                        reply_markup=reply_markup
                    )
                    success_count += 1
                    logger.info(f"✅ Sent to admin {admin_id}")
                except Exception as e:
                    logger.error(f"❌ Failed to send to admin {admin_id}: {e}")
                    
            logger.info(f"✅ Message sent to {success_count}/{len(ADMIN_IDS)} admins")
                    
        except Exception as e:
            logger.error(f"❌ Admin notification error: {e}")
            logger.error(traceback.format_exc())
            
    async def handle_callback(self, update, context):
        """Handle callback queries"""
        try:
            query = update.callback_query
            callback_data = query.data
            user_id = query.from_user.id
            
            logger.info(f"🎯 Callback: {callback_data} from {user_id}")
            
            if user_id not in ADMIN_IDS:
                await query.answer("❌ Доступ заборонений", show_alert=True)
                return
                
            # Answer immediately
            await query.answer("⏳ Обробляю...")
            
            if callback_data.startswith('approve_'):
                parts = callback_data.split('_')
                status = parts[1]
                message_id = int(parts[2])
                await self.approve_message(query, message_id, status)
                
            elif callback_data.startswith('reject_'):
                message_id = int(callback_data.split('_')[1])
                await self.reject_message(query, message_id)
                
        except Exception as e:
            logger.error(f"❌ Callback error: {e}")
            await query.answer(f"❌ Помилка: {str(e)}", show_alert=True)
            
    async def approve_message(self, query, message_id: int, status: str):
        """Approve and publish message"""
        try:
            logger.info(f"📤 Starting approval for message {message_id} with status {status}")
            
            if message_id not in self.message_store:
                logger.error(f"❌ Message {message_id} not in store")
                await query.answer("❌ Повідомлення не знайдено", show_alert=True)
                return
                
            status_emoji = "✅" if status == "open" else "❌"
            status_text = "Відкрито" if status == "open" else "Закрито"
            
            # Use GMT+3 timezone
            kyiv_tz = pytz.timezone('Europe/Kyiv')
            current_time = datetime.now(kyiv_tz).strftime("%H:%M")
            channel_text = f"{status_emoji} {status_text}\n🕓 {current_time}"
            
            logger.info(f"📢 Publishing to channel {TARGET_CHANNEL}: {channel_text}")
            
            # Publish to channel
            try:
                await self.bot.send_message(
                    chat_id=TARGET_CHANNEL,
                    text=channel_text
                )
                logger.info(f"✅ Successfully published to channel")
            except Exception as channel_error:
                logger.error(f"❌ Channel publish error: {channel_error}")
                await query.answer(f"❌ Помилка публікації в канал: {channel_error}", show_alert=True)
                return
            
            # Update message
            try:
                await query.edit_message_text(
                    f"✅ Опубліковано в канал!\n\n"
                    f"📋 Статус: {status_text}\n"
                    f"🕐 Час: {current_time}\n"
                    f"👤 Схвалено: {query.from_user.first_name}"
                )
                logger.info(f"✅ Message {message_id} published as {status}")
            except Exception as edit_error:
                logger.error(f"❌ Message edit error: {edit_error}")
                # Still successful if published to channel
                await query.answer("✅ Опубліковано в канал!", show_alert=False)
            
        except Exception as e:
            logger.error(f"❌ Approval error: {e}")
            logger.error(traceback.format_exc())
            await query.answer(f"❌ Помилка: {str(e)}", show_alert=True)
            
    async def reject_message(self, query, message_id: int):
        """Reject message"""
        try:
            await query.edit_message_text(
                f"❌ Повідомлення відхилено\n\n"
                f"👤 Відхилено: {query.from_user.first_name}\n"
                f"🕐 Час: {datetime.now().strftime('%H:%M')}"
            )
            
            logger.info(f"❌ Message {message_id} rejected")
            
        except Exception as e:
            logger.error(f"❌ Rejection error: {e}")
            
    async def notify_admins(self, message: str):
        """Notify all admins"""
        for admin_id in ADMIN_IDS:
            try:
                await self.bot.send_message(chat_id=admin_id, text=message)
                logger.info(f"✅ Notified admin {admin_id}")
            except Exception as e:
                logger.error(f"❌ Failed to notify admin {admin_id}: {e}")

async def main():
    """Main function"""
    bot = WorkingBot()
    await bot.start()

if __name__ == "__main__":
    asyncio.run(main())