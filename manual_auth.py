#!/usr/bin/env python3
"""
Manual authentication with code
"""

import asyncio
import os
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError, PhoneCodeExpiredError

# API credentials
API_ID = 29299324
API_HASH = "c262483dda2739c72637661b537dccac"
PHONE = "+380633952873"
CODE = "25414"

async def manual_auth():
    """Manual authentication with provided code"""
    
    print(f"🔄 Manual authentication for {PHONE}...")
    print(f"🔐 Using code: {CODE}")
    
    # Clean up old sessions
    if os.path.exists('auth_session.session'):
        os.remove('auth_session.session')
    if os.path.exists('new_account.session'):
        os.remove('new_account.session')
    
    # Create new session
    session_name = 'auth_session'
    client = TelegramClient(session_name, API_ID, API_HASH)
    
    try:
        await client.connect()
        
        # Check if already authorized
        if await client.is_user_authorized():
            print("✅ Already authorized")
            me = await client.get_me()
            print(f"👤 Logged in as: {me.first_name}")
            await client.disconnect()
            return True
        
        # Request code
        print("📨 Requesting new code...")
        try:
            sent_code = await client.send_code_request(PHONE)
            print(f"✅ Code sent, hash: {sent_code.phone_code_hash}")
            
            # Try to sign in with code
            print(f"🔐 Signing in with code: {CODE}")
            await client.sign_in(PHONE, CODE, phone_code_hash=sent_code.phone_code_hash)
            
            print("✅ Authentication successful!")
            
        except PhoneCodeExpiredError:
            print("❌ Previous code expired, requesting new one...")
            sent_code = await client.send_code_request(PHONE)
            print(f"✅ New code sent, hash: {sent_code.phone_code_hash}")
            
            # Notify that new code is needed
            from telegram import Bot
            bot = Bot(token="8189087426:AAF2XtTEwDRbwvWny-Hi2BPz_0ZeJHh9DEc")
            admin_ids = [6395626140, 7766810783, 564704015]
            
            for admin_id in admin_ids:
                try:
                    await bot.send_message(
                        chat_id=admin_id,
                        text=f"📨 НОВИЙ КОД ПОТРІБЕН\n\nПопередній код застарів.\nНовий код відправлено на {PHONE}\nНадайте новий код для завершення автентифікації."
                    )
                except:
                    pass
            
            await client.disconnect()
            return False
            
        except SessionPasswordNeededError:
            print("❌ 2FA password required")
            await client.disconnect()
            return False
        
        # Test connection
        me = await client.get_me()
        print(f"✅ Successfully authenticated as: {me.first_name}")
        
        # Notify success
        from telegram import Bot
        bot = Bot(token="8189087426:AAF2XtTEwDRbwvWny-Hi2BPz_0ZeJHh9DEc")
        admin_ids = [6395626140, 7766810783, 564704015]
        
        message = (
            f"🎉 АВТЕНТИФІКАЦІЯ ЗАВЕРШЕНА\n\n"
            f"👤 Акаунт: {me.first_name}\n"
            f"📱 Номер: {PHONE}\n\n"
            f"✅ Сесія створена: auth_session.session\n"
            f"✅ Система готова до запуску\n\n"
            f"Бот зараз буде запущений!"
        )
        
        for admin_id in admin_ids:
            try:
                await bot.send_message(chat_id=admin_id, text=message)
            except:
                pass
        
        await client.disconnect()
        
        print("✅ Authentication completed successfully")
        print("✅ Session saved as auth_session.session")
        return True
        
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        await client.disconnect()
        return False

if __name__ == "__main__":
    success = asyncio.run(manual_auth())
    if success:
        print("\n🎉 Ready to start bot!")
    else:
        print("\n❌ Authentication failed")