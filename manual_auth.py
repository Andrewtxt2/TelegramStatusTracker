#!/usr/bin/env python3
"""
Ручна автентифікація для Telegram API
Цей скрипт потрібно запустити в терміналі для введення коду
"""

import asyncio
import os
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError

async def manual_authenticate():
    """Ручна автентифікація з введенням коду"""
    
    api_id = int(os.getenv('TELEGRAM_API_ID', '26886585'))
    api_hash = os.getenv('TELEGRAM_API_HASH', '166e3719a0d93c12bf76af43fe91425f')
    phone = os.getenv('TELEGRAM_PHONE', '+380686850166')
    
    print(f"🔐 Автентифікація для: {phone}")
    print(f"📱 API ID: {api_id}")
    
    client = TelegramClient('monitor_session', api_id, api_hash)
    
    try:
        await client.connect()
        
        if await client.is_user_authorized():
            me = await client.get_me()
            print(f"✅ Вже авторизовано як: {me.first_name}")
            
            # Перевірка доступу до групи
            try:
                entity = await client.get_entity('pereizdvyshneve')
                print(f"✅ Доступ до групи: {entity.title}")
                return True
            except Exception as e:
                print(f"❌ Помилка доступу до групи: {e}")
                return False
        else:
            print("📞 Відправка коду підтвердження...")
            
            # Відправка коду
            sent_code = await client.send_code_request(phone)
            print(f"✅ Код відправлено на {phone}")
            print("💬 Перевірте SMS або повідомлення в Telegram")
            
            # Введення коду користувачем
            while True:
                try:
                    code = input("🔢 Введіть код підтвердження: ").strip()
                    if code:
                        break
                    print("❌ Код не може бути порожнім")
                except KeyboardInterrupt:
                    print("\n❌ Скасовано користувачем")
                    return False
            
            try:
                await client.sign_in(phone, code)
                print("✅ Код підтверджено!")
                
            except SessionPasswordNeededError:
                print("🔒 Потрібен пароль двофакторної автентифікації")
                while True:
                    try:
                        password = input("🔑 Введіть пароль: ").strip()
                        if password:
                            break
                        print("❌ Пароль не може бути порожнім")
                    except KeyboardInterrupt:
                        print("\n❌ Скасовано користувачем")
                        return False
                
                await client.sign_in(password=password)
                print("✅ Пароль підтверджено!")
            
            # Перевірка успішної автентифікації
            if await client.is_user_authorized():
                me = await client.get_me()
                print(f"🎉 Успішно авторизовано як: {me.first_name}")
                
                # Перевірка доступу до групи
                try:
                    entity = await client.get_entity('pereizdvyshneve')
                    print(f"✅ Доступ до групи підтверджено: {entity.title}")
                    print("🎯 Готово! Тепер можна запускати автоматичний моніторинг")
                    return True
                except Exception as e:
                    print(f"⚠️ Помилка доступу до групи: {e}")
                    print("Переконайтеся, що ви є учасником групи https://t.me/pereizdvyshneve")
                    return True  # Автентифікація успішна, навіть якщо немає доступу до групи
            else:
                print("❌ Автентифікація не вдалася")
                return False
                
    except Exception as e:
        print(f"❌ Помилка автентифікації: {e}")
        return False
    finally:
        await client.disconnect()

if __name__ == "__main__":
    print("🚀 Запуск ручної автентифікації Telegram API")
    print("📋 Інструкції:")
    print("   1. Після запуску буде відправлено код на ваш телефон")
    print("   2. Введіть отриманий код")
    print("   3. При необхідності введіть пароль 2FA")
    print("   4. Після успішної автентифікації можна запускати автоматичний моніторинг")
    print("-" * 60)
    
    result = asyncio.run(manual_authenticate())
    
    if result:
        print("\n🎉 Автентифікація завершена успішно!")
        print("💡 Тепер можете запустити автоматичний моніторинг:")
        print("   python auto_monitor.py")
    else:
        print("\n❌ Автентифікація не вдалася")
        print("💡 Спробуйте ще раз або зверніться за допомогою")