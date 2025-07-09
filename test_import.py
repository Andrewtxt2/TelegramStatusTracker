#!/usr/bin/env python3
"""
Test telegram imports
"""

try:
    from telegram.ext import Application, CallbackQueryHandler, CommandHandler
    from telegram import Bot as TelegramBot, InlineKeyboardButton, InlineKeyboardMarkup
    print("✅ python-telegram-bot imports successful")
except ImportError as e:
    print(f"❌ python-telegram-bot import error: {e}")

try:
    from telethon import TelegramClient, events
    print("✅ telethon imports successful")
except ImportError as e:
    print(f"❌ telethon import error: {e}")

try:
    from aiohttp import web
    print("✅ aiohttp imports successful")
except ImportError as e:
    print(f"❌ aiohttp import error: {e}")

print("\n🔍 Checking package versions:")
import sys
import pkg_resources

try:
    ptb_version = pkg_resources.get_distribution("python-telegram-bot").version
    print(f"python-telegram-bot: {ptb_version}")
except:
    print("python-telegram-bot: Not found")

try:
    telethon_version = pkg_resources.get_distribution("telethon").version
    print(f"telethon: {telethon_version}")
except:
    print("telethon: Not found")

try:
    aiohttp_version = pkg_resources.get_distribution("aiohttp").version
    print(f"aiohttp: {aiohttp_version}")
except:
    print("aiohttp: Not found")

try:
    telegram_version = pkg_resources.get_distribution("telegram").version
    print(f"telegram (conflict): {telegram_version}")
except:
    print("telegram (conflict): Not found - Good!")