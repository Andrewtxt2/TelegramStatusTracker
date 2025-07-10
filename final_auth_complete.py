#!/usr/bin/env python3
"""
Final authentication completion with code 81638
"""

import asyncio
import os
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError

# API credentials
API_ID = 29299324
API_HASH = "c262483dda2739c72637661b537dccac"
PHONE = "+380633952873"
CODE = "81638"

async def final_auth():
    """Final authentication attempt"""
    
    print(f"🔄 Final authentication with code: {CODE}")
    
    # Try to use existing session if available
    session_name = 'auth_session'
    client = TelegramClient(session_name, API_ID, API_HASH)
    
    try:
        await client.connect()
        
        # Check if already authorized
        if await client.is_user_authorized():
            print("✅ Already authorized")
            me = await client.get_me()
            print(f"👤 Logged in as: {me.first_name}")
            return True
        
        # Request fresh code and complete authentication
        print("📨 Requesting authentication...")
        sent_code = await client.send_code_request(PHONE)
        
        # Sign in with the provided code
        print(f"🔐 Signing in with code: {CODE}")
        await client.sign_in(PHONE, CODE, phone_code_hash=sent_code.phone_code_hash)
        
        # Test connection
        me = await client.get_me()
        print(f"✅ Successfully authenticated as: {me.first_name}")
        
        # Notify admins
        from telegram import Bot
        bot = Bot(token="8189087426:AAF2XtTEwDRbwvWny-Hi2BPz_0ZeJHh9DEc")
        admin_ids = [6395626140, 7766810783, 564704015]
        
        message = (
            f"🎉 АВТЕНТИФІКАЦІЯ ЗАВЕРШЕНА\n\n"
            f"👤 Акаунт: {me.first_name}\n"
            f"📱 Номер: {PHONE}\n\n"
            f"✅ Сесія створена: auth_session.session\n"
            f"✅ Система готова до запуску\n\n"
            f"Бот зараз буде запущений з усіма функціями!"
        )
        
        for admin_id in admin_ids:
            try:
                await bot.send_message(chat_id=admin_id, text=message)
            except:
                pass
        
        await client.disconnect()
        
        print("✅ Authentication completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        # Try with existing hash if available
        try:
            with open('code_hash.txt', 'r') as f:
                phone_code_hash = f.read().strip()
            print(f"🔄 Trying with saved hash: {phone_code_hash}")
            
            await client.sign_in(PHONE, CODE, phone_code_hash=phone_code_hash)
            
            me = await client.get_me()
            print(f"✅ Successfully authenticated as: {me.first_name}")
            
            # Notify success and clean up
            from telegram import Bot
            bot = Bot(token="8189087426:AAF2XtTEwDRbwvWny-Hi2BPz_0ZeJHh9DEc")
            admin_ids = [6395626140, 7766810783, 564704015]
            
            for admin_id in admin_ids:
                try:
                    await bot.send_message(chat_id=admin_id, text="🎉 АВТЕНТИФІКАЦІЯ ЗАВЕРШЕНА! Бот готовий до запуску.")
                except:
                    pass
            
            await client.disconnect()
            return True
            
        except Exception as e2:
            print(f"❌ Fallback authentication failed: {e2}")
            return False

if __name__ == "__main__":
    success = asyncio.run(final_auth())
    if success:
        print("\n🎉 Authentication complete!")
        print("Starting bot now...")
    else:
        print("\n❌ Authentication failed")