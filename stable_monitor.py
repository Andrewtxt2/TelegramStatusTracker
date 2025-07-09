#!/usr/bin/env python3
"""
Стабільний 24/7 моніторинг групи з автоматичним перезапуском
Працює з закритою вкладкою та автоматично відновлюється після помилок
"""
import asyncio
import json
import os
import sys
import time
import signal
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
from telethon import TelegramClient, events
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CallbackQueryHandler, Updater
from telegram.error import NetworkError, TimedOut, TelegramError
from config import Config
from logger import setup_logger

class StableMonitor:
    def __init__(self):
        self.logger = setup_logger("stable_monitor")
        self.config = Config()
        
        # MTProto клієнт для моніторингу (використовуємо існуючу сесію)
        self.api_id = int(os.getenv('TELEGRAM_API_ID', '0'))
        self.api_hash = os.getenv('TELEGRAM_API_HASH', '')
        self.client = TelegramClient('session', self.api_id, self.api_hash)
        
        # Bot для відправки повідомлень
        self.bot = Bot(token=self.config.bot_token)
        
        # Application для обробки callback
        self.application = None
        
        self.running = False
        self.start_time = time.time()
        self.message_storage = {}
        self.last_message_id = 0
        self.error_count = 0
        self.max_errors = 5
        self.restart_count = 0
        
        # Налаштування сигналів
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
    def signal_handler(self, signum, frame):
        """Обробка сигналів для graceful shutdown"""
        self.logger.info(f"Отримано сигнал {signum}, завершення роботи...")
        self.running = False
        
    async def start(self):
        """Запуск стабільного моніторингу з автоматичним перезапуском"""
        while True:
            try:
                await self.start_monitoring()
            except Exception as e:
                self.error_count += 1
                self.logger.error(f"Критична помилка #{self.error_count}: {e}")
                
                if self.error_count >= self.max_errors:
                    self.logger.critical("Досягнуто максимум помилок, повний перезапуск...")
                    self.restart_count += 1
                    self.error_count = 0
                    
                    if self.restart_count >= 3:
                        self.logger.critical("Максимум перезапусків досягнуто, вихід")
                        break
                
                # Очистка ресурсів
                await self.cleanup()
                
                # Затримка перед перезапуском
                wait_time = min(60, 10 * self.error_count)
                self.logger.info(f"Перезапуск через {wait_time} секунд...")
                await asyncio.sleep(wait_time)
                
    async def start_monitoring(self):
        """Запуск системи моніторингу"""
        try:
            self.logger.info("🚀 Запуск стабільного моніторингу...")
            
            # Ініціалізація MTProto клієнта
            await self.client.start()
            me = await self.client.get_me()
            self.logger.info(f"✅ MTProto підключено: {me.first_name}")
            
            # Знаходження групи
            try:
                entity = await self.client.get_entity('pereizdvyshneve')
                self.logger.info(f"✅ Група знайдена: {entity.title}")
            except Exception as e:
                self.logger.error(f"Помилка знаходження групи: {e}")
                # Спроба альтернативного способу
                entity = await self.client.get_entity('https://t.me/pereizdvyshneve')
                self.logger.info(f"✅ Група знайдена (альтернативний спосіб): {entity.title}")
            
            # Налаштування Bot Application для callback
            self.application = Application.builder().token(self.config.bot_token).build()
            self.application.add_handler(CallbackQueryHandler(self.handle_callback))
            
            # Ініціалізація
            await self.application.initialize()
            await self.application.start()
            
            # Запуск в фоновому режимі
            asyncio.create_task(self.start_polling_task())
            
            # Налаштування обробника нових повідомлень
            @self.client.on(events.NewMessage(chats=entity))
            async def handle_new_message(event):
                try:
                    await self.process_message(event)
                except Exception as e:
                    self.logger.error(f"Помилка обробки повідомлення: {e}")
                    
            self.running = True
            self.logger.info("✅ Стабільна система активна")
            
            # Показати статус
            await self.show_status()
            
            # Повідомити адміністраторів про запуск
            await self.notify_admins_startup()
            
            # Основний цикл з перевіркою здоров'я
            while self.running:
                try:
                    # Перевірка підключення
                    if not self.client.is_connected():
                        self.logger.warning("MTProto клієнт відключився, перепідключення...")
                        await self.client.connect()
                    
                    # Перевірка Bot API
                    await self.bot.get_me()
                    
                    # Очищення старих повідомлень з пам'яті
                    await self.cleanup_old_messages()
                    
                    await asyncio.sleep(30)  # Перевірка кожні 30 секунд
                    
                except Exception as e:
                    self.logger.error(f"Помилка в основному циклі: {e}")
                    await asyncio.sleep(10)
                    
        except Exception as e:
            self.logger.error(f"Помилка запуску моніторингу: {e}")
            raise
            
    async def start_polling_task(self):
        """Запуск polling в окремому task"""
        try:
            await self.application.updater.start_polling(
                drop_pending_updates=True,
                allowed_updates=["callback_query"]
            )
        except Exception as e:
            self.logger.error(f"Помилка polling: {e}")
            
    async def process_message(self, event):
        """Обробка нового повідомлення"""
        try:
            message_text = event.message.text
            if not message_text:
                return
                
            # Перевірка на дублікат
            if event.message.id <= self.last_message_id:
                return
                
            self.last_message_id = event.message.id
            
            self.logger.info(f"📨 Нове повідомлення ID {event.message.id}")
            
            # Аналіз повідомлення
            analysis = await self.analyze_message(message_text)
            self.logger.info(f"🤖 Аналіз: {analysis['suggested_status']} ({analysis['confidence']:.0%})")
            
            # Відправка адміністраторам
            await self.send_to_admins(message_text, analysis, event.message.id)
            
        except Exception as e:
            self.logger.error(f"Помилка обробки повідомлення: {e}")
            
    async def analyze_message(self, text):
        """Покращений аналіз тексту"""
        text_lower = text.lower()
        
        # Розширені ключові слова
        open_keywords = [
            'відкрито', 'відкрит', 'працює', 'відновлен', 'работает', 'open',
            'відкрили', 'запрацював', 'відновилось', 'проїзд можливий', 'дорога відкрита'
        ]
        
        closed_keywords = [
            'закрито', 'закрыт', 'зачинен', 'не працює', 'closed', 'заблокован',
            'закрили', 'перекрито', 'немає проїзду', 'дорога закрита', 'заблоковано'
        ]
        
        # Підрахунок збігів
        open_count = sum(1 for keyword in open_keywords if keyword in text_lower)
        closed_count = sum(1 for keyword in closed_keywords if keyword in text_lower)
        
        if open_count > closed_count:
            status = "відкрито"
            confidence = min(0.9, 0.5 + (open_count * 0.15))
        elif closed_count > open_count:
            status = "закрито"
            confidence = min(0.9, 0.5 + (closed_count * 0.15))
        else:
            status = "невизначено"
            confidence = 0.3
            
        return {
            "suggested_status": status,
            "confidence": confidence,
            "keywords_found": open_count + closed_count > 0,
            "open_keywords": open_count,
            "closed_keywords": closed_count
        }
        
    async def send_to_admins(self, message_text, analysis, message_id):
        """Відправка повідомлення адміністраторам з retry логікою"""
        try:
            # Зберігаємо повідомлення
            self.message_storage[message_id] = {
                'text': message_text,
                'analysis': analysis,
                'timestamp': datetime.now().isoformat()
            }
            
            # Створюємо клавіатуру
            keyboard = [
                [
                    InlineKeyboardButton("✅ ВІДКРИТО", callback_data=f"approve_open_{message_id}"),
                    InlineKeyboardButton("❌ ЗАКРИТО", callback_data=f"approve_closed_{message_id}")
                ],
                [InlineKeyboardButton("🗑 ВІДХИЛИТИ", callback_data=f"reject_{message_id}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Формуємо повідомлення
            admin_message = f"""🔔 Нове повідомлення з групи:

📝 {message_text}

🤖 Аналіз:
• Рекомендація: {analysis['suggested_status']}
• Упевненість: {analysis['confidence']:.0%}
• Ключові слова: {analysis['open_keywords']} відкрито, {analysis['closed_keywords']} закрито

Час: {datetime.now().strftime('%H:%M:%S')}

Оберіть дію:"""
            
            # Відправка всім адміністраторам
            admin_ids = self.config.admin_user_ids
            sent_count = 0
            
            for admin_id in admin_ids:
                for attempt in range(3):  # 3 спроби
                    try:
                        await self.bot.send_message(
                            chat_id=admin_id,
                            text=admin_message,
                            reply_markup=reply_markup
                        )
                        sent_count += 1
                        self.logger.info(f"✅ Відправлено адміністратору {admin_id}")
                        break
                    except Exception as e:
                        self.logger.warning(f"Спроба {attempt + 1} - помилка відправки адміністратору {admin_id}: {e}")
                        if attempt < 2:
                            await asyncio.sleep(2)
                            
            if sent_count == 0:
                self.logger.error("Не вдалося відправити жодному адміністратору!")
                # Спроба відправки повідомлення про помилку
                await self.notify_error("Не вдалося відправити повідомлення адміністраторам")
            else:
                self.logger.info(f"📤 Повідомлення відправлено {sent_count}/{len(admin_ids)} адміністраторам")
                    
        except Exception as e:
            self.logger.error(f"Критична помилка відправки: {e}")
            
    async def handle_callback(self, update, context):
        """Обробка callback з retry логікою"""
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
            try:
                await query.edit_message_text(f"❌ Помилка обробки: {e}")
            except:
                pass
                
    async def publish_to_channel(self, status, query, message_id):
        """Публікація в канал з retry логікою"""
        try:
            # Отримання часу в GMT+3
            kiev_tz = timezone(timedelta(hours=3))
            current_time = datetime.now(kiev_tz)
            time_str = current_time.strftime("%H:%M")
            
            # Формат: статус + час
            message = f"{status} 🕓 {time_str}"
            
            # Публікація в канал з retry
            target_channel = self.config.target_channel_id()
            
            for attempt in range(3):
                try:
                    await self.bot.send_message(chat_id=target_channel, text=message)
                    break
                except Exception as e:
                    self.logger.warning(f"Спроба {attempt + 1} публікації: {e}")
                    if attempt < 2:
                        await asyncio.sleep(2)
                    else:
                        raise
            
            # Підтвердження адміністратору
            original_text = self.message_storage.get(message_id, {}).get('text', 'Повідомлення')
            await query.edit_message_text(
                f"✅ Опубліковано в канал:\n{message}\n\n"
                f"📝 Оригінальне повідомлення:\n{original_text[:200]}{'...' if len(original_text) > 200 else ''}"
            )
            
            self.logger.info(f"✅ Опубліковано в канал: {message}")
            
            # Видаляємо з пам'яті
            if message_id in self.message_storage:
                del self.message_storage[message_id]
            
        except Exception as e:
            self.logger.error(f"Помилка публікації: {e}")
            try:
                await query.edit_message_text(f"❌ Помилка публікації: {e}")
            except:
                pass
                
    async def reject_message(self, query, message_id):
        """Відхилення повідомлення"""
        try:
            original_text = self.message_storage.get(message_id, {}).get('text', 'Повідомлення')
            await query.edit_message_text(
                f"🗑 Повідомлення відхилено\n\n"
                f"📝 Відхилене повідомлення:\n{original_text[:200]}{'...' if len(original_text) > 200 else ''}"
            )
            
            self.logger.info(f"🗑 Повідомлення {message_id} відхилено")
            
            # Видаляємо з пам'яті
            if message_id in self.message_storage:
                del self.message_storage[message_id]
                
        except Exception as e:
            self.logger.error(f"Помилка відхилення: {e}")
            
    async def cleanup_old_messages(self):
        """Очищення старих повідомлень з пам'яті"""
        try:
            current_time = datetime.now()
            old_messages = []
            
            for message_id, data in self.message_storage.items():
                message_time = datetime.fromisoformat(data['timestamp'])
                if (current_time - message_time).total_seconds() > 3600:  # 1 година
                    old_messages.append(message_id)
                    
            for message_id in old_messages:
                del self.message_storage[message_id]
                
            if old_messages:
                self.logger.info(f"Очищено {len(old_messages)} старих повідомлень")
                
        except Exception as e:
            self.logger.error(f"Помилка очищення: {e}")
            
    async def show_status(self):
        """Показати статус системи"""
        uptime = time.time() - self.start_time
        status = f"""
🟢 Стабільна система активна
⏰ Час роботи: {uptime:.0f} секунд
📊 Перезапусків: {self.restart_count}
🔄 Помилок: {self.error_count}/{self.max_errors}
💾 Повідомлень в пам'яті: {len(self.message_storage)}

✅ Моніторинг групи https://t.me/pereizdvyshneve
✅ Публікація в канал https://t.me/kryuvysh
✅ Адміністратори: {len(self.config.admin_user_ids)}

🕐 Запуск: {datetime.now().strftime('%H:%M:%S')}
"""
        self.logger.info(status)
        
    async def notify_admins_startup(self):
        """Повідомити адміністраторів про запуск"""
        try:
            startup_message = f"""🚀 Стабільна система запущена

✅ Моніторинг групи активний
✅ Автоматичне відновлення включено
✅ Працює з закритою вкладкою

Час запуску: {datetime.now().strftime('%H:%M:%S')}
Перезапуск #{self.restart_count + 1}"""

            for admin_id in self.config.admin_user_ids:
                try:
                    await self.bot.send_message(chat_id=admin_id, text=startup_message)
                except Exception as e:
                    self.logger.warning(f"Не вдалося повідомити адміністратора {admin_id}: {e}")
                    
        except Exception as e:
            self.logger.error(f"Помилка повідомлення про запуск: {e}")
            
    async def notify_error(self, error_message):
        """Повідомити адміністраторів про помилку"""
        try:
            error_notification = f"⚠️ Помилка системи:\n{error_message}\n\nЧас: {datetime.now().strftime('%H:%M:%S')}"
            
            for admin_id in self.config.admin_user_ids:
                try:
                    await self.bot.send_message(chat_id=admin_id, text=error_notification)
                except:
                    pass
                    
        except Exception as e:
            self.logger.error(f"Помилка повідомлення про помилку: {e}")
            
    async def cleanup(self):
        """Очистка ресурсів"""
        try:
            if self.application:
                await self.application.stop()
                self.application = None
                
            if self.client.is_connected():
                await self.client.disconnect()
                
            self.logger.info("Ресурси очищено")
            
        except Exception as e:
            self.logger.error(f"Помилка очистки: {e}")
            
    async def stop(self):
        """Graceful shutdown"""
        self.logger.info("Зупинка системи...")
        self.running = False
        await self.cleanup()
        self.logger.info("✅ Система зупинена")

async def main():
    """Головна функція"""
    monitor = StableMonitor()
    try:
        await monitor.start()
    except KeyboardInterrupt:
        await monitor.stop()
    except Exception as e:
        print(f"Критична помилка: {e}")
        await monitor.stop()

if __name__ == "__main__":
    asyncio.run(main())