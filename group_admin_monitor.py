#!/usr/bin/env python3
"""
Моніторинг групи через додавання бота як адміністратора
Бот буде автоматично отримувати всі повідомлення з групи
"""

import asyncio
import os
from config import Config
from bot_service import TelegramBotService
from logger import setup_logger
from message_analyzer import MessageAnalyzer
from telegram import Update, Bot
from telegram.ext import Application, MessageHandler, filters, ContextTypes
import signal
import sys

class GroupAdminMonitor:
    def __init__(self):
        self.logger = setup_logger("group_admin_monitor")
        self.config = Config()
        self.analyzer = MessageAnalyzer()
        self.bot_token = self.config.bot_token
        self.application = None
        self.running = False
        
    async def start(self):
        """Запуск моніторингу через бота-адміністратора"""
        try:
            self.logger.info("🚀 Запуск моніторингу через бота-адміністратора")
            
            # Створення додатку
            self.application = Application.builder().token(self.bot_token).build()
            
            # Додавання обробників
            await self.setup_handlers()
            
            # Запуск polling
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()
            
            self.running = True
            self.logger.info("✅ Моніторинг групи запущено")
            
            # Відправка інструкцій адміну
            await self.send_setup_instructions()
            
            # Основний цикл
            while self.running:
                await asyncio.sleep(1)
                
        except Exception as e:
            self.logger.error(f"Помилка запуску моніторингу: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            
    async def setup_handlers(self):
        """Налаштування обробників повідомлень"""
        
        # Обробник повідомлень з групи
        async def handle_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
            await self.process_group_message(update, context)
        
        # Фільтр для групових повідомлень
        group_filter = filters.ChatType.GROUPS & ~filters.COMMAND
        
        self.application.add_handler(MessageHandler(group_filter, handle_group_message))
        self.logger.info("Обробники повідомлень налаштовано")
        
    async def process_group_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обробка повідомлення з групи"""
        try:
            message = update.message
            chat = message.chat
            
            # Перевірка, чи це наша цільова група
            if not self.is_target_group(chat):
                return
                
            # Ігнорування повідомлень від ботів
            if message.from_user.is_bot:
                return
                
            if not message.text:
                return
                
            self.logger.info(f"📨 Нове повідомлення з групи {chat.title}: {message.message_id}")
            
            # Підготовка даних повідомлення
            message_data = {
                'message_id': message.message_id,
                'chat_id': message.chat_id,
                'chat_title': chat.title,
                'user_id': message.from_user.id,
                'username': message.from_user.username or '',
                'first_name': message.from_user.first_name or '',
                'text': message.text,
                'timestamp': message.date.isoformat(),
                'source': 'group_admin_monitor'
            }
            
            # Аналіз повідомлення
            analysis = await self.analyzer.analyze_message(message.text)
            
            # Відправка в адмін-групу
            await self.send_to_admin_group(message_data, analysis)
            
        except Exception as e:
            self.logger.error(f"Помилка обробки повідомлення з групи: {e}")
            
    def is_target_group(self, chat):
        """Перевірка, чи це цільова група для моніторингу"""
        # Перевірка за назвою групи
        if chat.title and 'переїзд' in chat.title.lower():
            return True
            
        # Перевірка за username групи
        if chat.username == 'pereizdvyshneve':
            return True
            
        # Можна додати інші критерії
        return False
        
    async def send_to_admin_group(self, message_data, analysis):
        """Відправка повідомлення в адмін-групу з аналізом"""
        try:
            admin_group_id = self.config.admin_group_id
            
            if not admin_group_id:
                self.logger.warning("ID адмін-групи не налаштовано")
                return
                
            # Підготовка аналізу
            suggested_status = analysis.get('suggested_status', 'невідомо')
            confidence = analysis.get('confidence', 0)
            
            status_emoji = "🟢" if suggested_status == "відкрито" else "🔴" if suggested_status == "закрито" else "⚪"
            
            formatted_text = f"""
🔄 **АВТОМАТИЧНО ЗНАЙДЕНО В ГРУПІ**

📍 **Група:** {message_data.get('chat_title', 'Невідомо')}
👤 **Від:** {message_data.get('first_name', '')} (@{message_data.get('username', 'невідомо')})
🕐 **Час:** {message_data['timestamp']}
🆔 **ID:** {message_data['message_id']}

🤖 **AI Аналіз:** {status_emoji} {suggested_status.upper()} 
📊 **Впевненість:** {confidence:.0%}

📝 **Текст:**
{message_data['text']}

⚡ _Автоматично знайдено ботом-адміністратором групи_
"""

            # Створення inline кнопок
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            
            keyboard = [
                [
                    InlineKeyboardButton("✅ ВІДКРИТО", callback_data=f"approve_open_{message_data['message_id']}"),
                    InlineKeyboardButton("❌ ЗАКРИТО", callback_data=f"approve_closed_{message_data['message_id']}"),
                ],
                [
                    InlineKeyboardButton("🗑 ВІДХИЛИТИ", callback_data=f"reject_{message_data['message_id']}"),
                    InlineKeyboardButton("🕐 ДОДАТИ ЧАС", callback_data=f"timestamp_{message_data['message_id']}")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Відправка через bot API
            bot = Bot(token=self.bot_token)
            await bot.send_message(
                chat_id=admin_group_id,
                text=formatted_text,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
            self.logger.info("✅ Повідомлення відправлено в адмін-групу")
            
        except Exception as e:
            self.logger.error(f"Помилка відправки в адмін-групу: {e}")
            
    async def send_setup_instructions(self):
        """Відправка інструкцій по налаштуванню"""
        try:
            admin_ids = self.config.admin_user_ids
            
            if not admin_ids:
                return
                
            instructions = """
🤖 **НАЛАШТУВАННЯ АВТОМАТИЧНОГО МОНІТОРИНГУ**

Для автоматичного моніторингу групи переїзду потрібно:

1️⃣ **Додати бота до групи як адміністратора:**
   • Перейти в групу https://t.me/pereizdvyshneve
   • Додати бота @your_bot_username
   • Надати права адміністратора (читання повідомлень)

2️⃣ **Після додавання бот буде:**
   ✅ Автоматично отримувати всі повідомлення
   ✅ Аналізувати статус AI
   ✅ Відправляти в адмін-групу для схвалення
   ✅ Публікувати затверджені в канал

🔧 **Поточний стан:** Очікування додавання до групи

_Після додавання бота до групи, автоматичний моніторинг запрацює негайно!_
"""

            bot = Bot(token=self.bot_token)
            
            for admin_id in admin_ids:
                try:
                    await bot.send_message(
                        chat_id=admin_id,
                        text=instructions,
                        parse_mode='Markdown'
                    )
                except Exception as e:
                    self.logger.error(f"Помилка відправки інструкцій адміну {admin_id}: {e}")
                    
        except Exception as e:
            self.logger.error(f"Помилка відправки інструкцій: {e}")
            
    async def stop(self):
        """Зупинка моніторингу"""
        self.logger.info("Зупинка моніторингу групи...")
        self.running = False
        
        if self.application:
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()
            
        self.logger.info("Моніторинг групи зупинено")
        
    def signal_handler(self, signum, frame):
        """Обробка системних сигналів"""
        self.logger.info(f"Отримано сигнал {signum}, зупинка...")
        asyncio.create_task(self.stop())

async def main():
    """Головна функція"""
    monitor = GroupAdminMonitor()
    
    # Реєстрація обробників сигналів
    signal.signal(signal.SIGINT, monitor.signal_handler)
    signal.signal(signal.SIGTERM, monitor.signal_handler)
    
    try:
        await monitor.start()
    except KeyboardInterrupt:
        await monitor.stop()
    except Exception as e:
        monitor.logger.critical(f"Критична помилка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())