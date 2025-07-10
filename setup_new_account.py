#!/usr/bin/env python3
"""
Setup new account with phone number
Creates authentication session for new account
"""

import asyncio
import os
import sys
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError

# API credentials
API_ID = 29299324
API_HASH = "c262483dda2739c72637661b537dccac"

async def setup_with_phone(phone_number):
    """Setup authentication with provided phone number"""
    
    print(f"🔄 Setting up authentication for {phone_number}...")
    
    # Create session name
    session_name = 'new_account'
    
    # Remove if exists
    if os.path.exists(f'{session_name}.session'):
        os.remove(f'{session_name}.session')
    
    # Create client
    client = TelegramClient(session_name, API_ID, API_HASH)
    
    try:
        await client.connect()
        
        print(f"📨 Sending code to {phone_number}...")
        await client.send_code_request(phone_number)
        
        print("✅ Code sent successfully!")
        print(f"📱 Check messages on {phone_number}")
        print("🔐 After receiving the code, the system will be ready for authentication")
        
        # Create placeholder session file
        await client.disconnect()
        
        # Update config with new phone
        import json
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
            
            config['mtproto_settings']['phone'] = phone_number
            
            with open('config.json', 'w') as f:
                json.dump(config, f, indent=2)
            
            print("✅ Config updated with new phone number")
            
        except Exception as e:
            print(f"⚠️ Config update failed: {e}")
        
        # Notify about next steps
        from telegram import Bot
        bot = Bot(token="8189087426:AAF2XtTEwDRbwvWny-Hi2BPz_0ZeJHh9DEc")
        
        admin_ids = [6395626140, 7766810783, 564704015]
        message = (
            f"📱 КОД ВІДПРАВЛЕНО\n\n"
            f"Номер: {phone_number}\n"
            f"Перевірте SMS та надайте код для завершення налаштування.\n\n"
            f"Після отримання коду система буде готова до роботи з усіма функціями:\n"
            f"✅ Моніторинг групи\n"
            f"✅ Кнопки схвалення\n"
            f"✅ Публікація в канал"
        )
        
        for admin_id in admin_ids:
            try:
                await bot.send_message(chat_id=admin_id, text=message)
            except:
                pass
        
        print("\n🎉 Phone number setup complete!")
        print("Next: provide the SMS code to complete authentication")
        
        return True
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 setup_new_account.py <phone_number>")
        print("Example: python3 setup_new_account.py +380123456789")
        sys.exit(1)
    
    phone = sys.argv[1]
    success = asyncio.run(setup_with_phone(phone))
    
    if success:
        print(f"\n✅ Setup completed for {phone}")
        print("Check your SMS and provide the code to complete setup")
    else:
        print("\n❌ Setup failed")