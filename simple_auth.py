#!/usr/bin/env python3
import asyncio
import sys
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError

async def authenticate():
    api_id = 26886585
    api_hash = "166e3719a0d93c12bf76af43fe91425f"
    phone = "+380686850166"
    
    print(f"Автентифікація для: {phone}")
    
    client = TelegramClient('session', api_id, api_hash)
    
    try:
        await client.connect()
        
        if await client.is_user_authorized():
            me = await client.get_me()
            print(f"Вже авторизовано: {me.first_name}")
            return True
        
        print("Відправка коду...")
        await client.send_code_request(phone)
        print(f"Код відправлено на {phone}")
        
        code = input("Введіть код: ")
        
        try:
            await client.sign_in(phone, code)
        except SessionPasswordNeededError:
            password = input("Введіть пароль 2FA: ")
            await client.sign_in(password=password)
        
        me = await client.get_me()
        print(f"Успішно авторизовано: {me.first_name}")
        
        # Перевірка групи
        try:
            entity = await client.get_entity('pereizdvyshneve')
            print(f"Доступ до групи: {entity.title}")
        except:
            print("Група не знайдена, але авторизація успішна")
        
        return True
        
    except Exception as e:
        print(f"Помилка: {e}")
        return False
    finally:
        await client.disconnect()

if __name__ == "__main__":
    success = asyncio.run(authenticate())
    if success:
        print("Готово! Можна запускати моніторинг")
    else:
        print("Помилка автентифікації")