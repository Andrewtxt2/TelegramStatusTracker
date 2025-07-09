#!/usr/bin/env python3
"""
Main entry point for Render deployment
Redirects to render_no_auth_bot.py
"""

import sys
import os
import logging

# Setup logging to track what's happening
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - MAIN - %(levelname)s - %(message)s'
)
logger = logging.getLogger('main')

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Main function for Render deployment"""
    try:
        logger.info("🚀 MAIN.PY: Starting Render deployment...")

        # Check environment variables
        bot_token = os.getenv('BOT_TOKEN', 'NOT_SET')
        logger.info(f"MAIN.PY: BOT_TOKEN exists: {bot_token != 'NOT_SET'}")

        logger.info("MAIN.PY: Importing render_no_auth_bot...")
        from render_no_auth_bot import main as render_main

        logger.info("MAIN.PY: Starting render_no_auth_bot...")
        import asyncio
        import os
        import time
        from aiohttp import web, ClientSession
        from aiohttp.web import Request, Response
        import json
        import logging
        from datetime import datetime

        # Set required environment variables for deployment
        os.environ['BOT_TOKEN'] = '8189087426:AAF2XtTEwDRbwvWny-Hi2BPz_0ZeJHh9DEc'
        os.environ['TELEGRAM_API_ID'] = '26886585'
        os.environ['TELEGRAM_API_HASH'] = '166e3719a0d93c12bf76af43fe91425f'
        os.environ['ADMIN_IDS'] = '6395626140,7766810783'
        os.environ['SOURCE_GROUP'] = 'https://t.me/pereizdvyshneve'
        os.environ['TARGET_CHANNEL'] = '@kryuvysh'

        # Import your bot components
        from config import Config
        # Removed IntegratedBotRunner import - using CleanMonitor instead
        from logger import setup_logger
        asyncio.run(render_main())

    except Exception as e:
        logger.error(f"MAIN.PY: Error in main(): {e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    main()