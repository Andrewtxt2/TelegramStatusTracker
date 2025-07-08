#!/usr/bin/env python3
"""
Швидка автентифікація з кодом
"""
import asyncio
import sys
from telethon import TelegramClient

async def quick_auth(code):
    client = TelegramClient('session', 26886585, '166e3719a0d93c12bf76af43fe91425f')
    await client.connect()
    
    phone = '+380686850166'
    
    try:
        # Отримуємо новий код
        sent = await client.send_code_request(phone)
        print(f'Код відправлено на {phone}')
        
        # Використовуємо код
        await client.sign_in(phone, code, phone_code_hash=sent.phone_code_hash)
        print('✅ Авторизація успішна!')
        
        me = await client.get_me()
        print(f'Авторизований як: {me.first_name}')
        
        await client.disconnect()
        return True
        
    except Exception as e:
        print(f'❌ Помилка авторизації: {e}')
        await client.disconnect()
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Використання: python3 quick_auth.py <код>")
        sys.exit(1)
    
    code = sys.argv[1]
    result = asyncio.run(quick_auth(code))
    
    if result:
        print("\n🚀 Готово! Тепер можна запустити бота.")
    else:
        print("\n❌ Спробуйте ще раз з новим кодом.")