#!/usr/bin/env python3
"""
Test main.py to isolate the issue
"""

import asyncio
import logging
import os

# Setup minimal logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('test_main')

async def test_render_import():
    """Test importing render_no_auth_bot"""
    try:
        logger.info("Testing render_no_auth_bot import...")
        
        # Check environment variables
        bot_token = os.getenv('BOT_TOKEN', 'NOT_SET')
        logger.info(f"BOT_TOKEN: {bot_token[:20]}...")
        
        # Import the module
        from render_no_auth_bot import main
        logger.info("render_no_auth_bot imported successfully")
        
        # Try to run it
        logger.info("Starting render_no_auth_bot...")
        await main()
        
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_render_import())