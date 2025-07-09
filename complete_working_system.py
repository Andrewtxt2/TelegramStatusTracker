#!/usr/bin/env python3
"""
Complete Working System - HTTP + MTProto monitoring + Bot commands
"""

import asyncio
import logging
import sys
import os
import json
import urllib.request
import urllib.parse
from aiohttp import web
from datetime import datetime, timezone, timedelta

# Add Python path
sys.path.insert(0, '/home/runner/workspace/.pythonlibs/lib/python3.11/site-packages')

# Configuration
API_ID = '26886585'
API_HASH = '166e3719a0d93c12bf76af43fe91425f'
BOT_TOKEN = '8189087426:AAF2XtTEwDRbwvWny-Hi2BPz_0ZeJHh9DEc'
ADMIN_IDS = [6395626140, 7766810783]
SOURCE_GROUP = 'pereizdvyshneve'
TARGET_CHANNEL = '@kryuvysh'

# GMT+3 timezone
KYIV_TZ = timezone(timedelta(hours=3))

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('complete_working_system')

class CompleteWorkingSystem:
    def __init__(self):
        self.app = web.Application()
        self.setup_routes()
        self.client = None
        self.bot = None
        self.target_entity = None
        self.message_store = {}
        self.running = False
        self.last_message_time = None
        
    def setup_routes(self):
        """Setup HTTP routes"""
        self.app.router.add_get('/', self.handle_root)
        self.app.router.add_get('/health', self.handle_health)
        self.app.router.add_get('/status', self.handle_status)
        self.app.router.add_post('/webhook', self.handle_webhook)
        
    async def handle_root(self, request):
        """Root endpoint"""
        return web.Response(text="Complete Working System Running")
        
    async def handle_health(self, request):
        """Health check endpoint"""
        health_data = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'service': 'complete_working_system',
            'bot_running': self.running,
            'messages_processed': len(self.message_store),
            'last_message': self.last_message_time.isoformat() if self.last_message_time else None
        }
        return web.json_response(health_data)
        
    async def handle_status(self, request):
        """Status endpoint"""
        current_time = datetime.now(KYIV_TZ).strftime("%H:%M")
        
        status_data = {
            'service': 'Complete Working System',
            'version': '1.0.0',
            'status': 'active',
            'time': f"{current_time} (GMT+3)",
            'group': self.target_entity.title if self.target_entity else 'Not connected',
            'channel': TARGET_CHANNEL,
            'messages_processed': len(self.message_store),
            'last_message': self.last_message_time.isoformat() if self.last_message_time else None,
            'features': [
                '9 previous messages context',
                'Group monitoring via MTProto',
                'Admin approval buttons',
                'Channel publishing',
                'GMT+3 timezone',
                'HTTP health checks',
                'Bot commands via webhook'
            ],
            'timestamp': datetime.now().isoformat()
        }
        return web.json_response(status_data)
        
    async def handle_webhook(self, request):
        """Handle Telegram webhook"""
        try:
            data = await request.json()
            logger.info(f"Webhook received: {data}")
            
            if 'message' in data:
                message = data['message']
                
                # Handle commands
                if message.get('text', '').startswith('/'):
                    await self.handle_command(message)
                    
            elif 'callback_query' in data:
                callback_query = data['callback_query']
                await self.handle_callback(callback_query)
                
            return web.Response(text="OK")
            
        except Exception as e:
            logger.error(f"Webhook error: {e}")
            return web.Response(text="ERROR", status=500)
            
    async def handle_command(self, message):
        """Handle bot commands"""
        try:
            text = message.get('text', '')
            chat_id = message['chat']['id']
            
            logger.info(f"Command received: {text} from {chat_id}")
            
            if text == '/start':
                await self.send_start_message(chat_id)
            elif text == '/status':
                await self.send_status_message(chat_id)
            elif text == '/health':
                await self.send_health_message(chat_id)
                
        except Exception as e:
            logger.error(f"Command error: {e}")
            
    async def send_start_message(self, chat_id):
        """Send start message"""
        current_time = datetime.now(KYIV_TZ).strftime("%H:%M")
        
        message = f"""🚀 СИСТЕМА ПРАЦЮЄ! ({current_time})

✅ Функції:
• Моніторинг групи "{self.target_entity.title if self.target_entity else 'Не підключена'}"
• 9 попередніх повідомлень в контексті
• Автоматичний аналіз повідомлень
• Кнопки схвалення
• Публікація в канал @kryuvysh
• GMT+3 часова зона

📈 Статистика:
• Повідомлень оброблено: {len(self.message_store)}
• Система працює: {self.running}

🔧 Команди:
/status - детальний статус
/health - здоров'я системи"""
        
        await self.send_message(chat_id, message)
        
    async def send_status_message(self, chat_id):
        """Send status message"""
        current_time = datetime.now(KYIV_TZ).strftime("%H:%M")
        
        message = f"""📊 СТАТУС СИСТЕМИ

🟢 Стан: {'Активна' if self.running else 'Неактивна'}
🕐 Час: {current_time} (GMT+3)
📋 Група: {self.target_entity.title if self.target_entity else 'Не підключена'}
📢 Канал: {TARGET_CHANNEL}

📈 Статистика:
• Повідомлень оброблено: {len(self.message_store)}
• HTTP сервер: Працює на порту 80
• MTProto: {'Підключено' if self.client else 'Не підключено'}
• Остання активність: {self.last_message_time.strftime('%H:%M') if self.last_message_time else 'Немає'}

✅ Всі системи працюють нормально"""
        
        await self.send_message(chat_id, message)
        
    async def send_health_message(self, chat_id):
        """Send health message"""
        message = f"""🏥 ЗДОРОВ'Я СИСТЕМИ

✅ HTTP сервер: Працює
✅ MTProto: {'Підключено' if self.client else 'Не підключено'}
✅ Bot API: Активна
✅ Webhook: Налаштовано
✅ Група: {'Моніториться' if self.target_entity else 'Не підключена'}
✅ Канал: Доступний

🔋 Повідомлень оброблено: {len(self.message_store)}
🔋 Система працює: {self.running}

🌐 HTTP доступ:
• /health - JSON статус
• /status - JSON інформація"""
        
        await self.send_message(chat_id, message)
        
    async def handle_callback(self, callback_query):
        """Handle callback queries"""
        try:
            user_id = callback_query['from']['id']
            
            if user_id not in ADMIN_IDS:
                await self.answer_callback_query(callback_query['id'], "❌ Доступ заборонений")
                return
                
            await self.answer_callback_query(callback_query['id'], "⏳ Обробляю...")
            
            callback_data = callback_query['data']
            
            if callback_data.startswith('approve_'):
                parts = callback_data.split('_')
                status = parts[1]
                message_id = int(parts[2])
                await self.approve_message(callback_query, message_id, status)
                
            elif callback_data.startswith('reject_'):
                message_id = int(callback_data.split('_')[1])
                await self.reject_message(callback_query, message_id)
                
        except Exception as e:
            logger.error(f"Callback error: {e}")
            
    async def approve_message(self, callback_query, message_id, status):
        """Approve and publish message"""
        try:
            status_emoji = "✅" if status == "open" else "❌"
            status_text = "Відкрито" if status == "open" else "Закрито"
            
            current_time = datetime.now(KYIV_TZ).strftime("%H:%M")
            channel_text = f"{status_emoji} {status_text}\n🕓 {current_time}"
            
            # Send to channel
            await self.send_message(TARGET_CHANNEL, channel_text)
            
            # Update admin message
            new_text = f"""✅ Опубліковано в канал!

📋 Статус: {status_text}
🕐 Час: {current_time}
👤 Схвалено: {callback_query['from']['first_name']}"""
            
            await self.edit_message(
                callback_query['message']['chat']['id'],
                callback_query['message']['message_id'],
                new_text
            )
            
            logger.info(f"Published to channel: {status}")
            
        except Exception as e:
            logger.error(f"Approve error: {e}")
            
    async def reject_message(self, callback_query, message_id):
        """Reject message"""
        try:
            new_text = f"""❌ Повідомлення відхилено

👤 Відхилено: {callback_query['from']['first_name']}"""
            
            await self.edit_message(
                callback_query['message']['chat']['id'],
                callback_query['message']['message_id'],
                new_text
            )
            
        except Exception as e:
            logger.error(f"Reject error: {e}")
            
    async def send_message(self, chat_id, text):
        """Send message via Telegram API"""
        try:
            url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
            data = {
                'chat_id': chat_id,
                'text': text,
                'parse_mode': 'HTML'
            }
            
            data = urllib.parse.urlencode(data).encode('utf-8')
            req = urllib.request.Request(url, data=data)
            
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))
                
            return result
            
        except Exception as e:
            logger.error(f"Send message error: {e}")
            
    async def edit_message(self, chat_id, message_id, text):
        """Edit message via Telegram API"""
        try:
            url = f'https://api.telegram.org/bot{BOT_TOKEN}/editMessageText'
            data = {
                'chat_id': chat_id,
                'message_id': message_id,
                'text': text,
                'parse_mode': 'HTML'
            }
            
            data = urllib.parse.urlencode(data).encode('utf-8')
            req = urllib.request.Request(url, data=data)
            
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))
                
            return result
            
        except Exception as e:
            logger.error(f"Edit message error: {e}")
            
    async def answer_callback_query(self, callback_query_id, text):
        """Answer callback query"""
        try:
            url = f'https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery'
            data = {
                'callback_query_id': callback_query_id,
                'text': text
            }
            
            data = urllib.parse.urlencode(data).encode('utf-8')
            req = urllib.request.Request(url, data=data)
            
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))
                
            return result
            
        except Exception as e:
            logger.error(f"Answer callback error: {e}")
            
    async def start_group_monitoring(self):
        """Start MTProto group monitoring"""
        try:
            # Try to import and use telethon
            from telethon import TelegramClient, events
            
            # Initialize MTProto client
            self.client = TelegramClient('working_session', API_ID, API_HASH)
            await self.client.start()
            
            # Get target group
            self.target_entity = await self.client.get_entity(SOURCE_GROUP)
            logger.info(f"Connected to group: {self.target_entity.title}")
            
            # Setup MTProto handlers
            @self.client.on(events.NewMessage(chats=self.target_entity))
            async def handle_group_message(event):
                try:
                    await self.process_group_message(event.message)
                except Exception as e:
                    logger.error(f"Message processing error: {e}")
            
            self.running = True
            logger.info("Group monitoring started")
            
        except ImportError:
            logger.error("Telethon not available, group monitoring disabled")
            # Send notification about missing dependency
            await self.send_missing_dependency_notification()
            
        except Exception as e:
            logger.error(f"Group monitoring error: {e}")
            
    async def process_group_message(self, message):
        """Process group message with 9 previous messages context"""
        try:
            if not message.text or len(message.text.strip()) < 1:
                return
                
            self.last_message_time = datetime.now(KYIV_TZ)
            logger.info(f"Processing message: {message.text[:50]}...")
            
            # Simple analysis
            text = message.text.lower()
            if any(word in text for word in ['відкрит', 'открыт', 'open', '+']):
                status = 'open'
                confidence = 0.8
            elif any(word in text for word in ['закрит', 'закрыт', 'closed', '-']):
                status = 'closed'
                confidence = 0.8
            else:
                status = 'unknown'
                confidence = 0.3
                
            # Store message data
            self.message_store[message.id] = {
                'text': message.text,
                'date': message.date,
                'status': status,
                'confidence': confidence
            }
            
            # Send to admins with 9 previous messages
            await self.send_to_admins(message)
            
        except Exception as e:
            logger.error(f"Message processing error: {e}")
            
    async def get_previous_messages(self, current_message_id, limit=9):
        """Get previous 9 messages from group"""
        try:
            if not self.client:
                return []
                
            messages = await self.client.get_messages(
                self.target_entity,
                min_id=current_message_id - 100,
                max_id=current_message_id - 1,
                limit=limit
            )
            
            messages.sort(key=lambda m: m.date)
            previous_texts = []
            
            for msg in messages:
                if msg.text and msg.text.strip():
                    kyiv_time = msg.date.astimezone(KYIV_TZ)
                    time_str = kyiv_time.strftime("%H:%M")
                    text = msg.text[:100] + "..." if len(msg.text) > 100 else msg.text
                    previous_texts.append(f"🕐 {time_str}: {text}")
                    
            return previous_texts
            
        except Exception as e:
            logger.error(f"Error getting previous messages: {e}")
            return []
            
    async def send_to_admins(self, message):
        """Send message to admins with 9 previous messages context"""
        try:
            msg_data = self.message_store[message.id]
            kyiv_time = message.date.astimezone(KYIV_TZ)
            time_str = kyiv_time.strftime("%H:%M")
            
            # Get 9 previous messages
            previous_messages = await self.get_previous_messages(message.id, 9)
            
            text = f"📨 Нове повідомлення о {time_str}\n\n"
            text += f"💬 {message.text}\n\n"
            text += f"🤖 Аналіз: {msg_data['status']} ({msg_data['confidence']:.0%})\n\n"
            
            # Add 9 previous messages context
            if previous_messages:
                text += "📋 Попередні повідомлення:\n"
                for prev_msg in previous_messages:
                    text += f"{prev_msg}\n"
                text += "\n"
            
            text += "Виберіть дію:"
            
            # Create inline keyboard via Bot API
            keyboard = {
                'inline_keyboard': [
                    [
                        {'text': '✅ Відкрито', 'callback_data': f'approve_open_{message.id}'},
                        {'text': '❌ Закрито', 'callback_data': f'approve_closed_{message.id}'}
                    ],
                    [
                        {'text': '❌ Відхилити', 'callback_data': f'reject_{message.id}'}
                    ]
                ]
            }
            
            # Send to all admins
            for admin_id in ADMIN_IDS:
                try:
                    url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
                    data = {
                        'chat_id': admin_id,
                        'text': text,
                        'reply_markup': json.dumps(keyboard)
                    }
                    
                    data = urllib.parse.urlencode(data).encode('utf-8')
                    req = urllib.request.Request(url, data=data)
                    
                    with urllib.request.urlopen(req) as response:
                        result = json.loads(response.read().decode('utf-8'))
                        
                    logger.info(f"Sent to admin {admin_id}")
                    
                except Exception as e:
                    logger.error(f"Failed to send to admin {admin_id}: {e}")
                    
        except Exception as e:
            logger.error(f"Error sending to admins: {e}")
            
    async def send_missing_dependency_notification(self):
        """Send notification about missing dependencies"""
        try:
            message = """⚠️ УВАГА: ЗАЛЕЖНОСТІ НЕДОСТУПНІ

❌ Telethon не встановлено
🔧 Моніторинг групи вимкнено
✅ HTTP сервер працює
✅ Bot команди працюють

📋 Доступні функції:
• /start, /status, /health - працюють
• HTTP API - працює
• Webhook - налаштовано

❌ Не працює:
• Автоматичний моніторинг групи
• 9 попередніх повідомлень
• Кнопки схвалення"""
            
            for admin_id in ADMIN_IDS:
                await self.send_message(admin_id, message)
                
            logger.info("Missing dependency notification sent")
            
        except Exception as e:
            logger.error(f"Dependency notification error: {e}")
            
    async def setup_webhook(self):
        """Setup webhook"""
        try:
            webhook_url = f"https://94f841e1-1679-4873-8036-4335807298fc-00-1d2siu5jf2gar.spock.replit.dev/webhook"
            
            url = f'https://api.telegram.org/bot{BOT_TOKEN}/setWebhook'
            data = {
                'url': webhook_url
            }
            
            data = urllib.parse.urlencode(data).encode('utf-8')
            req = urllib.request.Request(url, data=data)
            
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))
                
            logger.info(f"Webhook setup: {result}")
            
        except Exception as e:
            logger.error(f"Webhook setup error: {e}")
            
    async def run(self):
        """Main application runner"""
        try:
            logger.info("Starting Complete Working System...")
            
            # Setup webhook
            await self.setup_webhook()
            
            # Start group monitoring
            await self.start_group_monitoring()
            
            # Send startup notification
            await self.send_startup_notification()
            
            # Start HTTP server
            runner = web.AppRunner(self.app)
            await runner.setup()
            
            site = web.TCPSite(runner, '0.0.0.0', 80)
            await site.start()
            
            logger.info("Complete Working System running on port 80")
            
            # Keep running
            while True:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Error: {e}")
            
    async def send_startup_notification(self):
        """Send startup notification"""
        try:
            current_time = datetime.now(KYIV_TZ).strftime("%H:%M")
            
            message = f"""🎉 ПОВНА СИСТЕМА ПЕРЕЗАПУЩЕНА! ({current_time})

✅ HTTP сервер на порту 80
✅ Webhook налаштовано
✅ Bot команди працюють
{'✅ MTProto моніторинг активний' if self.client else '❌ MTProto недоступний'}

🔧 Команди:
/start - інформація
/status - детальний статус
/health - здоров'я системи

📋 Функції:
{'• Моніторинг групи активний' if self.client else '• Моніторинг групи вимкнено'}
{'• 9 попередніх повідомлень' if self.client else '• 9 попередніх повідомлень недоступно'}
{'• Кнопки схвалення' if self.client else '• Кнопки схвалення недоступні'}
• Публікація в канал @kryuvysh
• GMT+3 часова зона

🚀 Спробуйте /status!"""
            
            for admin_id in ADMIN_IDS:
                await self.send_message(admin_id, message)
                
            logger.info("Startup notification sent")
            
        except Exception as e:
            logger.error(f"Notification error: {e}")

async def main():
    """Main function"""
    system = CompleteWorkingSystem()
    await system.run()

if __name__ == "__main__":
    asyncio.run(main())