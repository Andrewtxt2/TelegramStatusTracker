#!/usr/bin/env python3
"""
Чистий моніторинг групи без конфліктів Bot API
Тільки MTProto для отримання повідомлень та Bot API для відправки
"""
import asyncio
import json
import os
import time
from datetime import datetime, timezone, timedelta
from telethon import TelegramClient, events
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CallbackQueryHandler
from config import Config
from logger import setup_logger

class CleanMonitor:
    def __init__(self):
        self.logger = setup_logger("clean_monitor")
        self.config = Config()
        
        # MTProto клієнт для моніторингу
        self.api_id = int(os.getenv('TELEGRAM_API_ID'))
        self.api_hash = os.getenv('TELEGRAM_API_HASH')
        self.client = TelegramClient('session', self.api_id, self.api_hash)
        
        # Bot для відправки повідомлень (БЕЗ polling)
        self.bot = Bot(token=self.config.bot_token)
        
        # Bot application тільки для callback обробки
        self.application = Application.builder().token(self.config.bot_token).build()
        
        self.running = False
        self.start_time = time.time()
        self.message_storage = {}  # Зберігання повідомлень для callback
        self.last_message_id = 0  # Для відстеження нових повідомлень
        
    async def start(self):
        """Запуск чистого моніторингу"""
        try:
            self.logger.info("✅ Запуск чистого моніторингу...")
            
            # Запуск MTProto клієнта
            await self.client.start()
            me = await self.client.get_me()
            self.logger.info(f"✅ MTProto підключено: {me.first_name}")
            
            # Знаходження групи
            entity = await self.client.get_entity('pereizdvyshneve')
            self.logger.info(f"✅ Група знайдена: {entity.title}")
            
            # Налаштування обробника повідомлень
            @self.client.on(events.NewMessage(chats=entity))
            async def handle_message(event):
                try:
                    await self.process_message(event)
                except Exception as e:
                    self.logger.error(f"Помилка обробки повідомлення: {e}")
            
            # Налаштування callback обробника
            self.application.add_handler(CallbackQueryHandler(self.handle_callback))
            await self.application.initialize()
            await self.application.start()
            
            self.running = True
            self.logger.info("✅ Система активна та готова до роботи")
            
            # Показати статус
            await self.show_status()
            
            # Основний цикл
            while self.running:
                await asyncio.sleep(1)
                
        except Exception as e:
            self.logger.error(f"Помилка запуску: {e}")
            raise
            
    async def process_message(self, event):
        """Обробка нового повідомлення"""
        try:
            message_text = event.message.text
            if not message_text:
                self.logger.debug("Повідомлення без тексту, пропускаємо")
                return
                
            # Перевірка чи повідомлення нове
            if event.message.id <= self.last_message_id:
                self.logger.debug(f"Повідомлення {event.message.id} вже оброблене")
                return
                
            self.last_message_id = event.message.id
            
            self.logger.info(f"📨 Нове повідомлення ID {event.message.id}: {message_text[:100]}...")
            
            # Аналіз повідомлення
            analysis = await self.analyze_message(message_text)
            self.logger.info(f"🤖 Аналіз: {analysis['suggested_status']} (упевненість: {analysis['confidence']:.0%})")
            
            # Відправка адміністраторам
            await self.send_to_admin(message_text, analysis, event.message.id)
            
        except Exception as e:
            self.logger.error(f"Помилка обробки повідомлення: {e}", exc_info=True)
            
    async def analyze_message(self, text):
        """Простий аналіз тексту"""
        text_lower = text.lower()
        
        # Ключові слова для відкрито/закрито
        open_keywords = ['відкрито', 'відкрит', 'працює', 'відновлен', 'работает', 'open']
        closed_keywords = ['закрито', 'закрыт', 'зачинен', 'не працює', 'closed']
        
        is_open = any(keyword in text_lower for keyword in open_keywords)
        is_closed = any(keyword in text_lower for keyword in closed_keywords)
        
        if is_open and not is_closed:
            status = "відкрито"
        elif is_closed and not is_open:
            status = "закрито"
        else:
            status = "невизначено"
            
        return {
            "suggested_status": status,
            "confidence": 0.8 if status != "невизначено" else 0.3,
            "keywords_found": is_open or is_closed
        }
        
    async def send_to_admin(self, message_text, analysis, message_id):
        """Відправка повідомлення адміністраторам"""
        try:
            # Зберігаємо повідомлення для callback
            self.message_storage[message_id] = {
                'text': message_text,
                'analysis': analysis,
                'timestamp': datetime.now().isoformat()
            }
            
            # Клавіатура з кнопками
            keyboard = [
                [
                    InlineKeyboardButton("✅ ВІДКРИТО", callback_data=f"approve_open_{message_id}"),
                    InlineKeyboardButton("❌ ЗАКРИТО", callback_data=f"approve_closed_{message_id}")
                ],
                [InlineKeyboardButton("🗑 ВІДХИЛИТИ", callback_data=f"reject_{message_id}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Формат повідомлення
            admin_message = f"""🔔 Нове повідомлення з групи:

📝 Текст: {message_text}

🤖 Аналіз:
Рекомендований статус: {analysis['suggested_status']}
Упевненість: {analysis['confidence']:.0%}

Оберіть дію:"""
            
            # Відправка адміністраторам
            admin_ids = self.config.admin_user_ids
            sent_count = 0
            
            for admin_id in admin_ids:
                try:
                    await self.bot.send_message(
                        chat_id=admin_id,
                        text=admin_message,
                        reply_markup=reply_markup
                    )
                    sent_count += 1
                    self.logger.info(f"✅ Відправлено адміністратору {admin_id}")
                except Exception as e:
                    self.logger.error(f"Помилка відправки адміністратору {admin_id}: {e}")
                    
            if sent_count == 0:
                self.logger.error("Не вдалося відправити жодному адміністратору!")
            else:
                self.logger.info(f"📤 Повідомлення відправлено {sent_count} адміністраторам")
                    
        except Exception as e:
            self.logger.error(f"Помилка відправки адміністраторам: {e}")
            
    async def show_status(self):
        """Показати статус системи"""
        status = f"""
✅ Поточний процес:
Моніторинг групи https://t.me/pereizdvyshneve

✅ MTProto клієнт успішно підключений
✅ Група знайдена: "🚦Пекельні Ворота | Вишневе Переїзд"
✅ Автоматично отримує всі нові повідомлення

Обробка повідомлень:
✅ AI аналізує текст на статус "відкрито/закрито"
✅ Відправляє в @Pereyizd_bot адміністраторам з кнопками:
  ✅ ВІДКРИТО
  ❌ ЗАКРИТО
  🗑 ВІДХИЛИТИ

Публікація в канал:
✅ Після натискання кнопки адміном
✅ Публікується в канал https://t.me/kryuvysh
✅ Формат: статус + час (GMT+3)

🟢 Система активна з {datetime.now().strftime('%H:%M:%S')}
"""
        self.logger.info(status)
        
    async def handle_callback(self, update, context):
        """Обробка натискання кнопок адміністраторів"""
        try:
            query = update.callback_query
            callback_data = query.data
            
            # Відповідь на callback
            await query.answer()
            
            # Парсинг callback data
            if callback_data.startswith("approve_open_"):
                message_id = int(callback_data.split("_")[-1])
                await self.publish_to_channel("✅ Відкрито", query, message_id)
            elif callback_data.startswith("approve_closed_"):
                message_id = int(callback_data.split("_")[-1])
                await self.publish_to_channel("❌ Закрито", query, message_id)
            elif callback_data.startswith("reject_"):
                message_id = int(callback_data.split("_")[-1])
                await self.reject_message(query, message_id)
            
        except Exception as e:
            self.logger.error(f"Помилка обробки callback: {e}")
            
    async def publish_to_channel(self, status, query, message_id):
        """Публікація статусу в канал"""
        try:
            # Отримання поточного часу в GMT+3
            kiev_tz = timezone(timedelta(hours=3))
            current_time = datetime.now(kiev_tz)
            time_str = current_time.strftime("%H:%M")
            
            # Формат повідомлення: статус + час
            message = f"{status} 🕓 {time_str}"
            
            # Відправка в канал
            target_channel = self.config.target_channel_id()
            await self.bot.send_message(chat_id=target_channel, text=message)
            
            # Підтвердження адміністратору
            original_text = self.message_storage.get(message_id, {}).get('text', 'Повідомлення')
            await query.edit_message_text(f"✅ Опубліковано в канал:\n{message}\n\n📝 Оригінальне повідомлення:\n{original_text[:200]}{'...' if len(original_text) > 200 else ''}")
            
            self.logger.info(f"✅ Опубліковано в канал: {message}")
            
            # Видаляємо з пам'яті
            if message_id in self.message_storage:
                del self.message_storage[message_id]
            
        except Exception as e:
            self.logger.error(f"Помилка публікації: {e}")
            await query.edit_message_text(f"❌ Помилка публікації: {e}")
            
    async def reject_message(self, query, message_id):
        """Відхилення повідомлення"""
        try:
            original_text = self.message_storage.get(message_id, {}).get('text', 'Повідомлення')
            await query.edit_message_text(f"🗑 Повідомлення відхилено\n\n📝 Відхилене повідомлення:\n{original_text[:200]}{'...' if len(original_text) > 200 else ''}")
            self.logger.info(f"🗑 Повідомлення {message_id} відхилено адміністратором")
            
            # Видаляємо з пам'яті
            if message_id in self.message_storage:
                del self.message_storage[message_id]
                
        except Exception as e:
            self.logger.error(f"Помилка відхилення: {e}")
            
    async def stop(self):
        """Зупинка системи"""
        self.running = False
        if self.client.is_connected():
            await self.client.disconnect()
        if self.application:
            await self.application.stop()
        self.logger.info("✅ Система зупинена")

async def main():
    """Головна функція"""
    monitor = CleanMonitor()
    try:
        await monitor.start()
    except KeyboardInterrupt:
        await monitor.stop()
    except Exception as e:
        print(f"Помилка: {e}")
        await monitor.stop()

if __name__ == "__main__":
    asyncio.run(main())