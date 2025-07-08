#!/usr/bin/env python3
"""
Простий автоматичний моніторинг групи
"""

import asyncio
import aiohttp
import json
from telethon import TelegramClient, events
from datetime import datetime
from config import Config
from logger import setup_logger
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup

class SimpleAutoMonitor:
    def __init__(self):
        self.logger = setup_logger("simple_auto_monitor")
        self.config = Config()
        
        # API credentials
        self.api_id = 26886585
        self.api_hash = "166e3719a0d93c12bf76af43fe91425f"
        self.phone = "+380686850166"
        
        self.client = TelegramClient('session', self.api_id, self.api_hash)
        self.bot_token = self.config.bot_token
        self.running = False
        
    async def start(self):
        """Запуск моніторингу"""
        try:
            self.logger.info("Запуск простого автоматичного моніторингу...")
            
            # Підключення
            await self.client.start(phone=self.phone)
            
            if not await self.client.is_user_authorized():
                self.logger.error("Не авторизований")
                return False
                
            me = await self.client.get_me()
            self.logger.info(f"Авторизовано: {me.first_name}")
            
            # Пошук групи
            try:
                entity = await self.client.get_entity('pereizdvyshneve')
                self.logger.info(f"Знайдено групу: {entity.title}")
            except Exception as e:
                self.logger.error(f"Група не знайдена: {e}")
                return False
            
            # Налаштування обробника
            @self.client.on(events.NewMessage(chats=entity))
            async def handle_message(event):
                await self.process_message(event)
            
            # Налаштування бота для обробки callback
            self.bot = Bot(token=self.bot_token)
            
            self.running = True
            self.logger.info("Моніторинг активний з підтримкою кнопок")
            
            # Головний цикл
            while self.running:
                await asyncio.sleep(1)
                
        except Exception as e:
            self.logger.error(f"Помилка: {e}")
            return False
            
    async def process_message(self, event):
        """Обробка повідомлення"""
        try:
            message = event.message
            
            if message.from_id is None:
                return
                
            # Ігнорування ботів
            sender = await message.get_sender()
            if sender.bot:
                return
                
            self.logger.info(f"Нове повідомлення від {sender.first_name}: {message.text[:50]}...")
            
            # Аналіз тексту
            text = message.text.lower() if message.text else ""
            status = "невідомо"
            
            # Розширений аналіз ключових слів
            open_keywords = ['відкрито', 'открыто', 'доступно', 'работает', 'открыт', 'доступен', 'працює', 'відкритий']
            closed_keywords = ['закрито', 'закрыто', 'недоступно', 'не работает', 'закрыт', 'недоступен', 'не працює', 'закритий']
            
            if any(word in text for word in open_keywords):
                status = "відкрито"
            elif any(word in text for word in closed_keywords):
                status = "закрито"
            
            # Відправка до бота (відправляємо всі повідомлення для перевірки)
            await self.send_to_bot({
                'text': message.text or '[Повідомлення без тексту]',
                'sender_name': sender.first_name or 'Невідомо',
                'sender_username': sender.username or '',
                'status': status,
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            self.logger.error(f"Помилка обробки: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            
    async def send_to_bot(self, data):
        """Відправка до бота з кнопками схвалення"""
        try:
            admin_ids = self.config.admin_user_ids
            
            status_emoji = "🟢" if data['status'] == "відкрито" else "🔴" if data['status'] == "закрито" else "⚪"
            
            text = f"""
🔄 **АВТОМАТИЧНО ЗНАЙДЕНО**

👤 **Від:** {data['sender_name']} (@{data['sender_username']})
🕐 **Час:** {data['timestamp']}
🤖 **AI Аналіз:** {status_emoji} {data['status'].upper()}

📝 **Текст:**
{data['text']}

⚡ _Знайдено автоматично_
"""

            # Створюємо унікальний ID для повідомлення
            import time
            message_id = int(time.time() * 1000) % 1000000
            
            # Кнопки схвалення
            keyboard = {
                "inline_keyboard": [
                    [
                        {"text": "✅ ВІДКРИТО", "callback_data": f"approve_open_{message_id}"},
                        {"text": "❌ ЗАКРИТО", "callback_data": f"approve_closed_{message_id}"}
                    ],
                    [
                        {"text": "🗑 ВІДХИЛИТИ", "callback_data": f"reject_{message_id}"}
                    ]
                ]
            }

            # Відправка адміністраторам з кнопками
            async with aiohttp.ClientSession() as session:
                success_count = 0
                for admin_id in admin_ids:
                    try:
                        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
                        payload = {
                            'chat_id': admin_id,
                            'text': text,
                            'parse_mode': 'Markdown',
                            'reply_markup': keyboard
                        }
                        
                        async with session.post(url, json=payload) as resp:
                            if resp.status == 200:
                                self.logger.info(f"Відправлено з кнопками {admin_id}")
                                success_count += 1
                            else:
                                response_text = await resp.text()
                                self.logger.error(f"Помилка {admin_id}: {resp.status} - {response_text}")
                                
                    except Exception as e:
                        self.logger.error(f"Помилка відправки {admin_id}: {e}")
                        
                self.logger.info(f"Повідомлення з кнопками відправлено {success_count} з {len(admin_ids)} адміністраторів")
                        
        except Exception as e:
            self.logger.error(f"Помилка відправки: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            
    async def stop(self):
        """Зупинка"""
        self.running = False
        await self.client.disconnect()

async def main():
    monitor = SimpleAutoMonitor()
    try:
        await monitor.start()
    except KeyboardInterrupt:
        await monitor.stop()

if __name__ == "__main__":
    asyncio.run(main())