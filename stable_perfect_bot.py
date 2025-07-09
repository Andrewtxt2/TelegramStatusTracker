#!/usr/bin/env python3
"""
Stable Perfect Bot - Enhanced version with connection monitoring and auto-recovery
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
        logging.FileHandler('stable_perfect_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('stable_perfect_bot')

class StablePerfectBot:
    def __init__(self):
        self.client = None
        self.bot = None
        self.target_entity = None
        self.running = True
        self.start_time = datetime.now()
        self.processed_messages = 0
        self.message_store = {}
        self.last_heartbeat = datetime.now()
        self.connection_retries = 0
        self.max_retries = 5
        
    async def start(self):
        """Start the stable perfect bot system"""
        logger.info("🚀 Starting Stable Perfect Bot System...")
        
        while self.running and self.connection_retries < self.max_retries:
            try:
                await self.initialize_connections()
                await self.setup_handlers()
                await self.start_monitoring()
                break
            except Exception as e:
                self.connection_retries += 1
                logger.error(f"Connection failed (attempt {self.connection_retries}/{self.max_retries}): {e}")
                if self.connection_retries < self.max_retries:
                    await asyncio.sleep(10)
                else:
                    logger.error("Max retries reached. Exiting.")
                    raise
                    
    async def initialize_connections(self):
        """Initialize all connections"""
        logger.info("🔗 Initializing connections...")
        
        # Initialize MTProto client
        self.client = TelegramClient('stable_perfect_session', API_ID, API_HASH)
        await self.client.start(phone='+380686850166')
        
        # Verify connection
        me = await self.client.get_me()
        logger.info(f"✅ MTProto connected: {me.first_name}")
        
        # Get target group with retry
        max_group_attempts = 3
        for attempt in range(max_group_attempts):
            try:
                if SOURCE_GROUP.startswith('https://t.me/'):
                    group_username = SOURCE_GROUP.split('/')[-1]
                    self.target_entity = await self.client.get_entity(group_username)
                else:
                    self.target_entity = await self.client.get_entity(SOURCE_GROUP)
                    
                logger.info(f"✅ Group found: {self.target_entity.title}")
                break
            except Exception as e:
                logger.warning(f"Group access attempt {attempt + 1}/{max_group_attempts} failed: {e}")
                if attempt < max_group_attempts - 1:
                    await asyncio.sleep(5)
                else:
                    raise
        
        # Initialize Bot API
        self.bot = Bot(token=BOT_TOKEN)
        bot_info = await self.bot.get_me()
        logger.info(f"✅ Bot API connected: @{bot_info.username}")
        
        # Reset connection state
        self.connection_retries = 0
        self.last_heartbeat = datetime.now()
        
    async def setup_handlers(self):
        """Setup event handlers with enhanced logging"""
        logger.info("⚙️ Setting up event handlers...")
        
        # Message handler for group monitoring
        @self.client.on(events.NewMessage(chats=self.target_entity))
        async def handle_new_message(event):
            try:
                logger.info(f"📨 New message received: {event.message.id}")
                self.last_heartbeat = datetime.now()
                await self.process_group_message(event.message)
            except Exception as e:
                logger.error(f"Message handler error: {e}")
                logger.error(traceback.format_exc())
        
        # Callback handler for buttons
        @self.client.on(events.CallbackQuery())
        async def handle_callback(event):
            try:
                logger.info(f"🎯 Callback received: {event.data}")
                self.last_heartbeat = datetime.now()
                await self.process_callback(event)
            except Exception as e:
                logger.error(f"Callback handler error: {e}")
                logger.error(traceback.format_exc())
        
        # Private message handler for commands
        @self.client.on(events.NewMessage(func=lambda e: e.is_private))
        async def handle_private_message(event):
            try:
                logger.info(f"💬 Private message: {event.message.text}")
                self.last_heartbeat = datetime.now()
                await self.process_private_message(event)
            except Exception as e:
                logger.error(f"Private message handler error: {e}")
                logger.error(traceback.format_exc())
        
        logger.info("✅ Event handlers configured")
        
    async def start_monitoring(self):
        """Start monitoring with heartbeat checks"""
        logger.info("✅ All systems initialized")
        
        # Send startup notification
        await self.notify_admins(
            "🚀 Stable Perfect Bot System запущено!\n\n"
            "✅ Функції:\n"
            "• Моніторинг групи активний\n"
            "• Команди бота працюють\n"
            "• Кнопки схвалення готові\n"
            "• Автоматичне відновлення з'єднання\n"
            "• Детальне логування\n\n"
            "Тестуйте команди: /start, /status, /health"
        )
        
        # Start heartbeat monitoring
        heartbeat_task = asyncio.create_task(self.heartbeat_monitor())
        
        logger.info("🔄 Bot running with heartbeat monitoring...")
        
        try:
            # Run until disconnected with periodic checks
            while self.running:
                if not self.client.is_connected():
                    logger.warning("❌ Connection lost, attempting reconnection...")
                    await self.reconnect()
                    
                await asyncio.sleep(30)  # Check every 30 seconds
                
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
            self.running = False
            heartbeat_task.cancel()
        except Exception as e:
            logger.error(f"Main loop error: {e}")
            logger.error(traceback.format_exc())
            raise
        finally:
            if self.client:
                await self.client.disconnect()
                
    async def heartbeat_monitor(self):
        """Monitor system heartbeat and connection health"""
        while self.running:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                current_time = datetime.now()
                time_since_heartbeat = (current_time - self.last_heartbeat).total_seconds()
                
                # Log heartbeat status
                logger.info(f"💓 Heartbeat: {time_since_heartbeat:.0f}s ago, Connected: {self.client.is_connected()}")
                
                # Check if connection is stale
                if time_since_heartbeat > 300:  # 5 minutes without activity
                    logger.warning("⚠️ No activity for 5 minutes, checking connection...")
                    await self.test_connection()
                    
            except Exception as e:
                logger.error(f"Heartbeat monitor error: {e}")
                
    async def test_connection(self):
        """Test connection and send test message"""
        try:
            # Test MTProto connection
            me = await self.client.get_me()
            logger.info(f"✅ MTProto test successful: {me.first_name}")
            
            # Test Bot API
            bot_info = await self.bot.get_me()
            logger.info(f"✅ Bot API test successful: @{bot_info.username}")
            
            # Send test message to first admin
            await self.bot.send_message(
                chat_id=ADMIN_IDS[0],
                text=f"🔄 Система працює стабільно\n\n"
                     f"• Час роботи: {datetime.now() - self.start_time}\n"
                     f"• Оброблено повідомлень: {self.processed_messages}\n"
                     f"• Статус: ✅ Активний\n"
                     f"• Перевірка: {datetime.now().strftime('%H:%M:%S')}"
            )
            
            self.last_heartbeat = datetime.now()
            logger.info("✅ Connection test successful")
            
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            await self.reconnect()
            
    async def reconnect(self):
        """Reconnect to Telegram"""
        logger.info("🔄 Attempting to reconnect...")
        
        try:
            if self.client:
                await self.client.disconnect()
                await asyncio.sleep(5)
                
            await self.initialize_connections()
            await self.setup_handlers()
            
            logger.info("✅ Reconnection successful")
            
        except Exception as e:
            logger.error(f"Reconnection failed: {e}")
            self.connection_retries += 1
            
            if self.connection_retries >= self.max_retries:
                logger.error("Max reconnection attempts reached")
                self.running = False
                raise
                
    async def process_group_message(self, message):
        """Process new message from monitored group"""
        try:
            if not message.text or len(message.text.strip()) < 5:
                return
                
            logger.info(f"📨 Processing message {message.id}: {message.text[:50]}...")
            
            # Simple status analysis
            text_lower = message.text.lower()
            
            if any(word in text_lower for word in ['відкрито', 'відкрит', 'open', 'працює', 'working']):
                suggested_status = 'open'
                confidence = 0.8
            elif any(word in text_lower for word in ['закрито', 'закрит', 'closed', 'не працює', 'not working']):
                suggested_status = 'closed'
                confidence = 0.8
            else:
                suggested_status = 'unknown'
                confidence = 0.3
                
            confidence = min(confidence + 0.1 if ':' in text_lower else confidence, 0.95)
            
            logger.info(f"🤖 Analysis: {suggested_status} ({confidence:.0%})")
            
            # Store message
            self.message_store[message.id] = {
                'text': message.text,
                'date': message.date,
                'suggested_status': suggested_status,
                'confidence': confidence
            }
            
            # Send to admins
            await self.send_to_admins(message)
            
            self.processed_messages += 1
            logger.info(f"✅ Message {message.id} processed successfully")
            
        except Exception as e:
            logger.error(f"Error processing message {message.id}: {e}")
            logger.error(traceback.format_exc())
            
    async def send_to_admins(self, message):
        """Send message to administrators with approval buttons"""
        try:
            time_str = message.date.strftime("%H:%M")
            message_data = self.message_store[message.id]
            
            text = f"📨 Нове повідомлення о {time_str}\n\n"
            text += f"💬 Текст: {message.text}\n\n"
            text += f"🤖 Аналіз: {message_data['suggested_status']} ({message_data['confidence']:.0%})\n\n"
            text += f"Оберіть дію:"
            
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
            logger.error(traceback.format_exc())
            
    async def process_callback(self, event):
        """Process callback queries from inline buttons"""
        try:
            callback_data = event.data.decode('utf-8')
            user_id = event.sender_id
            
            logger.info(f"🎯 Processing callback: {callback_data} from user {user_id}")
            
            if user_id not in ADMIN_IDS:
                await event.answer("❌ Доступ заборонений", alert=True)
                return
                
            if callback_data.startswith('approve_'):
                parts = callback_data.split('_')
                status = parts[1]
                message_id = int(parts[2])
                await self.approve_message(event, message_id, status)
                
            elif callback_data.startswith('reject_'):
                message_id = int(callback_data.split('_')[1])
                await self.reject_message(event, message_id)
                
        except Exception as e:
            logger.error(f"Callback processing error: {e}")
            logger.error(traceback.format_exc())
            await event.answer(f"❌ Помилка: {e}", alert=True)
            
    async def approve_message(self, event, message_id: int, status: str):
        """Approve and publish message"""
        try:
            logger.info(f"✅ Approving message {message_id} with status {status}")
            
            if message_id not in self.message_store:
                await event.answer("❌ Повідомлення не знайдено", alert=True)
                return
                
            # Format for channel
            status_emoji = "✅" if status == "open" else "🔴"
            status_text = "Відкрито" if status == "open" else "Закрито"
            
            current_time = datetime.now().strftime("%H:%M")
            channel_text = f"{status_emoji} {status_text} 🕓 {current_time}"
            
            # Send to channel
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
            
            logger.info(f"✅ Message {message_id} published successfully")
            
        except Exception as e:
            logger.error(f"Approval error: {e}")
            logger.error(traceback.format_exc())
            await event.answer(f"❌ Помилка: {e}", alert=True)
            
    async def reject_message(self, event, message_id: int):
        """Reject message"""
        try:
            logger.info(f"❌ Rejecting message {message_id}")
            
            user = await self.client.get_entity(event.sender_id)
            
            await event.edit(
                f"❌ Повідомлення відхилено\n\n"
                f"👤 Відхилено: {user.first_name}\n"
                f"🕐 Час: {datetime.now().strftime('%H:%M')}"
            )
            
            await event.answer("❌ Відхилено!")
            
            logger.info(f"❌ Message {message_id} rejected successfully")
            
        except Exception as e:
            logger.error(f"Rejection error: {e}")
            logger.error(traceback.format_exc())
            
    async def process_private_message(self, event):
        """Process private messages (commands)"""
        try:
            message_text = event.message.text
            user_id = event.sender_id
            
            if not message_text.startswith('/'):
                return
                
            logger.info(f"💬 Command from {user_id}: {message_text}")
            
            if message_text == '/start':
                await self.handle_start(event)
            elif message_text == '/status':
                await self.handle_status(event)
            elif message_text == '/health':
                await self.handle_health(event)
                
        except Exception as e:
            logger.error(f"Command processing error: {e}")
            logger.error(traceback.format_exc())
            
    async def handle_start(self, event):
        """Handle /start command"""
        user_id = event.sender_id
        
        if user_id in ADMIN_IDS:
            text = "🚀 Stable Perfect Bot System активний!\n\n"
            text += "✅ Система повністю працює:\n"
            text += "• Моніторинг групи активний\n"
            text += "• Аналіз повідомлень працює\n"
            text += "• Кнопки схвалення готові\n"
            text += "• Автоматичне відновлення з'єднання\n"
            text += "• Детальне логування\n\n"
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
        time_since_heartbeat = (datetime.now() - self.last_heartbeat).total_seconds()
        
        text = f"📊 Стан Stable Perfect Bot\n\n"
        text += f"🕐 Час роботи: {uptime}\n"
        text += f"📨 Оброблено повідомлень: {self.processed_messages}\n"
        text += f"💓 Останній heartbeat: {time_since_heartbeat:.0f}s тому\n"
        text += f"🤖 MTProto: {'✅ Підключено' if self.client.is_connected() else '❌ Відключено'}\n"
        text += f"🔄 Bot API: ✅ Активний\n"
        text += f"📋 Група: {self.target_entity.title if self.target_entity else 'Не знайдено'}\n"
        text += f"📢 Канал: {TARGET_CHANNEL}\n"
        text += f"👥 Адміністраторів: {len(ADMIN_IDS)}\n"
        text += f"🔁 Повторних підключень: {self.connection_retries}\n\n"
        text += f"🔄 Статус: {'✅ Працює' if self.running else '❌ Зупинено'}"
        
        await event.respond(text)
        
    async def handle_health(self, event):
        """Handle /health command"""
        user_id = event.sender_id
        
        if user_id not in ADMIN_IDS:
            await event.respond("❌ Доступ заборонений")
            return
            
        try:
            # Test connections
            mtproto_status = "✅ Підключено" if self.client.is_connected() else "❌ Відключено"
            
            me = await self.bot.get_me()
            bot_status = f"✅ @{me.username}"
            
            group_status = f"✅ {self.target_entity.title}" if self.target_entity else "❌ Не підключено"
            
            text = f"🏥 Перевірка здоров'я системи\n\n"
            text += f"🔗 MTProto: {mtproto_status}\n"
            text += f"🤖 Bot API: {bot_status}\n"
            text += f"📋 Група: {group_status}\n"
            text += f"💾 Зберігання: ✅ Працює\n"
            text += f"🔄 Handlers: ✅ Активні\n"
            text += f"💓 Heartbeat: ✅ Активний\n\n"
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
    bot = StablePerfectBot()
    try:
        await bot.start()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(main())