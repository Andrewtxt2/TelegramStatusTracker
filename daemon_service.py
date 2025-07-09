#!/usr/bin/env python3
"""
Daemon service for 24/7 operation independent of browser tabs
"""

import asyncio
import signal
import sys
import os
import logging
from production_bot import ProductionBot

class DaemonService:
    def __init__(self):
        self.bot = None
        self.running = True
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging for daemon"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('daemon_service.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger('daemon_service')
        
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
        if self.bot:
            asyncio.create_task(self.bot.stop())
            
    async def start(self):
        """Start daemon service"""
        # Setup signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        self.logger.info("🚀 Starting Daemon Service...")
        
        try:
            # Create and start bot
            self.bot = ProductionBot()
            await self.bot.start()
            
            # Keep running until stopped
            while self.running:
                await asyncio.sleep(1)
                
        except Exception as e:
            self.logger.error(f"Daemon error: {e}")
            raise
        finally:
            if self.bot:
                await self.bot.stop()
            self.logger.info("Daemon service stopped")

async def main():
    """Main daemon function"""
    daemon = DaemonService()
    await daemon.start()

if __name__ == "__main__":
    asyncio.run(main())