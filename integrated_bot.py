#!/usr/bin/env python3
"""
Integrated Telegram Bot with MTProto API monitoring
Combines bot functionality with direct group monitoring
"""

import asyncio
import signal
import sys
from datetime import datetime
from telethon import TelegramClient, events
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CallbackQueryHandler, ContextTypes
import aiohttp
import json
from config import Config
from logger import setup_logger

class IntegratedBotRunner:
    def __init__(self):
        self.logger = setup_logger("integrated_bot")
        self.config = Config()
        
        # MTProto API credentials
        self.api_id = 26886585
        self.api_hash = "166e3719a0d93c12bf76af43fe91425f"
        self.phone = "+380686850166"
        
        # Telegram client for monitoring
        self.client = TelegramClient('session', self.api_id, self.api_hash)
        
        # Bot for interactions
        self.bot_token = self.config.bot_token
        self.bot = Bot(token=self.bot_token)
        
        # Bot application for handling callbacks
        self.application = None
        self.running = False
        
    async def start(self):
        """Start both bot service and Telegram client monitoring"""
        try:
            self.logger.info("Запуск інтегрованої системи...")
            
            await self.start_with_api_monitoring()
            
        except Exception as e:
            self.logger.error(f"Помилка запуску: {e}")
            await self.handle_error(e)

    async def start_with_api_monitoring(self):
        """Start system with both bot and API monitoring"""
        try:
            # Запуск Telegram client
            await self.client.start(phone=self.phone)
            
            if not await self.client.is_user_authorized():
                self.logger.error("Користувач не авторизований")
                return False
                
            me = await self.client.get_me()
            self.logger.info(f"MTProto авторизовано: {me.first_name}")
            
            # Знаходимо групу
            try:
                entity = await self.client.get_entity('pereizdvyshneve')
                self.logger.info(f"Знайдено групу: {entity.title}")
            except Exception as e:
                self.logger.error(f"Група не знайдена: {e}")
                return False
            
            # Налаштування обробника повідомлень
            @self.client.on(events.NewMessage(chats=entity))
            async def handle_message(event):
                await self.process_group_message(event)
            
            # Запуск bot application для callback
            self.application = Application.builder().token(self.bot_token).build()
            
            # Додавання обробника callback
            self.application.add_handler(CallbackQueryHandler(self.handle_admin_callback))
            
            # Запуск bot application
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()
            
            self.running = True
            self.logger.info("Інтегрована система запущена та активна")
            
            # Основний цикл
            await self.run_main_loop()
            
        except Exception as e:
            self.logger.error(f"Помилка системи: {e}")
            await self.handle_error(e)
            
    async def run_main_loop(self):
        """Keep both services running"""
        try:
            while self.running:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("Отримано сигнал зупинки")
            await self.shutdown()
            
    async def process_group_message(self, event):
        """Process message from monitored group"""
        try:
            message = event.message
            
            if message.from_id is None:
                return
                
            # Ignore bots
            sender = await message.get_sender()
            if sender.bot:
                return
                
            self.logger.info(f"Нове повідомлення від {sender.first_name}: {message.text[:50] if message.text else '[без тексту]'}...")
            
            # Analyze text
            text = message.text.lower() if message.text else ""
            status = "невідомо"
            
            # Enhanced keyword analysis
            open_keywords = ['відкрито', 'открыто', 'доступно', 'работает', 'открыт', 'доступен', 'працює', 'відкритий']
            closed_keywords = ['закрито', 'закрыто', 'недоступно', 'не работает', 'закрыт', 'недоступен', 'не працює', 'закритий']
            
            if any(word in text for word in open_keywords):
                status = "відкрито"
            elif any(word in text for word in closed_keywords):
                status = "закрито"
            
            # Send to admin group with approval buttons
            await self.send_to_admin_group({
                'original_message_id': message.id,
                'text': message.text or '[Повідомлення без тексту]',
                'sender_name': sender.first_name or 'Невідомо',
                'sender_username': sender.username or '',
                'status': status,
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            self.logger.error(f"Помилка обробки повідомлення: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            
    async def send_to_admin_group(self, message_data):
        """Send message to admin group with approval buttons"""
        try:
            admin_ids = self.config.admin_user_ids
            
            status_emoji = "🟢" if message_data['status'] == "відкрито" else "🔴" if message_data['status'] == "закрито" else "⚪"
            
            text = f"""
🔄 **АВТОМАТИЧНО ЗНАЙДЕНО**

👤 **Від:** {message_data['sender_name']} (@{message_data['sender_username']})
🕐 **Час:** {message_data['timestamp']}
🤖 **AI Аналіз:** {status_emoji} {message_data['status'].upper()}

📝 **Текст:**
{message_data['text']}

⚡ _Знайдено автоматично_
"""

            # Create unique message ID
            import time
            message_id = int(time.time() * 1000) % 1000000
            
            # Store message data for callback processing
            await self.store_message_data(message_id, message_data)
            
            # Create approval buttons
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✅ ВІДКРИТО", callback_data=f"approve_open_{message_id}"),
                    InlineKeyboardButton("❌ ЗАКРИТО", callback_data=f"approve_closed_{message_id}")
                ],
                [
                    InlineKeyboardButton("🗑 ВІДХИЛИТИ", callback_data=f"reject_{message_id}")
                ]
            ])
            
            # Send to all admins
            success_count = 0
            for admin_id in admin_ids:
                try:
                    await self.bot.send_message(
                        chat_id=admin_id,
                        text=text,
                        parse_mode='Markdown',
                        reply_markup=keyboard
                    )
                    self.logger.info(f"Відправлено з кнопками адміністратору {admin_id}")
                    success_count += 1
                except Exception as e:
                    self.logger.error(f"Помилка відправки {admin_id}: {e}")
                    
            self.logger.info(f"Повідомлення з кнопками відправлено {success_count} з {len(admin_ids)} адміністраторів")
            
        except Exception as e:
            self.logger.error(f"Помилка відправки в адмін-групу: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            
    async def store_message_data(self, message_id, message_data):
        """Store message data for callback processing"""
        try:
            # Simple file-based storage for callback data
            import json
            import os
            
            callback_dir = "callback_data"
            if not os.path.exists(callback_dir):
                os.makedirs(callback_dir)
                
            with open(f"{callback_dir}/{message_id}.json", "w", encoding="utf-8") as f:
                json.dump(message_data, f, ensure_ascii=False, indent=2)
                
            self.logger.debug(f"Збережено дані повідомлення {message_id}")
            
        except Exception as e:
            self.logger.error(f"Помилка збереження даних: {e}")
            
    async def load_message_data(self, message_id):
        """Load message data for callback processing"""
        try:
            import json
            
            with open(f"callback_data/{message_id}.json", "r", encoding="utf-8") as f:
                return json.load(f)
                
        except Exception as e:
            self.logger.error(f"Помилка завантаження даних {message_id}: {e}")
            return None
            
    async def handle_admin_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle admin button callbacks"""
        try:
            query = update.callback_query
            await query.answer()
            
            data = query.data
            user_id = query.from_user.id
            
            # Check admin permissions
            admin_ids = self.config.admin_user_ids
            if user_id not in admin_ids:
                await query.edit_message_text("❌ У вас немає прав адміністратора")
                return
                
            self.logger.info(f"Callback від адміністратора {user_id}: {data}")
            
            # Parse callback data
            parts = data.split('_')
            if len(parts) < 3:
                await query.edit_message_text("❌ Помилка даних callback")
                return
                
            action = parts[0]
            status = parts[1] if len(parts) > 2 else ""
            message_id = parts[-1]
            
            # Load original message data
            message_data = await self.load_message_data(message_id)
            if not message_data:
                await query.edit_message_text("❌ Дані повідомлення не знайдено")
                return
            
            if action == "approve":
                await self.approve_message(query, message_data, status)
            elif action == "reject":
                await self.reject_message(query, message_data)
            else:
                await query.edit_message_text("❌ Невідома дія")
                
        except Exception as e:
            self.logger.error(f"Помилка обробки callback: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            
    async def approve_message(self, query, message_data, status):
        """Approve and forward message to target channel"""
        try:
            target_channel_id = self.config.target_channel_id or "@kryuvysh"
            
            # Format message for channel with requested format
            status_emoji = "✅" if status == "open" else "❌"
            status_text = "Відкрито" if status == "open" else "Закрито"
            current_time = datetime.now().strftime('%H:%M')
            
            channel_text = f"""{status_emoji} {status_text}
🕓 {current_time}

🔗 https://t.me/pereizdvyshneve"""

            # Publish to channel
            try:
                await self.bot.send_message(
                    chat_id=target_channel_id,
                    text=channel_text.strip()
                )
                
                # Update admin message
                await query.edit_message_text(
                    f"✅ **ОПУБЛІКОВАНО: {status_text.upper()}**\n\nВідправлено в канал @kryuvysh\n🕓 {current_time}",
                    parse_mode='Markdown'
                )
                
                self.logger.info(f"Повідомлення затверджено як '{status_text}' та опубліковано о {current_time}")
                
            except Exception as e:
                error_text = str(e)
                await query.edit_message_text(f"❌ Помилка публікації: {error_text}")
                self.logger.error(f"Помилка публікації в канал: {e}")
                
        except Exception as e:
            self.logger.error(f"Помилка схвалення: {e}")
            await query.edit_message_text(f"❌ Помилка: {e}")
            
    async def reject_message(self, query, message_data):
        """Reject message"""
        try:
            await query.edit_message_text(
                "🗑 **ВІДХИЛЕНО**\n\nПовідомлення не буде опубліковано",
                parse_mode='Markdown'
            )
            self.logger.info("Повідомлення відхилено")
            
        except Exception as e:
            self.logger.error(f"Помилка відхилення: {e}")
            
    async def handle_error(self, error: Exception):
        """Handle errors with recovery mechanisms"""
        self.logger.error(f"Обробка помилки: {error}")
        
        # Try to recover
        try:
            await asyncio.sleep(5)
            if not self.running:
                return
                
            self.logger.info("Спроба відновлення...")
            await self.start()
            
        except Exception as e:
            self.logger.critical(f"Не вдалося відновити: {e}")
            
    async def shutdown(self):
        """Gracefully shutdown all services"""
        try:
            self.logger.info("Зупинка інтегрованої системи...")
            self.running = False
            
            if self.application:
                await self.application.updater.stop()
                await self.application.stop()
                await self.application.shutdown()
                
            if self.client:
                await self.client.disconnect()
                
            self.logger.info("Система зупинена")
            
        except Exception as e:
            self.logger.error(f"Помилка зупинки: {e}")
            
    def signal_handler(self, signum, frame):
        """Handle system signals for graceful shutdown"""
        asyncio.create_task(self.shutdown())

async def main():
    """Main function to run the integrated system"""
    bot_runner = IntegratedBotRunner()
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, bot_runner.signal_handler)
    signal.signal(signal.SIGTERM, bot_runner.signal_handler)
    
    try:
        await bot_runner.start()
    except KeyboardInterrupt:
        await bot_runner.shutdown()
    except Exception as e:
        bot_runner.logger.critical(f"Критична помилка: {e}")

if __name__ == "__main__":
    asyncio.run(main())