#!/usr/bin/env python3
"""
Створення тестової історії повідомлень для демонстрації функціональності
"""

import json
from datetime import datetime, timezone, timedelta

def create_test_history():
    """Створення тестової історії з 14 повідомлень"""
    
    gmt_plus_3 = timezone(timedelta(hours=3))
    
    # Тестова історія останніх 14 повідомлень
    test_messages = [
        {
            "original_message_id": 1001,
            "text": "Переїзд працює нормально",
            "sender_name": "Олександр",
            "sender_username": "alex_user",
            "status": "відкрито",
            "timestamp": (datetime.now(gmt_plus_3) - timedelta(hours=5)).isoformat()
        },
        {
            "original_message_id": 1002,
            "text": "Затримка на переїзді, треба чекати",
            "sender_name": "Марія",
            "sender_username": "maria_user",
            "status": "закрито",
            "timestamp": (datetime.now(gmt_plus_3) - timedelta(hours=4, minutes=30)).isoformat()
        },
        {
            "original_message_id": 1003,
            "text": "Все відкрито, можна їхати",
            "sender_name": "Петро",
            "sender_username": "petro_user",
            "status": "відкрито",
            "timestamp": (datetime.now(gmt_plus_3) - timedelta(hours=4)).isoformat()
        },
        {
            "original_message_id": 1004,
            "text": "Ремонт на переїзді, заборонено проїзд",
            "sender_name": "Інна",
            "sender_username": "inna_user",
            "status": "закрито",
            "timestamp": (datetime.now(gmt_plus_3) - timedelta(hours=3, minutes=45)).isoformat()
        },
        {
            "original_message_id": 1005,
            "text": "Проїзд відновлено",
            "sender_name": "Андрій",
            "sender_username": "andrey_user",
            "status": "відкрито",
            "timestamp": (datetime.now(gmt_plus_3) - timedelta(hours=3)).isoformat()
        },
        {
            "original_message_id": 1006,
            "text": "Технічні роботи на переїзді",
            "sender_name": "Оксана",
            "sender_username": "oksana_user",
            "status": "закрито",
            "timestamp": (datetime.now(gmt_plus_3) - timedelta(hours=2, minutes=30)).isoformat()
        },
        {
            "original_message_id": 1007,
            "text": "Переїзд відкритий для проїзду",
            "sender_name": "Дмитро",
            "sender_username": "dmitro_user",
            "status": "відкрито",
            "timestamp": (datetime.now(gmt_plus_3) - timedelta(hours=2)).isoformat()
        },
        {
            "original_message_id": 1008,
            "text": "Аварійна ситуація, переїзд закрито",
            "sender_name": "Світлана",
            "sender_username": "svitlana_user",
            "status": "закрито",
            "timestamp": (datetime.now(gmt_plus_3) - timedelta(hours=1, minutes=45)).isoformat()
        },
        {
            "original_message_id": 1009,
            "text": "Все норм, їздимо",
            "sender_name": "Василь",
            "sender_username": "vasyl_user",
            "status": "відкрито",
            "timestamp": (datetime.now(gmt_plus_3) - timedelta(hours=1, minutes=30)).isoformat()
        },
        {
            "original_message_id": 1010,
            "text": "Черга на переїзді",
            "sender_name": "Юлія",
            "sender_username": "yulia_user",
            "status": "закрито",
            "timestamp": (datetime.now(gmt_plus_3) - timedelta(hours=1)).isoformat()
        },
        {
            "original_message_id": 1011,
            "text": "Проїзд вільний",
            "sender_name": "Сергій",
            "sender_username": "sergiy_user",
            "status": "відкрито",
            "timestamp": (datetime.now(gmt_plus_3) - timedelta(minutes=45)).isoformat()
        },
        {
            "original_message_id": 1012,
            "text": "Переїзд тимчасово закрито",
            "sender_name": "Наталія",
            "sender_username": "natalia_user",
            "status": "закрито",
            "timestamp": (datetime.now(gmt_plus_3) - timedelta(minutes=30)).isoformat()
        },
        {
            "original_message_id": 1013,
            "text": "Відкрито для руху",
            "sender_name": "Віталій",
            "sender_username": "vitaliy_user",
            "status": "відкрито",
            "timestamp": (datetime.now(gmt_plus_3) - timedelta(minutes=15)).isoformat()
        },
        {
            "original_message_id": 1014,
            "text": "Стоять вагони, переїзд заблоковано",
            "sender_name": "Катерина",
            "sender_username": "kateryna_user",
            "status": "закрито",
            "timestamp": (datetime.now(gmt_plus_3) - timedelta(minutes=5)).isoformat()
        }
    ]
    
    # Зберігаємо історію
    with open("recent_messages.json", "w", encoding="utf-8") as f:
        json.dump(test_messages, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Створено тестову історію з {len(test_messages)} повідомлень")
    print(f"📁 Файл: recent_messages.json")
    
    # Показуємо останні 5 повідомлень
    print("\n📊 Останні 5 повідомлень:")
    for i, msg in enumerate(test_messages[-5:], 1):
        time_str = msg['timestamp'][:16]
        print(f"{i}. {time_str} {msg['sender_name']}: {msg['text'][:40]}...")

if __name__ == "__main__":
    create_test_history()