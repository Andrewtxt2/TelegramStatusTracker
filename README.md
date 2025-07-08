# 24/7 Telegram Bot Service

A robust Telegram bot service for monitoring, analyzing, and forwarding relocation status messages with comprehensive health checking and deployment support.

## Features

- **24/7 Monitoring**: Continuous monitoring of Telegram groups
- **AI Analysis**: Intelligent message analysis for relocation status detection
- **Admin Approval**: Workflow with inline keyboard buttons for message approval
- **Health Monitoring**: Built-in HTTP health check endpoints for deployment
- **Error Recovery**: Automatic error handling and recovery mechanisms
- **Persistent Storage**: SQLite database for message history and bot state

## Deployment

### Quick Start

1. **Environment Variables**: Configure the following environment variables:
   ```
   BOT_TOKEN=your_telegram_bot_token
   SOURCE_GROUP_ID=source_group_id_or_username
   ADMIN_GROUP_ID=admin_group_id_or_username
   TARGET_CHANNEL_ID=target_channel_id_or_username
   ADMIN_USER_IDS=comma_separated_admin_user_ids
   ```

2. **Deploy to Replit**: 
   - The service runs on port 80 with health check endpoint at `/health`
   - Entry point: `app.py`
   - Click the Deploy button in Replit to deploy to Cloud Run

3. **Health Check**: The service provides multiple endpoints:
   - `/health` - Main health check (JSON response)
   - `/status` - Detailed service status
   - `/` - Basic service confirmation

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the service
python3 app.py
```

### Testing

```bash
# Run deployment readiness test
python3 test_deployment.py

# Test health endpoint
curl http://localhost:80/health

# Test status endpoint
curl http://localhost:80/status
```

## Architecture

The service combines:
- **Telegram Bot**: Handles message monitoring and user interactions
- **HTTP Server**: Provides health check endpoints for deployment
- **Database**: SQLite for persistent storage
- **Recovery System**: Automatic error handling and recovery

## Health Monitoring

The service includes comprehensive health monitoring:

- **HTTP Health Check**: Verifies web server is responding
- **Telegram Bot Health**: Validates bot connectivity to Telegram API
- **Database Health**: Ensures database operations are working
- **Service Status**: Tracks uptime and performance metrics

## Configuration

The service can be configured via:
- Environment variables (recommended for production)
- `config.json` file (for development)
- Default values (fallback)

## Files

- `app.py` - Main deployment entry point with HTTP server
- `integrated_bot.py` - Core bot functionality
- `config.py` - Configuration management
- `database.py` - Database operations
- `message_analyzer.py` - AI-powered message analysis
- `test_deployment.py` - Deployment readiness testing

## Support

For issues or questions, check the logs in the `/logs` directory or monitor the health endpoints.