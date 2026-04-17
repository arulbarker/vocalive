"""
Google TTS Integration - Updated to use Supabase config
"""

import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

from modules_client.config_manager import config_manager

logger = logging.getLogger('VocaLive')

class GoogleTTS:
    """Google Cloud TTS client with Supabase credentials"""

    def __init__(self):
        self.credentials = None
        self._load_credentials()

    def _load_credentials(self):
        """Load Google credentials from Supabase"""
        try:
            # Try to get from Supabase first
            credentials_data = config_manager.get_google_credentials("tts")
            if credentials_data:
                # Create temporary credentials file
                temp_creds_file = Path(tempfile.gettempdir()) / "google_tts_credentials.json"
                with open(temp_creds_file, 'w', encoding='utf-8') as f:
                    json.dump(credentials_data, f, indent=2)

                os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = str(temp_creds_file)
                self.credentials = credentials_data
                logger.info("Google TTS credentials loaded from Supabase")
                return

            # Fallback to local file
            local_creds_file = Path("config/gcloud_tts_credentials.json")
            if local_creds_file.exists():
                with open(local_creds_file, 'r', encoding='utf-8') as f:
                    self.credentials = json.load(f)
                os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = str(local_creds_file)
                logger.info("Google TTS credentials loaded from local file")
            else:
                logger.warning("Google TTS credentials not found")

        except Exception as e:
            logger.error(f"Error loading Google TTS credentials: {e}")

    def speak_with_google_cloud(self, text: str, voice_name: str, language_code: str,
                               output_device: int = None, also_play_on_speaker: bool = True,
                               on_finished=None) -> bool:
        """Generate speech using Google Cloud TTS"""
        if not self.credentials:
            logger.error("Google TTS credentials not available")
            return False

        try:
            from google.cloud import texttospeech

            # Create client
            client = texttospeech.TextToSpeechClient()

            # Configure synthesis input
            synthesis_input = texttospeech.SynthesisInput(text=text)

            # Configure voice
            voice = texttospeech.VoiceSelectionParams(
                language_code=language_code,
                name=voice_name
            )

            # Configure audio
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3
            )

            # Perform synthesis
            response = client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )

            # Save to temporary file
            temp_file = Path(tempfile.gettempdir()) / "tts_output.mp3"
            with open(temp_file, "wb") as out:
                out.write(response.audio_content)

            # Play audio
            self._play_audio(str(temp_file), output_device, also_play_on_speaker, on_finished)

            logger.info(f"Google TTS completed: {len(text)} chars")
            return True

        except Exception as e:
            logger.error(f"Google TTS error: {e}")
            return False

    def _play_audio(self, file_path: str, output_device: int = None,
                    also_play_on_speaker: bool = True, on_finished=None):
        """Play audio file"""
        try:
            import pygame

            pygame.mixer.init()
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()

            # Wait for completion
            while pygame.mixer.music.get_busy():
                pygame.time.wait(100)

            if on_finished:
                on_finished()

        except Exception as e:
            logger.error(f"Error playing audio: {e}")
            if on_finished:
                on_finished()

# Global instance
google_tts = GoogleTTS()

def speak_with_google_cloud(text: str, voice_name: str, language_code: str,
                           output_device: int = None, also_play_on_speaker: bool = True,
                           on_finished=None) -> bool:
    """Generate speech using Google Cloud TTS"""
    return google_tts.speak_with_google_cloud(
        text, voice_name, language_code, output_device, also_play_on_speaker, on_finished
    )
