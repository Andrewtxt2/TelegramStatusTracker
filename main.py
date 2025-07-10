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
        
        logger.info("MAIN.PY: Importing stable_render_bot...")
        from stable_render_bot import main as render_main
        
        logger.info("MAIN.PY: Starting stable_render_bot...")
        import asyncio
        asyncio.run(render_main())
        
    except Exception as e:
        logger.error(f"MAIN.PY: Error in main(): {e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    main()