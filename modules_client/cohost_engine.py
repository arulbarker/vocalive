# modules_client/cohost_engine.py

import json
import os
import logging
from pathlib import Path

logger = logging.getLogger('StreamMate')

class CohostEngine:
    """Engine untuk mengelola CoHost AI"""
    
    def __init__(self):
        """Initialize CoHost Engine"""
        self.config_path = Path("config/live_state.json")
        self.settings_path = Path("config/settings.json")
        self.voice_config = None
        self.cohost_name = "CoHost"
        self.load_config()
        logger.info("[COHOST] ✅ CoHost Engine initialized")
    
    def load_config(self):
        """Load configuration for CoHost"""
        try:
            # Load live state config
            if self.config_path.exists():
                with open(self.config_path, "r", encoding='utf-8') as f:
                    self.voice_config = json.load(f)
            
            # Load settings config
            if self.settings_path.exists():
                with open(self.settings_path, "r", encoding='utf-8') as f:
                    settings = json.load(f)
                    self.cohost_name = settings.get("cohost_name", "CoHost")
            
            logger.info(f"[COHOST] ✅ Configuration loaded for {self.cohost_name}")
        except Exception as e:
            logger.warning(f"[COHOST] ⚠️ Failed to load config: {e}")
    
    def get_voice_settings(self):
        """Get current voice settings"""
        if self.voice_config:
            return {
                "voice": self.voice_config.get("voice", "id-ID-Wavenet-A"),
                "use_virtual_mic": self.voice_config.get("virtual_mic_active", False),
                "device_index": self.voice_config.get("virtual_mic_device_index", None)
            }
        return {
            "voice": "id-ID-Wavenet-A",
            "use_virtual_mic": False,
            "device_index": None
        }
    
    def respond_with_voice(self, prompt):
        """Respond with voice using TTS"""
        try:
            logger.info(f"[COHOST] 🧠 {self.cohost_name} responding: {prompt[:50]}...")
            
            # Get voice settings
            voice_settings = self.get_voice_settings()
            
            # Import TTS function
            try:
                from modules.tts_google import speak_with_google_cloud
                
                if voice_settings["use_virtual_mic"] and voice_settings["device_index"] is not None:
                    speak_with_google_cloud(
                        prompt, 
                        voice_settings["voice"], 
                        device_index=voice_settings["device_index"], 
                        also_play_on_speaker=True
                    )
                else:
                    speak_with_google_cloud(
                        prompt, 
                        voice_settings["voice"], 
                        also_play_on_speaker=True
                    )
                
                logger.info("[COHOST] ✅ Voice response completed")
                
            except ImportError:
                # Fallback to server TTS if modules.tts_google not available
                logger.info("[COHOST] 🔄 Using server TTS as fallback")
                from modules_server.tts_engine import speak
                speak(
                    text=prompt,
                    language_code="id-ID",
                    voice_name=voice_settings["voice"]
                )
                
        except Exception as e:
            logger.error(f"[COHOST] ❌ Voice response failed: {e}")
    
    def generate_response(self, message, author="User"):
        """Generate AI response (placeholder for future AI integration)"""
        # This is a placeholder for AI response generation
        # In the future, this could integrate with DeepSeek or other AI
        responses = [
            f"Terima kasih {author} atas komentarnya!",
            f"Halo {author}! Senang melihat Anda di sini!",
            f"Pertanyaan yang menarik dari {author}!",
            f"Saya setuju dengan {author}!",
            f"Terima kasih sudah bergabung, {author}!"
        ]
        
        # Simple response selection (can be enhanced with AI later)
        import random
        response = random.choice(responses)
        
        logger.info(f"[COHOST] 💬 Generated response for {author}: {response}")
        return response
    
    def process_chat_message(self, message, author="User", respond_with_voice=True):
        """Process incoming chat message and optionally respond with voice"""
        try:
            logger.info(f"[COHOST] 📨 Processing message from {author}: {message}")
            
            # Generate response
            response = self.generate_response(message, author)
            
            # Respond with voice if enabled
            if respond_with_voice:
                self.respond_with_voice(response)
            
            return response
            
        except Exception as e:
            logger.error(f"[COHOST] ❌ Failed to process message: {e}")
            return None

# Legacy function for backward compatibility
def respond_with_voice(prompt):
    """Legacy function for backward compatibility"""
    cohost = CohostEngine()
    cohost.respond_with_voice(prompt)

