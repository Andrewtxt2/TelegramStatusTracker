# Render Deployment Instructions

## Problem Fixed
The original error was caused by a package conflict:
- `telegram==0.0.1` (incorrect package)
- `python-telegram-bot==20.7` (correct package)

The `telegram` package conflicts with `python-telegram-bot` and causes import errors.

## Solution
1. **Fixed Import**: Use `render_fixed_bot.py` instead of `working_bot.py`
2. **Correct Dependencies**: Only use `python-telegram-bot`, not `telegram`
3. **Session Conflict Fix**: Create unique session file for each deployment
4. **Error Recovery**: Automatic recovery from AuthKeyDuplicatedError

## Deployment Steps

### 1. Render Service Setup
- **Build Command**: `pip install -r render_requirements.txt`
- **Start Command**: `python3 render_no_auth_bot.py`
- **Port**: 5000 (automatically detected)

### 2. Environment Variables
Set these in Render dashboard:
```
TELEGRAM_API_ID=26886585
TELEGRAM_API_HASH=166e3719a0d93c12bf76af43fe91425f
BOT_TOKEN=8189087426:AAF2XtTEwDRbwvWny-Hi2BPz_0ZeJHh9DEc
ADMIN_IDS=6395626140,7766810783
SOURCE_GROUP=https://t.me/pereizdvyshneve
TARGET_CHANNEL=@kryuvysh
PORT=5000
```

### 3. Files to Include
- `render_no_auth_bot.py` (main application using existing session)
- `render_requirements.txt` (dependencies)
- `auth_session.session` (pre-authenticated session file)
- `RENDER_DEPLOY.md` (this file)

**Note**: The bot uses existing session files to avoid authentication prompts

### 4. Dependencies (render_requirements.txt)
```
aiohttp==3.8.6
aiosqlite==0.17.0
python-telegram-bot==20.7
telethon==1.40.0
pytz==2025.2
psutil==7.0.0
```

**Important**: Do NOT include `telegram==0.0.1` as it conflicts with `python-telegram-bot`

### 5. Health Check Endpoints
- `/` - Basic status
- `/health` - Detailed health check
- `/status` - Service status

### 6. Features
- ✅ 24/7 monitoring of Telegram group
- ✅ AI-powered message analysis
- ✅ Admin approval workflow with inline buttons
- ✅ Automatic channel publishing
- ✅ Web server for health checks
- ✅ Context-aware message processing

### 7. Troubleshooting
If you get import errors:
1. Check that only `python-telegram-bot` is installed (not `telegram`)
2. Verify all environment variables are set
3. Ensure `auth_session.session` file is uploaded
4. Check logs for authentication issues

### 8. Deployment Command
```bash
# In Render dashboard:
# Build: pip install -r render_requirements.txt
# Start: python3 render_no_auth_bot.py
```

### 9. AuthKeyDuplicatedError Fix
The `render_no_auth_bot.py` automatically handles session conflicts by:
1. Using existing pre-authenticated session files
2. Graceful fallback to web-only mode if MTProto fails
3. No authentication prompts during deployment
4. Automatic session file detection and usage

The bot will automatically:
1. Connect to Telegram using the session file
2. Start monitoring the specified group
3. Launch web server on port 5000
4. Send startup notification to admins
5. Begin processing messages with approval workflow