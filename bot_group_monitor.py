#!/usr/bin/env python3
"""
Простий моніторинг групи через додавання бота як учасника
Бот автоматично обробляє повідомлення з групи після додавання
"""

import asyncio
import os
from config import Config
from logger import setup_logger
from message_analyzer import MessageAnalyzer
from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import signal
import sys

class BotGroupMonitor:
    def __init__(self):
        self.logger = setup_logger("bot_group_monitor")
        self.config = Config()
        self.analyzer = MessageAnalyzer()
        self.bot_token = self.config.bot_token
        self.application = None
        self.running = False
        
    async def start(self):
        """Запуск бота для моніторингу групи"""
        try:
            self.logger.info("Запуск бота для моніторингу групи")
            
            # Створення додатку
            self.application = Application.builder().token(self.bot_token).build()
            
            # Додавання обробників
            self.setup_handlers()
            
            # Запуск polling
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()
            
            self.running = True
            self.logger.info("Бот для моніторингу групи запущено")
            
            # Відправка інструкцій
            await self.send_instructions()
            
            # Основний цикл
            while self.running:
                await asyncio.sleep(1)
                
        except Exception as e:
            self.logger.error(f"Помилка запуску: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            
    def setup_handlers(self):
        """Налаштування обробників"""
        
        # Обробник повідомлень з груп
        async def handle_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
            await self.process_group_message(update, context)
        
        # Обробник callback кнопок
        async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
            await self.handle_admin_callback(update, context)
        
        # Фільтри для групових повідомлень
        group_filter = filters.ChatType.GROUPS & ~filters.COMMAND & filters.TEXT
        
        self.application.add_handler(MessageHandler(group_filter, handle_group_message))
        self.application.add_handler(CallbackQueryHandler(handle_callback))
        
        self.logger.info("Обробники налаштовано")
        
    async def process_group_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обробка повідомлення з групи"""
        try:
            message = update.message
            chat = message.chat
            
            # Перевірка чи це потрібна група
            if not self.is_target_group(chat):
                return
                
            # Ігнорування ботів
            if message.from_user.is_bot:
                return
                
            self.logger.info(f"Нове повідомлення з групи {chat.title}")
            
            # Аналіз повідомлення
            analysis = await self.analyzer.analyze_message(message.text)
            
            # Підготовка даних
            message_data = {
                'message_id': message.message_id,
                'chat_id': message.chat_id,
                'chat_title': chat.title,
                'user_id': message.from_user.id,
                'username': message.from_user.username or '',
                'first_name': message.from_user.first_name or '',
                'text': message.text,
                'timestamp': message.date.isoformat(),
                'analysis': analysis
            }
            
            # Відправка в адмін-групу
            await self.send_to_admin_group(message_data)
            
        except Exception as e:
            self.logger.error(f"Помилка обробки повідомлення: {e}")
            
    def is_target_group(self, chat):
        """Перевірка чи це цільова група"""
        target_keywords = ['переїзд', 'перевезення', 'евакуація']
        
        # Перевірка назви групи
        if chat.title:
            title_lower = chat.title.lower()
            if any(keyword in title_lower for keyword in target_keywords):
                return True
                
        # Перевірка username
        if hasattr(chat, 'username') and chat.username:
            if chat.username == 'pereizdvyshneve':
                return True
                
        return False
        
    async def send_to_admin_group(self, message_data):
        """Відправка в адмін-групу"""
        try:
            admin_group_id = self.config.admin_group_id
            
            if not admin_group_id:
                self.logger.warning("Адмін-група не налаштована")
                return
                
            analysis = message_data['analysis']
            suggested_status = analysis.get('suggested_status', 'невідомо')
            confidence = analysis.get('confidence', 0)
            
            status_emoji = "🟢" if suggested_status == "відкрито" else "🔴" if suggested_status == "закрито" else "⚪"
            
            text = f"""
🔄 **АВТОМАТИЧНО ЗНАЙДЕНО**

📍 **Група:** {message_data['chat_title']}
👤 **Від:** {message_data['first_name']} (@{message_data['username'] or 'невідомо'})
🕐 **Час:** {message_data['timestamp']}

🤖 **AI Аналіз:** {status_emoji} {suggested_status.upper()} ({confidence:.0%})

📝 **Текст:**
{message_data['text']}

⚡ _Автоматично знайдено ботом_
"""

            # Кнопки схвалення
            keyboard = [
                [
                    InlineKeyboardButton("✅ ВІДКРИТО", callback_data=f"approve_open_{message_data['message_id']}"),
                    InlineKeyboardButton("❌ ЗАКРИТО", callback_data=f"approve_closed_{message_data['message_id']}")
                ],
                [
                    InlineKeyboardButton("🗑 ВІДХИЛИТИ", callback_data=f"reject_{message_data['message_id']}")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Відправка
            bot = Bot(token=self.bot_token)
            await bot.send_message(
                chat_id=admin_group_id,
                text=text,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
            self.logger.info("Повідомлення відправлено в адмін-групу")
            
        except Exception as e:
            self.logger.error(f"Помилка відправки в адмін-групу: {e}")
            
    async def handle_admin_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обробка кнопок адміністратора"""
        try:
            query = update.callback_query
            await query.answer()
            
            data = query.data
            user_id = query.from_user.id
            
            # Перевірка прав адміністратора
            admin_ids = self.config.admin_user_ids
            if user_id not in admin_ids:
                await query.edit_message_text("❌ У вас немає прав адміністратора")
                return
                
            if data.startswith('approve_'):
                status = 'відкрито' if 'open' in data else 'закрито'
                await self.approve_message(query, status)
            elif data.startswith('reject_'):
                await self.reject_message(query)
                
        except Exception as e:
            self.logger.error(f"Помилка обробки callback: {e}")
            
    async def approve_message(self, query, status):
        """Схвалення повідомлення"""
        try:
            target_channel_id = self.config.target_channel_id
            
            if not target_channel_id:
                await query.edit_message_text("❌ Канал не налаштований")
                return
                
            # Отримання тексту з оригінального повідомлення
            original_text = query.message.text
            
            # Витягуємо текст повідомлення
            text_start = original_text.find('📝 **Текст:**\n') + len('📝 **Текст:**\n')
            text_end = original_text.find('\n\n⚡')
            message_text = original_text[text_start:text_end].strip()
            
            # Формуємо повідомлення для каналу
            status_emoji = "🟢" if status == "відкрито" else "🔴"
            channel_text = f"""
{status_emoji} **ПЕРЕЇЗД {status.upper()}**

{message_text}

📅 {query.message.date.strftime('%d.%m.%Y %H:%M')}
✅ Затверджено адміністратором
"""

            # Публікація в канал
            bot = Bot(token=self.bot_token)
            await bot.send_message(
                chat_id=target_channel_id,
                text=channel_text,
                parse_mode='Markdown'
            )
            
            # Оновлення повідомлення в адмін-групі
            await query.edit_message_text(
                f"✅ **ЗАТВЕРДЖЕНО: {status.upper()}**\n\nОпубліковано в канал",
                parse_mode='Markdown'
            )
            
            self.logger.info(f"Повідомлення затверджено як '{status}' та опубліковано")
            
        except Exception as e:
            self.logger.error(f"Помилка схвалення: {e}")
            await query.edit_message_text(f"❌ Помилка: {e}")
            
    async def reject_message(self, query):
        """Відхилення повідомлення"""
        try:
            await query.edit_message_text(
                "🗑 **ВІДХИЛЕНО**\n\nПовідомлення не буде опубліковано",
                parse_mode='Markdown'
            )
            self.logger.info("Повідомлення відхилено")
            
        except Exception as e:
            self.logger.error(f"Помилка відхилення: {e}")
            
    async def send_instructions(self):
        """Відправка інструкцій адміністраторам"""
        try:
            admin_ids = self.config.admin_user_ids
            
            instructions = """
🤖 **АВТОМАТИЧНИЙ МОНІТОРИНГ АКТИВОВАНО**

Для повноцінної роботи додайте бота до групи переїзду:

1️⃣ **Відкрийте групу:** https://t.me/pereizdvyshneve
2️⃣ **Додайте бота:** натисніть "Додати учасника" та знайдіть бота
3️⃣ **Готово!** Бот почне автоматично моніторити повідомлення

✅ **Після додавання бот буде:**
• Автоматично отримувати всі повідомлення з групи
• Аналізувати статус через AI
• Відправляти в цю адмін-групу для схвалення
• Публікувати затверджені в канал

🔧 **Поточний стан:** Очікування додавання до групи
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
                    self.logger.error(f"Помилка відправки інструкцій {admin_id}: {e}")
                    
        except Exception as e:
            self.logger.error(f"Помилка відправки інструкцій: {e}")
            
    async def stop(self):
        """Зупинка бота"""
        self.logger.info("Зупинка бота...")
        self.running = False
        
        if self.application:
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()
            
    def signal_handler(self, signum, frame):
        """Обробка сигналів"""
        asyncio.create_task(self.stop())

async def main():
    """Головна функція"""
    monitor = BotGroupMonitor()
    
    signal.signal(signal.SIGINT, monitor.signal_handler)
    signal.signal(signal.SIGTERM, monitor.signal_handler)
    
    try:
        await monitor.start()
    except KeyboardInterrupt:
        await monitor.stop()
    except Exception as e:
        monitor.logger.critical(f"Критична помилка: {e}")

if __name__ == "__main__":
    asyncio.run(main())