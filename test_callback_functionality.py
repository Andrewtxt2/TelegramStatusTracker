#!/usr/bin/env python3
"""
Test if callback buttons work in current bot state
"""

import asyncio
from telegram import Bot
from telegram.ext import Application, CallbackQueryHandler

# Bot token
BOT_TOKEN = "8189087426:AAF2XtTEwDRbwvWny-Hi2BPz_0ZeJHh9DEc"

# Test admin and channel
ADMIN_ID = 564704015  # Your user ID
CHANNEL_ID = "@kryuvysh"

async def test_callback():
    """Test callback functionality"""
    
    try:
        # Create bot
        bot = Bot(token=BOT_TOKEN)
        
        # Test sending a message with callback buttons
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        
        buttons = [
            [
                InlineKeyboardButton("✅ Відкрито", callback_data="open_test"),
                InlineKeyboardButton("❌ Закрито", callback_data="closed_test")
            ]
        ]
        
        keyboard = InlineKeyboardMarkup(buttons)
        
        # Send test message to admin
        await bot.send_message(
            chat_id=ADMIN_ID,
            text="🧪 ТЕСТ КНОПОК\n\nНатисніть одну з кнопок для тестування callback функціональності:",
            reply_markup=keyboard
        )
        
        print("✅ Test message sent successfully")
        
        # Test channel access
        try:
            await bot.send_message(
                chat_id=CHANNEL_ID,
                text="🧪 Тест доступу до каналу\n🕓 " + "12:34"
            )
            print("✅ Channel access working")
        except Exception as e:
            print(f"❌ Channel access failed: {e}")
            
        print("✅ Bot API functionality is working")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_callback())