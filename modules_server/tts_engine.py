#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VocaLive - Text-to-Speech Engine
Google Cloud Text-to-Speech implementation with fallback to pyttsx3
"""

import os
import sys
import json
import time
import logging
import tempfile
import threading
from pathlib import Path
from typing import Optional, Dict, Any

try:
    import pygame
except ImportError:
    pygame = None

try:
    import pyttsx3
except ImportError:
    pyttsx3 = None

try:
    from google.cloud import texttospeech
except ImportError:
    texttospeech = None

# Setup logging
logger = logging.getLogger('VocaLive')

class TTSEngine:
    """Text-to-Speech Engine with Google Cloud TTS and pyttsx3 fallback"""
    
    def __init__(self):
        self.google_client = None
        self.pyttsx3_engine = None
        self.voice_model = "id-ID-Standard-A"
        self.language_code = "id-ID"
        self.temp_dir = Path("temp")
        self.temp_dir.mkdir(exist_ok=True)
        
        # Initialize pygame mixer for audio playback
        self.pygame_available = False
        if pygame:
            try:
                pygame.mixer.init()
                self.pygame_available = True
            except Exception as e:
                logger.warning(f"Failed to initialize pygame mixer: {e}")
                self.pygame_available = False
        
        self._initialize_engines()
    
    def _initialize_engines(self):
        """Initialize TTS engines"""
        # Try to initialize Google Cloud TTS
        self._initialize_google_tts()
        
        # Initialize pyttsx3 as fallback
        if pyttsx3:
            try:
                self.pyttsx3_engine = pyttsx3.init()
                logger.info("pyttsx3 engine initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize pyttsx3: {e}")
    
    def _initialize_google_tts(self):
        """Initialize Google Cloud TTS using service account credentials"""
        if not texttospeech:
            logger.warning("Google Cloud TTS library not available")
            return
        
        try:
            # First, try to load credentials from settings.json
            settings = self._load_settings()
            credentials_path = settings.get('google_tts_credentials')
            
            if credentials_path and Path(credentials_path).exists():
                try:
                    with open(credentials_path, 'r') as f:
                        cred_data = json.load(f)
                    
                    # Check if it's service account credentials
                    if "type" in cred_data and cred_data["type"] == "service_account":
                        self.google_client = texttospeech.TextToSpeechClient.from_service_account_file(
                            credentials_path
                        )
                        logger.info(f"Google Cloud TTS initialized with credentials from settings: {credentials_path}")
                        return
                    else:
                        logger.warning(f"Invalid credentials format in {credentials_path}. Please use service account JSON file.")
                except Exception as e:
                    logger.warning(f"Failed to load credentials from {credentials_path}: {e}")
            
            # Fallback: Load service account credentials from default config
            config_path = Path("config/gcloud_tts_credentials.json")
            if config_path.exists():
                with open(config_path, 'r') as f:
                    cred_data = json.load(f)
                
                # Check if it's service account credentials and not placeholder
                if ("type" in cred_data and cred_data["type"] == "service_account" and 
                    not any("REPLACE_WITH" in str(value) for value in cred_data.values())):
                    self.google_client = texttospeech.TextToSpeechClient.from_service_account_file(
                        str(config_path)
                    )
                    logger.info("Google Cloud TTS initialized with service account credentials from config")
                    return
                else:
                    logger.warning("Invalid credentials format or placeholder values in gcloud_tts_credentials.json")
            
            # Try default credentials as fallback
            self.google_client = texttospeech.TextToSpeechClient()
            logger.info("Google Cloud TTS initialized with default credentials")
            
        except Exception as e:
            logger.warning(f"Failed to initialize Google Cloud TTS: {e}")
            logger.info("Please ensure valid Google Cloud TTS credentials are configured")
            self.google_client = None
    

    

    
    def _load_settings(self) -> Dict[str, Any]:
        """Load settings from config file"""
        try:
            settings_path = Path("config/settings.json")
            if settings_path.exists():
                with open(settings_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                
                # Update voice settings
                self.voice_model = settings.get('cohost_voice_model', 'id-ID-Standard-A')
                
                # Extract language code from voice model
                if '-' in self.voice_model:
                    parts = self.voice_model.split('-')
                    if len(parts) >= 2:
                        self.language_code = f"{parts[0]}-{parts[1]}"
                
                return settings
        except Exception as e:
            logger.warning(f"Failed to load settings: {e}")
        
        return {}
    
    def _calculate_credits(self, text: str) -> float:
        """Calculate TTS credits based on character count (for logging only)"""
        char_count = len(text)
        # Google TTS pricing: approximately 0.03 credits per character (logging only)
        return round(char_count * 0.03, 4)
    
    def _play_audio_file(self, file_path: str):
        """Play audio file using pygame"""
        if not self.pygame_available or not pygame:
            logger.warning("pygame not available for audio playback")
            return
        
        try:
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()
            
            # Wait for playback to complete
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
                
        except Exception as e:
            logger.error(f"Failed to play audio file: {e}")
    
    def speak_google_tts(self, text: str, voice_name: str = None, language_code: str = None) -> bool:
        """Speak text using Google Cloud TTS with optional voice override"""
        if not self.google_client:
            return False
        
        try:
            start_time = time.time()
            
            # Load current settings only if no override provided
            if not voice_name and not language_code:
                self._load_settings()
            
            # Use provided parameters or fall back to instance settings
            current_voice = voice_name or self.voice_model
            current_lang = language_code or self.language_code
            
            # Log TTS start
            logger.info(f"TTS started: {text[:50]}{'...' if len(text) > 50 else ''} (voice={current_voice}, lang={current_lang})")
            
            # Calculate and log credits (for monitoring only, no actual deduction)
            credits = self._calculate_credits(text)
            logger.info(f"TTS Usage logged: {len(text)} chars = {credits:.4f} credits (monitoring only)")
            
            # Prepare the synthesis input
            synthesis_input = texttospeech.SynthesisInput(text=text)
            
            # Build the voice request
            voice = texttospeech.VoiceSelectionParams(
                language_code=current_lang,
                name=current_voice
            )
            
            # Select the type of audio file
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3
            )
            
            # Perform the text-to-speech request
            response = self.google_client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            
            # Save audio to temporary file
            temp_file = self.temp_dir / f"tts_{hash(text) & 0xffffffff:08x}.mp3"
            with open(temp_file, "wb") as out:
                out.write(response.audio_content)
            
            # Play the audio
            self._play_audio_file(str(temp_file))
            
            # Clean up temporary file
            try:
                temp_file.unlink()
            except Exception:
                pass
            
            # Log completion
            duration = time.time() - start_time
            logger.info(f"TTS completed (Google Cloud) in {duration:.2f}s")
            
            return True
            
        except Exception as e:
            logger.error(f"Google TTS failed: {e}")
            return False
    
    def speak_pyttsx3(self, text: str) -> bool:
        """Speak text using pyttsx3 fallback"""
        if not self.pyttsx3_engine:
            return False
        
        try:
            logger.info(f"Using pyttsx3 fallback for TTS: {text[:50]}{'...' if len(text) > 50 else ''}")
            
            # Configure voice properties
            voices = self.pyttsx3_engine.getProperty('voices')
            if voices:
                # Try to use female voice if available
                for voice in voices:
                    if 'female' in voice.name.lower() or 'woman' in voice.name.lower():
                        self.pyttsx3_engine.setProperty('voice', voice.id)
                        break
            
            # Set speech rate
            self.pyttsx3_engine.setProperty('rate', 150)
            
            # Speak the text
            self.pyttsx3_engine.say(text)
            self.pyttsx3_engine.runAndWait()
            
            logger.info("TTS completed (pyttsx3 fallback)")
            return True
            
        except Exception as e:
            logger.error(f"pyttsx3 TTS failed: {e}")
            return False
    
    def speak(self, text: str, voice_name: str = None, language_code: str = None) -> bool:
        """Main speak function with fallback logic and voice override support"""
        if not text or not text.strip():
            return False
        
        # Clean the text
        text = text.strip()
        
        # Try Google TTS first with voice override
        if self.speak_google_tts(text, voice_name=voice_name, language_code=language_code):
            return True
        
        # Fallback to pyttsx3
        logger.warning("Google TTS failed, falling back to pyttsx3")
        if self.speak_pyttsx3(text):
            return True
        
        # If all fails
        logger.error("All TTS engines failed")
        return False

# Global TTS engine instance
_tts_engine = None
_tts_lock = threading.Lock()

def get_tts_engine() -> TTSEngine:
    """Get or create TTS engine instance (thread-safe)"""
    global _tts_engine
    
    if _tts_engine is None:
        with _tts_lock:
            if _tts_engine is None:
                _tts_engine = TTSEngine()
    
    return _tts_engine

def speak(text: str, language_code: str = "id-ID", voice_name: str = None, output_device=None, on_finished=None) -> bool:
    """Main speak function - entry point for TTS with compatibility parameters"""
    try:
        engine = get_tts_engine()
        
        # Use parameters directly without modifying engine instance
        # This ensures each call uses the specified voice without affecting other calls
        result = engine.speak(text, voice_name=voice_name, language_code=language_code)
        
        # Call on_finished callback if provided
        if on_finished and callable(on_finished):
            try:
                on_finished()
            except Exception as e:
                logger.warning(f"on_finished callback failed: {e}")
        
        return result
    except Exception as e:
        logger.error(f"TTS speak function failed: {e}")
        return False

# For backward compatibility
def speak_text(text: str) -> bool:
    """Alias for speak function"""
    return speak(text)

if __name__ == "__main__":
    # Test the TTS engine
    test_text = "Halo, ini adalah test Text-to-Speech engine VocaLive."
    print(f"Testing TTS with text: {test_text}")
    
    success = speak(test_text)
    print(f"TTS test {'successful' if success else 'failed'}")