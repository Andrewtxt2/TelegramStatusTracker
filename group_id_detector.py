#!/usr/bin/env python3
"""
Автоматичне визначення ID адмін-групи
"""

import asyncio
import json
from config import Config
from telegram import Bot
from telegram.ext import Application, MessageHandler, filters, ContextTypes

class GroupIdDetector:
    def __init__(self):
        self.config = Config()
        self.bot_token = self.config.bot_token
        self.application = None
        
    async def setup_detector(self):
        """Налаштування детектора ID групи"""
        self.application = Application.builder().token(self.bot_token).build()
        
        # Обробник для всіх повідомлень
        self.application.add_handler(MessageHandler(filters.ALL, self.handle_message))
        
        print("Детектор ID групи запущено...")
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()
        
    async def handle_message(self, update, context: ContextTypes.DEFAULT_TYPE):
        """Обробка повідомлень для визначення ID групи"""
        chat = update.effective_chat
        user = update.effective_user
        
        if chat.type in ['group', 'supergroup']:
            print(f"Знайдено групу: {chat.title}")
            print(f"ID групи: {chat.id}")
            print(f"Тип: {chat.type}")
            
            # Перевіряємо, чи це потрібна адмін-група
            admin_ids = [564704015, 6395626140, 7766810783]
            
            if user and user.id in admin_ids:
                print(f"Повідомлення від адміністратора {user.first_name} (ID: {user.id})")
                
                # Оновлюємо конфігурацію з правильним ID групи
                await self.update_config(chat.id, chat.title)
                
                # Надсилаємо підтвердження
                await update.message.reply_text(
                    f"✅ Бот налаштовано!\n"
                    f"Група: {chat.title}\n"
                    f"ID: {chat.id}\n"
                    f"Тепер бот буде надсилати повідомлення сюди для схвалення."
                )
                
    async def update_config(self, group_id, group_title):
        """Оновлення конфігурації з правильним ID групи"""
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            config_data['admin_group_id'] = group_id
            config_data['admin_group_title'] = group_title
            
            with open('config.json', 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            print(f"Конфігурацію оновлено: admin_group_id = {group_id}")
            
        except Exception as e:
            print(f"Помилка оновлення конфігурації: {e}")

async def main():
    detector = GroupIdDetector()
    await detector.setup_detector()

if __name__ == "__main__":
    asyncio.run(main())