# modules_client/greeting_tts_cache.py - TTS Cache Manager untuk Custom Greeting System

import os
import json
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from modules_server.tts_engine import speak, get_tts_engine
import shutil

class GreetingTTSCache:
    """Manage TTS cache for custom greeting system with hash-based filenames"""
    
    def __init__(self, cache_dir="greeting_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
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
                print(f"[TTS_CACHE] Error loading metadata: {e}")
                return {}
        return {}
    
    def _save_metadata(self):
        """Save cache metadata"""
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[TTS_CACHE] Error saving metadata: {e}")
    
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

                    print(f"[TTS_CACHE] ✅ Cache HIT - Using cached file: {filename}")
                    return str(file_path)

        print(f"[TTS_CACHE] ❌ Cache MISS - Need to generate TTS")
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
                print(f"[TTS_CACHE] File already cached: {cached_file}")
                return cached_file

        print(f"[TTS_CACHE] 🔄 Generating NEW TTS (will save to cache): {text[:50]}...")

        try:
            # Import TTS engine
            from modules_server import tts_engine
            import tempfile
            import glob

            # Detect file extension based on voice (Gemini uses WAV, others use MP3)
            is_gemini = voice_name and voice_name.startswith('Gemini-')
            extension = ".wav" if is_gemini else ".mp3"

            # Create temp directory to monitor for generated files
            temp_dir = Path("temp")
            temp_dir.mkdir(exist_ok=True)

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

                    print(f"[TTS_CACHE] ✅ Saved to cache: {cache_filename} ({file_size} bytes)")

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
                    print(f"[TTS_CACHE] ⚠️ TTS generated but audio file not found")
                    return None
            else:
                print(f"[TTS_CACHE] ❌ Failed to generate TTS")
                return None

        except Exception as e:
            print(f"[TTS_CACHE] ❌ Error generating and saving TTS: {e}")
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
            print(f"[TTS_CACHE] 💰 API SAVED! Playing from cache (no API call)")

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

                    print(f"[TTS_CACHE] ✅ Played from cache successfully (Total API calls saved: {self.metadata[hash_key].get('api_calls_saved', 0)})")

                    # Execute callback if provided
                    if on_finished and callable(on_finished):
                        try:
                            on_finished()
                        except Exception as cb_error:
                            print(f"[TTS_CACHE] Callback error: {cb_error}")

                    return True
                else:
                    print(f"[TTS_CACHE] ⚠️ Failed to play cached file, will regenerate")
                    # Fall through to regeneration

            except Exception as e:
                print(f"[TTS_CACHE] ⚠️ Error playing cached file: {e}, will regenerate")
                import traceback
                traceback.print_exc()
                # Fall through to regeneration

        # CACHE MISS - Generate new TTS and save to cache
        print(f"[TTS_CACHE] 💸 API CALL - Generating NEW TTS and saving to cache")

        cached_path = self.generate_and_save_tts(text, voice_name, language_code)

        if cached_path:
            print(f"[TTS_CACHE] ✅ Generated and cached successfully")

            # Execute callback if provided
            if on_finished and callable(on_finished):
                try:
                    on_finished()
                except Exception as cb_error:
                    print(f"[TTS_CACHE] Callback error: {cb_error}")

            return True
        else:
            print(f"[TTS_CACHE] ❌ Failed to generate and cache TTS")
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
                            print(f"[TTS_CACHE] Cleaned old file: {filename}")
                        
                        del self.metadata[hash_key]
                        cleaned_count += 1
                        
                except (ValueError, KeyError) as e:
                    print(f"[TTS_CACHE] Error processing metadata entry: {e}")
                    # Remove corrupted metadata entry
                    del self.metadata[hash_key]
                    cleaned_count += 1
            
            if cleaned_count > 0:
                self._save_metadata()
                print(f"[TTS_CACHE] Cleaned {cleaned_count} old cache files")
            
        except Exception as e:
            print(f"[TTS_CACHE] Error during cleanup: {e}")
    
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
                    print(f"[TTS_CACHE] Batch render {i+1}/{len(texts)}: {target_filename}")
                else:
                    print(f"[TTS_CACHE] Slot {i+1} gagal di-render, skip")
            except Exception as e:
                print(f"[TTS_CACHE] Slot {i+1} error: {e}, skip")

        print(f"[TTS_CACHE] Batch '{batch_id}': {len(successful_files)}/{len(texts)} slot berhasil")
        return successful_files

    def swap_batch(self, old_batch_id: str, new_files: list) -> list:
        """
        Atomic swap: ganti referensi active_files ke new_files.
        Hapus file dengan prefix old_batch_id setelah swap.
        Return new_files yang dipakai. Return [] jika new_files kosong.
        """
        if not new_files:
            print(f"[TTS_CACHE] swap_batch aborted — new_files kosong, batch lama dipertahankan")
            return []
        if old_batch_id:
            self.cleanup_batch(old_batch_id)
        print(f"[TTS_CACHE] Atomic swap selesai — {len(new_files)} file aktif")
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
                print(f"[TTS_CACHE] Gagal hapus {f.name}: {e}")
        if deleted:
            print(f"[TTS_CACHE] Cleaned {deleted} file batch '{batch_id}'")

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
            print(f"[TTS_CACHE] Error getting stats: {e}")
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