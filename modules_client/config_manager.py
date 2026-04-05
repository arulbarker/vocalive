"""Config Manager - Local configuration only"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger('VocaLive')

class ConfigManager:
    """Configuration manager for local settings"""
    
    def __init__(self, config_file: str = "config/settings.json"):
        self.config_file = Path(config_file)
        

    
    def get_api_key(self, key_name: str) -> Optional[str]:
        """Get API key from local config"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # Check in various possible locations
                if key_name in config:
                    return config[key_name]
                elif 'api_keys' in config and key_name in config['api_keys']:
                    return config['api_keys'][key_name]
                elif 'credentials' in config and key_name in config['credentials']:
                    return config['credentials'][key_name]
                    
        except Exception as e:
            logger.error(f"Error getting {key_name} from local config: {e}")
        
        return None
    

    
    def load_settings(self) -> Dict[str, Any]:
        """Load all settings from local config"""
        settings = {}
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
            except Exception as e:
                logger.error(f"Error loading local settings: {e}")
        
        logger.debug("Loading settings from local config only")
        
        return settings
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        settings = self.load_settings()
        return settings.get(key, default)
    
    def set(self, key: str, value: Any) -> bool:
        """Set configuration value (local only for now)"""
        try:
            settings = self.load_settings()
            settings[key] = value
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            logger.error(f"Error setting config {key}: {e}")
            return False
    
    def save(self) -> bool:
        """Save current settings"""
        try:
            settings = self.load_settings()
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            return False
    
    def get_all_settings(self) -> Dict[str, Any]:
        """Get all settings from configuration"""
        return self.load_settings()

# Global instance
config_manager = ConfigManager()

