# 24/7 Telegram Bot Service

## Overview

This is a robust 24/7 Telegram bot service designed to monitor, analyze, and forward relocation status messages. The bot continuously monitors a source group for messages, analyzes them using AI-powered text analysis to determine relocation status (open/closed), and forwards approved messages to a target channel. The system includes comprehensive error handling, recovery mechanisms, and database persistence for reliable operation.

## System Architecture

The application follows a modular architecture with clear separation of concerns:

### Core Components
- **Bot Service**: Central orchestrator handling Telegram API interactions and message processing
- **Message Analyzer**: AI-powered text analysis for relocation status detection
- **Database Manager**: Persistent storage using SQLite with async operations
- **Recovery Manager**: Comprehensive error handling and automatic recovery system
- **Configuration Manager**: Centralized configuration with JSON file and environment variable support

### Architecture Pattern
The system uses an event-driven architecture with async/await patterns for handling concurrent operations. The bot service acts as the main coordinator, delegating specific tasks to specialized components.

## Key Components

### 1. TelegramBotService (`bot_service.py`)
- **Purpose**: Core bot logic and Telegram API integration
- **Key Features**:
  - Continuous message monitoring with polling
  - Message forwarding with admin approval workflow
  - Error handling with retry mechanisms
  - Health check monitoring
- **Design Decision**: Uses python-telegram-bot library for robust Telegram API handling

### 2. MessageAnalyzer (`message_analyzer.py`)
- **Purpose**: AI-powered message analysis for relocation status detection
- **Key Features**:
  - Keyword-based status detection (open/closed)
  - Multi-language support (English, Ukrainian, Russian)
  - Confidence scoring for analysis results
  - Time-based pattern recognition
- **Design Decision**: Uses rule-based analysis instead of ML models for reliability and speed

### 3. DatabaseManager (`database.py`)
- **Purpose**: Persistent data storage and state management
- **Key Features**:
  - Async SQLite operations using aiosqlite
  - Message storage with analysis results
  - Bot state management
  - Thread-safe operations with async locks
- **Design Decision**: SQLite chosen for simplicity and reliability in single-instance deployment

### 4. RecoveryManager (`recovery_manager.py`)
- **Purpose**: Comprehensive error handling and recovery
- **Key Features**:
  - Error classification and tracking
  - Automatic recovery strategies
  - Retry logic with exponential backoff
  - Recovery level determination
- **Design Decision**: Implements multiple recovery levels to handle different failure scenarios

### 5. Configuration System (`config.py`)
- **Purpose**: Centralized configuration management
- **Key Features**:
  - JSON file configuration
  - Environment variable overrides
  - Runtime configuration validation
  - Default value handling
- **Design Decision**: Hybrid approach allows flexibility for different deployment environments

## Data Flow

1. **Message Monitoring**: Bot continuously polls the source group for new messages
2. **Message Analysis**: Incoming messages are analyzed by MessageAnalyzer for relocation status
3. **Database Storage**: Messages and analysis results are stored in SQLite database
4. **Admin Approval**: Messages requiring approval are sent to admin group with inline keyboards
5. **Message Forwarding**: Approved messages are forwarded to target channel
6. **Error Handling**: Any errors trigger the recovery manager for appropriate recovery actions

## External Dependencies

### Core Dependencies
- **python-telegram-bot**: Primary Telegram Bot API library
- **aiosqlite**: Async SQLite database operations
- **asyncio**: Asynchronous programming support

### System Dependencies
- **SQLite**: Embedded database for data persistence
- **JSON**: Configuration file format
- **Logging**: Built-in Python logging with rotation

### External APIs
- **Telegram Bot API**: Primary interface for bot operations
- **Telegram MTProto**: Used by the bot framework for communication

## Deployment Strategy

### Cloud Run Deployment
- **Entry Point**: app.py (combines bot service with HTTP server)
- **Health Check**: HTTP endpoint at /health on port 80
- **Status Monitoring**: Additional endpoints at /status and /
- **Architecture**: Hybrid bot + web server for deployment compatibility

### HTTP Server Integration
- **Technology**: aiohttp web server running alongside Telegram bot
- **Health Endpoints**: 
  - `/health` - JSON response with service status and health checks
  - `/status` - Detailed service information and uptime
  - `/` - Basic service confirmation
- **Port Configuration**: Port 80 for Cloud Run compatibility

### Configuration Management
- **Environment Variables**: Used for sensitive data (tokens, IDs)
- **JSON Configuration**: Used for application settings and preferences
- **Default Values**: Provides fallback configuration for missing settings

### Monitoring and Health Checks
- **HTTP Health Checks**: Automated health monitoring via HTTP endpoints
- **Telegram Bot Health**: Verifies bot connectivity to Telegram API
- **Error Tracking**: Comprehensive error logging and tracking
- **Recovery Mechanisms**: Automatic recovery from common failures

### Data Persistence
- **SQLite Database**: Local file-based storage for reliability
- **Backup Strategy**: Configurable backup intervals
- **Data Cleanup**: Automatic cleanup of old data

## Changelog

```
Changelog:
- July 08, 2025. Initial setup with 24/7 bot service
- July 08, 2025. Added multiple administrators support (IDs: 564704015, 7766810783)
- July 08, 2025. Enhanced configuration system to merge config file and environment variables
- July 08, 2025. Bot successfully deployed and running with AI analysis and approval workflow
- July 08, 2025. Successfully configured Telegram MTProto API authentication
- July 08, 2025. Activated automatic group monitoring for https://t.me/pereizdvyshneve
- July 08, 2025. Full automation achieved - bot now automatically monitors group without manual forwarding
- July 08, 2025. Implemented integrated system with approval buttons for admin workflow
- July 08, 2025. All administrators configured and receiving messages with inline keyboard buttons
- July 08, 2025. Finalized publication format: status + time only (e.g., "✅ Відкрито 🕓 11:17")
- July 08, 2025. Configured GMT+2 timezone and admin-controlled status logic  
- July 08, 2025. Updated to GMT+3 timezone and added recent 14 messages context for admins
- July 08, 2025. Implemented persistent message history storage and loading for continuous context
- July 08, 2025. Added HTTP health check server for deployment compatibility with Cloud Run
- July 08, 2025. Created app.py as new deployment entry point with web server and health endpoints
- July 08, 2025. Configured deployment with port 80 and health check endpoint at /health
- July 08, 2025. Resolved Bot API polling conflicts by creating clean_monitor.py with MTProto-only monitoring
- July 08, 2025. Implemented complete workflow: group monitoring → admin approval → channel publication
- July 08, 2025. System now runs as stable background service without polling conflicts
- July 08, 2025. Created stable_monitor.py with automatic restart, error recovery, and closed-tab operation
- July 08, 2025. Deployed stable version with retry logic, proper error handling, and graceful shutdown
```

## User Preferences

```
Preferred communication style: Simple, everyday language.
```