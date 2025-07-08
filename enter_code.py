#!/usr/bin/env python3
import asyncio
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError

async def enter_code():
    api_id = 26886585
    api_hash = "166e3719a0d93c12bf76af43fe91425f"
    phone = "+380686850166"
    code = "22214"  # Код який ви отримали
    
    print(f"Використання коду: {code}")
    
    client = TelegramClient('session', api_id, api_hash)
    
    try:
        await client.connect()
        
        if await client.is_user_authorized():
            me = await client.get_me()
            print(f"Вже авторизовано: {me.first_name}")
            return True
        
        print("Використання коду для авторизації...")
        
        try:
            await client.sign_in(phone, code)
            print("Код підтверджено!")
        except SessionPasswordNeededError:
            print("Потрібен пароль 2FA")
            # Якщо потрібен пароль, виведемо повідомлення
            return "need_password"
        except Exception as e:
            print(f"Помилка з кодом: {e}")
            return False
        
        me = await client.get_me()
        print(f"Успішно авторизовано: {me.first_name}")
        
        # Перевірка доступу до групи
        try:
            entity = await client.get_entity('pereizdvyshneve')
            print(f"Доступ до групи: {entity.title}")
        except Exception as e:
            print(f"Група не знайдена: {e}")
        
        return True
        
    except Exception as e:
        print(f"Помилка: {e}")
        return False
    finally:
        await client.disconnect()

if __name__ == "__main__":
    result = asyncio.run(enter_code())
    if result == True:
        print("✅ Авторизація успішна!")
    elif result == "need_password":
        print("⚠️ Потрібен пароль 2FA")
    else:
        print("❌ Помилка авторизації")