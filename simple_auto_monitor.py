#!/usr/bin/env python3
"""
Спрощений автоматичний моніторинг без API авторизації
Використовує webhook та інші методи для отримання повідомлень
"""

import asyncio
import aiohttp
import json
from datetime import datetime
from config import Config
from logger import setup_logger
from message_analyzer import MessageAnalyzer

class SimpleAutoMonitor:
    def __init__(self):
        self.logger = setup_logger("simple_auto")
        self.config = Config()
        self.analyzer = MessageAnalyzer()
        self.bot_token = self.config.bot_token
        self.running = False
        
    async def start(self):
        """Запуск спрощеного моніторингу"""
        self.logger.info("🚀 Запуск спрощеного автоматичного моніторингу")
        
        # Запуск веб-сервера для webhook
        await self.setup_webhook()
        
        self.running = True
        
        # Основний цикл
        while self.running:
            await asyncio.sleep(1)
            
    async def setup_webhook(self):
        """Налаштування webhook для отримання повідомлень"""
        try:
            # Інформація про webhook
            webhook_url = "https://your-replit-url.replit.app/webhook"  # Буде автоматично згенеровано
            
            url = f"https://api.telegram.org/bot{self.bot_token}/setWebhook"
            payload = {
                'url': webhook_url,
                'allowed_updates': ['message', 'callback_query']
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    result = await response.json()
                    if result.get('ok'):
                        self.logger.info("✅ Webhook налаштовано успішно")
                    else:
                        self.logger.error(f"❌ Помилка налаштування webhook: {result}")
                        
        except Exception as e:
            self.logger.error(f"Помилка налаштування webhook: {e}")
            
    async def process_forwarded_message(self, message_text, sender_info):
        """Обробка пересланого повідомлення"""
        try:
            # Аналіз повідомлення
            analysis = await self.analyzer.analyze_message(message_text)
            
            # Відправка в адмін-групу з результатами аналізу
            await self.send_to_admin_group(message_text, sender_info, analysis)
            
        except Exception as e:
            self.logger.error(f"Помилка обробки повідомлення: {e}")
            
    async def send_to_admin_group(self, text, sender_info, analysis):
        """Відправка в адмін-групу з кнопками"""
        try:
            admin_group_id = self.config.admin_group_id
            
            if not admin_group_id:
                self.logger.warning("ID адмін-групи не налаштовано")
                return
                
            # AI аналіз
            suggested_status = analysis.get('suggested_status', 'невідомо')
            confidence = analysis.get('confidence', 0)
            
            status_emoji = "🟢" if suggested_status == "відкрито" else "🔴" if suggested_status == "закрито" else "⚪"
            
            formatted_text = f"""
📨 **НОВЕ ПОВІДОМЛЕННЯ З ГРУПИ ПЕРЕЇЗДУ**

👤 **Від:** {sender_info.get('name', 'Невідомо')}
🤖 **AI Аналіз:** {status_emoji} {suggested_status.upper()} (впевненість: {confidence:.0%})

📝 **Текст:**
{text}

⚡ _Натисніть кнопку для затвердження статусу_
"""

            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            payload = {
                'chat_id': admin_group_id,
                'text': formatted_text,
                'parse_mode': 'Markdown',
                'reply_markup': {
                    'inline_keyboard': [[
                        {'text': '✅ ВІДКРИТО', 'callback_data': f'approve_open_{hash(text)}'},
                        {'text': '❌ ЗАКРИТО', 'callback_data': f'approve_closed_{hash(text)}'},
                        {'text': '🗑 ВІДХИЛИТИ', 'callback_data': f'reject_{hash(text)}'}
                    ]]
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        self.logger.info("✅ Повідомлення відправлено в адмін-групу")
                    else:
                        error_text = await response.text()
                        self.logger.error(f"❌ Помилка відправки: {error_text}")
                        
        except Exception as e:
            self.logger.error(f"Помилка відправки в адмін-групу: {e}")
            
    async def stop(self):
        """Зупинка моніторингу"""
        self.logger.info("Зупинка спрощеного моніторингу...")
        self.running = False

async def main():
    """Головна функція"""
    monitor = SimpleAutoMonitor()
    
    try:
        await monitor.start()
    except KeyboardInterrupt:
        await monitor.stop()
    except Exception as e:
        monitor.logger.critical(f"Критична помилка: {e}")

if __name__ == "__main__":
    asyncio.run(main())