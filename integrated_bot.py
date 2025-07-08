"""
Integrated Telegram Bot with MTProto API monitoring
Combines bot functionality with direct group monitoring
"""

import asyncio
import sys
import signal
import os
from typing import Optional
from bot_service import TelegramBotService
from telegram_client import TelegramGroupMonitor
from recovery_manager import RecoveryManager
from logger import setup_logger
from config import Config

class IntegratedBotRunner:
    def __init__(self):
        self.logger = setup_logger("integrated_bot")
        self.config = Config()
        self.bot_service: Optional[TelegramBotService] = None
        self.telegram_monitor: Optional[TelegramGroupMonitor] = None
        self.recovery_manager = RecoveryManager()
        self.running = False
        
    async def start(self):
        """Start both bot service and Telegram client monitoring"""
        try:
            self.logger.info("Starting Integrated Telegram Bot System...")
            
            # Start in bot-only mode for stability
            # MTProto API integration will be added later after manual authentication
            self.logger.info("Starting bot-only mode with enhanced features")
            await self.start_bot_only()
                
        except Exception as e:
            self.logger.error(f"Error starting integrated system: {e}")
            await self.handle_error(e)
            
    async def start_with_api_monitoring(self):
        """Start system with both bot and API monitoring"""
        try:
            # Initialize services
            self.bot_service = TelegramBotService(self.config)
            self.telegram_monitor = TelegramGroupMonitor(self.config)
            
            # Start bot service first
            self.logger.info("Starting bot service...")
            await self.bot_service.start()
            
            # Start Telegram client monitoring
            self.logger.info("Starting Telegram API monitoring...")
            
            # Run both services concurrently
            self.running = True
            
            # Create tasks for both services
            bot_task = asyncio.create_task(self.run_bot_service())
            monitor_task = asyncio.create_task(self.run_monitor_service())
            
            # Wait for either to complete (or fail)
            done, pending = await asyncio.wait(
                [bot_task, monitor_task],
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # Cancel remaining tasks
            for task in pending:
                task.cancel()
                
            # Check if any task failed
            for task in done:
                try:
                    await task
                except Exception as e:
                    self.logger.error(f"Service failed: {e}")
                    
        except Exception as e:
            self.logger.error(f"Error in integrated startup: {e}")
            raise
            
    async def start_bot_only(self):
        """Start only the bot service"""
        try:
            self.bot_service = TelegramBotService(self.config)
            await self.bot_service.start()
            self.running = True
            
            # Keep running
            while self.running:
                await asyncio.sleep(1)
                
        except Exception as e:
            self.logger.error(f"Error in bot-only mode: {e}")
            raise
            
    async def run_bot_service(self):
        """Keep bot service running"""
        try:
            while self.running:
                await asyncio.sleep(1)
        except Exception as e:
            self.logger.error(f"Bot service error: {e}")
            raise
            
    async def run_monitor_service(self):
        """Keep monitor service running"""
        try:
            await self.telegram_monitor.start()
        except Exception as e:
            self.logger.error(f"Monitor service error: {e}")
            raise
            
    async def handle_error(self, error: Exception):
        """Handle errors with recovery mechanisms"""
        self.logger.error(f"Handling error: {error}")
        
        if self.recovery_manager.can_recover():
            self.logger.info("Attempting recovery...")
            await self.recovery_manager.recover()
            
            # Restart services
            await self.shutdown()
            await asyncio.sleep(5)
            await self.start()
        else:
            self.logger.critical("Recovery failed. Manual intervention required.")
            sys.exit(1)
            
    async def shutdown(self):
        """Gracefully shutdown all services"""
        self.logger.info("Shutting down integrated system...")
        self.running = False
        
        if self.bot_service:
            await self.bot_service.stop()
            
        if self.telegram_monitor:
            await self.telegram_monitor.stop()
            
        self.logger.info("Integrated system shutdown complete")
        
    def signal_handler(self, signum, frame):
        """Handle system signals for graceful shutdown"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        asyncio.create_task(self.shutdown())

async def main():
    """Main function to run the integrated system"""
    runner = IntegratedBotRunner()
    
    # Register signal handlers
    signal.signal(signal.SIGINT, runner.signal_handler)
    signal.signal(signal.SIGTERM, runner.signal_handler)
    
    try:
        await runner.start()
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