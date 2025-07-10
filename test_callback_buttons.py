#!/usr/bin/env python3
"""
Test callback buttons functionality in web-only mode
"""

import asyncio
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup

BOT_TOKEN = "8189087426:AAF2XtTEwDRbwvWny-Hi2BPz_0ZeJHh9DEc"
ADMIN_IDS = [6395626140, 7766810783, 564704015]

async def test_callback_buttons():
    """Test callback button functionality"""
    
    bot = Bot(token=BOT_TOKEN)
    
    # Test message with callback buttons
    message = "🧪 Тест callback кнопок\n\nПеревірка роботи кнопок схвалення в web-only режимі"
    
    # Create inline keyboard
    keyboard = [
        [
            InlineKeyboardButton("✅ Схвалити", callback_data="approve_test"),
            InlineKeyboardButton("❌ Відхилити", callback_data="reject_test")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        # Send to all admins
        for admin_id in ADMIN_IDS:
            try:
                await bot.send_message(
                    chat_id=admin_id,
                    text=message,
                    reply_markup=reply_markup
                )
                print(f"✅ Test message sent to admin {admin_id}")
            except Exception as e:
                print(f"❌ Failed to send to admin {admin_id}: {e}")
                
        print("\n🎉 Test messages sent successfully!")
        print("Please check your Telegram and click the buttons to test callback functionality")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_callback_buttons())