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
import base64
import logging
import tempfile
import threading
from pathlib import Path
from typing import Optional, Dict, Any

try:
    import requests as _requests
except ImportError:
    _requests = None

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
        self.google_api_key = None   # plain API key (REST auth)
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
        """Initialize Google Cloud TTS — supports API key or service account credentials"""
        # Always try to load an API key from settings first (simplest auth)
        try:
            settings = self._load_settings()
            api_key = settings.get('google_tts_api_key', '').strip()
            if api_key:
                self.google_api_key = api_key
                logger.info("Google Cloud TTS will use API key authentication")
                return
        except Exception as e:
            logger.warning(f"Failed to read google_tts_api_key from settings: {e}")

        if not texttospeech:
            logger.warning("Google Cloud TTS library not available")
            return

        try:
            # Fall back to service account credentials
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
                self.voice_model = settings.get('tts_voice', settings.get('cohost_voice_model', 'id-ID-Standard-A'))
                
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
            # Stop and unload current track first to release file lock
            pygame.mixer.music.stop()
            pygame.mixer.music.unload()
            pygame.mixer.music.load(file_path)
            logger.info("[TTS] playback: started %s", file_path)
            pygame.mixer.music.play()

            # Wait for playback to complete
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)

            # Unload after playback so the file can be deleted
            pygame.mixer.music.unload()
            logger.info("[TTS] playback: finished")

        except Exception as e:
            logger.error(f"Failed to play audio file: {e}")
    
    def _speak_with_gemini(self, text: str, voice_name: str) -> bool:
        """Panggil Gemini 2.5 Flash Lite TTS API — voices multilingual, output WAV"""
        if not _requests:
            logger.warning("requests library not available for Gemini TTS")
            return False

        # voice_name: "Gemini-Puck" or "Gemini-Puck (MALE)" -> "Puck"
        raw_voice = voice_name.split('(')[0].strip().replace("Gemini-", "", 1)
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"gemini-2.5-flash-preview-tts:generateContent?key={self.google_api_key}"
        )
        payload = {
            "contents": [{"parts": [{"text": text}]}],
            "generationConfig": {
                "responseModalities": ["AUDIO"],
                "speechConfig": {
                    "voiceConfig": {
                        "prebuiltVoiceConfig": {"voiceName": raw_voice}
                    }
                }
            }
        }
        try:
            resp = _requests.post(url, json=payload, timeout=20)
            logger.info("[TTS] gemini_tts: status=%d", resp.status_code)
            resp.raise_for_status()
            data = resp.json()
            inline = data["candidates"][0]["content"]["parts"][0]["inlineData"]
            audio_b64 = inline["data"]
            mime_type = inline.get("mimeType", "audio/L16;rate=24000")
            audio_bytes = base64.b64decode(audio_b64)

            temp_file = self.temp_dir / f"tts_{int(time.time()*1000)}.wav"

            # Gemini TTS returns raw PCM (Linear16) — must wrap with WAV headers
            # otherwise pygame raises "Unknown WAVE format"
            sample_rate = 24000
            for part in mime_type.split(';'):
                part = part.strip()
                if part.startswith("rate="):
                    try:
                        sample_rate = int(part.split("=")[1])
                    except Exception:
                        pass

            import wave as _wave
            with _wave.open(str(temp_file), 'wb') as wf:
                wf.setnchannels(1)    # mono
                wf.setsampwidth(2)    # 16-bit PCM = 2 bytes
                wf.setframerate(sample_rate)
                wf.writeframes(audio_bytes)

            self._play_audio_file(str(temp_file))
            try:
                temp_file.unlink()
            except Exception:
                pass
            logger.info(f"TTS completed (Gemini Flash / {raw_voice}, {sample_rate}Hz)")
            return True
        except Exception as e:
            logger.error(f"Gemini TTS failed: {e}")
            return False

    def _speak_with_api_key(self, text: str, voice_name: str, language_code: str) -> bool:
        """Call Google Cloud TTS REST API using an API key (no service account needed)"""
        if not _requests:
            logger.warning("requests library not available for API key TTS")
            return False

        url = f"https://texttospeech.googleapis.com/v1/text:synthesize?key={self.google_api_key}"
        payload = {
            "input": {"text": text},
            "voice": {"languageCode": language_code, "name": voice_name},
            "audioConfig": {"audioEncoding": "MP3"}
        }
        try:
            resp = _requests.post(url, json=payload, timeout=15)
            logger.info("[TTS] cloud_tts: status=%d", resp.status_code)
            if not resp.ok:
                err = resp.json() if resp.headers.get("content-type","").startswith("application/json") else resp.text
                msg = err.get("error", {}).get("message", str(err)) if isinstance(err, dict) else str(err)[:300]
                logger.error(f"Google TTS {resp.status_code}: {msg}")
                # Hint if API not enabled on the key
                if resp.status_code in (400, 403) and ("not been used" in msg or "disabled" in msg or "not enabled" in msg):
                    logger.error("💡 Fix: buka Google Cloud Console → API key → Restrictions → enable 'Cloud Text-to-Speech API'")
                return False
            resp.raise_for_status()
            audio_bytes = base64.b64decode(resp.json()["audioContent"])
            temp_file = self.temp_dir / f"tts_{int(time.time()*1000)}.mp3"
            temp_file.write_bytes(audio_bytes)
            self._play_audio_file(str(temp_file))
            try:
                temp_file.unlink()
            except Exception:
                pass
            return True
        except Exception as e:
            logger.error(f"Google TTS (API key) failed: {e}")
            return False

    def speak_google_tts(self, text: str, voice_name: str = None, language_code: str = None) -> bool:
        """Speak text using Google Cloud TTS with optional voice override"""
        if not self.google_client and not self.google_api_key:
            return False
        
        # Load current settings if no voice override — so Gemini vs Standard routing is correct
        if not voice_name:
            self._load_settings()

        # Strip gender suffix e.g. "id-ID-Standard-A (FEMALE)" -> "id-ID-Standard-A"
        raw_voice = voice_name or self.voice_model
        current_voice = raw_voice.split('(')[0].strip()
        current_lang = language_code or self.language_code

        logger.info(f"TTS started: {text[:50]}{'...' if len(text) > 50 else ''} (voice={current_voice}, lang={current_lang})")
        logger.info("[TTS] routing: voice=%s → backend=%s", current_voice, "gemini" if current_voice.startswith("Gemini-") else "cloud_api")

        # --- Gemini Flash TTS path ---
        if self.google_api_key and current_voice.startswith("Gemini-"):
            return self._speak_with_gemini(text, current_voice)

        # --- Google Cloud TTS REST path (API key) ---
        if self.google_api_key:
            return self._speak_with_api_key(text, current_voice, current_lang)

        # --- Service account path (Python client library) ---
        if not self.google_client:
            return False

        try:
            start_time = time.time()

            credits = self._calculate_credits(text)
            logger.info(f"TTS Usage logged: {len(text)} chars = {credits:.4f} credits (monitoring only)")

            synthesis_input = texttospeech.SynthesisInput(text=text)
            voice = texttospeech.VoiceSelectionParams(
                language_code=current_lang,
                name=current_voice
            )
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3
            )

            response = self.google_client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )

            temp_file = self.temp_dir / f"tts_{int(time.time()*1000)}.mp3"
            with open(temp_file, "wb") as out:
                out.write(response.audio_content)

            self._play_audio_file(str(temp_file))
            try:
                temp_file.unlink()
            except Exception:
                pass

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
        logger.warning("[TTS] fallback: Google TTS gagal, menggunakan pyttsx3")
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

