#!/usr/bin/env python3
"""
Main entry point for the 24/7 Telegram Bot Service
Handles continuous monitoring and management of relocation status messages
"""

import asyncio
import sys
import signal
import os
from typing import Optional
from bot_service import TelegramBotService
from recovery_manager import RecoveryManager
from logger import setup_logger
from config import Config

class BotRunner:
    def __init__(self):
        self.logger = setup_logger()
        self.config = Config()
        self.bot_service: Optional[TelegramBotService] = None
        self.recovery_manager = RecoveryManager()
        self.running = False
        
    async def start_bot(self):
        """Initialize and start the bot service"""
        try:
            self.logger.info("Starting 24/7 Telegram Bot Service...")
            
            # Initialize bot service
            self.bot_service = TelegramBotService(self.config)
            
            # Start the bot
            await self.bot_service.start()
            self.running = True
            
            self.logger.info("Bot service started successfully")
            
            # Keep the service running
            while self.running:
                await asyncio.sleep(1)
                
        except Exception as e:
            self.logger.error(f"Error starting bot service: {e}")
            await self.handle_error(e)
            
    async def handle_error(self, error: Exception):
        """Handle errors with recovery mechanisms"""
        self.logger.error(f"Handling error: {error}")
        
        # Check if recovery is possible
        if self.recovery_manager.can_recover():
            self.logger.info("Attempting recovery...")
            await self.recovery_manager.recover()
            
            # Restart bot service
            if self.bot_service:
                await self.bot_service.stop()
            
            await asyncio.sleep(5)  # Wait before restart
            await self.start_bot()
        else:
            self.logger.critical("Recovery failed. Manual intervention required.")
            sys.exit(1)
            
    async def shutdown(self):
        """Gracefully shutdown the bot service"""
        self.logger.info("Shutting down bot service...")
        self.running = False
        
        if self.bot_service:
            await self.bot_service.stop()
            
        self.logger.info("Bot service shutdown complete")
        
    def signal_handler(self, signum, frame):
        """Handle system signals for graceful shutdown"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        asyncio.create_task(self.shutdown())

async def main():
    """Main function to run the bot service"""
    runner = BotRunner()
    
    # Register signal handlers
    signal.signal(signal.SIGINT, runner.signal_handler)
    signal.signal(signal.SIGTERM, runner.signal_handler)
    
    try:
        await runner.start_bot()
    except KeyboardInterrupt:
        await runner.shutdown()
    except Exception as e:
        runner.logger.critical(f"Critical error in main: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Ensure event loop is running
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    asyncio.run(main())
