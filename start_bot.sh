#!/bin/bash

# 24/7 Telegram Bot Startup Script
# This script handles bot startup with automatic restart capabilities

BOT_NAME="telegram_relocation_bot"
BOT_SCRIPT="main.py"
LOG_FILE="logs/startup.log"
PID_FILE="bot.pid"
RESTART_DELAY=10
MAX_RESTARTS=10

# Create logs directory if it doesn't exist
mkdir -p logs

# Function to log messages
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Function to check if bot is running
is_bot_running() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            return 0
        else
            rm -f "$PID_FILE"
            return 1
        fi
    fi
    return 1
}

# Function to start bot
start_bot() {
    log_message "Starting $BOT_NAME..."
    
    # Check if already running
    if is_bot_running; then
        log_message "Bot is already running (PID: $(cat $PID_FILE))"
        return 1
    fi
    
    # Start bot in background
    nohup python3 "$BOT_SCRIPT" > "logs/bot_output.log" 2>&1 &
    BOT_PID=$!
    
    # Save PID
    echo "$BOT_PID" > "$PID_FILE"
    
    # Wait a moment and check if it's still running
    sleep 2
    if ps -p "$BOT_PID" > /dev/null 2>&1; then
        log_message "Bot started successfully (PID: $BOT_PID)"
        return 0
    else
        log_message "Bot failed to start"
        rm -f "$PID_FILE"
        return 1
    fi
}

# Function to stop bot
stop_bot() {
    log_message "Stopping $BOT_NAME..."
    
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            kill "$PID"
            sleep 5
            
            # Force kill if still running
            if ps -p "$PID" > /dev/null 2>&1; then
                kill -9 "$PID"
                sleep 2
            fi
            
            rm -f "$PID_FILE"
            log_message "Bot stopped"
        else
            log_message "Bot was not running"
            rm -f "$PID_FILE"
        fi
    else
        log_message "No PID file found"
    fi
}

# Function to restart bot
restart_bot() {
    log_message "Restarting $BOT_NAME..."
    stop_bot
    sleep "$RESTART_DELAY"
    start_bot
}

# Function to check bot status
check_status() {
    if is_bot_running; then
        PID=$(cat "$PID_FILE")
        log_message "Bot is running (PID: $PID)"
        return 0
    else
        log_message "Bot is not running"
        return 1
    fi
}

# Function to monitor bot and restart if needed
monitor_bot() {
    log_message "Starting bot monitoring..."
    restart_count=0
    
    while true; do
        if ! is_bot_running; then
            log_message "Bot is not running, attempting restart..."
            
            if [ $restart_count -ge $MAX_RESTARTS ]; then
                log_message "Maximum restart attempts reached ($MAX_RESTARTS). Stopping monitor."
                exit 1
            fi
            
            restart_count=$((restart_count + 1))
            log_message "Restart attempt $restart_count/$MAX_RESTARTS"
            
            if start_bot; then
                log_message "Bot restarted successfully"
                restart_count=0  # Reset counter on successful restart
            else
                log_message "Failed to restart bot"
                sleep "$RESTART_DELAY"
            fi
        else
            # Bot is running, reset restart counter
            restart_count=0
        fi
        
        # Check every 30 seconds
        sleep 30
    done
}

# Function to run bot in service mode
run_service() {
    log_message "Starting $BOT_NAME in service mode..."
    
    # Set up signal handlers
    trap 'log_message "Received SIGTERM, shutting down..."; stop_bot; exit 0' TERM
    trap 'log_message "Received SIGINT, shutting down..."; stop_bot; exit 0' INT
    
    # Start bot
    if start_bot; then
        # Start monitoring
        monitor_bot
    else
        log_message "Failed to start bot in service mode"
        exit 1
    fi
}

# Function to install dependencies
install_dependencies() {
    log_message "Installing dependencies..."
    
    # Check if requirements.txt exists
    if [ ! -f "requirements.txt" ]; then
        log_message "Creating requirements.txt..."
        cat > requirements.txt << EOF
python-telegram-bot>=20.0
aiohttp>=3.8.0
aiosqlite>=0.17.0
psutil>=5.9.0
EOF
    fi
    
    # Install dependencies
    pip3 install -r requirements.txt
    
    if [ $? -eq 0 ]; then
        log_message "Dependencies installed successfully"
    else
        log_message "Failed to install dependencies"
        exit 1
    fi
}

# Function to setup bot
setup_bot() {
    log_message "Setting up bot..."
    
    # Install dependencies
    install_dependencies
    
    # Create necessary directories
    mkdir -p logs
    
    # Check if config file exists
    if [ ! -f "config.json" ]; then
        log_message "Warning: config.json not found. Please configure the bot before starting."
        log_message "You can copy config.json.example and modify it with your settings."
    fi
    
    # Initialize database
    python3 -c "
import asyncio
from database import DatabaseManager
async def init_db():
    db = DatabaseManager()
    await db.initialize()
    print('Database initialized')
asyncio.run(init_db())
"
    
    log_message "Bot setup completed"
}

# Function to show help
show_help() {
    echo "Usage: $0 {start|stop|restart|status|monitor|service|setup|help}"
    echo ""
    echo "Commands:"
    echo "  start     - Start the bot"
    echo "  stop      - Stop the bot"
    echo "  restart   - Restart the bot"
    echo "  status    - Check bot status"
    echo "  monitor   - Start bot with monitoring (restarts if crashes)"
    echo "  service   - Run bot as a service with monitoring"
    echo "  setup     - Setup bot dependencies and configuration"
    echo "  help      - Show this help message"
}

# Main script logic
case "$1" in
    start)
        start_bot
        ;;
    stop)
        stop_bot
        ;;
    restart)
        restart_bot
        ;;
    status)
        check_status
        ;;
    monitor)
        monitor_bot
        ;;
    service)
        run_service
        ;;
    setup)
        setup_bot
        ;;
    help)
        show_help
        ;;
    *)
        echo "Invalid command: $1"
        show_help
        exit 1
        ;;
esac

exit 0
