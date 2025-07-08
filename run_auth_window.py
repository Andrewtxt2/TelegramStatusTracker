
#!/usr/bin/env python3
"""
Запуск вікна авторизації
"""

import sys
import os

# Додаємо поточну директорію в PATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from auth_window import main
    main()
except ImportError as e:
    print(f"❌ Помилка імпорту: {e}")
    print("🔧 Встановлюю необхідні пакети...")
    os.system("pip install tkinter")
    from auth_window import main
    main()
except Exception as e:
    print(f"❌ Помилка запуску: {e}")
    input("Натисніть Enter для закриття...")
