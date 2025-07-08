#!/usr/bin/env python3
"""
Автоматичний моніторинг групи через Telethon API
Запускає сесію користувача для моніторингу групи pereizdvyshneve
"""

import asyncio
import os
import sys
from telethon import TelegramClient, events
from telethon.tl.types import Message
from datetime import datetime
import aiohttp
import json
from config import Config
from logger import setup_logger

class AutoGroupMonitor:
    def __init__(self):
        self.logger = setup_logger("auto_monitor")
        self.config = Config()
        
        # API credentials
        self.api_id = int(os.getenv('TELEGRAM_API_ID', '26886585'))
        self.api_hash = os.getenv('TELEGRAM_API_HASH', '166e3719a0d93c12bf76af43fe91425f')
        self.phone = os.getenv('TELEGRAM_PHONE', '+380686850166')
        
        if not all([self.api_id, self.api_hash, self.phone]):
            self.logger.error("Missing API credentials")
            return
            
        self.client = TelegramClient('auto_session', self.api_id, self.api_hash)
        self.bot_token = self.config.bot_token
        self.running = False
        
    async def start(self):
        """Запуск автоматичного моніторингу"""
        try:
            self.logger.info("Запуск автоматичного моніторингу групи...")
            
            # Підключення до Telegram
            await self.client.start(phone=self.phone)
            
            if not await self.client.is_user_authorized():
                self.logger.error("Користувач не авторизований")
                return False
                
            me = await self.client.get_me()
            self.logger.info(f"Авторизовано як: {me.first_name}")
            
            # Налаштування обробників подій
            await self.setup_handlers()
            
            self.running = True
            self.logger.info("Автоматичний моніторинг запущено успішно!")
            
            # Запуск моніторингу
            await self.client.run_until_disconnected()
            
        except Exception as e:
            self.logger.error(f"Помилка запуску моніторингу: {e}")
            return False
            
    async def setup_handlers(self):
        """Налаштування обробників повідомлень"""
        # Моніторинг групи pereizdvyshneve
        @self.client.on(events.NewMessage(chats=['pereizdvyshneve']))
        async def handle_group_message(event):
            await self.process_message(event)
            
        self.logger.info("Обробники повідомлень налаштовано")
        
    async def process_message(self, event):
        """Обробка нового повідомлення з групи"""
        try:
            message = event.message
            
            if not message.text:
                return
                
            self.logger.info(f"Нове повідомлення з групи: {message.id}")
            
            # Отримання інформації про відправника
            sender = await message.get_sender()
            sender_username = getattr(sender, 'username', '') or ''
            sender_name = getattr(sender, 'first_name', '') or ''
            
            # Підготовка даних повідомлення
            message_data = {
                'message_id': message.id,
                'chat_id': message.chat_id,
                'user_id': message.sender_id,
                'username': sender_username,
                'first_name': sender_name,
                'text': message.text,
                'timestamp': message.date.isoformat(),
                'source': 'auto_monitor'
            }
            
            # Відправка до бота для аналізу
            await self.send_to_bot(message_data)
            
        except Exception as e:
            self.logger.error(f"Помилка обробки повідомлення: {e}")
            
    async def send_to_bot(self, message_data):
        """Відправка повідомлення до бота для аналізу"""
        try:
            # Отримання ID адмін-групи
            admin_group_id = self.config.admin_group_id
            
            if not admin_group_id:
                self.logger.warning("ID адмін-групи не налаштовано")
                return
                
            # Форматування повідомлення для адмін-групи
            formatted_text = f"""
🆕 **АВТОМАТИЧНО ЗНАЙДЕНО ПОВІДОМЛЕННЯ**

👤 **Від:** {message_data.get('first_name', '')} (@{message_data.get('username', 'Невідомо')})
🕐 **Час:** {message_data['timestamp']}
🆔 **ID повідомлення:** {message_data['message_id']}

📝 **Текст:**
{message_data['text']}

🤖 _Автоматично знайдено через API моніторинг групи pereizdvyshneve_
"""

            # Відправка через Bot API
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            payload = {
                'chat_id': admin_group_id,
                'text': formatted_text,
                'parse_mode': 'Markdown',
                'reply_markup': {
                    'inline_keyboard': [[
                        {'text': '✅ ВІДКРИТО', 'callback_data': f'approve_open_{message_data["message_id"]}'},
                        {'text': '❌ ЗАКРИТО', 'callback_data': f'approve_closed_{message_data["message_id"]}'},
                        {'text': '🗑 ВІДХИЛИТИ', 'callback_data': f'reject_{message_data["message_id"]}'}
                    ]]
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        self.logger.info("Повідомлення відправлено в адмін-групу")
                    else:
                        error_text = await response.text()
                        self.logger.error(f"Помилка відправки в адмін-групу: {error_text}")
                        
        except Exception as e:
            self.logger.error(f"Помилка відправки до бота: {e}")
            
    async def stop(self):
        """Зупинка моніторингу"""
        self.logger.info("Зупинка автоматичного моніторингу...")
        self.running = False
        if self.client.is_connected():
            await self.client.disconnect()
        self.logger.info("Автоматичний моніторинг зупинено")

async def main():
    """Головна функція"""
    monitor = AutoGroupMonitor()
    
    try:
        await monitor.start()
    except KeyboardInterrupt:
        await monitor.stop()
    except Exception as e:
        monitor.logger.critical(f"Критична помилка: {e}")

if __name__ == "__main__":
    asyncio.run(main())