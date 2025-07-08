#!/usr/bin/env python3
"""
Main application entry point for deployment
Runs both the Telegram bot and HTTP health check server
"""

import asyncio
import signal
import sys
from datetime import datetime, timezone, timedelta
from aiohttp import web, ClientSession
from telethon import TelegramClient, events
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CallbackQueryHandler, ContextTypes
import json
import os
from config import Config
from logger import setup_logger
from integrated_bot import IntegratedBotRunner

class TelegramBotApp:
    def __init__(self):
        self.logger = setup_logger("telegram_bot_app")
        self.bot_runner = IntegratedBotRunner()
        self.web_app = None
        self.runner = None
        self.site = None
        self.running = False
        
    async def health_check(self, request):
        """Health check endpoint for deployment"""
        try:
            # Check if bot is running
            if not self.bot_runner.running:
                return web.Response(
                    text="Bot not running",
                    status=503,
                    headers={'Content-Type': 'text/plain'}
                )
            
            # Check if bot can respond to Telegram API
            try:
                await self.bot_runner.bot.get_me()
                bot_status = "healthy"
            except Exception as e:
                self.logger.error(f"Bot health check failed: {e}")
                bot_status = "unhealthy"
                
            health_data = {
                "status": "healthy" if bot_status == "healthy" else "unhealthy",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "services": {
                    "telegram_bot": bot_status,
                    "web_server": "healthy"
                }
            }
            
            status_code = 200 if health_data["status"] == "healthy" else 503
            return web.Response(
                text=json.dumps(health_data, indent=2),
                status=status_code,
                headers={'Content-Type': 'application/json'}
            )
            
        except Exception as e:
            self.logger.error(f"Health check error: {e}")
            return web.Response(
                text=f"Health check error: {str(e)}",
                status=500,
                headers={'Content-Type': 'text/plain'}
            )
    
    async def status_endpoint(self, request):
        """Status endpoint with detailed information"""
        try:
            status_data = {
                "service": "Telegram Bot Service",
                "version": "1.0.0",
                "uptime": self.bot_runner.logger.get_uptime() if hasattr(self.bot_runner.logger, 'get_uptime') else "unknown",
                "bot_running": self.bot_runner.running,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            return web.Response(
                text=json.dumps(status_data, indent=2),
                status=200,
                headers={'Content-Type': 'application/json'}
            )
            
        except Exception as e:
            self.logger.error(f"Status endpoint error: {e}")
            return web.Response(
                text=f"Status error: {str(e)}",
                status=500,
                headers={'Content-Type': 'text/plain'}
            )
    
    async def root_endpoint(self, request):
        """Root endpoint"""
        return web.Response(
            text="24/7 Telegram Bot Service is running",
            status=200,
            headers={'Content-Type': 'text/plain'}
        )
    
    async def setup_web_server(self):
        """Setup the web server for health checks"""
        try:
            self.web_app = web.Application()
            
            # Add routes
            self.web_app.router.add_get('/', self.root_endpoint)
            self.web_app.router.add_get('/health', self.health_check)
            self.web_app.router.add_get('/status', self.status_endpoint)
            
            # Setup runner
            self.runner = web.AppRunner(self.web_app)
            await self.runner.setup()
            
            # Get port from environment or use default
            port = int(os.getenv('PORT', 80))
            
            # Create site
            self.site = web.TCPSite(self.runner, '0.0.0.0', port)
            await self.site.start()
            
            self.logger.info(f"Web server started on port {port}")
            
        except Exception as e:
            self.logger.error(f"Failed to setup web server: {e}")
            raise
    
    async def start(self):
        """Start both the bot and web server"""
        try:
            self.logger.info("Starting Telegram Bot Application...")
            
            # Start web server first
            await self.setup_web_server()
            
            # Start bot runner
            bot_task = asyncio.create_task(self.bot_runner.start())
            
            # Wait for bot to be ready
            await asyncio.sleep(2)
            
            self.running = True
            self.logger.info("Application started successfully")
            
            # Keep both services running
            await bot_task
            
        except Exception as e:
            self.logger.error(f"Application startup failed: {e}")
            await self.stop()
            raise
    
    async def stop(self):
        """Stop both services"""
        try:
            self.logger.info("Stopping application...")
            self.running = False
            
            # Stop bot runner
            if self.bot_runner:
                await self.bot_runner.shutdown()
            
            # Stop web server
            if self.site:
                await self.site.stop()
            
            if self.runner:
                await self.runner.cleanup()
                
            self.logger.info("Application stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping application: {e}")
    
    def signal_handler(self, signum, frame):
        """Handle system signals for graceful shutdown"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        asyncio.create_task(self.stop())
        sys.exit(0)

async def main():
    """Main function to run the application"""
    app = TelegramBotApp()
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, app.signal_handler)
    signal.signal(signal.SIGTERM, app.signal_handler)
    
    try:
        await app.start()
    except KeyboardInterrupt:
        await app.stop()
    except Exception as e:
        app.logger.error(f"Application error: {e}")
        await app.stop()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())