# modules_client/sequential_greeting_manager.py - AI-Powered Greeting System

import time
import threading
import random
from datetime import datetime
from enum import Enum

from modules_client.config_manager import ConfigManager
import logging

logger = logging.getLogger("VocaLive.GreetingAI")

REGEN_INTERVAL_SECONDS = 7200  # 2 jam, tidak bisa diubah user


class GreetingState(Enum):
    IDLE            = "idle"
    PREPARING       = "preparing"
    ACTIVE          = "active"
    PAUSED          = "paused"
    WAITING_RESUME  = "waiting_resume"


def get_jittered_interval(base_seconds: float) -> float:
    """Tambah ±25% variasi acak pada interval — mencegah pola mekanikal."""
    factor = random.uniform(0.75, 1.25)
    return base_seconds * factor


class SequentialGreetingManager:
    """
    AI-Powered Greeting System
    - AI generate 10 sapaan unik setiap 2 jam
    - Startup: TTS pre-render semua 10 (audio plays once as side-effect)
    - Regen: hanya update text list, TTS di-render lazy saat pertama kali diputar
    - Putar acak dengan interval bervariasi (±25%)
    - Jika AI gagal, tetap pakai teks lama
    """

    def __init__(self):
        self.cfg = ConfigManager()

        self.state = GreetingState.IDLE
        self.is_enabled = False

        # Active greeting texts (list of str) — source of truth
        self.active_texts = []
        self.texts_lock = threading.Lock()

        # Threading
        self.playback_timer = None
        self.regen_timer = None
        self.should_stop = False
        self.thread_lock = threading.Lock()

        # Playback interval (dari settings, bisa diubah user)
        self.greeting_interval = 180

        # Trigger coordination
        self.trigger_active = False
        self.pending_resume_timer = None
        self.resume_delay = 3

        # Status callback untuk update UI
        self.status_callback = None

        logger.info("[GREETING_AI] Manager initialized")

    # ─── Public API ───────────────────────────────────────────────

    def start(self):
        """Start Greeting AI — generate teks + prerender TTS, lalu mulai playback."""
        with self.thread_lock:
            if self.state != GreetingState.IDLE:
                logger.info("[GREETING_AI] Already running")
                return

            self.is_enabled = self.cfg.get("greeting_ai_enabled", False)
            if not self.is_enabled:
                logger.info("[GREETING_AI] Disabled in settings")
                return

            self.greeting_interval = self.cfg.get("sequential_greeting_interval", 180)
            self.should_stop = False
            self.state = GreetingState.PREPARING

        self._notify_status("preparing", "Sedang menyiapkan sapaan AI...")

        prep_thread = threading.Thread(target=self._prepare_and_start, daemon=True)
        prep_thread.start()

    def stop(self):
        """Stop semua timer dan playback."""
        with self.thread_lock:
            if self.state == GreetingState.IDLE:
                return

            logger.info("[GREETING_AI] Stopping...")
            self.should_stop = True
            self.state = GreetingState.IDLE

            for t in [self.playback_timer, self.regen_timer, self.pending_resume_timer]:
                if t:
                    t.cancel()
            self.playback_timer = None
            self.regen_timer = None
            self.pending_resume_timer = None

        self._notify_status("idle", "Greeting AI tidak aktif")
        logger.info("[GREETING_AI] Stopped")

    def on_trigger_start(self):
        """Pause greeting saat trigger reply sedang diproses."""
        with self.thread_lock:
            if self.state == GreetingState.ACTIVE:
                self.state = GreetingState.PAUSED
                self.trigger_active = True
                if self.pending_resume_timer:
                    self.pending_resume_timer.cancel()
                    self.pending_resume_timer = None
                logger.info("[GREETING_AI] Paused for trigger reply")

    def on_trigger_complete(self):
        """Resume greeting setelah trigger reply selesai."""
        with self.thread_lock:
            if self.state == GreetingState.PAUSED:
                self.state = GreetingState.WAITING_RESUME
                self.trigger_active = False
                self.pending_resume_timer = threading.Timer(
                    self.resume_delay, self._resume_after_trigger
                )
                self.pending_resume_timer.start()
                logger.info(f"[GREETING_AI] Trigger done, resume in {self.resume_delay}s")

    def set_greeting_interval(self, seconds: float):
        """Update interval dari UI (Cohost Tab)."""
        self.greeting_interval = max(10, seconds)
        self.cfg.set("sequential_greeting_interval", self.greeting_interval)
        logger.info(f"[GREETING_AI] Interval set to {self.greeting_interval}s")

    def set_play_mode(self, mode: str):
        """Placeholder untuk backward compat — sistem ini selalu random."""
        pass

    def prepare_texts(self):
        """
        Generate 10 teks sapaan dan simpan ke active_texts.
        Bisa dipanggil sebelum start() — misalnya saat user toggle ON di Config tab.
        Tidak memulai playback timer.
        """
        if self.state not in (GreetingState.IDLE,):
            logger.info("[GREETING_AI] prepare_texts: sistem sedang berjalan, pakai force_regenerate")
            return
        self._notify_status("preparing", "Sedang menyiapkan sapaan AI...")
        prep_thread = threading.Thread(target=self._prepare_texts_only, daemon=True)
        prep_thread.start()

    def force_regenerate(self):
        """Manual trigger regenerasi dari tombol UI (bisa dipanggil kapan saja)."""
        logger.info("[GREETING_AI] Manual regenerate triggered")
        regen_thread = threading.Thread(target=self._regenerate, daemon=True)
        regen_thread.start()

    def get_status(self) -> dict:
        with self.texts_lock:
            text_count = len(self.active_texts)
        last_updated = self.cfg.get("greeting_ai_last_updated", None)
        return {
            "state": self.state.value,
            "enabled": self.is_enabled,
            "active_texts": text_count,
            "interval_seconds": self.greeting_interval,
            "last_updated": last_updated,
        }

    # ─── Internal ─────────────────────────────────────────────────

    def _prepare_texts_only(self):
        """Background thread: hanya generate teks, simpan ke active_texts. Tidak mulai timer."""
        try:
            texts = self._generate_texts()
            with self.texts_lock:
                self.active_texts = texts
            self._save_last_updated()
            self._notify_status("active", f"Siap — {len(texts)} sapaan tersedia (belum live)")
            logger.info(f"[GREETING_AI] Texts prepared: {len(texts)} items (waiting for live start)")
        except Exception as e:
            logger.error(f"[GREETING_AI] prepare_texts_only failed: {e}")
            self._notify_status("error", f"Gagal menyiapkan sapaan: {e}")

    def _prepare_and_start(self):
        """Background thread: generate AI texts (atau pakai yg sudah ada) lalu mulai playback."""
        try:
            # Cek apakah teks sudah di-prepare sebelumnya (misal saat user toggle ON)
            with self.texts_lock:
                already_prepared = len(self.active_texts) > 0

            if already_prepared:
                logger.info("[GREETING_AI] Using pre-prepared texts, skipping AI generation")
                with self.texts_lock:
                    texts = self.active_texts
            else:
                texts = self._generate_texts()
                with self.texts_lock:
                    self.active_texts = texts
                self._save_last_updated()

            if self.should_stop:
                return

            with self.thread_lock:
                if not self.should_stop:
                    self.state = GreetingState.ACTIVE

            self._notify_status("active", f"Aktif — {len(texts)} sapaan tersedia")
            self._schedule_next_playback()
            self._schedule_next_regen()

            logger.info(f"[GREETING_AI] Started with {len(texts)} texts")

        except Exception as e:
            logger.error(f"[GREETING_AI] Prepare failed: {e}")
            import traceback
            traceback.print_exc()
            with self.thread_lock:
                self.state = GreetingState.IDLE
            self._notify_status("error", f"Gagal menyiapkan sapaan: {e}")

    def _generate_texts(self) -> list:
        """Panggil AI generator, return list teks sapaan."""
        from modules_client.greeting_ai_generator import generate_greetings_with_ai
        logger.info("[GREETING_AI] Generating greeting texts via Gemini...")
        return generate_greetings_with_ai()

    def _get_voice_params(self) -> tuple:
        """Return (voice_name, language_code) dari settings."""
        voice_setting = self.cfg.get("tts_voice", "id-ID-Standard-A (FEMALE)")
        voice_name = voice_setting.split("(")[0].strip() if "(" in voice_setting else voice_setting

        if voice_name.startswith("Gemini-"):
            language_code = "id-ID"
        elif voice_name.startswith("ms-"):
            language_code = "ms-MY"
        elif voice_name.startswith("en-"):
            parts = voice_name.split("-")
            language_code = f"{parts[0]}-{parts[1]}" if len(parts) >= 2 else "en-US"
        else:
            language_code = "id-ID"

        return voice_name, language_code

    def _schedule_next_playback(self):
        """Schedule playback berikutnya dengan interval bervariasi."""
        if self.should_stop:
            return
        jittered = get_jittered_interval(self.greeting_interval)

        def callback():
            if not self.should_stop and self.state == GreetingState.ACTIVE:
                self._play_random_greeting()

        self.playback_timer = threading.Timer(jittered, callback)
        self.playback_timer.daemon = True
        self.playback_timer.start()
        logger.info(f"[GREETING_AI] Next playback in {jittered:.1f}s")

    def _play_random_greeting(self):
        """Pilih teks acak dan putar via cache (lazy render + simpan, hemat API)."""
        chosen_text = None
        with self.texts_lock:
            if self.active_texts:
                chosen_text = random.choice(self.active_texts)

        if not chosen_text:
            logger.info("[GREETING_AI] No active texts to play")
            self._schedule_next_playback()
            return

        try:
            from modules_client.greeting_tts_cache import get_greeting_cache
            voice_name, language_code = self._get_voice_params()
            cache = get_greeting_cache()
            success = cache.play_greeting_with_cache(
                text=chosen_text,
                voice_name=voice_name,
                language_code=language_code
            )
            logger.error(f"[GREETING_AI] {'Played' if success else 'Failed'}: {chosen_text[:40]}...")
        except Exception as e:
            logger.error(f"[GREETING_AI] Playback error: {e}")

        if not self.should_stop and self.state == GreetingState.ACTIVE:
            self._schedule_next_playback()

    def _schedule_next_regen(self):
        """Schedule regenerasi AI berikutnya (2 jam)."""
        if self.should_stop:
            return

        self.regen_timer = threading.Timer(REGEN_INTERVAL_SECONDS, self._regenerate)
        self.regen_timer.daemon = True
        self.regen_timer.start()
        logger.info(f"[GREETING_AI] Next regen in {REGEN_INTERVAL_SECONDS / 3600:.1f}h")

    def _regenerate(self):
        """
        Generate 10 teks baru + atomic swap text list.
        TIDAK prerender — TTS di-render lazy saat pertama kali diputar.
        Ini mencegah 10 audio bermain serentak di tengah siaran.
        """
        if self.should_stop:
            return

        logger.info("[GREETING_AI] Starting regeneration...")
        self._notify_status("regenerating", "Memperbarui sapaan AI...")

        try:
            new_texts = self._generate_texts()

            if self.should_stop:
                return

            # Hapus cache audio lama sebelum teks baru aktif
            try:
                from modules_client.greeting_tts_cache import get_greeting_cache
                get_greeting_cache().cleanup_greeting_audio()
            except Exception as ce:
                logger.error(f"[GREETING_AI] Cache cleanup error (non-fatal): {ce}")

            with self.texts_lock:
                self.active_texts = new_texts

            self._save_last_updated()
            self._notify_status("active", f"Aktif — {len(new_texts)} sapaan diperbarui")
            logger.info(f"[GREETING_AI] Regeneration done — {len(new_texts)} new texts loaded")

        except Exception as e:
            logger.error(f"[GREETING_AI] Regeneration failed: {e}")
            self._notify_status("active", "Aktif — pakai sapaan sebelumnya")

        if not self.should_stop:
            self._schedule_next_regen()

    def _resume_after_trigger(self):
        """Resume playback setelah jeda trigger selesai."""
        with self.thread_lock:
            if self.state == GreetingState.WAITING_RESUME and not self.should_stop:
                self.state = GreetingState.ACTIVE
                logger.info("[GREETING_AI] Resumed after trigger")
                self._schedule_next_playback()

    def _save_last_updated(self):
        ts = datetime.now().strftime("%H:%M")
        self.cfg.set("greeting_ai_last_updated", ts)

    def _notify_status(self, state: str, message: str):
        if self.status_callback and callable(self.status_callback):
            try:
                self.status_callback(state, message)
            except Exception as e:
                logger.error(f"[GREETING_AI] Status callback error: {e}")


# Global instance
_sequential_greeting_manager = None


def get_sequential_greeting_manager():
    global _sequential_greeting_manager
    if _sequential_greeting_manager is None:
        _sequential_greeting_manager = SequentialGreetingManager()
    return _sequential_greeting_manager
