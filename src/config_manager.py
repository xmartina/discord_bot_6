"""
Configuration Manager for Discord Monitoring Bot
Handles loading and validation of configuration settings
"""

import yaml
import os
from typing import Dict, Any, List, Optional
from pathlib import Path

class ConfigManager:
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self.config = self._load_config()
        self._validate_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as file:
                config = yaml.safe_load(file)
                return config
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML configuration: {e}")

    def _validate_config(self):
        """Validate required configuration fields"""
        required_fields = [
            'discord.token',
            'discord.user_id'
        ]

        for field in required_fields:
            if not self._get_nested_value(field):
                raise ValueError(f"Required configuration field missing or empty: {field}")

    def _get_nested_value(self, key: str) -> Any:
        """Get nested configuration value using dot notation"""
        keys = key.split('.')
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return None

        return value

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value with optional default"""
        value = self._get_nested_value(key)
        return value if value is not None else default

    def get_discord_token(self) -> str:
        """Get Discord bot token"""
        token = self.get('discord.token')
        if not token or token == "YOUR_BOT_TOKEN_HERE":
            raise ValueError("Discord bot token not configured. Please update config.yaml")
        return token

    def get_user_id(self) -> int:
        """Get Discord user ID for notifications"""
        user_id = self.get('discord.user_id')
        if not user_id or user_id == "YOUR_USER_ID_HERE":
            raise ValueError("Discord user ID not configured. Please update config.yaml")
        return int(user_id)

    def get_user_token(self) -> Optional[str]:
        """Get Discord user token for user monitoring"""
        token = self.get('discord.user_token')
        if not token or token == "YOUR_USER_TOKEN_HERE":
            return None
        return token

    def is_user_monitoring_enabled(self) -> bool:
        """Check if user monitoring is enabled"""
        return self.get('user_monitoring.enabled', True)

    def get_user_monitoring_interval(self) -> int:
        """Get user monitoring check interval in seconds"""
        return self.get('user_monitoring.check_interval', 7)

    def should_monitor_user_servers(self) -> bool:
        """Check if user servers should be monitored"""
        return self.get('user_monitoring.monitor_user_servers', True)

    def should_combine_monitoring(self) -> bool:
        """Check if bot and user monitoring should be combined"""
        return self.get('user_monitoring.combine_with_bot_monitoring', True)

    def get_notification_method(self) -> str:
        """Get notification method"""
        return self.get('notifications.method', 'discord_dm')

    def get_notification_frequency(self) -> str:
        """Get notification frequency"""
        return self.get('notifications.frequency', 'instant')

    def is_detailed_format(self) -> bool:
        """Check if detailed user format is enabled"""
        return self.get('notifications.detailed_format', True)

    def get_user_details_config(self) -> Dict[str, bool]:
        """Get user details configuration"""
        return self.get('user_details', {
            'include_username': True,
            'include_display_name': True,
            'include_user_id': True,
            'include_account_age': True,
            'include_avatar': True,
            'include_join_date': True,
            'include_verification_status': True
        })

    def should_monitor_all_servers(self) -> bool:
        """Check if all servers should be monitored"""
        return self.get('servers.monitor_all', True)

    def get_excluded_servers(self) -> List[int]:
        """Get list of excluded server IDs"""
        excluded = self.get('servers.excluded_servers', [])
        return [int(server_id) for server_id in excluded]

    def is_auto_discover_enabled(self) -> bool:
        """Check if auto-discovery is enabled"""
        return self.get('servers.auto_discover', True)

    def get_max_servers(self) -> int:
        """Get maximum number of servers to monitor"""
        return self.get('servers.max_servers', 100)

    def get_minimum_account_age_days(self) -> int:
        """Get minimum account age filter in days"""
        return self.get('filters.minimum_account_age_days', 0)

    def should_ignore_bots(self) -> bool:
        """Check if bot accounts should be ignored"""
        return self.get('filters.ignore_bots', True)

    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration"""
        return self.get('database', {
            'type': 'sqlite',
            'path': 'data/member_joins.db',
            'backup_enabled': True,
            'backup_interval_hours': 24
        })

    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration"""
        return self.get('logging', {
            'level': 'INFO',
            'file': 'logs/bot.log',
            'max_file_size_mb': 10,
            'backup_count': 5
        })

    def get_timezone(self) -> str:
        """Get configured timezone"""
        return self.get('timezone', 'UTC')

    def get_rate_limit_buffer(self) -> float:
        """Get rate limit buffer in seconds"""
        return self.get('performance.rate_limit_buffer', 1.0)

    def create_directories(self):
        """Create necessary directories"""
        directories = [
            'data',
            'logs',
            'backups'
        ]

        for directory in directories:
            Path(directory).mkdir(exist_ok=True)

    def update_config(self, key: str, value: Any):
        """Update configuration value and save to file"""
        keys = key.split('.')
        config_section = self.config

        # Navigate to the parent of the target key
        for k in keys[:-1]:
            if k not in config_section:
                config_section[k] = {}
            config_section = config_section[k]

        # Set the value
        config_section[keys[-1]] = value

        # Save to file
        with open(self.config_path, 'w', encoding='utf-8') as file:
            yaml.dump(self.config, file, default_flow_style=False, indent=2)

    def is_configured(self) -> bool:
        """Check if bot is properly configured"""
        try:
            self.get_discord_token()
            self.get_user_id()
            return True
        except ValueError:
            return False
