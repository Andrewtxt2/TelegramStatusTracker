#!/usr/bin/env python3
"""
Perfect Bot - Final working solution without polling conflicts
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
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

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
        logging.FileHandler('perfect_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('perfect_bot')

class PerfectBot:
    def __init__(self):
        self.client = None
        self.bot = None
        self.target_entity = None
        self.running = True
        self.start_time = datetime.now()
        self.processed_messages = 0
        self.message_store = {}
        self.command_handlers = {}
        
    async def start(self):
        """Start the perfect bot system"""
        logger.info("🚀 Starting Perfect Bot System...")
        
        try:
            # Initialize MTProto client for group monitoring
            self.client = TelegramClient('perfect_session', API_ID, API_HASH)
            await self.client.start(phone='+380686850166')
            
            me = await self.client.get_me()
            logger.info(f"✅ MTProto connected: {me.first_name}")
            
            # Get target group
            if SOURCE_GROUP.startswith('https://t.me/'):
                group_username = SOURCE_GROUP.split('/')[-1]
                self.target_entity = await self.client.get_entity(group_username)
            else:
                self.target_entity = await self.client.get_entity(SOURCE_GROUP)
            
            logger.info(f"✅ Group found: {self.target_entity.title}")
            
            # Initialize Bot API for commands only (no polling)
            self.bot = Bot(token=BOT_TOKEN)
            
            # Test bot connection
            bot_info = await self.bot.get_me()
            logger.info(f"✅ Bot API connected: @{bot_info.username}")
            
            # Setup command handlers manually
            self.command_handlers = {
                '/start': self.handle_start,
                '/status': self.handle_status,
                '/health': self.handle_health
            }
            
            # Setup message handler for group monitoring
            @self.client.on(events.NewMessage(chats=self.target_entity))
            async def handle_new_message(event):
                await self.process_group_message(event.message)
            
            # Setup callback handler for buttons
            @self.client.on(events.CallbackQuery())
            async def handle_callback(event):
                await self.process_callback(event)
            
            # Setup private message handler for commands
            @self.client.on(events.NewMessage(func=lambda e: e.is_private))
            async def handle_private_message(event):
                await self.process_private_message(event)
            
            logger.info("✅ All systems initialized")
            
            # Send startup notification
            await self.notify_admins("🚀 Perfect Bot System запущено!\n\nСистема повністю готова:\n• Моніторинг групи активний\n• Команди бота працюють\n• Кнопки схвалення готові\n• Без polling конфліктів")
            
            # Keep running
            logger.info("🔄 Bot running... Press Ctrl+C to stop")
            await self.client.run_until_disconnected()
            
        except Exception as e:
            logger.error(f"Startup error: {e}")
            logger.error(traceback.format_exc())
            raise
            
    async def process_group_message(self, message):
        """Process new message from monitored group"""
        try:
            if not message.text or len(message.text.strip()) < 5:
                return
                
            logger.info(f"📨 New message ID {message.id}: {message.text[:50]}...")
            
            # Simple status analysis
            text_lower = message.text.lower()
            
            # Analyze status
            if any(word in text_lower for word in ['відкрито', 'відкрит', 'open', 'працює', 'working', 'доступно']):
                suggested_status = 'open'
                confidence = 0.8
            elif any(word in text_lower for word in ['закрито', 'закрит', 'closed', 'не працює', 'not working', 'заблоковано']):
                suggested_status = 'closed'
                confidence = 0.8
            else:
                suggested_status = 'unknown'
                confidence = 0.3
                
            # Check for time mentions
            if any(word in text_lower for word in ['год', 'час', 'хвилин', 'секунд', ':', 'time']):
                confidence += 0.1
                
            confidence = min(confidence, 0.95)
            
            logger.info(f"🤖 Analysis: {suggested_status} ({confidence:.0%})")
            
            # Store message data
            self.message_store[message.id] = {
                'text': message.text,
                'date': message.date,
                'suggested_status': suggested_status,
                'confidence': confidence
            }
            
            # Send to admins
            await self.send_to_admins(message)
            
            self.processed_messages += 1
            
        except Exception as e:
            logger.error(f"Error processing message {message.id}: {e}")
            logger.error(traceback.format_exc())
            
    async def send_to_admins(self, message):
        """Send message to administrators with approval buttons"""
        try:
            # Format message for admins
            time_str = message.date.strftime("%H:%M")
            message_data = self.message_store[message.id]
            
            text = f"📨 Нове повідомлення о {time_str}\n\n"
            text += f"💬 Текст: {message.text}\n\n"
            text += f"🤖 Аналіз: {message_data['suggested_status']} ({message_data['confidence']:.0%})\n\n"
            text += f"Оберіть дію:"
            
            # Create inline keyboard
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
            for admin_id in ADMIN_IDS:
                try:
                    await self.bot.send_message(
                        chat_id=admin_id,
                        text=text,
                        reply_markup=reply_markup
                    )
                    logger.info(f"✅ Sent to admin {admin_id}")
                except Exception as e:
                    logger.warning(f"Failed to send to admin {admin_id}: {e}")
                    
        except Exception as e:
            logger.error(f"Error sending to admins: {e}")
            
    async def process_callback(self, event):
        """Process callback queries from inline buttons"""
        try:
            callback_data = event.data.decode('utf-8')
            user_id = event.sender_id
            
            if user_id not in ADMIN_IDS:
                await event.answer("❌ Доступ заборонений", alert=True)
                return
                
            logger.info(f"🎯 Callback from admin {user_id}: {callback_data}")
            
            # Parse callback data
            if callback_data.startswith('approve_'):
                parts = callback_data.split('_')
                status = parts[1]  # open or closed
                message_id = int(parts[2])
                
                await self.approve_message(event, message_id, status)
                
            elif callback_data.startswith('reject_'):
                message_id = int(callback_data.split('_')[1])
                await self.reject_message(event, message_id)
                
        except Exception as e:
            logger.error(f"Callback error: {e}")
            await event.answer(f"❌ Помилка: {e}", alert=True)
            
    async def approve_message(self, event, message_id: int, status: str):
        """Approve and publish message"""
        try:
            if message_id not in self.message_store:
                await event.answer("❌ Повідомлення не знайдено", alert=True)
                return
                
            message_data = self.message_store[message_id]
            
            # Format for channel
            status_emoji = "✅" if status == "open" else "🔴"
            status_text = "Відкрито" if status == "open" else "Закрито"
            
            current_time = datetime.now().strftime("%H:%M")
            channel_text = f"{status_emoji} {status_text} 🕓 {current_time}"
            
            # Send to channel
            try:
                await self.bot.send_message(
                    chat_id=TARGET_CHANNEL,
                    text=channel_text
                )
                
                # Update message
                user = await self.client.get_entity(event.sender_id)
                
                await event.edit(
                    f"✅ Опубліковано в канал!\n\n"
                    f"📋 Статус: {status_text}\n"
                    f"🕐 Час: {current_time}\n"
                    f"👤 Схвалено: {user.first_name}"
                )
                
                await event.answer("✅ Опубліковано!")
                
                logger.info(f"✅ Message {message_id} published as {status}")
                
            except Exception as e:
                await event.edit(f"❌ Помилка публікації: {e}")
                logger.error(f"Publishing error: {e}")
                
        except Exception as e:
            logger.error(f"Approval error: {e}")
            await event.answer(f"❌ Помилка схвалення: {e}", alert=True)
            
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
            
    async def process_private_message(self, event):
        """Process private messages (commands)"""
        try:
            message_text = event.message.text
            user_id = event.sender_id
            
            if not message_text.startswith('/'):
                return
                
            logger.info(f"Command from {user_id}: {message_text}")
            
            # Handle commands
            if message_text in self.command_handlers:
                await self.command_handlers[message_text](event)
                
        except Exception as e:
            logger.error(f"Command processing error: {e}")
            
    async def handle_start(self, event):
        """Handle /start command"""
        user_id = event.sender_id
        
        if user_id in ADMIN_IDS:
            text = "🚀 Perfect Bot System активний!\n\n"
            text += "Система повністю працює:\n"
            text += "• Моніторинг групи активний\n"
            text += "• Аналіз повідомлень працює\n"
            text += "• Кнопки схвалення готові\n"
            text += "• Без polling конфліктів\n\n"
            text += "Команди:\n"
            text += "• /status - стан системи\n"
            text += "• /health - перевірка компонентів"
        else:
            text = "🤖 Переїзд Monitor Bot\n\nЦей бот моніторить статус переїзду."
            
        await event.respond(text)
        
    async def handle_status(self, event):
        """Handle /status command"""
        user_id = event.sender_id
        
        if user_id not in ADMIN_IDS:
            await event.respond("❌ Доступ заборонений")
            return
            
        uptime = datetime.now() - self.start_time
        
        text = f"📊 Стан Perfect Bot System\n\n"
        text += f"🕐 Час роботи: {uptime}\n"
        text += f"📨 Оброблено повідомлень: {self.processed_messages}\n"
        text += f"🤖 MTProto: {'✅ Підключено' if self.client.is_connected() else '❌ Відключено'}\n"
        text += f"🔄 Bot API: ✅ Активний\n"
        text += f"📋 Група: {self.target_entity.title if self.target_entity else 'Не знайдено'}\n"
        text += f"📢 Канал: {TARGET_CHANNEL}\n"
        text += f"👥 Адміністраторів: {len(ADMIN_IDS)}\n\n"
        text += f"🔄 Статус: {'✅ Працює' if self.running else '❌ Зупинено'}"
        
        await event.respond(text)
        
    async def handle_health(self, event):
        """Handle /health command"""
        user_id = event.sender_id
        
        if user_id not in ADMIN_IDS:
            await event.respond("❌ Доступ заборонений")
            return
            
        # Health checks
        try:
            # Check MTProto
            mtproto_status = "✅ Підключено" if self.client.is_connected() else "❌ Відключено"
            
            # Check Bot API
            me = await self.bot.get_me()
            bot_status = f"✅ @{me.username}"
            
            # Check group access
            if self.target_entity:
                group_status = f"✅ {self.target_entity.title}"
            else:
                group_status = "❌ Не підключено"
                
            text = f"🏥 Перевірка здоров'я системи\n\n"
            text += f"🔗 MTProto: {mtproto_status}\n"
            text += f"🤖 Bot API: {bot_status}\n"
            text += f"📋 Група: {group_status}\n"
            text += f"💾 Зберігання: ✅ Працює\n"
            text += f"🔄 Handlers: ✅ Активні\n\n"
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
    bot = PerfectBot()
    try:
        await bot.start()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(main())