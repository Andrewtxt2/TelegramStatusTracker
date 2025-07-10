#!/usr/bin/env python3
"""
Quick authentication setup - handles the full flow
"""

import asyncio
import os
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError

# API credentials
API_ID = 29299324
API_HASH = "c262483dda2739c72637661b537dccac"
PHONE = "+380633952873"

class AuthHandler:
    def __init__(self):
        self.client = None
        self.phone_code_hash = None
        
    async def start_auth(self):
        """Start authentication process"""
        
        print(f"🔄 Starting authentication for {PHONE}...")
        
        # Clean up old sessions
        if os.path.exists('auth_session.session'):
            os.remove('auth_session.session')
        
        # Create new session
        session_name = 'auth_session'
        self.client = TelegramClient(session_name, API_ID, API_HASH)
        
        try:
            await self.client.connect()
            
            # Check if already authorized
            if await self.client.is_user_authorized():
                print("✅ Already authorized")
                me = await self.client.get_me()
                print(f"👤 Logged in as: {me.first_name}")
                return True
            
            # Request code
            print("📨 Requesting authentication code...")
            sent_code = await self.client.send_code_request(PHONE)
            self.phone_code_hash = sent_code.phone_code_hash
            
            print(f"✅ Code sent to {PHONE}")
            print(f"📱 Check your SMS messages")
            
            # Save state
            with open('auth_state.txt', 'w') as f:
                f.write(f"{PHONE}\n{self.phone_code_hash}")
            
            await self.client.disconnect()
            
            # Notify admins
            from telegram import Bot
            bot = Bot(token="8189087426:AAF2XtTEwDRbwvWny-Hi2BPz_0ZeJHh9DEc")
            admin_ids = [6395626140, 7766810783, 564704015]
            
            message = (
                f"📨 КОД АВТЕНТИФІКАЦІЇ ВІДПРАВЛЕНО\n\n"
                f"📱 Номер: {PHONE}\n"
                f"🔐 Перевірте SMS та надайте код\n\n"
                f"Після отримання коду система буде готова до запуску."
            )
            
            for admin_id in admin_ids:
                try:
                    await bot.send_message(chat_id=admin_id, text=message)
                except:
                    pass
            
            print("✅ Authentication setup complete")
            print("📱 Please provide the SMS code when received")
            return True
            
        except Exception as e:
            print(f"❌ Authentication setup failed: {e}")
            return False
    
    async def complete_auth(self, code):
        """Complete authentication with code"""
        
        print(f"🔄 Completing authentication with code: {code}")
        
        # Load saved state
        try:
            with open('auth_state.txt', 'r') as f:
                lines = f.read().strip().split('\n')
                phone = lines[0]
                phone_code_hash = lines[1]
        except:
            print("❌ No saved authentication state")
            return False
        
        # Use existing session
        session_name = 'auth_session'
        self.client = TelegramClient(session_name, API_ID, API_HASH)
        
        try:
            await self.client.connect()
            
            # Sign in with code
            print(f"🔐 Signing in...")
            await self.client.sign_in(phone, code, phone_code_hash=phone_code_hash)
            
            # Test connection
            me = await self.client.get_me()
            print(f"✅ Successfully authenticated as: {me.first_name}")
            
            # Notify admins
            from telegram import Bot
            bot = Bot(token="8189087426:AAF2XtTEwDRbwvWny-Hi2BPz_0ZeJHh9DEc")
            admin_ids = [6395626140, 7766810783, 564704015]
            
            message = (
                f"🎉 АВТЕНТИФІКАЦІЯ ЗАВЕРШЕНА\n\n"
                f"👤 Акаунт: {me.first_name}\n"
                f"📱 Номер: {phone}\n\n"
                f"✅ Сесія створена: auth_session.session\n"
                f"✅ Система готова до запуску\n\n"
                f"Бот зараз буде запущений з усіма функціями!"
            )
            
            for admin_id in admin_ids:
                try:
                    await bot.send_message(chat_id=admin_id, text=message)
                except:
                    pass
            
            await self.client.disconnect()
            
            # Clean up
            if os.path.exists('auth_state.txt'):
                os.remove('auth_state.txt')
            
            print("✅ Authentication completed successfully")
            return True
            
        except SessionPasswordNeededError:
            print("❌ 2FA password required")
            return False
        except Exception as e:
            print(f"❌ Authentication failed: {e}")
            return False

async def main():
    """Main authentication flow"""
    
    auth = AuthHandler()
    
    # Start authentication
    success = await auth.start_auth()
    
    if success:
        print("\n✅ Authentication setup complete!")
        print("Please provide the SMS code to complete the process")
        return True
    else:
        print("\n❌ Authentication setup failed")
        return False

if __name__ == "__main__":
    asyncio.run(main())