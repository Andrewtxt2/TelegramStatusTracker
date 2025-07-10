#!/usr/bin/env python3
"""
Complete authentication with SMS code
Finalizes the new account setup
"""

import asyncio
import os
import sys
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError

# API credentials
API_ID = 29299324
API_HASH = "c262483dda2739c72637661b537dccac"

async def complete_with_code(phone_number, code, password=None):
    """Complete authentication with code"""
    
    print(f"🔄 Completing authentication for {phone_number}...")
    
    # Use existing session
    session_name = 'new_account'
    client = TelegramClient(session_name, API_ID, API_HASH)
    
    try:
        await client.connect()
        
        print(f"🔐 Signing in with code: {code}")
        
        try:
            await client.sign_in(phone_number, code)
            print("✅ Authentication successful!")
            
        except SessionPasswordNeededError:
            if password:
                await client.sign_in(password=password)
                print("✅ Authentication with 2FA successful!")
            else:
                print("❌ 2FA password required but not provided")
                print("Usage: python3 complete_auth_with_code.py <phone> <code> <2fa_password>")
                return False
        
        # Test the account
        me = await client.get_me()
        print(f"👤 Logged in as: {me.first_name}")
        
        # Create main session file
        await client.disconnect()
        
        # Copy to auth_session.session
        import shutil
        shutil.copy('new_account.session', 'auth_session.session')
        print("✅ Session saved as auth_session.session")
        
        # Notify completion
        from telegram import Bot
        bot = Bot(token="8189087426:AAF2XtTEwDRbwvWny-Hi2BPz_0ZeJHh9DEc")
        
        admin_ids = [6395626140, 7766810783, 564704015]
        message = (
            f"🎉 АВТЕНТИФІКАЦІЯ ЗАВЕРШЕНА\n\n"
            f"👤 Акаунт: {me.first_name}\n"
            f"📱 Номер: {phone_number}\n\n"
            f"✅ Сесія створена\n"
            f"✅ Система готова до запуску\n\n"
            f"Зараз бот буде перезапущений з новим акаунтом!"
        )
        
        for admin_id in admin_ids:
            try:
                await bot.send_message(chat_id=admin_id, text=message)
            except:
                pass
        
        print("\n🎉 Authentication complete!")
        print("✅ New account authenticated")
        print("✅ Session created")
        print("✅ Ready to start bot")
        
        return True
        
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 complete_auth_with_code.py <phone> <code> [2fa_password]")
        print("Example: python3 complete_auth_with_code.py +380123456789 12345")
        sys.exit(1)
    
    phone = sys.argv[1]
    code = sys.argv[2]
    password = sys.argv[3] if len(sys.argv) > 3 else None
    
    success = asyncio.run(complete_with_code(phone, code, password))
    
    if success:
        print(f"\n✅ Authentication completed for {phone}")
        print("Bot can now be started with: python3 main.py")
    else:
        print("\n❌ Authentication failed")