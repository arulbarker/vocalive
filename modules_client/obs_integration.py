"""
OBS WebSocket Integration for CoHost Seller
Handles automatic scene switching based on product triggers
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, Optional, Any
import threading
import time

try:
    import obsws_python as obs
    OBS_AVAILABLE = True
except ImportError:
    OBS_AVAILABLE = False
    print("obs-websocket-py not installed. OBS integration disabled.")

logger = logging.getLogger('StreamMate.OBS')

class OBSIntegration:
    """OBS WebSocket integration for automatic scene switching"""
    
    def __init__(self):
        self.client = None
        self.connected = False
        self.host = "localhost"
        self.port = 4455
        self.password = ""
        self.config_file = Path("config/obs_config.json")
        self.scene_mappings = {}
        self.load_config()
        
    def load_config(self):
        """Load OBS configuration from file"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.host = config.get("host", "localhost")
                    self.port = config.get("port", 4455)
                    self.password = config.get("password", "")
                    self.scene_mappings = config.get("scene_mappings", {})
                    logger.info(f"OBS config loaded: {self.host}:{self.port}")
            else:
                self.save_config()
        except Exception as e:
            logger.error(f"Error loading OBS config: {e}")
    
    def save_config(self):
        """Save OBS configuration to file"""
        try:
            config = {
                "host": self.host,
                "port": self.port,
                "password": self.password,
                "scene_mappings": self.scene_mappings
            }
            
            # Ensure config directory exists
            self.config_file.parent.mkdir(exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            logger.info("OBS config saved")
        except Exception as e:
            logger.error(f"Error saving OBS config: {e}")
    
    def connect(self) -> bool:
        """Connect to OBS WebSocket"""
        if not OBS_AVAILABLE:
            logger.error("OBS WebSocket library not available")
            return False
            
        try:
            self.client = obs.ReqClient(
                host=self.host,
                port=self.port,
                password=self.password,
                timeout=3
            )
            
            # Test connection
            version_info = self.client.get_version()
            self.connected = True
            logger.info(f"Connected to OBS Studio {version_info.obs_version}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to OBS: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Disconnect from OBS WebSocket"""
        try:
            if self.client:
                self.client.disconnect()
                self.connected = False
                logger.info("Disconnected from OBS")
        except Exception as e:
            logger.error(f"Error disconnecting from OBS: {e}")
    
    def test_connection(self) -> Dict[str, Any]:
        """Test OBS connection and return status"""
        if not OBS_AVAILABLE:
            return {
                "connected": False,
                "error": "OBS WebSocket library not installed"
            }
        
        try:
            if self.connect():
                scenes = self.get_scene_list()
                current_scene = self.get_current_scene()
                self.disconnect()
                
                return {
                    "connected": True,
                    "scenes": scenes,
                    "current_scene": current_scene,
                    "obs_version": "Connected successfully"
                }
            else:
                return {
                    "connected": False,
                    "error": "Connection failed"
                }
        except Exception as e:
            return {
                "connected": False,
                "error": str(e)
            }
    
    def get_scene_list(self) -> list:
        """Get list of available scenes from OBS"""
        try:
            if not self.connected:
                if not self.connect():
                    return []
            
            scenes_response = self.client.get_scene_list()
            scenes = [scene['sceneName'] for scene in scenes_response.scenes]
            logger.info(f"Available scenes: {scenes}")
            return scenes
            
        except Exception as e:
            logger.error(f"Error getting scene list: {e}")
            return []
    
    def get_current_scene(self) -> str:
        """Get current active scene"""
        try:
            if not self.connected:
                if not self.connect():
                    return ""
            
            current_scene = self.client.get_current_program_scene()
            return current_scene.current_program_scene_name
            
        except Exception as e:
            logger.error(f"Error getting current scene: {e}")
            return ""
    
    def switch_scene(self, scene_name: str) -> bool:
        """Switch to specified scene"""
        try:
            if not self.connected:
                if not self.connect():
                    logger.error("Cannot connect to OBS for scene switch")
                    return False
            
            # Check if scene exists
            available_scenes = self.get_scene_list()
            if scene_name not in available_scenes:
                logger.error(f"Scene '{scene_name}' not found in OBS. Available: {available_scenes}")
                return False
            
            # Switch scene
            self.client.set_current_program_scene(scene_name)
            logger.info(f"✅ Switched to scene: {scene_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error switching scene to '{scene_name}': {e}")
            return False
    
    def add_scene_mapping(self, trigger: str, scene_name: str, product_name: str = ""):
        """Add scene mapping for product trigger"""
        self.scene_mappings[trigger.lower()] = {
            "scene": scene_name,
            "product": product_name,
            "created_at": time.time()
        }
        self.save_config()
        logger.info(f"Scene mapping added: '{trigger}' → '{scene_name}'")
    
    def remove_scene_mapping(self, trigger: str):
        """Remove scene mapping"""
        trigger_lower = trigger.lower()
        if trigger_lower in self.scene_mappings:
            del self.scene_mappings[trigger_lower]
            self.save_config()
            logger.info(f"Scene mapping removed: '{trigger}'")
    
    def get_scene_for_trigger(self, trigger: str) -> Optional[str]:
        """Get scene name for given trigger"""
        trigger_lower = trigger.lower()
        mapping = self.scene_mappings.get(trigger_lower)
        if mapping:
            return mapping.get("scene")
        return None
    
    def handle_product_trigger(self, comment: str, available_triggers: Dict[str, Any]) -> bool:
        """
        Handle product trigger from comment and switch scene if matched
        
        Args:
            comment: User comment text
            available_triggers: Dict of trigger -> product data
            
        Returns:
            bool: True if scene was switched
        """
        comment_lower = comment.lower().strip()
        
        # Check each trigger
        for trigger, product_data in available_triggers.items():
            if trigger.lower() in comment_lower:
                scene_name = product_data.get("scene_obs", "")
                product_name = product_data.get("judul_barang", "")
                
                if scene_name:
                    logger.info(f"🎯 Trigger detected: '{trigger}' → Product: '{product_name}' → Scene: '{scene_name}'")
                    
                    if self.switch_scene(scene_name):
                        logger.info(f"✅ Scene switched successfully for product: {product_name}")
                        return True
                    else:
                        logger.error(f"❌ Failed to switch scene for product: {product_name}")
                        return False
                else:
                    logger.warning(f"⚠️ No scene configured for trigger: '{trigger}'")
                    return False
        
        return False
    
    def update_connection_settings(self, host: str, port: int, password: str = ""):
        """Update OBS connection settings"""
        self.host = host
        self.port = port
        self.password = password
        self.save_config()
        
        # Reconnect if was connected
        if self.connected:
            self.disconnect()
            self.connect()

# Global instance
obs_integration = OBSIntegration()

def get_obs_integration() -> OBSIntegration:
    """Get global OBS integration instance"""
    return obs_integration 