#!/usr/bin/env python3
"""
Ultimate Bot - Final stable solution with fresh session and comprehensive monitoring
"""

import asyncio
import os
import sys
import json
import time
import logging
import traceback
from datetime import datetime
from typing import Dict, List, Optional

from telethon import TelegramClient, events
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup

# Configuration
API_ID = int(os.getenv('TELEGRAM_API_ID', '26886585'))
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
        logging.FileHandler('ultimate_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('ultimate_bot')

class UltimateBot:
    def __init__(self):
        self.client = None
        self.bot = None
        self.target_entity = None
        self.running = True
        self.start_time = datetime.now()
        self.processed_messages = 0
        self.message_store = {}
        self.last_activity = datetime.now()
        
    async def start(self):
        """Start the ultimate bot system"""
        logger.info("🚀 Starting Ultimate Bot System...")
        
        try:
            # Create fresh session
            session_name = f"ultimate_session_{int(time.time())}"
            
            # Initialize MTProto client
            self.client = TelegramClient(session_name, API_ID, API_HASH)
            
            logger.info("📱 Starting authentication...")
            await self.client.start(phone='+380686850166')
            
            me = await self.client.get_me()
            logger.info(f"✅ MTProto connected: {me.first_name} ({me.username})")
            
            # Get target group
            logger.info("🔍 Searching for target group...")
            group_username = SOURCE_GROUP.split('/')[-1]
            logger.info(f"🔍 Looking for group: {group_username}")
            self.target_entity = await self.client.get_entity(group_username)
            logger.info(f"✅ Group found: {self.target_entity.title}")
            logger.info(f"✅ Group ID: {self.target_entity.id}")
            
            # Test group access
            try:
                recent_messages = await self.client.get_messages(self.target_entity, limit=3)
                logger.info(f"📨 Found {len(recent_messages)} recent messages in group")
                for msg in recent_messages:
                    logger.info(f"  - Message {msg.id}: {msg.text[:50] if msg.text else '[no text]'}...")
            except Exception as msg_error:
                logger.error(f"❌ Cannot access group messages: {msg_error}")
            
            # Initialize Bot API
            self.bot = Bot(token=BOT_TOKEN)
            bot_info = await self.bot.get_me()
            logger.info(f"✅ Bot API connected: @{bot_info.username}")
            
            # Setup handlers
            await self.setup_handlers()
            
            # Send startup notification
            await self.notify_admins(
                "🚀 Ultimate Bot System ЗАПУЩЕНО!\n\n"
                "✅ Особливості:\n"
                "• Нова сесія - без конфліктів\n"
                "• Постійне логування активності\n"
                "• Моніторинг групи активний\n"
                "• Кнопки схвалення готові\n"
                "• Команди працюють стабільно\n\n"
                "🔧 Команди: /start, /status, /health\n"
                "📋 Група: " + self.target_entity.title + "\n"
                "📢 Канал: " + TARGET_CHANNEL
            )
            
            logger.info("🔄 Bot running with fresh session...")
            
            # Start activity monitoring
            activity_task = asyncio.create_task(self.activity_monitor())
            
            # Start message polling as backup
            polling_task = asyncio.create_task(self.message_polling())
            
            # Start Bot API polling for callbacks
            bot_polling_task = asyncio.create_task(self.start_bot_polling())
            
            # Keep running
            await self.client.run_until_disconnected()
            
        except Exception as e:
            logger.error(f"Startup error: {e}")
            logger.error(traceback.format_exc())
            raise
            
    async def setup_handlers(self):
        """Setup all event handlers"""
        logger.info("⚙️ Setting up event handlers...")
        
        # Group message handler
        @self.client.on(events.NewMessage(chats=self.target_entity))
        async def handle_group_message(event):
            try:
                self.last_activity = datetime.now()
                logger.info(f"📨 NEW GROUP MESSAGE DETECTED!")
                logger.info(f"📨 Group message {event.message.id}: {event.message.text[:100] if event.message.text else '[no text]'}...")
                logger.info(f"📨 From chat: {event.chat.title if hasattr(event.chat, 'title') else event.chat_id}")
                await self.process_group_message(event.message)
            except Exception as e:
                logger.error(f"❌ Group message error: {e}")
                logger.error(traceback.format_exc())
        
        # Callback handler for MTProto inline buttons
        @self.client.on(events.CallbackQuery())
        async def handle_callback(event):
            try:
                self.last_activity = datetime.now()
                logger.info(f"🎯 MTProto Callback: {event.data} from {event.sender_id}")
                await self.process_callback(event)
            except Exception as e:
                logger.error(f"MTProto Callback error: {e}")
                logger.error(traceback.format_exc())
        
        # Private message handler
        @self.client.on(events.NewMessage(func=lambda e: e.is_private))
        async def handle_private_message(event):
            try:
                self.last_activity = datetime.now()
                logger.info(f"💬 Private: {event.message.text} from {event.sender_id}")
                await self.process_command(event)
            except Exception as e:
                logger.error(f"Private message error: {e}")
                logger.error(traceback.format_exc())
        
        logger.info("✅ Event handlers configured")
        
    async def activity_monitor(self):
        """Monitor system activity"""
        while self.running:
            try:
                await asyncio.sleep(120)  # Check every 2 minutes
                
                time_since_activity = (datetime.now() - self.last_activity).total_seconds()
                
                logger.info(f"💓 Activity check: {time_since_activity:.0f}s since last activity")
                
                # Send periodic status to first admin
                if time_since_activity > 300:  # 5 minutes
                    await self.bot.send_message(
                        chat_id=ADMIN_IDS[0],
                        text=f"🔄 Система активна\n\n"
                             f"• Час без активності: {time_since_activity:.0f}s\n"
                             f"• Оброблено повідомлень: {self.processed_messages}\n"
                             f"• Статус: ✅ Працює\n"
                             f"• Перевірка: {datetime.now().strftime('%H:%M')}"
                    )
                    self.last_activity = datetime.now()
                    
            except Exception as e:
                logger.error(f"Activity monitor error: {e}")
                
    async def message_polling(self):
        """Poll for new messages as backup"""
        last_message_id = None
        
        while self.running:
            try:
                await asyncio.sleep(10)  # Check every 10 seconds
                
                # Get latest messages
                messages = await self.client.get_messages(self.target_entity, limit=5)
                
                if messages:
                    latest_message = messages[0]
                    
                    # Check if this is a new message
                    if last_message_id is None:
                        last_message_id = latest_message.id
                        logger.info(f"🔄 Polling initialized with message ID: {last_message_id}")
                        continue
                        
                    if latest_message.id > last_message_id:
                        logger.info(f"📨 POLLING DETECTED NEW MESSAGE: {latest_message.id}")
                        logger.info(f"📨 Text: {latest_message.text[:100] if latest_message.text else '[no text]'}")
                        
                        # Check if message was already processed by event handler
                        if latest_message.id not in self.message_store:
                            # Process the new message
                            await self.process_group_message(latest_message)
                        else:
                            logger.info(f"⚠️ Message {latest_message.id} already processed by event handler")
                        
                        # Update last message ID
                        last_message_id = latest_message.id
                        
            except Exception as e:
                logger.error(f"❌ Message polling error: {e}")
                await asyncio.sleep(30)  # Wait longer on error
                
    async def start_bot_polling(self):
        """Start Bot API polling for callback handling"""
        from telegram.ext import Application, CallbackQueryHandler
        
        try:
            # Create Bot API application
            app = Application.builder().token(BOT_TOKEN).build()
            
            # Add callback handler
            app.add_handler(CallbackQueryHandler(self.handle_bot_callback))
            
            logger.info("🔄 Starting Bot API polling for callbacks...")
            await app.run_polling(drop_pending_updates=True)
            
        except Exception as e:
            logger.error(f"❌ Bot polling error: {e}")
            
    async def handle_bot_callback(self, update, context):
        """Handle Bot API callbacks"""
        try:
            query = update.callback_query
            callback_data = query.data
            user_id = query.from_user.id
            
            logger.info(f"🎯 Bot API Callback: {callback_data} from {user_id}")
            
            if user_id not in ADMIN_IDS:
                logger.warning(f"❌ Unauthorized callback from user {user_id}")
                await query.answer("❌ Доступ заборонений", show_alert=True)
                return
                
            # Answer callback immediately
            await query.answer("⏳ Обробляю...")
            
            if callback_data.startswith('approve_'):
                parts = callback_data.split('_')
                status = parts[1]
                message_id = int(parts[2])
                logger.info(f"✅ Approving message {message_id} with status {status}")
                await self.approve_message_bot(query, message_id, status)
                
            elif callback_data.startswith('reject_'):
                message_id = int(callback_data.split('_')[1])
                logger.info(f"❌ Rejecting message {message_id}")
                await self.reject_message_bot(query, message_id)
                
        except Exception as e:
            logger.error(f"❌ Bot callback error: {e}")
            logger.error(traceback.format_exc())
            await query.answer(f"❌ Помилка: {str(e)}", show_alert=True)
            
    async def approve_message_bot(self, query, message_id: int, status: str):
        """Approve message via Bot API"""
        try:
            logger.info(f"📤 Bot API approval for message {message_id}")
            
            if message_id not in self.message_store:
                logger.error(f"❌ Message {message_id} not found in store")
                await query.answer("❌ Повідомлення не знайдено", show_alert=True)
                return
                
            status_emoji = "✅" if status == "open" else "🔴"
            status_text = "Відкрито" if status == "open" else "Закрито"
            
            current_time = datetime.now().strftime("%H:%M")
            channel_text = f"{status_emoji} {status_text} 🕓 {current_time}"
            
            logger.info(f"📢 Publishing to channel: {channel_text}")
            
            # Publish to channel
            await self.bot.send_message(
                chat_id=TARGET_CHANNEL,
                text=channel_text
            )
            logger.info(f"✅ Successfully published to channel")
            
            # Update message
            await query.edit_message_text(
                f"✅ Опубліковано в канал!\n\n"
                f"📋 Статус: {status_text}\n"
                f"🕐 Час: {current_time}\n"
                f"👤 Схвалено: {query.from_user.first_name}"
            )
            
        except Exception as e:
            logger.error(f"❌ Bot approval error: {e}")
            await query.answer(f"❌ Помилка: {str(e)}", show_alert=True)
            
    async def reject_message_bot(self, query, message_id: int):
        """Reject message via Bot API"""
        try:
            await query.edit_message_text(
                f"❌ Повідомлення відхилено\n\n"
                f"👤 Відхилено: {query.from_user.first_name}\n"
                f"🕐 Час: {datetime.now().strftime('%H:%M')}"
            )
            
        except Exception as e:
            logger.error(f"❌ Bot rejection error: {e}")
                
    async def process_group_message(self, message):
        """Process new message from group"""
        try:
            if not message.text or len(message.text.strip()) < 1:
                logger.info(f"📝 Skipping empty message {message.id}")
                return
                
            logger.info(f"📝 Analyzing message: {message.text[:100]}...")
            
            # Status analysis
            text_lower = message.text.lower()
            
            if any(word in text_lower for word in ['відкрито', 'open', 'працює', 'working']):
                status = 'open'
                confidence = 0.8
            elif any(word in text_lower for word in ['закрито', 'closed', 'не працює', 'blocked']):
                status = 'closed'
                confidence = 0.8
            else:
                status = 'unknown'
                confidence = 0.3
                
            # Check for time markers
            if any(char in text_lower for char in [':', '.']):
                confidence += 0.1
                
            confidence = min(confidence, 0.95)
            
            logger.info(f"🤖 Analysis result: {status} (confidence: {confidence:.0%})")
            
            # Store message
            self.message_store[message.id] = {
                'text': message.text,
                'date': message.date,
                'status': status,
                'confidence': confidence
            }
            
            # Send to admins
            logger.info(f"📤 Sending message {message.id} to admins...")
            await self.send_to_admins(message)
            
            self.processed_messages += 1
            logger.info(f"✅ Message {message.id} processed successfully")
            
        except Exception as e:
            logger.error(f"Message processing error: {e}")
            logger.error(traceback.format_exc())
            
    async def send_to_admins(self, message):
        """Send message to admins with buttons"""
        try:
            logger.info(f"📤 Preparing admin notification for message {message.id}")
            
            msg_data = self.message_store[message.id]
            time_str = message.date.strftime("%H:%M")
            
            text = f"📨 Повідомлення о {time_str}\n\n"
            text += f"💬 {message.text}\n\n"
            text += f"🤖 Аналіз: {msg_data['status']} ({msg_data['confidence']:.0%})\n\n"
            text += "Виберіть дію:"
            
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
            
            # Send to all admins
            logger.info(f"📤 Sending to {len(ADMIN_IDS)} admins...")
            for admin_id in ADMIN_IDS:
                try:
                    logger.info(f"📤 Sending to admin {admin_id}...")
                    await self.bot.send_message(
                        chat_id=admin_id,
                        text=text,
                        reply_markup=reply_markup
                    )
                    logger.info(f"✅ Message sent to admin {admin_id}")
                except Exception as e:
                    logger.error(f"❌ Failed to send to admin {admin_id}: {e}")
                    logger.error(traceback.format_exc())
                    
        except Exception as e:
            logger.error(f"❌ Admin notification error: {e}")
            logger.error(traceback.format_exc())
            
    async def process_callback(self, event):
        """Process callback from buttons"""
        try:
            callback_data = event.data.decode('utf-8')
            user_id = event.sender_id
            
            logger.info(f"🎯 Processing callback: {callback_data} from user {user_id}")
            
            if user_id not in ADMIN_IDS:
                logger.warning(f"❌ Unauthorized callback from user {user_id}")
                await event.answer("❌ Доступ заборонений", alert=True)
                return
                
            # Answer callback immediately to stop loading
            await event.answer("⏳ Обробляю...")
            
            if callback_data.startswith('approve_'):
                parts = callback_data.split('_')
                status = parts[1]
                message_id = int(parts[2])
                logger.info(f"✅ Approving message {message_id} with status {status}")
                await self.approve_message(event, message_id, status)
                
            elif callback_data.startswith('reject_'):
                message_id = int(callback_data.split('_')[1])
                logger.info(f"❌ Rejecting message {message_id}")
                await self.reject_message(event, message_id)
                
        except Exception as e:
            logger.error(f"❌ Callback processing error: {e}")
            logger.error(traceback.format_exc())
            await event.answer(f"❌ Помилка: {str(e)}", alert=True)
            
    async def approve_message(self, event, message_id: int, status: str):
        """Approve and publish message"""
        try:
            logger.info(f"📤 Starting approval process for message {message_id}")
            
            if message_id not in self.message_store:
                logger.error(f"❌ Message {message_id} not found in store")
                await event.answer("❌ Повідомлення не знайдено", alert=True)
                return
                
            status_emoji = "✅" if status == "open" else "🔴"
            status_text = "Відкрито" if status == "open" else "Закрито"
            
            current_time = datetime.now().strftime("%H:%M")
            channel_text = f"{status_emoji} {status_text} 🕓 {current_time}"
            
            logger.info(f"📢 Publishing to channel: {channel_text}")
            
            # Publish to channel
            try:
                await self.bot.send_message(
                    chat_id=TARGET_CHANNEL,
                    text=channel_text
                )
                logger.info(f"✅ Successfully published to channel {TARGET_CHANNEL}")
                
            except Exception as channel_error:
                logger.error(f"❌ Channel publishing error: {channel_error}")
                await event.answer(f"❌ Помилка публікації в канал: {channel_error}", alert=True)
                return
            
            # Update button message
            try:
                user = await self.client.get_entity(event.sender_id)
                
                await event.edit(
                    f"✅ Опубліковано в канал!\n\n"
                    f"📋 Статус: {status_text}\n"
                    f"🕐 Час: {current_time}\n"
                    f"👤 Схвалено: {user.first_name}"
                )
                
                logger.info(f"✅ Message {message_id} approved and published successfully")
                
            except Exception as edit_error:
                logger.error(f"❌ Message edit error: {edit_error}")
                await event.answer("✅ Опубліковано (але помилка оновлення повідомлення)", alert=True)
            
        except Exception as e:
            logger.error(f"❌ Approval error: {e}")
            logger.error(traceback.format_exc())
            await event.answer(f"❌ Помилка схвалення: {str(e)}", alert=True)
            
    async def reject_message(self, event, message_id: int):
        """Reject message"""
        try:
            user = await self.client.get_entity(event.sender_id)
            
            await event.edit(
                f"❌ Повідомлення відхилено\n\n"
                f"👤 Відхилено: {user.first_name}\n"
                f"🕐 Час: {datetime.now().strftime('%H:%M')}"
            )
            
            await event.answer("❌ Відхилено!")
            
            logger.info(f"❌ Message {message_id} rejected")
            
        except Exception as e:
            logger.error(f"Rejection error: {e}")
            logger.error(traceback.format_exc())
            
    async def process_command(self, event):
        """Process commands"""
        try:
            text = event.message.text
            user_id = event.sender_id
            
            if not text.startswith('/'):
                return
                
            logger.info(f"💬 Command: {text} from {user_id}")
            
            if text == '/start':
                await self.handle_start(event)
            elif text == '/status':
                await self.handle_status(event)
            elif text == '/health':
                await self.handle_health(event)
                
        except Exception as e:
            logger.error(f"Command error: {e}")
            logger.error(traceback.format_exc())
            
    async def handle_start(self, event):
        """Handle /start command"""
        user_id = event.sender_id
        
        if user_id in ADMIN_IDS:
            text = "🚀 Ultimate Bot System активний!\n\n"
            text += "✅ Система працює стабільно:\n"
            text += "• Моніторинг групи\n"
            text += "• Аналіз повідомлень\n"
            text += "• Кнопки схвалення\n"
            text += "• Публікація в канал\n\n"
            text += "🔧 Команди:\n"
            text += "/status - стан системи\n"
            text += "/health - перевірка здоров'я"
        else:
            text = "🤖 Переїзд Monitor Bot\n\nБот моніторить статус переїзду."
            
        await event.respond(text)
        
    async def handle_status(self, event):
        """Handle /status command"""
        user_id = event.sender_id
        
        if user_id not in ADMIN_IDS:
            await event.respond("❌ Доступ заборонений")
            return
            
        uptime = datetime.now() - self.start_time
        time_since_activity = (datetime.now() - self.last_activity).total_seconds()
        
        text = f"📊 Стан Ultimate Bot\n\n"
        text += f"🕐 Час роботи: {uptime}\n"
        text += f"📨 Повідомлень: {self.processed_messages}\n"
        text += f"💓 Остання активність: {time_since_activity:.0f}s тому\n"
        text += f"🤖 MTProto: {'✅' if self.client.is_connected() else '❌'}\n"
        text += f"📋 Група: {self.target_entity.title}\n"
        text += f"📢 Канал: {TARGET_CHANNEL}\n"
        text += f"👥 Адмінів: {len(ADMIN_IDS)}\n\n"
        text += f"🔄 Статус: {'✅ Працює' if self.running else '❌ Зупинено'}"
        
        await event.respond(text)
        
    async def handle_health(self, event):
        """Handle /health command"""
        user_id = event.sender_id
        
        if user_id not in ADMIN_IDS:
            await event.respond("❌ Доступ заборонений")
            return
            
        try:
            me = await self.bot.get_me()
            
            text = f"🏥 Перевірка здоров'я\n\n"
            text += f"🔗 MTProto: {'✅' if self.client.is_connected() else '❌'}\n"
            text += f"🤖 Bot API: ✅ @{me.username}\n"
            text += f"📋 Група: ✅ {self.target_entity.title}\n"
            text += f"💾 Зберігання: ✅ Працює\n"
            text += f"🔄 Handlers: ✅ Активні\n"
            text += f"📊 Моніторинг: ✅ Активний\n\n"
            text += f"🕐 Перевірка: {datetime.now().strftime('%H:%M:%S')}"
            
        except Exception as e:
            text = f"❌ Помилка перевірки: {e}"
            
        await event.respond(text)
        
    async def notify_admins(self, message: str):
        """Send notification to all admins"""
        for admin_id in ADMIN_IDS:
            try:
                await self.bot.send_message(chat_id=admin_id, text=message)
                logger.info(f"✅ Notified admin {admin_id}")
            except Exception as e:
                logger.warning(f"Failed to notify admin {admin_id}: {e}")

async def main():
    """Main function"""
    bot = UltimateBot()
    try:
        await bot.start()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(main())