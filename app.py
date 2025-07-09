#!/usr/bin/env python3
"""
Entry point for Replit deployment
Combines Telegram bot with HTTP server for health checks
"""

import asyncio
import os
import time
from aiohttp import web, ClientSession
from aiohttp.web import Request, Response
import json
import logging
from datetime import datetime

# Import your bot components
from config import Config
# Removed IntegratedBotRunner import - using CleanMonitor instead
from logger import setup_logger

class TelegramBotApp:
    def __init__(self):
        self.logger = setup_logger()
        self.config = Config()
        self.bot_service = None
        self.app = web.Application()
        self.setup_routes()
        self.start_time = time.time()

    def setup_routes(self):
        """Setup HTTP routes for health checks"""
        self.app.router.add_get('/', self.handle_root)
        self.app.router.add_get('/health', self.handle_health)
        self.app.router.add_get('/status', self.handle_status)

    async def handle_root(self, request: Request) -> Response:
        """Root endpoint"""
        return web.Response(
            text="24/7 Telegram Bot Service is running",
            content_type='text/plain'
        )

    async def handle_health(self, request: Request) -> Response:
        """Health check endpoint"""
        try:
            health_data = {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "uptime": time.time() - self.start_time,
                "service": "telegram-bot",
                "version": "1.0.0"
            }

            # Check bot service health
            if self.bot_service and hasattr(self.bot_service, 'running'):
                health_data["bot_running"] = self.bot_service.running
            else:
                health_data["bot_running"] = False

            return web.json_response(health_data)

        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return web.json_response(
                {"status": "unhealthy", "error": str(e)},
                status=500
            )

    async def handle_status(self, request: Request) -> Response:
        """Status endpoint with detailed information"""
        try:
            status_data = {
                "service": "24/7 Telegram Bot Service",
                "status": "running",
                "uptime_seconds": time.time() - self.start_time,
                "config_loaded": bool(self.config.bot_token),
                "database_path": self.config.database_path,
                "log_level": self.config.log_level
            }

            return web.json_response(status_data)

        except Exception as e:
            self.logger.error(f"Status check failed: {e}")
            return web.json_response(
                {"status": "error", "error": str(e)},
                status=500
            )

    async def start_bot_service(self):
        """Start the Telegram bot service"""
        try:
            self.logger.info("Starting Telegram Bot Service...")
            from working_bot import WorkingBot
            self.bot_service = WorkingBot()
            await self.bot_service.start()
            self.logger.info("Telegram Bot Service started successfully")
        except Exception as e:
            self.logger.error(f"Failed to start bot service: {e}")
            raise

    async def start_web_server(self):
        """Start the web server"""
        try:
            # Використовуємо порт 80 для Cloud Run
            preferred_ports = [80]
            
            runner = web.AppRunner(self.app)
            await runner.setup()
            
            site = None
            for port in preferred_ports:
                try:
                    site = web.TCPSite(runner, '0.0.0.0', port)
                    await site.start()
                    self.logger.info(f"Web server started on port {port}")
                    break
                except OSError as e:
                    if "address already in use" in str(e).lower():
                        self.logger.warning(f"Port {port} already in use, trying next...")
                        continue
                    else:
                        raise
            
            if site is None:
                raise Exception("Could not bind to any available port")
                
            return runner

        except Exception as e:
            self.logger.error(f"Failed to start web server: {e}")
            raise

    async def run(self):
        """Main application entry point"""
        try:
            self.logger.info("Starting Telegram Bot Application...")

            # Validate configuration
            if not self.config.validate_config():
                raise Exception("Configuration validation failed")

            # Start web server first
            runner = await self.start_web_server()

            # Start bot service
            await self.start_bot_service()

            self.logger.info("Application started successfully")

            # Keep the application running
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                self.logger.info("Received shutdown signal")
            finally:
                # Cleanup
                if self.bot_service:
                    await self.bot_service.shutdown()
                await runner.cleanup()

        except Exception as e:
            self.logger.error(f"Application failed to start: {e}")
            raise

async def main():
    """Main function"""
    app = TelegramBotApp()
    await app.run()

if __name__ == "__main__":
    # Run the application
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Application stopped by user")
    except Exception as e:
        print(f"Application failed: {e}")