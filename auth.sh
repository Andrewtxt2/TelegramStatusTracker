#!/bin/bash
echo "=== Автентифікація Telegram API ==="
echo "Запуск скрипту автентифікації..."
echo ""

python3 simple_auth.py

echo ""
echo "Якщо автентифікація успішна, запустіть:"
echo "python3 auto_monitor.py"