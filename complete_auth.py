#!/usr/bin/env python3
import asyncio
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError

async def complete_auth():
    api_id = 26886585
    api_hash = "166e3719a0d93c12bf76af43fe91425f"
    phone = "+380686850166"
    code = "36832"
    
    print("Завершення автентифікації...")
    
    client = TelegramClient('session', api_id, api_hash)
    
    try:
        await client.connect()
        
        if await client.is_user_authorized():
            me = await client.get_me()
            print(f"Вже авторизовано: {me.first_name}")
            return True
        
        # Відправка коду та отримання hash
        print("Отримання phone_code_hash...")
        sent_code = await client.send_code_request(phone)
        phone_code_hash = sent_code.phone_code_hash
        
        print(f"Використання коду: {code}")
        
        try:
            await client.sign_in(phone, code, phone_code_hash=phone_code_hash)
            print("Код підтверджено!")
        except SessionPasswordNeededError:
            print("Потрібен пароль 2FA")
            return "need_password"
        except Exception as e:
            print(f"Помилка з кодом: {e}")
            # Можливо код застарів, спробуємо ще раз
            print("Спробуємо з новим кодом...")
            return "need_new_code"
        
        me = await client.get_me()
        print(f"Успішно авторизовано: {me.first_name}")
        
        # Перевірка доступу до групи
        try:
            entity = await client.get_entity('pereizdvyshneve')
            print(f"Доступ до групи: {entity.title}")
        except Exception as e:
            print(f"Перевірка групи: {e}")
        
        return True
        
    except Exception as e:
        print(f"Помилка: {e}")
        return False
    finally:
        await client.disconnect()

if __name__ == "__main__":
    result = asyncio.run(complete_auth())
    if result == True:
        print("✅ Авторизація завершена!")
        print("Тепер можна запускати автоматичний моніторинг")
    elif result == "need_password":
        print("⚠️ Потрібен пароль 2FA")
    elif result == "need_new_code":
        print("⚠️ Потрібен новий код")
    else:
        print("❌ Помилка авторизації")