def reinitialize_tts_engine() -> bool:
    """Reset and recreate the global TTS engine instance (picks up new credentials/settings)"""
    global _tts_engine
    with _tts_lock:
        try:
            _tts_engine = TTSEngine()
            logger.info("TTS engine reinitialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to reinitialize TTS engine: {e}")
            _tts_engine = None
            return False

def speak(text: str, language_code: str = "id-ID", voice_name: str = None, output_device=None, on_finished=None, force_google_tts: bool = False) -> bool:
    """Main speak function - entry point for TTS with compatibility parameters"""
    logger.info("[TTS] speak: text_len=%d, voice=%s", len(text), voice_name)
    try:
        engine = get_tts_engine()

        if force_google_tts:
            result = engine.speak_google_tts(text, voice_name=voice_name, language_code=language_code)
        else:
            # Use parameters directly without modifying engine instance
            # This ensures each call uses the specified voice without affecting other calls
            result = engine.speak(text, voice_name=voice_name, language_code=language_code)

        # Call on_finished callback if provided
        if on_finished and callable(on_finished):
            try:
                on_finished()
            except Exception as e:
                logger.warning(f"on_finished callback failed: {e}")

        if result:
            try:
                from modules_client.telemetry import capture as _tel_capture
                _tel_capture("tts_played", {"voice": voice_name or "default"})
            except Exception:
                pass
        else:
            try:
                from modules_client.telemetry import capture as _tel_capture
                _tel_capture("tts_failed", {"voice": voice_name or "default", "error": "engine_speak_failed"})
            except Exception:
                pass

        return result
    except Exception as e:
        logger.error(f"TTS speak function failed: {e}")
        try:
            from modules_client.telemetry import capture as _tel_capture
            _tel_capture("tts_failed", {"voice": voice_name or "default", "error": "exception_in_speak"})
        except Exception:
            pass
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