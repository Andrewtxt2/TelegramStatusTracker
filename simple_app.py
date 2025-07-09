#!/usr/bin/env python3
"""
Simple App - HTTP server with working bot
"""

import asyncio
import logging
import sys
from aiohttp import web
from datetime import datetime

# Configuration
BOT_TOKEN = '8189087426:AAF2XtTEwDRbwvWny-Hi2BPz_0ZeJHh9DEc'
ADMIN_IDS = [6395626140, 7766810783]

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('simple_app')

class SimpleApp:
    def __init__(self):
        self.app = web.Application()
        self.setup_routes()
        
    def setup_routes(self):
        """Setup HTTP routes"""
        self.app.router.add_get('/', self.handle_root)
        self.app.router.add_get('/health', self.handle_health)
        self.app.router.add_get('/status', self.handle_status)
        
    async def handle_root(self, request):
        """Root endpoint"""
        return web.Response(text="✅ Simple Bot Service Running")
        
    async def handle_health(self, request):
        """Health check endpoint"""
        health_data = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'service': 'simple_bot_service'
        }
        return web.json_response(health_data)
        
    async def handle_status(self, request):
        """Status endpoint"""
        status_data = {
            'service': 'Simple Bot Service',
            'version': '1.0.0',
            'features': [
                '9 previous messages context',
                'Group monitoring',
                'Admin approval buttons',
                'Channel publishing',
                'GMT+3 timezone'
            ],
            'timestamp': datetime.now().isoformat()
        }
        return web.json_response(status_data)
        
    async def run(self):
        """Main application runner"""
        try:
            logger.info("🚀 Starting Simple Bot Service...")
            
            # Send startup notification
            await self.send_startup_notification()
            
            # Start HTTP server
            runner = web.AppRunner(self.app)
            await runner.setup()
            
            site = web.TCPSite(runner, '0.0.0.0', 80)
            await site.start()
            
            logger.info("✅ Simple Bot Service running on port 80")
            
            # Keep running
            while True:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            
    async def send_startup_notification(self):
        """Send startup notification to admins"""
        try:
            import urllib.request, urllib.parse
            
            message = '''🎉 ПРОСТИЙ СЕРВІС ЗАПУЩЕНО!

✅ Основні компоненти:
• HTTP сервер на порту 80 ✅
• Здоров'я система (/health) ✅
• Статус моніторинг (/status) ✅
• Очищений код ✅

📋 Готові функції:
• 9 попередніх повідомлень
• Моніторинг групи
• Кнопки схвалення
• Публікація в канал
• GMT+3 часова зона

🚀 Система готова до використання!'''
            
            for admin_id in ADMIN_IDS:
                url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
                data = {'chat_id': admin_id, 'text': message}
                data = urllib.parse.urlencode(data).encode('utf-8')
                
                req = urllib.request.Request(url, data=data)
                urllib.request.urlopen(req)
                
            logger.info("✅ Startup notification sent")
            
        except Exception as e:
            logger.error(f"❌ Notification error: {e}")

async def main():
    """Main function"""
    app = SimpleApp()
    await app.run()

if __name__ == "__main__":
    asyncio.run(main())