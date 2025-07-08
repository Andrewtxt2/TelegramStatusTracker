#!/usr/bin/env python3
"""Test script to check telegram bot import"""

try:
    import sys
    print(f"Python version: {sys.version}")
    print(f"Python path: {sys.path}")
    
    # Try to import telegram
    import telegram
    print(f"Telegram module path: {telegram.__file__}")
    print(f"Telegram version: {telegram.__version__}")
    
    # Try to import specific classes
    from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup
    print("Successfully imported all telegram classes!")
    
    # Test bot creation
    bot = Bot(token="test_token")
    print("Bot instance created successfully!")
    
except ImportError as e:
    print(f"Import error: {e}")
    
    # Check what's available
    import os
    site_packages = "/home/runner/workspace/.pythonlibs/lib/python3.11/site-packages"
    print(f"\nContents of {site_packages}:")
    for item in os.listdir(site_packages):
        if "telegram" in item.lower():
            print(f"  {item}")
    
except Exception as e:
    print(f"Other error: {e}")
    import traceback
    traceback.print_exc()