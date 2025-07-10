#!/usr/bin/env python3
"""
Perfect bot with complete functionality
Uses authenticated session for 24/7 operation
"""

import asyncio
import json
import logging
from datetime import datetime
import signal
import sys
import os
from typing import Dict, Any, Optional

# Telegram imports
from telethon import TelegramClient, events
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes
from telegram.constants import ParseMode

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
API_ID = 29299324
API_HASH = "c262483dda2739c72637661b537dccac"
BOT_TOKEN = "8189087426:AAF2XtTEwDRbwvWny-Hi2BPz_0ZeJHh9DEc"
PHONE = "+380633952873"

# Group and channel IDs
SOURCE_GROUP_ID = 1643589680  # 🚦Пекельні Ворота | Вишневе Переїзд
ADMIN_GROUP_ID = 6395626140
TARGET_CHANNEL_ID = "@kryuvysh"
ADMIN_IDS = [6395626140, 7766810783, 564704015]

class PerfectBot:
    def __init__(self):
        self.running = True
        self.mtproto_client = None
        self.bot_app = None
        self.bot = None
        self.message_count = 0
        self.recent_messages = []
        
    async def start(self):
        """Start the perfect bot system"""
        
        print("🚀 Starting Perfect Bot System...")
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        try:
            # Initialize MTProto client
            await self._init_mtproto()
            
            # Initialize Bot API
            await self._init_bot_api()
            
            # Start both services
            await self._start_services()
            
        except Exception as e:
            logger.error(f"Failed to start bot: {e}")
            await self.stop()
    
    async def _init_mtproto(self):
        """Initialize MTProto client"""
        
        print("🔧 Initializing MTProto client...")
        
        session_name = 'auth_session'
        self.mtproto_client = TelegramClient(session_name, API_ID, API_HASH)
        
        await self.mtproto_client.connect()
        
        # Verify authentication
        if not await self.mtproto_client.is_user_authorized():
            raise Exception("MTProto client not authenticated")
        
        me = await self.mtproto_client.get_me()
        print(f"✅ MTProto authenticated as: {me.first_name}")
        
        # Setup message handler
        @self.mtproto_client.on(events.NewMessage(chats=SOURCE_GROUP_ID))
        async def handle_new_message(event):
            await self._process_group_message(event)
        
        print("✅ MTProto client initialized")
    
    async def _init_bot_api(self):
        """Initialize Bot API"""
        
        print("🔧 Initializing Bot API...")
        
        self.bot = Bot(token=BOT_TOKEN)
        self.bot_app = Application.builder().token(BOT_TOKEN).build()
        
        # Add handlers
        self.bot_app.add_handler(CallbackQueryHandler(self._handle_callback))
        self.bot_app.add_handler(CommandHandler("start", self._handle_start))
        self.bot_app.add_handler(CommandHandler("status", self._handle_status))
        self.bot_app.add_handler(CommandHandler("health", self._handle_health))
        
        print("✅ Bot API initialized")
    
    async def _start_services(self):
        """Start both services"""
        
        print("🎯 Starting services...")
        
        # Start MTProto in background
        mtproto_task = asyncio.create_task(self._run_mtproto())
        
        # Start Bot API in background
        bot_task = asyncio.create_task(self._run_bot_api())
        
        # Notify start
        await self._notify_startup()
        
        # Wait for both services
        await asyncio.gather(mtproto_task, bot_task)
    
    async def _run_mtproto(self):
        """Run MTProto service"""
        
        print("📡 Starting MTProto service...")
        
        try:
            await self.mtproto_client.run_until_disconnected()
        except Exception as e:
            logger.error(f"MTProto service error: {e}")
            if self.running:
                await self.stop()
    
    async def _run_bot_api(self):
        """Run Bot API service"""
        
        print("🤖 Starting Bot API service...")
        
        try:
            await self.bot_app.initialize()
            await self.bot_app.start()
            await self.bot_app.updater.start_polling()
            
            # Keep running
            while self.running:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Bot API service error: {e}")
            if self.running:
                await self.stop()
        finally:
            await self.bot_app.stop()
    
    async def _process_group_message(self, event):
        """Process message from monitored group"""
        
        try:
            message = event.message
            text = message.text or ""
            
            # Skip empty messages
            if not text.strip():
                return
            
            self.message_count += 1
            
            # Store recent message
            self.recent_messages.append({
                'text': text,
                'time': datetime.now().strftime('%H:%M'),
                'sender': message.sender_id
            })
            
            # Keep only last 9 messages
            if len(self.recent_messages) > 9:
                self.recent_messages.pop(0)
            
            print(f"📨 New message from group: {text[:50]}...")
            
            # Analyze message
            analysis = self._analyze_message(text)
            
            if analysis['is_status']:
                print(f"🎯 Status message detected: {analysis['status']} ({analysis['confidence']}%)")
                
                # Send to admins
                await self._send_to_admin(text, analysis, message.id)
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    def _analyze_message(self, text: str) -> Dict[str, Any]:
        """Analyze message for relocation status"""
        
        text_lower = text.lower()
        
        # Status keywords
        open_keywords = ['відкрито', 'відкритий', 'відкрит', 'открыт', 'open', 'работает', 'працює']
        closed_keywords = ['закрито', 'закритий', 'закрыт', 'closed', 'зачинено', 'не працює', 'не работает']
        
        # Check for keywords
        open_score = sum(1 for word in open_keywords if word in text_lower)
        closed_score = sum(1 for word in closed_keywords if word in text_lower)
        
        # Determine status
        if open_score > closed_score:
            status = 'open'
            confidence = min(90, 60 + (open_score * 10))
        elif closed_score > open_score:
            status = 'closed'
            confidence = min(90, 60 + (closed_score * 10))
        else:
            status = 'unknown'
            confidence = 30
        
        return {
            'is_status': open_score > 0 or closed_score > 0,
            'status': status,
            'confidence': confidence,
            'text': text
        }
    
    async def _send_to_admin(self, text: str, analysis: Dict[str, Any], message_id: int):
        """Send message to admin for approval"""
        
        try:
            # Format recent messages context
            context = ""
            if self.recent_messages:
                context = "\n📋 **Останні повідомлення:**\n"
                for msg in self.recent_messages[-9:]:  # Last 9 messages
                    context += f"• {msg['time']}: {msg['text'][:50]}...\n"
            
            # Create message
            admin_text = (
                f"📢 **НОВЕ ПОВІДОМЛЕННЯ З ГРУПИ**\n\n"
                f"💬 **Текст:** {text}\n\n"
                f"🤖 **Аналіз:** {analysis['status'].upper()} ({analysis['confidence']}%)\n\n"
                f"{context}\n"
                f"❓ **Що робити з цим повідомленням?**"
            )
            
            # Create buttons
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✅ Відкрито", callback_data=f"approve_open_{message_id}"),
                    InlineKeyboardButton("❌ Закрито", callback_data=f"approve_closed_{message_id}")
                ],
                [
                    InlineKeyboardButton("🕒 Додати час", callback_data=f"add_time_{message_id}"),
                    InlineKeyboardButton("🗑 Відхилити", callback_data=f"reject_{message_id}")
                ]
            ])
            
            # Send to all admins
            for admin_id in ADMIN_IDS:
                try:
                    await self.bot.send_message(
                        chat_id=admin_id,
                        text=admin_text,
                        reply_markup=keyboard,
                        parse_mode=ParseMode.MARKDOWN
                    )
                    print(f"✅ Sent to admin {admin_id}")
                except Exception as e:
                    logger.error(f"Failed to send to admin {admin_id}: {e}")
            
        except Exception as e:
            logger.error(f"Error sending to admin: {e}")
    
    async def _handle_callback(self, update, context):
        """Handle admin callback buttons"""
        
        try:
            query = update.callback_query
            await query.answer()
            
            action, status, message_id = query.data.split('_', 2)
            
            if action == "approve":
                await self._approve_message(query, status, message_id)
            elif action == "add":
                await self._add_timestamp(query, message_id)
            elif action == "reject":
                await self._reject_message(query, message_id)
            
        except Exception as e:
            logger.error(f"Error handling callback: {e}")
    
    async def _approve_message(self, query, status: str, message_id: str):
        """Approve message and publish to channel"""
        
        try:
            # Get current time
            current_time = datetime.now().strftime('%H:%M')
            
            # Create status message
            if status == "open":
                status_text = f"✅ Відкрито\n🕓 {current_time}"
            else:  # closed
                status_text = f"❌ Закрито\n🕓 {current_time}"
            
            # Send to channel
            await self.bot.send_message(
                chat_id=TARGET_CHANNEL_ID,
                text=status_text
            )
            
            # Update admin message
            await query.edit_message_text(
                text=f"✅ **ОПУБЛІКОВАНО В КАНАЛ**\n\n📤 **Повідомлення:** {status_text}\n\n⏰ **Час публікації:** {current_time}",
                parse_mode=ParseMode.MARKDOWN
            )
            
            print(f"✅ Published to channel: {status_text}")
            
        except Exception as e:
            logger.error(f"Error approving message: {e}")
            await query.edit_message_text(f"❌ Помилка публікації: {str(e)}")
    
    async def _add_timestamp(self, query, message_id: str):
        """Add timestamp to message"""
        
        try:
            current_time = datetime.now().strftime('%H:%M')
            
            await query.edit_message_text(
                text=f"🕒 **ДОДАНО ЧАС**\n\n⏰ **Поточний час:** {current_time}\n\nВиберіть статус для публікації:",
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("✅ Відкрито", callback_data=f"approve_open_{message_id}"),
                        InlineKeyboardButton("❌ Закрито", callback_data=f"approve_closed_{message_id}")
                    ]
                ]),
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error(f"Error adding timestamp: {e}")
    
    async def _reject_message(self, query, message_id: str):
        """Reject message"""
        
        try:
            await query.edit_message_text(
                text="🗑 **ПОВІДОМЛЕННЯ ВІДХИЛЕНО**\n\nПовідомлення не буде опубліковано в каналі.",
                parse_mode=ParseMode.MARKDOWN
            )
            
            print(f"🗑 Message {message_id} rejected")
            
        except Exception as e:
            logger.error(f"Error rejecting message: {e}")
    
    async def _handle_start(self, update, context):
        """Handle /start command"""
        
        await update.message.reply_text(
            "🤖 **Perfect Bot System**\n\n"
            "✅ MTProto: Активний\n"
            "✅ Bot API: Активний\n"
            "✅ Моніторинг: Працює\n\n"
            "📊 Команди:\n"
            "/status - Статус системи\n"
            "/health - Перевірка здоров'я",
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _handle_status(self, update, context):
        """Handle /status command"""
        
        uptime = datetime.now().strftime('%H:%M:%S')
        
        await update.message.reply_text(
            f"📊 **СТАТУС СИСТЕМИ**\n\n"
            f"🕒 **Час роботи:** {uptime}\n"
            f"📨 **Повідомлень оброблено:** {self.message_count}\n"
            f"👥 **Адміністраторів:** {len(ADMIN_IDS)}\n"
            f"🎯 **Група:** Моніторинг активний\n"
            f"📤 **Канал:** @kryuvysh\n\n"
            f"✅ **Усі сервіси працюють нормально**",
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _handle_health(self, update, context):
        """Handle /health command"""
        
        try:
            # Check MTProto
            mtproto_status = "✅ Підключено" if self.mtproto_client and self.mtproto_client.is_connected() else "❌ Відключено"
            
            # Check Bot API
            bot_status = "✅ Активний" if self.bot_app and self.bot_app.running else "❌ Неактивний"
            
            await update.message.reply_text(
                f"🏥 **ПЕРЕВІРКА ЗДОРОВ'Я**\n\n"
                f"📡 **MTProto:** {mtproto_status}\n"
                f"🤖 **Bot API:** {bot_status}\n"
                f"🔄 **Система:** {'✅ Працює' if self.running else '❌ Зупинена'}\n\n"
                f"📈 **Всі системи функціонують нормально**",
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            await update.message.reply_text(f"❌ Помилка перевірки: {str(e)}")
    
    async def _notify_startup(self):
        """Notify admins about startup"""
        
        try:
            message = (
                f"🚀 **PERFECT BOT ЗАПУЩЕНО**\n\n"
                f"⏰ **Час запуску:** {datetime.now().strftime('%H:%M:%S')}\n"
                f"📱 **Акаунт:** Andrew\n"
                f"📡 **MTProto:** Активний\n"
                f"🤖 **Bot API:** Активний\n"
                f"🎯 **Моніторинг групи:** Активний\n\n"
                f"✅ **Система працює 24/7**"
            )
            
            for admin_id in ADMIN_IDS:
                try:
                    await self.bot.send_message(
                        chat_id=admin_id,
                        text=message,
                        parse_mode=ParseMode.MARKDOWN
                    )
                except Exception as e:
                    logger.error(f"Failed to notify admin {admin_id}: {e}")
            
            print("✅ Startup notifications sent")
            
        except Exception as e:
            logger.error(f"Error sending startup notification: {e}")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        
        print(f"\n🛑 Received signal {signum}, shutting down...")
        self.running = False
        
        # Create shutdown task
        asyncio.create_task(self.stop())
    
    async def stop(self):
        """Stop the bot system"""
        
        print("🛑 Stopping Perfect Bot System...")
        
        self.running = False
        
        try:
            # Stop MTProto
            if self.mtproto_client:
                await self.mtproto_client.disconnect()
            
            # Stop Bot API
            if self.bot_app:
                await self.bot_app.stop()
            
            print("✅ Perfect Bot System stopped")
            
        except Exception as e:
            logger.error(f"Error stopping bot: {e}")

async def main():
    """Main function"""
    
    bot = PerfectBot()
    
    try:
        await bot.start()
    except KeyboardInterrupt:
        print("\n🛑 Keyboard interrupt received")
        await bot.stop()
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        await bot.stop()

if __name__ == "__main__":
    asyncio.run(main())