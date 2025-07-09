#!/usr/bin/env python3
"""
Daemon моніторинг групи що працює незалежно від браузера
Повністю автономний сервіс з власним lifecycle
"""
import asyncio
import json
import os
import sys
import time
import signal
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
from telethon import TelegramClient, events
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CallbackQueryHandler
from telegram.error import NetworkError, TimedOut, TelegramError
from config import Config

# Налаштування логування
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('daemon_monitor.log'),
        logging.StreamHandler()
    ]
)

class DaemonMonitor:
    def __init__(self):
        self.logger = logging.getLogger("daemon_monitor")
        self.config = Config()
        
        # MTProto клієнт
        mtproto_config = self.config.get('mtproto_settings', {})
        self.api_id = int(mtproto_config.get('api_id', os.getenv('TELEGRAM_API_ID', '0')))
        self.api_hash = mtproto_config.get('api_hash', os.getenv('TELEGRAM_API_HASH', ''))
        
        # Унікальне ім'я сесії для daemon
        self.session_name = 'daemon_session'
        self.client = TelegramClient(self.session_name, self.api_id, self.api_hash)
        
        # Bot для відправки
        self.bot = Bot(token=self.config.bot_token)
        
        # Callback application (окремий процес)
        self.callback_app = None
        self.callback_task = None
        
        # Стан системи
        self.running = False
        self.start_time = time.time()
        self.message_storage = {}
        self.last_message_id = 0
        self.health_check_interval = 60  # Кожну хвилину
        self.last_health_check = time.time()
        
        # Налаштування graceful shutdown
        self.shutdown_event = asyncio.Event()
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
    def _signal_handler(self, signum, frame):
        """Обробка сигналів"""
        self.logger.info(f"Отримано сигнал {signum}, ініціюємо зупинку...")
        self.shutdown_event.set()
        
    async def start(self):
        """Запуск daemon сервісу"""
        try:
            self.logger.info("🚀 Запуск daemon моніторингу...")
            
            # Перевірка залежностей
            await self._check_dependencies()
            
            # Ініціалізація MTProto
            await self._initialize_mtproto()
            
            # Запуск callback обробника
            await self._start_callback_handler()
            
            # Основний цикл
            await self._run_main_loop()
            
        except Exception as e:
            self.logger.error(f"Критична помилка daemon: {e}")
            await self._cleanup()
            raise
            
    async def _check_dependencies(self):
        """Перевірка всіх залежностей"""
        self.logger.info("Перевірка залежностей...")
        
        # Перевірка API credentials
        if not self.api_id or not self.api_hash:
            raise ValueError("Telegram API credentials не налаштовані")
            
        self.logger.info(f"API ID: {self.api_id}")
            
        # Перевірка bot token
        if not self.config.bot_token:
            raise ValueError("Bot token не налаштований")
            
        # Перевірка конфігурації
        if not self.config.admin_user_ids:
            raise ValueError("Адміністратори не налаштовані")
            
        self.logger.info("✅ Всі залежності перевірено")
        
    async def _initialize_mtproto(self):
        """Ініціалізація MTProto клієнта"""
        try:
            self.logger.info("Ініціалізація MTProto...")
            
            # Використовуємо існуючу сесію напряму
            if os.path.exists("session.session"):
                self.client = TelegramClient('session', self.api_id, self.api_hash)
                self.logger.info("Використовуємо існуючу сесію")
            
            # Підключення
            await self.client.start()
            me = await self.client.get_me()
            self.logger.info(f"✅ MTProto підключено: {me.first_name}")
            
            # Знаходження групи
            entity = await self.client.get_entity('https://t.me/pereizdvyshneve')
            self.logger.info(f"✅ Група знайдена: {entity.title}")
            
            # Налаштування обробника
            @self.client.on(events.NewMessage(chats=entity))
            async def handle_message(event):
                if not self.running:
                    return
                try:
                    await self._process_message(event)
                except Exception as e:
                    self.logger.error(f"Помилка обробки повідомлення: {e}")
                    
            self.logger.info("✅ MTProto ініціалізовано")
            
        except Exception as e:
            self.logger.error(f"Помилка ініціалізації MTProto: {e}")
            raise
            
    async def _start_callback_handler(self):
        """Запуск callback обробника в окремому процесі"""
        try:
            self.logger.info("Запуск callback обробника...")
            
            # Створення application
            self.callback_app = Application.builder().token(self.config.bot_token).build()
            self.callback_app.add_handler(CallbackQueryHandler(self._handle_callback))
            
            # Ініціалізація
            await self.callback_app.initialize()
            await self.callback_app.start()
            
            # Запуск polling в окремому task
            self.callback_task = asyncio.create_task(self._callback_polling())
            
            self.logger.info("✅ Callback обробник запущено")
            
        except Exception as e:
            self.logger.error(f"Помилка запуску callback обробника: {e}")
            raise
            
    async def _callback_polling(self):
        """Polling для callback запитів"""
        try:
            await self.callback_app.updater.start_polling(
                drop_pending_updates=True,
                allowed_updates=["callback_query"]
            )
            
            # Чекаємо на shutdown
            await self.shutdown_event.wait()
            
        except Exception as e:
            self.logger.error(f"Помилка callback polling: {e}")
        finally:
            if self.callback_app:
                await self.callback_app.updater.stop()
                await self.callback_app.stop()
                
    async def _run_main_loop(self):
        """Основний цикл daemon"""
        self.running = True
        self.logger.info("✅ Daemon активний та готовий до роботи")
        
        # Повідомлення про запуск
        await self._notify_startup()
        
        try:
            while self.running and not self.shutdown_event.is_set():
                # Health check
                current_time = time.time()
                if current_time - self.last_health_check >= self.health_check_interval:
                    await self._perform_health_check()
                    self.last_health_check = current_time
                
                # Очистка старих повідомлень
                await self._cleanup_old_messages()
                
                # Короткий sleep
                try:
                    await asyncio.wait_for(self.shutdown_event.wait(), timeout=10)
                    break
                except asyncio.TimeoutError:
                    continue
                    
        except Exception as e:
            self.logger.error(f"Помилка в основному циклі: {e}")
        finally:
            self.running = False
            await self._cleanup()
            
    async def _process_message(self, event):
        """Обробка нового повідомлення"""
        try:
            if not event.message or not event.message.text:
                return
                
            # Перевірка на дублікат
            if event.message.id <= self.last_message_id:
                return
                
            self.last_message_id = event.message.id
            message_text = event.message.text
            
            self.logger.info(f"📨 Нове повідомлення ID {event.message.id}")
            self.logger.info(f"📝 Текст: {message_text[:100]}...")
            
            # Аналіз
            analysis = self._analyze_message(message_text)
            self.logger.info(f"🤖 Аналіз: {analysis['suggested_status']} ({analysis['confidence']:.0%})")
            
            # Відправка адміністраторам
            await self._send_to_admins(message_text, analysis, event.message.id)
            
        except Exception as e:
            self.logger.error(f"Помилка обробки повідомлення: {e}")
            
    def _analyze_message(self, text):
        """Аналіз тексту повідомлення"""
        text_lower = text.lower()
        
        # Розширені ключові слова
        open_keywords = [
            'відкрито', 'відкрит', 'працює', 'відновлен', 'работает', 'open',
            'відкрили', 'запрацював', 'відновилось', 'проїзд можливий', 'дорога відкрита',
            'переїзд працює', 'шлагбаум підняти', 'можна їхати'
        ]
        
        closed_keywords = [
            'закрито', 'закрыт', 'зачинен', 'не працює', 'closed', 'заблокован',
            'закрили', 'перекрито', 'немає проїзду', 'дорога закрита', 'заблоковано',
            'переїзд закрито', 'шлагбаум опущено', 'їхати не можна'
        ]
        
        # Підрахунок збігів
        open_count = sum(1 for keyword in open_keywords if keyword in text_lower)
        closed_count = sum(1 for keyword in closed_keywords if keyword in text_lower)
        
        # Визначення статусу
        if open_count > closed_count:
            status = "відкрито"
            confidence = min(0.9, 0.6 + (open_count * 0.1))
        elif closed_count > open_count:
            status = "закрито"
            confidence = min(0.9, 0.6 + (closed_count * 0.1))
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
        
    async def _send_to_admins(self, message_text, analysis, message_id):
        """Відправка повідомлення адміністраторам"""
        try:
            # Зберігаємо повідомлення
            self.message_storage[message_id] = {
                'text': message_text,
                'analysis': analysis,
                'timestamp': datetime.now().isoformat()
            }
            
            # Клавіатура
            keyboard = [
                [
                    InlineKeyboardButton("✅ ВІДКРИТО", callback_data=f"approve_open_{message_id}"),
                    InlineKeyboardButton("❌ ЗАКРИТО", callback_data=f"approve_closed_{message_id}")
                ],
                [InlineKeyboardButton("🗑 ВІДХИЛИТИ", callback_data=f"reject_{message_id}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Повідомлення
            admin_message = f"""🔔 Нове повідомлення з групи:

📝 {message_text}

🤖 Аналіз:
• Рекомендація: {analysis['suggested_status']}
• Упевненість: {analysis['confidence']:.0%}
• Ключові слова: {analysis['open_keywords']} відкрито, {analysis['closed_keywords']} закрито

Час: {datetime.now().strftime('%H:%M:%S')}
ID: {message_id}

Оберіть дію:"""
            
            # Відправка
            sent_count = 0
            for admin_id in self.config.admin_user_ids:
                try:
                    await self.bot.send_message(
                        chat_id=admin_id,
                        text=admin_message,
                        reply_markup=reply_markup
                    )
                    sent_count += 1
                    self.logger.info(f"✅ Відправлено адміністратору {admin_id}")
                except Exception as e:
                    self.logger.warning(f"Помилка відправки адміністратору {admin_id}: {e}")
                    
            self.logger.info(f"📤 Повідомлення відправлено {sent_count}/{len(self.config.admin_user_ids)} адміністраторам")
            
        except Exception as e:
            self.logger.error(f"Помилка відправки адміністраторам: {e}")
            
    async def _handle_callback(self, update, context):
        """Обробка callback запитів"""
        try:
            query = update.callback_query
            await query.answer()
            
            callback_data = query.data
            self.logger.info(f"🔘 Callback: {callback_data}")
            
            if callback_data.startswith("approve_open_"):
                message_id = int(callback_data.split("_")[-1])
                await self._publish_to_channel("✅ Відкрито", query, message_id)
            elif callback_data.startswith("approve_closed_"):
                message_id = int(callback_data.split("_")[-1])
                await self._publish_to_channel("❌ Закрито", query, message_id)
            elif callback_data.startswith("reject_"):
                message_id = int(callback_data.split("_")[-1])
                await self._reject_message(query, message_id)
                
        except Exception as e:
            self.logger.error(f"Помилка callback: {e}")
            
    async def _publish_to_channel(self, status, query, message_id):
        """Публікація в канал"""
        try:
            # Час в GMT+3
            kiev_tz = timezone(timedelta(hours=3))
            current_time = datetime.now(kiev_tz)
            time_str = current_time.strftime("%H:%M")
            
            # Повідомлення
            message = f"{status} 🕓 {time_str}"
            
            # Публікація
            target_channel = self.config.target_channel_id
            await self.bot.send_message(chat_id=target_channel, text=message)
            
            # Підтвердження
            original_text = self.message_storage.get(message_id, {}).get('text', 'Повідомлення')
            await query.edit_message_text(
                f"✅ Опубліковано в канал:\n{message}\n\n"
                f"📝 Оригінальне повідомлення:\n{original_text[:200]}{'...' if len(original_text) > 200 else ''}"
            )
            
            self.logger.info(f"✅ Опубліковано в канал: {message}")
            
            # Видалення з пам'яті
            if message_id in self.message_storage:
                del self.message_storage[message_id]
                
        except Exception as e:
            self.logger.error(f"Помилка публікації: {e}")
            
    async def _reject_message(self, query, message_id):
        """Відхилення повідомлення"""
        try:
            original_text = self.message_storage.get(message_id, {}).get('text', 'Повідомлення')
            await query.edit_message_text(
                f"🗑 Повідомлення відхилено\n\n"
                f"📝 Відхилене повідомлення:\n{original_text[:200]}{'...' if len(original_text) > 200 else ''}"
            )
            
            self.logger.info(f"🗑 Повідомлення {message_id} відхилено")
            
            if message_id in self.message_storage:
                del self.message_storage[message_id]
                
        except Exception as e:
            self.logger.error(f"Помилка відхилення: {e}")
            
    async def _perform_health_check(self):
        """Перевірка здоров'я системи"""
        try:
            # Перевірка MTProto
            if not self.client.is_connected():
                self.logger.warning("MTProto відключився, перепідключення...")
                await self.client.connect()
                
            # Перевірка Bot API
            await self.bot.get_me()
            
            # Статистика
            uptime = time.time() - self.start_time
            self.logger.info(f"❤️ Health check OK (uptime: {uptime:.0f}s, messages: {len(self.message_storage)})")
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            
    async def _cleanup_old_messages(self):
        """Очистка старих повідомлень"""
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
                self.logger.info(f"🧹 Очищено {len(old_messages)} старих повідомлень")
                
        except Exception as e:
            self.logger.error(f"Помилка очистки: {e}")
            
    async def _notify_startup(self):
        """Повідомлення про запуск"""
        try:
            startup_message = f"""🚀 Daemon система запущена

✅ Повністю автономний режим
✅ Не залежить від браузера
✅ Моніторинг групи активний

Час запуску: {datetime.now().strftime('%H:%M:%S')}
PID: {os.getpid()}"""

            for admin_id in self.config.admin_user_ids:
                try:
                    await self.bot.send_message(chat_id=admin_id, text=startup_message)
                except Exception as e:
                    self.logger.warning(f"Не вдалося повідомити адміністратора {admin_id}: {e}")
                    
        except Exception as e:
            self.logger.error(f"Помилка повідомлення про запуск: {e}")
            
    async def _cleanup(self):
        """Очистка ресурсів"""
        try:
            self.logger.info("🧹 Очистка ресурсів...")
            
            if self.callback_task:
                self.callback_task.cancel()
                try:
                    await self.callback_task
                except asyncio.CancelledError:
                    pass
                    
            if self.callback_app:
                await self.callback_app.stop()
                
            if self.client.is_connected():
                await self.client.disconnect()
                
            self.logger.info("✅ Очистка завершена")
            
        except Exception as e:
            self.logger.error(f"Помилка очистки: {e}")

async def main():
    """Головна функція daemon"""
    daemon = DaemonMonitor()
    
    try:
        await daemon.start()
    except KeyboardInterrupt:
        print("\nПереривання користувачем...")
    except Exception as e:
        print(f"Критична помилка: {e}")
        logging.error(f"Критична помилка: {e}")
    finally:
        await daemon._cleanup()

if __name__ == "__main__":
    asyncio.run(main())