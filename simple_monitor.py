#!/usr/bin/env python3
"""
Simple monitoring bot that works with forwarded messages
Enhanced with automatic detection and improved workflow
"""

import asyncio
import os
import sys
from config import Config
from bot_service import TelegramBotService
from logger import setup_logger
from database import DatabaseManager
from message_analyzer import MessageAnalyzer
import signal

class SimpleBotMonitor:
    def __init__(self):
        self.logger = setup_logger("simple_monitor")
        self.config = Config()
        self.bot_service = None
        self.running = False
        
    async def start(self):
        """Start the enhanced bot service"""
        try:
            self.logger.info("Starting Enhanced Telegram Bot Service...")
            
            # Initialize bot service
            self.bot_service = TelegramBotService(self.config)
            await self.bot_service.start()
            
            self.running = True
            self.logger.info("Enhanced bot service started successfully!")
            
            # Send startup notification to admin
            await self.send_startup_notification()
            
            # Keep running
            while self.running:
                await asyncio.sleep(1)
                
        except Exception as e:
            self.logger.error(f"Error starting enhanced bot service: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            
    async def send_startup_notification(self):
        """Send startup notification to admin"""
        try:
            message = """
🤖 **Бот переїзду запущений!**

✅ Система працює 24/7
✅ AI-аналіз статусу активований
✅ Автоматичне схвалення налаштовано

📝 **Як працює:**
• Перешліть повідомлення з групи переїзду
• Бот автоматично проаналізує статус
• Ви отримаєте кнопки для схвалення
• Затверджені повідомлення публікуються в канал

🔄 **Команди:**
/status - перевірити статус бота
/health - перевірити здоров'я системи

**Готовий до роботи!** 🚀
"""
            
            if self.bot_service:
                await self.bot_service.notify_admin(message)
                
        except Exception as e:
            self.logger.error(f"Error sending startup notification: {e}")
            
    async def stop(self):
        """Stop the bot service"""
        self.logger.info("Stopping enhanced bot service...")
        self.running = False
        
        if self.bot_service:
            await self.bot_service.stop()
            
        self.logger.info("Enhanced bot service stopped")
        
    def signal_handler(self, signum, frame):
        """Handle system signals"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        asyncio.create_task(self.stop())

async def main():
    """Main function"""
    monitor = SimpleBotMonitor()
    
    # Register signal handlers
    signal.signal(signal.SIGINT, monitor.signal_handler)
    signal.signal(signal.SIGTERM, monitor.signal_handler)
    
    try:
        await monitor.start()
    except KeyboardInterrupt:
        await monitor.stop()
    except Exception as e:
        monitor.logger.critical(f"Critical error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())