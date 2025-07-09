"""
Configuration manager for bot settings
Loads configuration from JSON file and environment variables
"""

import json
import os
from typing import Dict, Any, Optional, List
from logger import setup_logger

class Config:
    def __init__(self, config_file: str = "config.json"):
        self.logger = setup_logger()
        self.config_file = config_file
        self.config_data: Dict[str, Any] = {}
        self.load_config()
        
    def load_config(self):
        """Load configuration from file and environment variables"""
        try:
            # Load from config file
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config_data = json.load(f)
                    self.logger.info(f"Configuration loaded from {self.config_file}")
            else:
                self.logger.warning(f"Config file {self.config_file} not found, using defaults")
                self.config_data = {}
                
            # Override with environment variables
            self.load_from_env()
            
        except Exception as e:
            self.logger.error(f"Error loading configuration: {e}")
            self.config_data = {}
            
    def load_from_env(self):
        """Load configuration from environment variables"""
        env_mappings = {
            'BOT_TOKEN': 'bot_token',
            'SOURCE_GROUP_ID': 'source_group_id',
            'SOURCE_GROUP_LINK': 'source_group_link',
            'ADMIN_GROUP_ID': 'admin_group_id',
            'ADMIN_GROUP_LINK': 'admin_group_link',
            'TARGET_CHANNEL_ID': 'target_channel_id',
            'TARGET_CHANNEL_LINK': 'target_channel_link',
            'ADMIN_USER_ID': 'admin_user_id',
            'ADDITIONAL_ADMIN_IDS': 'additional_admin_ids',
            'DATABASE_PATH': 'database_path',
            'LOG_LEVEL': 'log_level',
            'MAX_ERRORS': 'max_errors',
            'RETRY_DELAY': 'retry_delay',
            'HEALTH_CHECK_INTERVAL': 'health_check_interval'
        }
        
        for env_var, config_key in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value:
                # Convert numeric values
                if config_key in ['source_group_id', 'admin_group_id', 'target_channel_id', 
                                'admin_user_id', 'max_errors', 'retry_delay', 'health_check_interval']:
                    try:
                        env_value = int(env_value)
                    except ValueError:
                        self.logger.warning(f"Invalid numeric value for {env_var}: {env_value}")
                        continue
                elif config_key == 'additional_admin_ids':
                    # Handle comma-separated admin IDs from environment
                    try:
                        env_value = [int(id.strip()) for id in env_value.split(',') if id.strip()]
                    except ValueError:
                        self.logger.warning(f"Invalid format for {env_var}: {env_value}")
                        continue
                        
                # Don't overwrite config file values with environment values for additional_admin_ids
                if config_key == 'additional_admin_ids' and self.config_data.get(config_key):
                    # Merge environment and config file admin IDs
                    existing_ids = self.config_data.get(config_key, [])
                    if isinstance(existing_ids, list):
                        combined_ids = list(set(existing_ids + env_value))
                        self.config_data[config_key] = combined_ids
                    else:
                        self.config_data[config_key] = env_value
                else:
                    self.config_data[config_key] = env_value
                self.logger.debug(f"Config {config_key} set from environment variable {env_var}")
                
    @property
    def bot_token(self) -> str:
        """Get bot token"""
        env_token = os.getenv('BOT_TOKEN')
        config_token = self.config_data.get('bot_token', '')
        
        self.logger.debug(f"Environment BOT_TOKEN: {'SET' if env_token else 'NOT_SET'}")
        self.logger.debug(f"Config bot_token: {'SET' if config_token else 'NOT_SET'}")
        
        token = env_token or config_token
        if not token:
            self.logger.error("BOT_TOKEN not found in environment variables or config file")
        else:
            self.logger.info(f"Using bot_token: {token[:10]}...")
        return token
        
    @property
    def source_group_id(self):
        """Get source group ID or link"""
        id_val = self.config_data.get('source_group_id', os.getenv('SOURCE_GROUP_ID', '0'))
        if id_val and id_val != '0':
            try:
                return int(id_val)
            except ValueError:
                return id_val
        
        # Try to get from link
        link = self.config_data.get('source_group_link', os.getenv('SOURCE_GROUP_LINK', ''))
        if link:
            if link.startswith('https://t.me/'):
                username = link[13:]
                if username.startswith('+'):
                    return link  # Return full invite link
                return f"@{username}"
            return link
        return 0
        
    @property
    def admin_group_id(self):
        """Get admin group ID or link"""
        id_val = self.config_data.get('admin_group_id', os.getenv('ADMIN_GROUP_ID', '0'))
        if id_val and id_val != '0':
            try:
                return int(id_val)
            except ValueError:
                return id_val
        
        # Try to get from link
        link = self.config_data.get('admin_group_link', os.getenv('ADMIN_GROUP_LINK', ''))
        if link:
            if link.startswith('https://t.me/'):
                username = link[13:]
                if username.startswith('+'):
                    return link  # Return full invite link
                return f"@{username}"
            return link
        return 0
        
    @property
    def target_channel_id(self):
        """Get target channel ID or link"""
        id_val = self.config_data.get('target_channel_id', os.getenv('TARGET_CHANNEL_ID', '0'))
        if id_val and id_val != '0':
            try:
                return int(id_val)
            except ValueError:
                return id_val
        
        # Try to get from link
        link = self.config_data.get('target_channel_link', os.getenv('TARGET_CHANNEL_LINK', ''))
        if link:
            if link.startswith('https://t.me/'):
                username = link[13:]
                if username.startswith('+'):
                    return link  # Return full invite link
                return f"@{username}"
            return link
        return 0
        
    @property
    def admin_user_id(self) -> int:
        """Get admin user ID"""
        return self.config_data.get('admin_user_id', int(os.getenv('ADMIN_USER_ID', '0')))
    
    @property
    def admin_user_ids(self) -> List[int]:
        """Get list of admin user IDs"""
        ids = []
        
        # Primary admin
        primary_id = self.admin_user_id
        if primary_id and primary_id != 0:
            ids.append(primary_id)
        
        # Additional admins from config file
        additional_ids = self.config_data.get('additional_admin_ids', [])
        if isinstance(additional_ids, str):
            # Handle comma-separated string
            try:
                additional_ids = [int(id.strip()) for id in additional_ids.split(',') if id.strip()]
            except ValueError:
                self.logger.warning("Invalid format for additional_admin_ids")
                additional_ids = []
        elif isinstance(additional_ids, list):
            # Convert to integers, filtering out invalid values
            valid_ids = []
            for id_val in additional_ids:
                try:
                    if isinstance(id_val, (int, str)) and str(id_val).isdigit():
                        valid_ids.append(int(id_val))
                except (ValueError, TypeError):
                    continue
            additional_ids = valid_ids
        
        ids.extend(additional_ids)
        
        # From environment variable
        env_ids = os.getenv('ADDITIONAL_ADMIN_IDS', '')
        if env_ids:
            try:
                env_ids = [int(id.strip()) for id in env_ids.split(',') if id.strip()]
                ids.extend(env_ids)
            except ValueError:
                self.logger.warning("Invalid format for ADDITIONAL_ADMIN_IDS environment variable")
        
        return list(set(ids))  # Remove duplicates
        
    @property
    def database_path(self) -> str:
        """Get database path"""
        return self.config_data.get('database_path', os.getenv('DATABASE_PATH', 'bot_data.db'))
        
    @property
    def log_level(self) -> str:
        """Get log level"""
        return self.config_data.get('log_level', os.getenv('LOG_LEVEL', 'INFO'))
        
    @property
    def max_errors(self) -> int:
        """Get maximum errors before restart"""
        return self.config_data.get('max_errors', int(os.getenv('MAX_ERRORS', '10')))
        
    @property
    def retry_delay(self) -> int:
        """Get retry delay in seconds"""
        return self.config_data.get('retry_delay', int(os.getenv('RETRY_DELAY', '5')))
        
    @property
    def health_check_interval(self) -> int:
        """Get health check interval in seconds"""
        return self.config_data.get('health_check_interval', int(os.getenv('HEALTH_CHECK_INTERVAL', '300')))
        
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self.config_data.get(key, default)
        
    def set(self, key: str, value: Any):
        """Set configuration value"""
        self.config_data[key] = value
        
    def save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config_data, f, indent=2, ensure_ascii=False)
            self.logger.info(f"Configuration saved to {self.config_file}")
        except Exception as e:
            self.logger.error(f"Error saving configuration: {e}")
            
    async def resolve_chat_id(self, chat_link: str) -> Optional[int]:
        """Resolve chat ID from Telegram link"""
        try:
            if not chat_link:
                return None
                
            # Remove https://t.me/ prefix if present
            if chat_link.startswith('https://t.me/'):
                chat_link = chat_link[13:]
            elif chat_link.startswith('t.me/'):
                chat_link = chat_link[5:]
                
            # Handle invite links
            if chat_link.startswith('+') or chat_link.startswith('joinchat/'):
                # For invite links, we need to join the chat first to get the ID
                # This requires the bot to be added to the chat
                self.logger.warning(f"Invite link detected: {chat_link}. Bot must be added to the chat first.")
                return None
                
            # For public channels/groups, use the username
            return f"@{chat_link}"
            
        except Exception as e:
            self.logger.error(f"Error resolving chat ID: {e}")
            return None
    
    def validate_config(self) -> bool:
        """Validate configuration"""
        required_fields = [
            'bot_token'
        ]
        
        missing_fields = []
        for field in required_fields:
            if field == 'bot_token':
                # Check both environment variable and config file
                token = os.getenv('BOT_TOKEN') or self.config_data.get('bot_token', '')
                if not token:
                    missing_fields.append(field)
                    self.logger.error(f"bot_token not found in environment or config file")
                else:
                    self.logger.info(f"bot_token found: {token[:10]}...")
            else:
                value = getattr(self, field, None)
                if not value:
                    missing_fields.append(field)
                    
        if missing_fields:
            self.logger.error(f"Missing required configuration fields: {missing_fields}")
            return False
            
        # Check if we have either IDs or links
        if not (self.source_group_id or self.config_data.get('source_group_link')):
            self.logger.error("Either SOURCE_GROUP_ID or SOURCE_GROUP_LINK must be provided")
            return False
            
        if not (self.admin_group_id or self.config_data.get('admin_group_link')):
            self.logger.error("Either ADMIN_GROUP_ID or ADMIN_GROUP_LINK must be provided")
            return False
            
        if not (self.target_channel_id or self.config_data.get('target_channel_link')):
            self.logger.error("Either TARGET_CHANNEL_ID or TARGET_CHANNEL_LINK must be provided")
            return False
            
        self.logger.info("Configuration validation passed")
        return True
        
    def __str__(self) -> str:
        """String representation of config (with sensitive data masked)"""
        safe_config = self.config_data.copy()
        if 'bot_token' in safe_config:
            safe_config['bot_token'] = '***MASKED***'
        return json.dumps(safe_config, indent=2, ensure_ascii=False)
