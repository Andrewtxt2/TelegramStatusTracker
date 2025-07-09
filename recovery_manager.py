"""
Recovery manager for handling bot failures and automatic recovery
Implements retry logic, error tracking, and recovery strategies
"""

import asyncio
import time
import traceback
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime, timedelta
from enum import Enum
from logger import setup_logger

class RecoveryLevel(Enum):
    """Recovery levels for different types of failures"""
    NONE = 0
    RETRY = 1
    RESTART = 2
    MANUAL = 3

class ErrorType(Enum):
    """Types of errors that can occur"""
    NETWORK = "network"
    API = "api"
    DATABASE = "database"
    TELEGRAM = "telegram"
    SYSTEM = "system"
    UNKNOWN = "unknown"

class RecoveryManager:
    def __init__(self):
        self.logger = setup_logger()
        self.error_history: List[Dict[str, Any]] = []
        self.recovery_attempts: Dict[str, int] = {}
        self.last_recovery_time: Optional[datetime] = None
        self.max_recovery_attempts = 5
        self.recovery_cooldown = 300  # 5 minutes
        self.error_threshold = 10
        self.recovery_strategies: Dict[ErrorType, Callable] = {
            ErrorType.NETWORK: self._recover_network,
            ErrorType.API: self._recover_api,
            ErrorType.DATABASE: self._recover_database,
            ErrorType.TELEGRAM: self._recover_telegram,
            ErrorType.SYSTEM: self._recover_system
        }
        
    async def handle_error(self, error: Exception, context: str = "") -> RecoveryLevel:
        """Handle an error and determine recovery level"""
        try:
            error_type = self._classify_error(error)
            error_data = {
                'type': error_type,
                'message': str(error),
                'context': context,
                'timestamp': datetime.now(),
                'traceback': traceback.format_exc()
            }
            
            self.error_history.append(error_data)
            self.logger.error(f"Error handled: {error_type.value} - {error}")
            
            # Determine recovery level
            recovery_level = self._determine_recovery_level(error_type, error)
            
            # Execute recovery if possible
            if recovery_level == RecoveryLevel.RETRY:
                await self._execute_recovery(error_type, error_data)
            elif recovery_level == RecoveryLevel.RESTART:
                self.logger.critical("Bot restart required")
                return RecoveryLevel.RESTART
            elif recovery_level == RecoveryLevel.MANUAL:
                self.logger.critical("Manual intervention required")
                return RecoveryLevel.MANUAL
                
            return recovery_level
            
        except Exception as e:
            self.logger.critical(f"Error in recovery manager: {e}")
            return RecoveryLevel.MANUAL
            
    def _classify_error(self, error: Exception) -> ErrorType:
        """Classify error type"""
        error_str = str(error).lower()
        error_class = error.__class__.__name__.lower()
        
        # Network errors
        if any(keyword in error_str for keyword in ['network', 'connection', 'timeout', 'unreachable']):
            return ErrorType.NETWORK
            
        # API errors
        if any(keyword in error_str for keyword in ['api', 'rate limit', 'forbidden', 'unauthorized']):
            return ErrorType.API
            
        # Database errors
        if any(keyword in error_str for keyword in ['database', 'sqlite', 'sql', 'table']):
            return ErrorType.DATABASE
            
        # Telegram errors
        if any(keyword in error_str for keyword in ['telegram', 'bot', 'chat', 'message']):
            return ErrorType.TELEGRAM
            
        # System errors
        if any(keyword in error_str for keyword in ['memory', 'disk', 'permission', 'file']):
            return ErrorType.SYSTEM
            
        return ErrorType.UNKNOWN
        
    def _determine_recovery_level(self, error_type: ErrorType, error: Exception) -> RecoveryLevel:
        """Determine appropriate recovery level"""
        error_key = f"{error_type.value}_{str(error)}"
        
        # Check if we've exceeded maximum attempts
        if self.recovery_attempts.get(error_key, 0) >= self.max_recovery_attempts:
            return RecoveryLevel.MANUAL
            
        # Check if we're in cooldown period
        if self.last_recovery_time:
            time_since_last = datetime.now() - self.last_recovery_time
            if time_since_last < timedelta(seconds=self.recovery_cooldown):
                return RecoveryLevel.NONE
                
        # Check recent error frequency
        recent_errors = self._get_recent_errors(minutes=10)
        if len(recent_errors) >= self.error_threshold:
            return RecoveryLevel.RESTART
            
        # Determine based on error type
        if error_type in [ErrorType.NETWORK, ErrorType.API]:
            return RecoveryLevel.RETRY
        elif error_type == ErrorType.DATABASE:
            return RecoveryLevel.RETRY
        elif error_type == ErrorType.TELEGRAM:
            return RecoveryLevel.RETRY
        elif error_type == ErrorType.SYSTEM:
            return RecoveryLevel.RESTART
        else:
            return RecoveryLevel.MANUAL
            
    async def _execute_recovery(self, error_type: ErrorType, error_data: Dict[str, Any]):
        """Execute recovery strategy"""
        try:
            error_key = f"{error_type.value}_{error_data['message']}"
            self.recovery_attempts[error_key] = self.recovery_attempts.get(error_key, 0) + 1
            self.last_recovery_time = datetime.now()
            
            self.logger.info(f"Executing recovery for {error_type.value} (attempt {self.recovery_attempts[error_key]})")
            
            # Execute specific recovery strategy
            if error_type in self.recovery_strategies:
                await self.recovery_strategies[error_type](error_data)
            else:
                await self._generic_recovery(error_data)
                
        except Exception as e:
            self.logger.error(f"Error during recovery execution: {e}")
            
    async def _recover_network(self, error_data: Dict[str, Any]):
        """Recover from network errors"""
        self.logger.info("Recovering from network error...")
        
        # Wait before retrying
        await asyncio.sleep(5)
        
        # Test connectivity
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get('https://api.telegram.org') as response:
                    if response.status == 200:
                        self.logger.info("Network connectivity restored")
                    else:
                        self.logger.warning("Network connectivity test failed")
        except Exception as e:
            self.logger.warning(f"Network test failed: {e}")
            
    async def _recover_api(self, error_data: Dict[str, Any]):
        """Recover from API errors"""
        self.logger.info("Recovering from API error...")
        
        # Check if it's a rate limit error
        if 'rate limit' in error_data['message'].lower():
            # Wait for rate limit to reset
            await asyncio.sleep(60)
            self.logger.info("Rate limit recovery wait completed")
        else:
            # Generic API error recovery
            await asyncio.sleep(10)
            
    async def _recover_database(self, error_data: Dict[str, Any]):
        """Recover from database errors"""
        self.logger.info("Recovering from database error...")
        
        try:
            # Attempt to reinitialize database
            from database import DatabaseManager
            db = DatabaseManager()
            await db.initialize()
            self.logger.info("Database reinitialized successfully")
        except Exception as e:
            self.logger.error(f"Database recovery failed: {e}")
            
    async def _recover_telegram(self, error_data: Dict[str, Any]):
        """Recover from Telegram errors"""
        self.logger.info("Recovering from Telegram error...")
        
        # Wait before retrying
        await asyncio.sleep(5)
        
        # Check specific Telegram errors
        if 'chat not found' in error_data['message'].lower():
            self.logger.warning("Chat not found - configuration may need update")
        elif 'bot was blocked' in error_data['message'].lower():
            self.logger.warning("Bot was blocked by user")
        elif 'message not modified' in error_data['message'].lower():
            self.logger.info("Message not modified - this is expected")
        else:
            self.logger.info("Generic Telegram error recovery")
            
    async def _recover_system(self, error_data: Dict[str, Any]):
        """Recover from system errors"""
        self.logger.info("Recovering from system error...")
        
        # Check disk space
        import shutil
        free_space = shutil.disk_usage('.').free
        if free_space < 100 * 1024 * 1024:  # Less than 100MB
            self.logger.warning("Low disk space detected")
            
        # Check memory usage using /proc/meminfo (Linux-specific)
        try:
            with open('/proc/meminfo', 'r') as f:
                meminfo = f.read()
                mem_total = int([line for line in meminfo.split('\n') if 'MemTotal' in line][0].split()[1])
                mem_available = int([line for line in meminfo.split('\n') if 'MemAvailable' in line][0].split()[1])
                memory_percent = ((mem_total - mem_available) / mem_total) * 100
                if memory_percent > 90:
                    self.logger.warning("High memory usage detected")
        except (FileNotFoundError, IndexError, ValueError):
            self.logger.info("Memory usage check skipped (not available in this environment)")
            
        await asyncio.sleep(10)
        
    async def _generic_recovery(self, error_data: Dict[str, Any]):
        """Generic recovery strategy"""
        self.logger.info("Executing generic recovery...")
        await asyncio.sleep(5)
        
    def _get_recent_errors(self, minutes: int = 10) -> List[Dict[str, Any]]:
        """Get errors from recent time period"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        return [error for error in self.error_history if error['timestamp'] > cutoff_time]
        
    def can_recover(self) -> bool:
        """Check if recovery is possible"""
        # Check if we're in cooldown
        if self.last_recovery_time:
            time_since_last = datetime.now() - self.last_recovery_time
            if time_since_last < timedelta(seconds=self.recovery_cooldown):
                return False
                
        # Check recent error frequency
        recent_errors = self._get_recent_errors(minutes=5)
        if len(recent_errors) >= self.error_threshold:
            return False
            
        return True
        
    async def recover(self):
        """Generic recovery method"""
        self.logger.info("Starting recovery process...")
        
        # Clear error history if too old
        cutoff_time = datetime.now() - timedelta(hours=1)
        self.error_history = [error for error in self.error_history if error['timestamp'] > cutoff_time]
        
        # Reset recovery attempts for old errors
        self.recovery_attempts.clear()
        
        # Wait before recovery
        await asyncio.sleep(10)
        
        self.logger.info("Recovery process completed")
        
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics"""
        recent_errors = self._get_recent_errors(minutes=60)
        error_types = {}
        
        for error in recent_errors:
            error_type = error['type'].value
            error_types[error_type] = error_types.get(error_type, 0) + 1
            
        return {
            'total_errors': len(self.error_history),
            'recent_errors': len(recent_errors),
            'error_types': error_types,
            'recovery_attempts': dict(self.recovery_attempts),
            'last_recovery': self.last_recovery_time.isoformat() if self.last_recovery_time else None
        }
        
    def reset_statistics(self):
        """Reset error statistics"""
        self.error_history.clear()
        self.recovery_attempts.clear()
        self.last_recovery_time = None
        self.logger.info("Error statistics reset")
