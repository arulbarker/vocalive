# modules_client/greeting_tts_cache.py - TTS Cache Manager untuk Custom Greeting System

import hashlib
import json
import logging
import os
import shutil
import sys
from datetime import datetime, timedelta
from pathlib import Path

from modules_server.tts_engine import get_tts_engine, speak

logger = logging.getLogger("VocaLive.GreetingCache")


def _get_app_root() -> Path:
    """Root folder app: direktori EXE (frozen) atau root project (dev)."""
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).parent.parent


class GreetingTTSCache:
    """Manage TTS cache for custom greeting system with hash-based filenames"""

    def __init__(self, cache_dir=None):
        if cache_dir is None:
            cache_dir = _get_app_root() / "greeting_cache"
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Cache metadata file
        self.metadata_file = self.cache_dir / "cache_metadata.json"
        self.metadata = self._load_metadata()

    def _load_metadata(self):
        """Load cache metadata"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"[TTS_CACHE] Error loading metadata: {e}")
                return {}
        return {}

    def _save_metadata(self):
        """Save cache metadata"""
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"[TTS_CACHE] Error saving metadata: {e}")

    def _generate_hash(self, text, voice_name, language_code):
        """Generate hash for unique filename"""
        content = f"{text.strip()}_{voice_name}_{language_code}"
        hash_obj = hashlib.md5(content.encode('utf-8'))
        return hash_obj.hexdigest()[:12]  # Use first 12 characters

    def _generate_filename(self, text, voice_name, language_code, extension=".mp3"):
        """Generate filename based on content hash"""
        hash_str = self._generate_hash(text, voice_name, language_code)
        # Support both MP3 and WAV (Gemini uses WAV)
        return f"greeting_{hash_str}{extension}"

    def get_cached_file(self, text, voice_name, language_code):
        """Get cached TTS file if exists - check both MP3 and WAV"""
        if not text or not text.strip():
            return None

        hash_key = self._generate_hash(text, voice_name, language_code)

        # Check if we have metadata for this greeting
        if hash_key in self.metadata:
            # Try to find existing file (could be .mp3 or .wav)
            for extension in [".mp3", ".wav"]:
                filename = self._generate_filename(text, voice_name, language_code, extension)
                file_path = self.cache_dir / filename

                if file_path.exists():
                    # Update last used time in metadata
                    self.metadata[hash_key]["last_used"] = datetime.now().isoformat()
                    self.metadata[hash_key]["play_count"] = self.metadata[hash_key].get("play_count", 0) + 1
                    self._save_metadata()

                    logger.info(f"[TTS_CACHE] ✅ Cache HIT - Using cached file: {filename}")
                    return str(file_path)

        logger.info("[TTS_CACHE] ❌ Cache MISS - Need to generate TTS")
        return None

    def generate_and_save_tts(self, text, voice_name, language_code, force_regenerate=False):
        """Generate TTS via API and save the audio file to cache"""
        if not text or not text.strip():
            return None

        text = text.strip()
        hash_key = self._generate_hash(text, voice_name, language_code)

        # Check if already cached (unless force_regenerate)
        if not force_regenerate:
            cached_file = self.get_cached_file(text, voice_name, language_code)
            if cached_file:
                logger.info(f"[TTS_CACHE] File already cached: {cached_file}")
                return cached_file

        logger.info(f"[TTS_CACHE] 🔄 Generating NEW TTS (will save to cache): {text[:50]}...")

        try:
            # Import TTS engine
            import glob
            import tempfile

            from modules_server import tts_engine

            # Detect file extension based on voice (Gemini uses WAV, others use MP3)
            is_gemini = voice_name and voice_name.startswith('Gemini-')
            extension = ".wav" if is_gemini else ".mp3"

            # Create temp directory to monitor for generated files
            temp_dir = _get_app_root() / "temp"
            temp_dir.mkdir(parents=True, exist_ok=True)

            # Get list of existing temp files before generation
            before_files = set(temp_dir.glob("*.*"))

            # Generate TTS (this will create a temp file)
            success = speak(
                text=text,
                voice_name=voice_name,
                language_code=language_code,
                force_google_tts=True
            )

            if success:
                # Get list of new files after generation
                after_files = set(temp_dir.glob("*.*"))
                new_files = after_files - before_files

                # Find the newly generated audio file
                audio_file = None
                for file_path in new_files:
                    if file_path.suffix.lower() in ['.mp3', '.wav', '.ogg']:
                        audio_file = file_path
                        break

                if audio_file and audio_file.exists():
                    # Determine actual extension from generated file
                    actual_extension = audio_file.suffix

                    # Copy to cache directory
                    cache_filename = self._generate_filename(text, voice_name, language_code, actual_extension)
                    cache_path = self.cache_dir / cache_filename

                    shutil.copy2(str(audio_file), str(cache_path))
                    file_size = cache_path.stat().st_size

                    logger.info(f"[TTS_CACHE] ✅ Saved to cache: {cache_filename} ({file_size} bytes)")

                    # Save metadata
                    self.metadata[hash_key] = {
                        "text": text,
                        "voice_name": voice_name,
                        "language_code": language_code,
                        "filename": cache_filename,
                        "file_size": file_size,
                        "extension": actual_extension,
                        "created": datetime.now().isoformat(),
                        "last_used": datetime.now().isoformat(),
                        "play_count": 1,
                        "api_calls_saved": 0
                    }
                    self._save_metadata()

                    return str(cache_path)
                else:
                    logger.info("[TTS_CACHE] ⚠️ TTS generated but audio file not found")
                    return None
            else:
                logger.error("[TTS_CACHE] ❌ Failed to generate TTS")
                return None

        except Exception as e:
            logger.error(f"[TTS_CACHE] ❌ Error generating and saving TTS: {e}")
            import traceback
            traceback.print_exc()
            return None

    # Keep old method for backward compatibility
    def generate_and_cache_tts(self, text, voice_name, language_code, force_regenerate=False):
        """Alias for generate_and_save_tts (backward compatibility)"""
        return self.generate_and_save_tts(text, voice_name, language_code, force_regenerate)

    def play_from_cache_or_generate(self, text, voice_name, language_code, on_finished=None):
        """Smart TTS playback - use cache if available, otherwise generate and cache"""
        if not text or not text.strip():
            return False

        text = text.strip()
        hash_key = self._generate_hash(text, voice_name, language_code)

        # Try to get cached file first
        cached_file = self.get_cached_file(text, voice_name, language_code)

        if cached_file:
            # CACHE HIT - Play from file (NO API CALL!)
            logger.info("[TTS_CACHE] 💰 API SAVED! Playing from cache (no API call)")

            try:
                # Get TTS engine to play the cached file
                engine = get_tts_engine()

                # Estimate duration for playback
                estimated_duration = engine._estimate_audio_duration(text)

                # Play the cached audio file
                result = engine._play_audio_file(cached_file, estimated_duration)
                success = result.get('success', False) if isinstance(result, dict) else result

                if success:
                    # Update metadata - increment API calls saved counter
                    if hash_key in self.metadata:
                        self.metadata[hash_key]["api_calls_saved"] = self.metadata[hash_key].get("api_calls_saved", 0) + 1
                        self._save_metadata()

                    logger.info(f"[TTS_CACHE] ✅ Played from cache successfully (Total API calls saved: {self.metadata[hash_key].get('api_calls_saved', 0)})")

                    # Execute callback if provided
                    if on_finished and callable(on_finished):
                        try:
                            on_finished()
                        except Exception as cb_error:
                            logger.error(f"[TTS_CACHE] Callback error: {cb_error}")

                    return True
                else:
                    logger.error("[TTS_CACHE] ⚠️ Failed to play cached file, will regenerate")
                    # Fall through to regeneration

            except Exception as e:
                logger.error(f"[TTS_CACHE] ⚠️ Error playing cached file: {e}, will regenerate")
                import traceback
                traceback.print_exc()
                # Fall through to regeneration

        # CACHE MISS - Generate new TTS and save to cache
        logger.info("[TTS_CACHE] 💸 API CALL - Generating NEW TTS and saving to cache")

        cached_path = self.generate_and_save_tts(text, voice_name, language_code)

        if cached_path:
            logger.info("[TTS_CACHE] ✅ Generated and cached successfully")

            # Execute callback if provided
            if on_finished and callable(on_finished):
                try:
                    on_finished()
                except Exception as cb_error:
                    logger.error(f"[TTS_CACHE] Callback error: {cb_error}")

            return True
        else:
            logger.error("[TTS_CACHE] ❌ Failed to generate and cache TTS")
            return False

    # Keep old method for backward compatibility
    def play_cached_tts(self, text, voice_name, language_code):
        """Alias for play_from_cache_or_generate (backward compatibility)"""
        return self.play_from_cache_or_generate(text, voice_name, language_code)

    def cleanup_old_cache(self, max_age_days=30, max_unused_days=7):
        """Clean up old unused cache files"""
        try:
            current_time = datetime.now()
            cutoff_date = current_time - timedelta(days=max_age_days)
            unused_cutoff = current_time - timedelta(days=max_unused_days)

            cleaned_count = 0

            for hash_key, data in list(self.metadata.items()):
                try:
                    created_date = datetime.fromisoformat(data["created"])
                    last_used_date = datetime.fromisoformat(data["last_used"])

                    # Remove if too old or unused for too long
                    if created_date < cutoff_date or last_used_date < unused_cutoff:
                        filename = data["filename"]
                        file_path = self.cache_dir / filename

                        if file_path.exists():
                            file_path.unlink()
                            logger.info(f"[TTS_CACHE] Cleaned old file: {filename}")

                        del self.metadata[hash_key]
                        cleaned_count += 1

                except (ValueError, KeyError) as e:
                    logger.error(f"[TTS_CACHE] Error processing metadata entry: {e}")
                    # Remove corrupted metadata entry
                    del self.metadata[hash_key]
                    cleaned_count += 1

            if cleaned_count > 0:
                self._save_metadata()
                logger.info(f"[TTS_CACHE] Cleaned {cleaned_count} old cache files")

        except Exception as e:
            logger.error(f"[TTS_CACHE] Error during cleanup: {e}")

    def play_greeting_with_cache(self, text: str, voice_name: str, language_code: str) -> bool:
        """
        Play greeting dengan cache — hemat API call.
        Cache HIT: putar file, 0 API call.
        Cache MISS: generate via API → simpan ke cache → putar.
        """
        if not text or not text.strip():
            return False
        text = text.strip()

        # voice_name dari _get_voice_params sudah clean (sudah strip gender suffix)
        clean_voice = voice_name.split('(')[0].strip() if voice_name else ""
        is_gemini = clean_voice.startswith("Gemini-")
        ext = ".wav" if is_gemini else ".mp3"

        hash_key = self._generate_hash(text, clean_voice, language_code)
        cache_path = self.cache_dir / f"greeting_{hash_key}{ext}"

        if not cache_path.exists():
            logger.info(f"[TTS_CACHE] Cache MISS — generate: {text[:40]}...")
            ok = self._generate_audio_to_file(text, clean_voice, language_code, cache_path)
            if not ok:
                # Fallback: speak() langsung (1 API call, tidak di-cache)
                logger.info("[TTS_CACHE] generate gagal, fallback ke speak()")
                from modules_server.tts_engine import speak
                return speak(text=text, voice_name=voice_name, language_code=language_code)
        else:
            logger.info(f"[TTS_CACHE] Cache HIT — {cache_path.name}")

        from modules_server.tts_engine import get_tts_engine
        get_tts_engine()._play_audio_file(str(cache_path))
        return True

    def _generate_audio_to_file(self, text: str, clean_voice: str, language_code: str, cache_path: Path) -> bool:
        """Generate TTS audio via API dan simpan langsung ke cache_path (tanpa playback)."""
        try:
            import base64

            import requests

            from modules_server.tts_engine import get_tts_engine

            engine = get_tts_engine()
            api_key = engine.google_api_key
            if not api_key:
                logger.warning("[TTS_CACHE] Tidak ada API key — skip generate")
                return False

            if clean_voice.startswith("Gemini-"):
                raw_voice = clean_voice.replace("Gemini-", "", 1)
                url = (
                    "https://generativelanguage.googleapis.com/v1beta/models/"
                    f"gemini-2.5-flash-preview-tts:generateContent?key={api_key}"
                )
                payload = {
                    "contents": [{"parts": [{"text": text}]}],
                    "generationConfig": {
                        "responseModalities": ["AUDIO"],
                        "speechConfig": {
                            "voiceConfig": {"prebuiltVoiceConfig": {"voiceName": raw_voice}}
                        }
                    }
                }
                resp = requests.post(url, json=payload, timeout=20)
                resp.raise_for_status()
                data = resp.json()
                inline = data["candidates"][0]["content"]["parts"][0]["inlineData"]
                audio_bytes = base64.b64decode(inline["data"])
                mime_type = inline.get("mimeType", "audio/L16;rate=24000")

                sample_rate = 24000
                for part in mime_type.split(';'):
                    part = part.strip()
                    if part.startswith("rate="):
                        try:
                            sample_rate = int(part.split("=")[1])
                        except Exception:
                            pass

                import wave as _wave
                with _wave.open(str(cache_path), 'wb') as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)
                    wf.setframerate(sample_rate)
                    wf.writeframes(audio_bytes)
            else:
                url = f"https://texttospeech.googleapis.com/v1/text:synthesize?key={api_key}"
                payload = {
                    "input": {"text": text},
                    "voice": {"languageCode": language_code, "name": clean_voice},
                    "audioConfig": {"audioEncoding": "MP3"}
                }
                resp = requests.post(url, json=payload, timeout=15)
                resp.raise_for_status()
                audio_bytes = base64.b64decode(resp.json()["audioContent"])
                cache_path.write_bytes(audio_bytes)

            logger.info(f"[TTS_CACHE] ✅ Audio disimpan: {cache_path.name} ({cache_path.stat().st_size} bytes)")
            return True

        except Exception as e:
            logger.info(f"[TTS_CACHE] ❌ Generate audio gagal: {e}")
            try:
                if cache_path.exists():
                    cache_path.unlink()
            except Exception:
                pass
            return False

    def cleanup_greeting_audio(self) -> None:
        """Hapus semua file greeting_*.mp3/wav — dipanggil saat teks di-regenerate tiap 2 jam."""
        deleted = 0
        for f in self.cache_dir.glob("greeting_*.*"):
            if f.suffix.lower() in ('.mp3', '.wav'):
                try:
                    f.unlink()
                    deleted += 1
                except Exception as e:
                    logger.info(f"[TTS_CACHE] Gagal hapus {f.name}: {e}")
        if deleted:
            logger.info(f"[TTS_CACHE] Cleaned {deleted} file greeting audio lama")

    def prerender_batch(self, texts: list, voice_name: str, language_code: str, batch_id: str) -> list:
        """
        Pre-render list teks ke file audio dengan prefix batch_id.
        Return list path file yang berhasil di-render.
        Teks yang gagal di-skip (tidak crash).
        PENTING: Dipanggil dari background thread — tidak memutar audio.
        """
        successful_files = []

        for i, text in enumerate(texts):
            if not text or not text.strip():
                continue

            text = text.strip()
            is_gemini = voice_name and voice_name.startswith('Gemini-')
            extension = ".wav" if is_gemini else ".mp3"
            target_filename = f"greeting_ai_{batch_id}_{i:02d}{extension}"
            target_path = self.cache_dir / target_filename

            try:
                # generate_and_save_tts sudah handle: render → copy ke cache → return path
                # Tapi ia pakai nama file hash-based, kita perlu rename ke target_filename
                cached = self.generate_and_save_tts(text, voice_name, language_code)
                if cached and Path(cached).exists():
                    shutil.copy2(cached, str(target_path))
                    successful_files.append(str(target_path))
                    logger.info(f"[TTS_CACHE] Batch render {i+1}/{len(texts)}: {target_filename}")
                else:
                    logger.warning(f"[TTS_CACHE] Slot {i+1} gagal di-render, skip")
            except Exception as e:
                logger.error(f"[TTS_CACHE] Slot {i+1} error: {e}, skip")

        logger.info(f"[TTS_CACHE] Batch '{batch_id}': {len(successful_files)}/{len(texts)} slot berhasil")
        return successful_files

    def swap_batch(self, old_batch_id: str, new_files: list) -> list:
        """
        Atomic swap: ganti referensi active_files ke new_files.
        Hapus file dengan prefix old_batch_id setelah swap.
        Return new_files yang dipakai. Return [] jika new_files kosong.
        """
        if not new_files:
            logger.info("[TTS_CACHE] swap_batch aborted — new_files kosong, batch lama dipertahankan")
            return []
        if old_batch_id:
            self.cleanup_batch(old_batch_id)
        logger.info(f"[TTS_CACHE] Atomic swap selesai — {len(new_files)} file aktif")
        return new_files

    def cleanup_batch(self, batch_id: str) -> None:
        """Hapus semua file dengan prefix greeting_ai_{batch_id}_"""
        prefix = f"greeting_ai_{batch_id}_"
        deleted = 0
        for f in self.cache_dir.glob(f"{prefix}*"):
            try:
                f.unlink()
                deleted += 1
            except Exception as e:
                logger.info(f"[TTS_CACHE] Gagal hapus {f.name}: {e}")
        if deleted:
            logger.info(f"[TTS_CACHE] Cleaned {deleted} file batch '{batch_id}'")

    def get_files_for_batch(self, batch_id: str) -> list:
        """Return list path file yang ada untuk batch_id ini."""
        prefix = f"greeting_ai_{batch_id}_"
        return [str(f) for f in sorted(self.cache_dir.glob(f"{prefix}*"))]

    def get_cache_stats(self):
        """Get cache statistics"""
        try:
            total_files = len(self.metadata)
            total_size = sum(data.get("file_size", 0) for data in self.metadata.values())

            # Count files by age
            current_time = datetime.now()
            recent_count = 0  # Less than 7 days

            for data in self.metadata.values():
                try:
                    created_date = datetime.fromisoformat(data["created"])
                    if (current_time - created_date).days < 7:
                        recent_count += 1
                except (ValueError, KeyError):
                    pass

            return {
                "total_files": total_files,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "recent_files": recent_count,
                "cache_dir": str(self.cache_dir)
            }

        except Exception as e:
            logger.error(f"[TTS_CACHE] Error getting stats: {e}")
            return {
                "total_files": 0,
                "total_size_mb": 0,
                "recent_files": 0,
                "cache_dir": str(self.cache_dir)
            }

# Global cache instance
_greeting_cache = None

def get_greeting_cache():
    """Get global greeting cache instance"""
    global _greeting_cache
    if _greeting_cache is None:
        _greeting_cache = GreetingTTSCache()
    return _greeting_cache
