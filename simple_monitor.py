#!/usr/bin/env python3
"""
Простий моніторинг групи через Bot API
Бот додається в групу як учасник і автоматично отримує повідомлення
"""
import asyncio
import json
import os
from datetime import datetime
from typing import Dict, Any

from telegram import Bot, Update
from telegram.ext import Application, MessageHandler, CallbackQueryHandler, filters

from config import Config
from message_analyzer import MessageAnalyzer
from logger import setup_logger

class SimpleMonitor:
    def __init__(self):
        self.config = Config()
        self.logger = setup_logger("simple_monitor")
        self.analyzer = MessageAnalyzer()
        self.bot = Bot(token=self.config.bot_token)
        self.application = None
        self.recent_messages = []
        
    async def start(self):
        """Запуск простого моніторингу"""
        try:
            self.logger.info("✅ Запуск простого моніторингу групи...")
            
            # Створюємо додаток
            self.application = Application.builder().token(self.config.bot_token).build()
            
            # Додаємо обробники
            self.application.add_handler(MessageHandler(
                filters.TEXT & ~filters.COMMAND, 
                self.handle_message
            ))
            self.application.add_handler(CallbackQueryHandler(self.handle_callback))
            
            # Запускаємо бота
            await self.application.initialize()
            await self.application.start()
            
            self.logger.info("✅ Бот запущено успішно")
            self.logger.info("✅ Додайте бота @Pereyizd_bot в групу https://t.me/pereizdvyshneve")
            self.logger.info("✅ Система очікує повідомлення з групи...")
            
            # Показуємо статус
            await self.show_status()
            
            # Запускаємо polling
            await self.application.updater.start_polling()
            
            # Очікуємо
            await asyncio.Event().wait()
            
        except Exception as e:
            self.logger.error(f"Помилка запуску: {e}")
            
    async def handle_message(self, update: Update, context):
        """Обробка повідомлень з групи"""
        try:
            message = update.effective_message
            chat = update.effective_chat
            
            # Перевіряємо чи це повідомлення з нашої групи
            if not self.is_target_group(chat):
                return
                
            # Отримуємо текст повідомлення
            text = message.text or message.caption or ""
            if not text:
                return
                
            self.logger.info(f"📨 Нове повідомлення ID {message.message_id}: {text[:30]}...")
            
            # Аналізуємо повідомлення
            analysis = await self.analyzer.analyze_message(text)
            self.logger.info(f"🤖 Аналіз: {analysis['status']} (упевненість: {analysis['confidence']:.0%})")
            
            # Додаємо в історію
            self.recent_messages.append({
                'id': message.message_id,
                'text': text,
                'time': datetime.now().strftime('%H:%M'),
                'analysis': analysis
            })
            
            # Залишаємо тільки останні 14 повідомлень
            if len(self.recent_messages) > 14:
                self.recent_messages = self.recent_messages[-14:]
                
            # Відправляємо адміністраторам
            await self.send_to_admin(text, analysis, message.message_id)
            
        except Exception as e:
            self.logger.error(f"Помилка обробки повідомлення: {e}")
            
    def is_target_group(self, chat):
        """Перевірка чи це цільова група"""
        target_username = "pereizdvyshneve"
        
        # Перевіряємо username
        if chat.username and chat.username.lower() == target_username.lower():
            return True
            
        # Перевіряємо title
        if chat.title and "пекельні ворота" in chat.title.lower():
            return True
            
        return False
        
    async def send_to_admin(self, message_text: str, analysis: Dict[str, Any], message_id: int):
        """Відправка повідомлення адміністраторам"""
        try:
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            
            # Створюємо контекст з останніми повідомленнями
            context_text = "\n".join([
                f"🕐 {msg['time']} - {msg['text'][:50]}..." 
                for msg in self.recent_messages[-5:]
            ])
            
            # Формуємо повідомлення
            admin_message = f"""📨 Нове повідомлення з групи:

{message_text}

🤖 Аналіз AI:
Статус: {analysis['status']}
Упевненість: {analysis['confidence']:.0%}

📋 Останні повідомлення:
{context_text}

Оберіть дію:"""
            
            # Створюємо кнопки
            keyboard = [
                [
                    InlineKeyboardButton("✅ ВІДКРИТО", callback_data=f"approve_open_{message_id}"),
                    InlineKeyboardButton("❌ ЗАКРИТО", callback_data=f"approve_closed_{message_id}")
                ],
                [
                    InlineKeyboardButton("🗑 ВІДХИЛИТИ", callback_data=f"reject_{message_id}")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Відправляємо адміністраторам
            admin_ids = self.config.admin_user_ids
            sent_count = 0
            
            for admin_id in admin_ids:
                try:
                    await self.bot.send_message(
                        chat_id=admin_id,
                        text=admin_message,
                        reply_markup=reply_markup
                    )
                    self.logger.info(f"✅ Відправлено адміністратору {admin_id}")
                    sent_count += 1
                except Exception as e:
                    self.logger.error(f"Помилка відправки адміністратору {admin_id}: {e}")
                    
            self.logger.info(f"📤 Повідомлення відправлено {sent_count} адміністраторам")
            
        except Exception as e:
            self.logger.error(f"Помилка відправки адміністраторам: {e}")
            
    async def handle_callback(self, update: Update, context):
        """Обробка натискання кнопок адміністраторів"""
        try:
            query = update.callback_query
            await query.answer()
            
            data = query.data
            self.logger.info(f"📱 Натиснуто кнопку: {data}")
            
            if data.startswith("approve_"):
                # Схвалення
                if "_open_" in data:
                    status = "відкрито"
                elif "_closed_" in data:
                    status = "закрито"
                else:
                    return
                    
                message_id = data.split("_")[-1]
                await self.publish_to_channel(status, query, message_id)
                
            elif data.startswith("reject_"):
                # Відхилення
                message_id = data.split("_")[-1]
                await self.reject_message(query, message_id)
                
        except Exception as e:
            self.logger.error(f"Помилка обробки callback: {e}")
            
    async def publish_to_channel(self, status: str, query, message_id: str):
        """Публікація статусу в канал"""
        try:
            # Формуємо статус
            status_emoji = "✅" if status == "відкрито" else "❌"
            status_text = status.upper()
            
            # Поточний час GMT+3
            current_time = datetime.now()
            time_str = current_time.strftime('%H:%M')
            
            # Формуємо повідомлення
            channel_message = f"{status_emoji} {status_text} 🕓 {time_str}"
            
            # Відправляємо в канал
            await self.bot.send_message(
                chat_id=self.config.target_channel_id,
                text=channel_message
            )
            
            # Оновлюємо повідомлення адміністратора
            await query.edit_message_text(
                text=f"✅ Опубліковано в канал:\n{channel_message}",
                reply_markup=None
            )
            
            self.logger.info(f"📢 Опубліковано в канал: {channel_message}")
            
        except Exception as e:
            self.logger.error(f"Помилка публікації в канал: {e}")
            await query.edit_message_text(
                text=f"❌ Помилка публікації: {e}",
                reply_markup=None
            )
            
    async def reject_message(self, query, message_id: str):
        """Відхилення повідомлення"""
        try:
            await query.edit_message_text(
                text="🗑 Повідомлення відхилено",
                reply_markup=None
            )
            
            self.logger.info(f"🗑 Повідомлення {message_id} відхилено")
            
        except Exception as e:
            self.logger.error(f"Помилка відхилення: {e}")
            
    async def show_status(self):
        """Показати статус системи"""
        current_time = datetime.now().strftime('%H:%M:%S')
        
        status_message = f"""
✅ Поточний процес:
Моніторинг групи через Bot API

✅ Бот @Pereyizd_bot активний
✅ Очікує повідомлення з групи https://t.me/pereizdvyshneve
✅ Адміністратори: {len(self.config.admin_user_ids)} користувачів

Обробка повідомлень:
✅ AI аналізує текст на статус "відкрито/закрито"
✅ Відправляє адміністраторам з кнопками:
  ✅ ВІДКРИТО
  ❌ ЗАКРИТО
  🗑 ВІДХИЛИТИ

Публікація в канал:
✅ Після натискання кнопки адміном
✅ Публікується в канал https://t.me/kryuvysh
✅ Формат: статус + час (GMT+3)

🟢 Система активна з {current_time}
"""
        
        self.logger.info(status_message)
        
    async def stop(self):
        """Зупинка системи"""
        try:
            if self.application:
                await self.application.stop()
                await self.application.shutdown()
            self.logger.info("✅ Система зупинена")
        except Exception as e:
            self.logger.error(f"Помилка зупинки: {e}")

async def main():
    """Головна функція"""
    monitor = SimpleMonitor()
    
    try:
        await monitor.start()
    except KeyboardInterrupt:
        print("\n⏹ Зупинка системи...")
    except Exception as e:
        print(f"❌ Помилка: {e}")
    finally:
        await monitor.stop()

if __name__ == "__main__":
    asyncio.run(main())