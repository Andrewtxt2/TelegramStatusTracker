"""
Logging configuration for 24/7 bot operations
Provides structured logging with rotation and error tracking
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from typing import Optional

def setup_logger(name: str = "telegram_bot", level: str = "INFO") -> logging.Logger:
    """Setup logger with file rotation and console output"""
    
    # Create logger
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
        
    # Set log level
    log_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(log_level)
    
    # Create logs directory if it doesn't exist
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    logger.addHandler(console_handler)
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        os.path.join(log_dir, f"{name}.log"),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    logger.addHandler(file_handler)
    
    # Error file handler
    error_handler = logging.handlers.RotatingFileHandler(
        os.path.join(log_dir, f"{name}_errors.log"),
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    logger.addHandler(error_handler)
    
    # Critical file handler
    critical_handler = logging.handlers.RotatingFileHandler(
        os.path.join(log_dir, f"{name}_critical.log"),
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3
    )
    critical_handler.setLevel(logging.CRITICAL)
    critical_handler.setFormatter(detailed_formatter)
    logger.addHandler(critical_handler)
    
    return logger

class BotLogger:
    """Enhanced logger for bot operations"""
    
    def __init__(self, name: str = "telegram_bot"):
        self.logger = setup_logger(name)
        self.start_time = datetime.now()
        
    def info(self, message: str, **kwargs):
        """Log info message"""
        self.logger.info(self._format_message(message, **kwargs))
        
    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self.logger.debug(self._format_message(message, **kwargs))
        
    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self.logger.warning(self._format_message(message, **kwargs))
        
    def error(self, message: str, **kwargs):
        """Log error message"""
        self.logger.error(self._format_message(message, **kwargs))
        
    def critical(self, message: str, **kwargs):
        """Log critical message"""
        self.logger.critical(self._format_message(message, **kwargs))
        
    def bot_event(self, event_type: str, message: str, **kwargs):
        """Log bot-specific events"""
        formatted_message = f"[{event_type.upper()}] {message}"
        self.logger.info(self._format_message(formatted_message, **kwargs))
        
    def api_call(self, method: str, success: bool, duration: Optional[float] = None, **kwargs):
        """Log API calls"""
        status = "SUCCESS" if success else "FAILED"
        duration_str = f" ({duration:.2f}s)" if duration else ""
        message = f"[API] {method} - {status}{duration_str}"
        self.logger.info(self._format_message(message, **kwargs))
        
    def message_processed(self, message_id: int, status: str, **kwargs):
        """Log message processing"""
        message = f"[MSG] ID:{message_id} - {status.upper()}"
        self.logger.info(self._format_message(message, **kwargs))
        
    def health_check(self, status: str, **kwargs):
        """Log health check"""
        uptime = datetime.now() - self.start_time
        message = f"[HEALTH] {status.upper()} - Uptime: {uptime}"
        self.logger.info(self._format_message(message, **kwargs))
        
    def _format_message(self, message: str, **kwargs) -> str:
        """Format message with additional context"""
        if kwargs:
            context = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
            return f"{message} | {context}"
        return message
        
    def get_uptime(self) -> str:
        """Get bot uptime"""
        uptime = datetime.now() - self.start_time
        return str(uptime)

# Global logger instance
_logger_instance = None

def get_logger() -> BotLogger:
    """Get global logger instance"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = BotLogger()
    return _logger_instance

# Convenience functions
def log_info(message: str, **kwargs):
    """Log info message"""
    get_logger().info(message, **kwargs)
    
def log_error(message: str, **kwargs):
    """Log error message"""
    get_logger().error(message, **kwargs)
    
def log_warning(message: str, **kwargs):
    """Log warning message"""
    get_logger().warning(message, **kwargs)
    
def log_debug(message: str, **kwargs):
    """Log debug message"""
    get_logger().debug(message, **kwargs)
    
def log_critical(message: str, **kwargs):
    """Log critical message"""
    get_logger().critical(message, **kwargs)
    
def log_bot_event(event_type: str, message: str, **kwargs):
    """Log bot event"""
    get_logger().bot_event(event_type, message, **kwargs)
    
def log_api_call(method: str, success: bool, duration: Optional[float] = None, **kwargs):
    """Log API call"""
    get_logger().api_call(method, success, duration, **kwargs)
    
def log_message_processed(message_id: int, status: str, **kwargs):
    """Log message processing"""
    get_logger().message_processed(message_id, status, **kwargs)
    
def log_health_check(status: str, **kwargs):
    """Log health check"""
    get_logger().health_check(status, **kwargs)
