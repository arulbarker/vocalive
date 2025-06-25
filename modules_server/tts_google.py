# modules_server/tts_google.py
import os
import sys
import json
import logging
import tempfile
import threading
from pathlib import Path
from google.cloud import texttospeech
from dotenv import load_dotenv
import sounddevice as sd
import soundfile as sf
import time
import traceback

# Load environment variables
load_dotenv()

logger = logging.getLogger('StreamMate')

def speak_with_google_cloud(
    text: str,
    voice_name: str = "id-ID-Standard-A",
    language_code: str = "id-ID",
    device_index: int = None,
    also_play_on_speaker: bool = True,
    on_finished: callable = None
):
    """
    Advanced Google Cloud TTS dengan voice model yang spesifik
    
    Args:
        text (str): Text to synthesize
        voice_name (str): Voice model name (e.g. 'id-ID-Standard-A')
        language_code (str): Language code (e.g. 'id-ID')
        device_index (int): Audio output device
        also_play_on_speaker (bool): Play on default speaker
        on_finished (callable): Callback when finished
    """
    try:
        # Import Google Cloud TTS
        print(f"[GCLOUD-TTS] Google Cloud TTS imported successfully")
        
        # Create client
        client = texttospeech.TextToSpeechClient()
        print(f"[GCLOUD-TTS] Client created successfully")
        
        # Parse voice name to get language and gender
        voice_info = _parse_voice_name(voice_name)
        actual_lang = language_code or voice_info.get('language', 'id-ID')
        
        print(f"[GCLOUD-TTS] Voice request: {voice_name}")
        print(f"[GCLOUD-TTS] Language: {actual_lang}")
        print(f"[GCLOUD-TTS] Gender: {voice_info.get('gender', 'UNKNOWN')}")
        
        # Set the text input to be synthesized
        synthesis_input = texttospeech.SynthesisInput(text=text)
        
        # Build the voice request
        voice_gender = texttospeech.SsmlVoiceGender.NEUTRAL
        if voice_info.get('gender') == 'MALE':
            voice_gender = texttospeech.SsmlVoiceGender.MALE
        elif voice_info.get('gender') == 'FEMALE':
            voice_gender = texttospeech.SsmlVoiceGender.FEMALE
        
        # Voice selection with fallback
        voice = texttospeech.VoiceSelectionParams(
            language_code=actual_lang,
            name=voice_name,  # Try exact voice name first
            ssml_gender=voice_gender,
        )
        
        # Select the type of audio file you want returned
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=1.0,  # Normal speed
            pitch=0.0,          # Normal pitch
            volume_gain_db=0.0  # Normal volume
        )
        
        # Apply voice-specific adjustments
        if voice_info.get('gender') == 'MALE':
            # Male voice adjustments
            audio_config.pitch = -2.0          # Slightly lower pitch
            audio_config.speaking_rate = 0.9   # Slightly slower
            print(f"[GCLOUD-TTS] Applied MALE voice adjustments")
        elif voice_info.get('gender') == 'FEMALE':
            # Female voice adjustments  
            audio_config.pitch = 1.0           # Slightly higher pitch
            audio_config.speaking_rate = 1.1   # Slightly faster
            print(f"[GCLOUD-TTS] Applied FEMALE voice adjustments")
        
        print(f"[GCLOUD-TTS] Making synthesis request...")
        
        # Perform the text-to-speech request
        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )
        
        print(f"[GCLOUD-TTS] ✅ Synthesis successful, audio size: {len(response.audio_content)} bytes")
        
        # Play the audio
        if also_play_on_speaker:
            _play_google_audio(response.audio_content, on_finished)
        else:
            print(f"[GCLOUD-TTS] Audio ready but playback skipped")
            if on_finished:
                on_finished()
                
    except ImportError as e:
        logger.error(f"[GCLOUD-TTS] Google Cloud TTS not available: {e}")
        print(f"[GCLOUD-TTS] ❌ Import error: {e}")
        if on_finished:
            on_finished()
    except Exception as e:
        logger.error(f"[GCLOUD-TTS] Synthesis error: {e}")
        print(f"[GCLOUD-TTS] ❌ Synthesis error: {e}")
        
        # Try to get more specific error info
        if hasattr(e, 'code'):
            print(f"[GCLOUD-TTS] Error code: {e.code}")
        if hasattr(e, 'details'):
            print(f"[GCLOUD-TTS] Error details: {e.details}")
            
        if on_finished:
            on_finished()

