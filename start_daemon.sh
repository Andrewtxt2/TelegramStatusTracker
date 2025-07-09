#!/bin/bash

# Start daemon in background
echo "Starting Telegram Bot Daemon..."

# Kill existing processes
pkill -f "python.*daemon_service.py" || true
pkill -f "python.*production_bot.py" || true

# Wait a moment
sleep 2

# Start daemon in background
nohup python3 daemon_service.py > daemon_output.log 2>&1 &

# Get PID
PID=$!
echo "Daemon started with PID: $PID"
echo $PID > daemon.pid

# Check if it's running
sleep 2
if ps -p $PID > /dev/null; then
    echo "✅ Daemon is running"
    echo "Logs: tail -f daemon_output.log"
else
    echo "❌ Daemon failed to start"
    exit 1
fi