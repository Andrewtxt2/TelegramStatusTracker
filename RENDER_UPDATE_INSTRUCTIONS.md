# Render Deployment Update Instructions

## ❌ Current Problem
Render is using `working_bot.py` which causes AuthKeyDuplicatedError.

## ✅ Solution
Change the start command to use `main.py` instead.

## 🔧 How to Fix in Render Dashboard

### Option 1: Update Start Command
1. Go to your Render service dashboard
2. Navigate to "Settings" → "Environment"
3. Change **Start Command** from:
   ```
   python3 working_bot.py
   ```
   to:
   ```
   python3 main.py
   ```

### Option 2: Use render.yaml (Recommended)
1. Add the `render.yaml` file to your repository
2. Render will automatically use this configuration

## 📁 Files to Upload/Update

### Essential Files:
- `main.py` - New entry point
- `render_no_auth_bot.py` - Main application
- `render_requirements.txt` - Dependencies
- `auth_session.session` - Pre-authenticated session
- `render.yaml` - Render configuration

### Remove/Ignore:
- `working_bot.py` - Causes session conflicts
- Any other session files (if causing conflicts)

## 🌐 Environment Variables
Make sure these are set in Render:
```
TELEGRAM_API_ID=26886585
TELEGRAM_API_HASH=166e3719a0d93c12bf76af43fe91425f
BOT_TOKEN=8189087426:AAF2XtTEwDRbwvWny-Hi2BPz_0ZeJHh9DEc
ADMIN_IDS=6395626140,7766810783
SOURCE_GROUP=https://t.me/pereizdvyshneve
TARGET_CHANNEL=@kryuvysh
PORT=5000
```

## 🔄 Deployment Steps

### Quick Fix (If you can't update files):
1. In Render dashboard, change start command to: `python3 main.py`
2. Redeploy

### Complete Fix:
1. Push updated files to GitHub
2. Render will auto-deploy with new configuration
3. Start command: `python3 main.py`

## ✅ Expected Result
After the fix:
- No AuthKeyDuplicatedError
- Bot starts successfully
- All services healthy: MTProto, Bot API, Web server
- Messages processed in real-time
- Health checks at `/health`, `/status`, `/`

## 🚨 Important Notes
- The `main.py` file imports `render_no_auth_bot.py`
- Uses existing session files (no auth prompts)
- Automatic fallback to web-only mode if MTProto fails
- All functionality preserved: group monitoring, admin approval, channel publishing

## 🎯 File Structure
```
project/
├── main.py                 # Entry point (NEW)
├── render_no_auth_bot.py   # Main application
├── render_requirements.txt # Dependencies
├── auth_session.session    # Pre-authenticated session
├── render.yaml            # Render configuration
└── RENDER_UPDATE_INSTRUCTIONS.md # This file
```

Simply change the start command to `python3 main.py` and the bot will work perfectly!