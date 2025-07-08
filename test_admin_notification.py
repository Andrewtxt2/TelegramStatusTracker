#!/usr/bin/env python3
"""
Test script to verify admin notification system with new admins
"""

import asyncio
from config import Config
from bot_service import TelegramBotService

async def test_admin_notifications():
    """Test sending notifications to all admins"""
    config = Config()
    bot_service = TelegramBotService(config)
    
    # Get all admin IDs
    admin_ids = config.admin_user_ids
    print(f"Configured admin IDs: {admin_ids}")
    
    # Create test message
    test_message = """
🔔 **Тест повідомлень для адміністраторів**

✅ ID адміністраторів: 564704015, 7766810783
✅ Система сповіщень працює
✅ Всі адміністратори отримають це повідомлення

🤖 Бот готовий до роботи!
"""
    
    try:
        # Send notification to all admins
        await bot_service.notify_admin(test_message)
        print("✅ Test notification sent successfully!")
        
    except Exception as e:
        print(f"❌ Error sending notification: {e}")

if __name__ == "__main__":
    asyncio.run(test_admin_notifications())