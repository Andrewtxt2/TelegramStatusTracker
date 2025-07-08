
#!/usr/bin/env python3
"""
Графічне вікно для введення коду авторизації Telegram
"""

import tkinter as tk
from tkinter import messagebox, simpledialog
import asyncio
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
import threading

class TelegramAuthWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Telegram Bot - Авторизація")
        self.root.geometry("500x400")
        self.root.resizable(False, False)
        
        # Центрування вікна
        self.center_window()
        
        # Налаштування Telegram
        self.api_id = 26886585
        self.api_hash = "166e3719a0d93c12bf76af43fe91425f"
        self.phone = "+380633952873"  # Ваш номер
        
        self.client = None
        self.phone_code_hash = None
        
        self.create_widgets()
        
    def center_window(self):
        """Центрування вікна на екрані"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
        
    def create_widgets(self):
        """Створення елементів інтерфейсу"""
        # Заголовок
        title = tk.Label(self.root, text="🔐 Авторизація Telegram Bot", 
                        font=("Arial", 16, "bold"))
        title.pack(pady=20)
        
        # Інформація про номер
        phone_label = tk.Label(self.root, text=f"📱 Номер телефону: {self.phone}", 
                              font=("Arial", 12))
        phone_label.pack(pady=10)
        
        # Статус
        self.status_label = tk.Label(self.root, text="⏳ Готовий до авторизації", 
                                    font=("Arial", 11), fg="blue")
        self.status_label.pack(pady=5)
        
        # Кнопка відправки коду
        self.send_code_btn = tk.Button(self.root, text="📞 Відправити код", 
                                      command=self.send_code_clicked,
                                      font=("Arial", 12), bg="#4CAF50", fg="white",
                                      padx=20, pady=10)
        self.send_code_btn.pack(pady=20)
        
        # Поле для коду
        code_frame = tk.Frame(self.root)
        code_frame.pack(pady=10)
        
        tk.Label(code_frame, text="🔑 Код з SMS/Telegram:", 
                font=("Arial", 11)).pack()
        
        self.code_entry = tk.Entry(code_frame, font=("Arial", 14), width=20, 
                                  justify="center")
        self.code_entry.pack(pady=5)
        self.code_entry.bind('<Return>', lambda e: self.verify_code_clicked())
        
        # Кнопка підтвердження коду
        self.verify_btn = tk.Button(self.root, text="✅ Підтвердити код", 
                                   command=self.verify_code_clicked,
                                   font=("Arial", 12), bg="#2196F3", fg="white",
                                   padx=20, pady=10, state="disabled")
        self.verify_btn.pack(pady=10)
        
        # Лог область
        log_frame = tk.Frame(self.root)
        log_frame.pack(pady=20, padx=20, fill="both", expand=True)
        
        tk.Label(log_frame, text="📋 Лог:", font=("Arial", 10)).pack(anchor="w")
        
        self.log_text = tk.Text(log_frame, height=8, width=60, 
                               font=("Courier", 9))
        self.log_text.pack(fill="both", expand=True)
        
        # Кнопка закриття
        close_btn = tk.Button(self.root, text="❌ Закрити", 
                             command=self.close_window,
                             font=("Arial", 11), bg="#f44336", fg="white")
        close_btn.pack(pady=10)
        
    def log_message(self, message):
        """Додавання повідомлення в лог"""
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.root.update()
        
    def send_code_clicked(self):
        """Обробка натискання кнопки відправки коду"""
        self.send_code_btn.config(state="disabled")
        self.status_label.config(text="📞 Відправляю код...", fg="orange")
        
        # Запуск в окремому потоці
        threading.Thread(target=self.send_code_async, daemon=True).start()
        
    def send_code_async(self):
        """Асинхронна відправка коду"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.send_code())
            loop.close()
            
            if result:
                self.root.after(0, self.code_sent_success)
            else:
                self.root.after(0, self.code_sent_error)
                
        except Exception as e:
            self.root.after(0, lambda: self.code_sent_error(str(e)))
            
    async def send_code(self):
        """Відправка коду авторизації"""
        try:
            self.client = TelegramClient('auth_session', self.api_id, self.api_hash)
            await self.client.connect()
            
            if await self.client.is_user_authorized():
                me = await self.client.get_me()
                self.root.after(0, lambda: self.log_message(f"✅ Вже авторизовано як: {me.first_name}"))
                return True
            
            self.root.after(0, lambda: self.log_message(f"📞 Відправляю код на {self.phone}..."))
            
            sent_code = await self.client.send_code_request(self.phone)
            self.phone_code_hash = sent_code.phone_code_hash
            
            self.root.after(0, lambda: self.log_message("✅ Код успішно відправлено!"))
            return True
            
        except Exception as e:
            self.root.after(0, lambda: self.log_message(f"❌ Помилка: {e}"))
            return False
            
    def code_sent_success(self):
        """Успішна відправка коду"""
        self.status_label.config(text="✅ Код відправлено! Введіть код:", fg="green")
        self.verify_btn.config(state="normal")
        self.code_entry.config(state="normal")
        self.code_entry.focus()
        
    def code_sent_error(self, error=None):
        """Помилка відправки коду"""
        self.status_label.config(text="❌ Помилка відправки коду", fg="red")
        self.send_code_btn.config(state="normal")
        if error:
            self.log_message(f"❌ Помилка: {error}")
            
    def verify_code_clicked(self):
        """Обробка натискання кнопки підтвердження коду"""
        code = self.code_entry.get().strip()
        if not code:
            messagebox.showerror("Помилка", "Введіть код підтвердження!")
            return
            
        if not self.phone_code_hash:
            messagebox.showerror("Помилка", "Спочатку відправте код!")
            return
            
        self.verify_btn.config(state="disabled")
        self.code_entry.config(state="disabled")
        self.status_label.config(text="🔄 Перевіряю код...", fg="orange")
        
        # Запуск в окремому потоці
        threading.Thread(target=self.verify_code_async, args=(code,), daemon=True).start()
        
    def verify_code_async(self, code):
        """Асинхронна перевірка коду"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.verify_code(code))
            loop.close()
            
            if result == "success":
                self.root.after(0, self.auth_success)
            elif result == "need_password":
                self.root.after(0, self.need_password)
            else:
                self.root.after(0, self.auth_error)
                
        except Exception as e:
            self.root.after(0, lambda: self.auth_error(str(e)))
            
    async def verify_code(self, code):
        """Перевірка коду авторизації"""
        try:
            if not self.client:
                return "error"
                
            self.root.after(0, lambda: self.log_message(f"🔑 Перевіряю код: {code}"))
            
            await self.client.sign_in(self.phone, code, phone_code_hash=self.phone_code_hash)
            
            me = await self.client.get_me()
            self.root.after(0, lambda: self.log_message(f"🎉 Успішно авторизовано як: {me.first_name}"))
            
            # Перевірка доступу до групи
            try:
                entity = await self.client.get_entity('pereizdvyshneve')
                self.root.after(0, lambda: self.log_message(f"✅ Доступ до групи: {entity.title}"))
            except Exception as e:
                self.root.after(0, lambda: self.log_message(f"⚠️ Група не знайдена: {e}"))
            
            return "success"
            
        except SessionPasswordNeededError:
            self.root.after(0, lambda: self.log_message("🔒 Потрібен пароль 2FA"))
            return "need_password"
        except Exception as e:
            self.root.after(0, lambda: self.log_message(f"❌ Помилка коду: {e}"))
            return "error"
            
    def auth_success(self):
        """Успішна авторизація"""
        self.status_label.config(text="🎉 Авторизація успішна!", fg="green")
        messagebox.showinfo("Успіх", "Авторизація успішна!\nТепер можете запускати бота.")
        
    def need_password(self):
        """Потрібен пароль 2FA"""
        self.status_label.config(text="🔒 Потрібен пароль 2FA", fg="orange")
        password = simpledialog.askstring("2FA", "Введіть пароль двофакторної автентифікації:", show="*")
        if password:
            threading.Thread(target=self.verify_password_async, args=(password,), daemon=True).start()
            
    def verify_password_async(self, password):
        """Асинхронна перевірка пароля 2FA"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.verify_password(password))
            loop.close()
            
            if result:
                self.root.after(0, self.auth_success)
            else:
                self.root.after(0, self.auth_error)
                
        except Exception as e:
            self.root.after(0, lambda: self.auth_error(str(e)))
            
    async def verify_password(self, password):
        """Перевірка пароля 2FA"""
        try:
            await self.client.sign_in(password=password)
            me = await self.client.get_me()
            self.root.after(0, lambda: self.log_message(f"🎉 Успішно авторизовано як: {me.first_name}"))
            return True
        except Exception as e:
            self.root.after(0, lambda: self.log_message(f"❌ Помилка пароля: {e}"))
            return False
            
    def auth_error(self, error=None):
        """Помилка авторизації"""
        self.status_label.config(text="❌ Помилка авторизації", fg="red")
        self.verify_btn.config(state="normal")
        self.code_entry.config(state="normal")
        if error:
            self.log_message(f"❌ Помилка: {error}")
            
    def close_window(self):
        """Закриття вікна"""
        if self.client:
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.client.disconnect())
                loop.close()
            except:
                pass
        self.root.destroy()
        
    def run(self):
        """Запуск GUI"""
        self.root.mainloop()

def main():
    """Головна функція"""
    print("🚀 Запуск вікна авторизації Telegram...")
    app = TelegramAuthWindow()
    app.run()

if __name__ == "__main__":
    main()