def _parse_voice_name(voice_name):
    """Parse voice name to extract language and gender info"""
    voice_info = {
        'language': 'id-ID',
        'gender': 'NEUTRAL'
    }
    
    if not voice_name:
        return voice_info
    
    try:
        # Load voice config untuk gender mapping
        from modules_server.tts_engine import _load_voice_config, _get_voice_gender_from_config, _get_voice_lang_from_config
        
        # Get gender from config
        gender = _get_voice_gender_from_config(voice_name)
        if gender:
            voice_info['gender'] = gender
            
        # Get language from config
        lang = _get_voice_lang_from_config(voice_name)
        if lang:
            voice_info['language'] = lang
            
        print(f"[GCLOUD-TTS] Parsed voice '{voice_name}': {voice_info}")
        
    except Exception as e:
        print(f"[GCLOUD-TTS] Error parsing voice name: {e}")
        
        # Fallback parsing berdasarkan nama
        if voice_name.startswith('id-ID'):
            voice_info['language'] = 'id-ID'
        elif voice_name.startswith('en-US'):
            voice_info['language'] = 'en-US'
        elif voice_name.startswith('en-GB'):
            voice_info['language'] = 'en-GB'
        elif voice_name.startswith('en-AU'):
            voice_info['language'] = 'en-AU'
        
        # Simple gender detection dari nama
        if 'Standard-A' in voice_name or 'Standard-C' in voice_name:
            voice_info['gender'] = 'FEMALE'
        elif 'Standard-B' in voice_name or 'Standard-D' in voice_name:
            voice_info['gender'] = 'MALE'
    
    return voice_info

def _play_google_audio(audio_content, on_finished=None):
    """Play audio content from Google Cloud TTS SILENTLY (no CMD popup)"""
    try:
        print(f"[GCLOUD-TTS] Playing audio content ({len(audio_content)} bytes) - SILENT MODE")
        
        # Import pydub untuk audio processing
        from pydub import AudioSegment
        import subprocess
        
        # Create temp file untuk audio
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
            temp_file.write(audio_content)
            temp_path = temp_file.name
        
        try:
            # Load audio dengan pydub (SILENTLY)
            print(f"[GCLOUD-TTS] Loading audio from temp file...")
            audio_segment = AudioSegment.from_mp3(temp_path)
            print(f"[GCLOUD-TTS] Audio loaded: {len(audio_segment)}ms duration")
            
            # Play audio dalam thread terpisah dengan SILENT mode
            def silent_play_thread():
                try:
                    # Use our enhanced _safe_audio_play function untuk silent playback
                    from modules_server.tts_engine import _safe_audio_play
                    
                    print(f"[GCLOUD-TTS] Using silent audio playback...")
                    success = _safe_audio_play(audio_segment)
                    
                    if success:
                        print(f"[GCLOUD-TTS] ✅ Silent playback completed")
                    else:
                        print(f"[GCLOUD-TTS] ⚠️ Silent playback failed, trying fallback")
                        
                        # Last resort fallback (sudah silent karena global suppression)
                        try:
                            from pydub.playback import play
                            play(audio_segment)
                            print(f"[GCLOUD-TTS] ✅ Fallback playback completed (silent)")
                                
                        except Exception as fallback_error:
                            print(f"[GCLOUD-TTS] ❌ Fallback playback error: {fallback_error}")
                    
                except Exception as e:
                    print(f"[GCLOUD-TTS] ❌ Silent playback error: {e}")
                finally:
                    # Cleanup
                    try:
                        Path(temp_path).unlink()
                        print(f"[GCLOUD-TTS] Temp file cleaned up")
                    except:
                        pass
                    
                    if on_finished:
                        try:
                            on_finished()
                            print(f"[GCLOUD-TTS] Callback executed")
                        except Exception as callback_error:
                            print(f"[GCLOUD-TTS] Callback error: {callback_error}")
            
            # Start silent playback thread
            thread = threading.Thread(target=silent_play_thread, daemon=True)
            thread.start()
            print(f"[GCLOUD-TTS] Silent playback thread started")
            
        except Exception as e:
            print(f"[GCLOUD-TTS] Audio processing error: {e}")
            # Cleanup on error
            try:
                Path(temp_path).unlink()
            except:
                pass
            if on_finished:
                on_finished()
                
    except ImportError:
        print(f"[GCLOUD-TTS] pydub not available for audio playback")
        if on_finished:
            on_finished()
    except Exception as e:
        print(f"[GCLOUD-TTS] Audio playback error: {e}")
        if on_finished:
            on_finished()

def test_google_cloud_tts():
    """Test function untuk Google Cloud TTS"""
    print("=== TESTING GOOGLE CLOUD TTS ===")
    
    test_voices = [
        ("id-ID-Standard-A", "Halo, ini adalah tes suara perempuan Indonesia"),
        ("id-ID-Standard-B", "Halo, ini adalah tes suara laki-laki Indonesia"),
        ("en-US-Standard-C", "Hello, this is a female English voice test"),
        ("en-US-Standard-D", "Hello, this is a male English voice test"),
    ]
    
    for voice_name, text in test_voices:
        print(f"\nTesting voice: {voice_name}")
        
        def test_callback():
            print(f"✅ {voice_name} test completed")
        
        speak_with_google_cloud(
            text=text,
            voice_name=voice_name,
            on_finished=test_callback
        )
        
        # Wait a bit between tests
        time.sleep(2)
    
    print("=== GOOGLE CLOUD TTS TEST COMPLETED ===")

if __name__ == "__main__":
    test_google_cloud_tts()
