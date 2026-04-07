# Greeting AI System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ganti 10 slot sapaan manual dengan AI-generated greetings yang auto-regenerate setiap 2 jam, sehingga audio fingerprint selalu berubah dan tidak terdeteksi spam oleh TikTok.

**Architecture:** Buat module baru `greeting_ai_generator.py` untuk generasi teks, extend `greeting_tts_cache.py` dengan batch pre-render + atomic swap, lalu refactor `sequential_greeting_manager.py` agar tidak lagi baca slot dari config tapi dari AI. UI di `config_tab.py` diganti dari 10 input manual menjadi ON/OFF toggle + status indicator.

**Tech Stack:** Python 3.10, PyQt6, Gemini REST API (`generativelanguage.googleapis.com`), existing `modules_server/tts_engine.speak()`, `modules_client/config_manager.ConfigManager`

---

## File Map

| Aksi | File | Tanggung Jawab |
|------|------|----------------|
| **CREATE** | `modules_client/greeting_ai_generator.py` | Generate 10 teks via Gemini + clean_greeting_text() |
| **MODIFY** | `modules_client/greeting_tts_cache.py` | Tambah prerender_batch(), swap_batch(), cleanup_batch(), get_active_files() |
| **MODIFY** | `modules_client/sequential_greeting_manager.py` | Pakai AI generator + batch cache + jitter + 2h regen |
| **MODIFY** | `ui/config_tab.py` | Ganti 10 slot manual → ON/OFF toggle + status UI |
| **MODIFY** | `config/settings_default.json` | Tambah greeting_ai_enabled, greeting_ai_last_updated |

---

## Task 1: Module greeting_ai_generator.py

**Files:**
- Create: `modules_client/greeting_ai_generator.py`

- [ ] **Step 1: Buat file baru**

```python
# modules_client/greeting_ai_generator.py
"""
Greeting AI Generator — generate 10 sapaan unik via Gemini
Teks plain (tanpa tanda baca/simbol) untuk TTS yang bersih
"""

import re
import json
import logging
import time
import requests
from typing import List

from modules_client.config_manager import config_manager

logger = logging.getLogger('VocaLive')

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
GEMINI_MODEL    = "gemini-3.1-flash-lite-preview"
GEMINI_FALLBACK = "gemini-flash-lite-latest"

FALLBACK_GREETINGS = [
    "Halo semuanya selamat datang di live kami",
    "Hai guys makasih udah mampir ke sini",
    "Selamat datang di live streaming kita hari ini",
    "Halo teman teman senang banget ada kalian di sini",
    "Hai hai welcome di live kita",
    "Semuanya udah hadir nih makasih ya udah join",
    "Halo guys ayo nonton bareng bareng di sini",
    "Hai semuanya yuk kita mulai live hari ini",
    "Selamat datang guys semoga betah di sini ya",
    "Halo teman teman baru dan yang sudah setia nonton",
]


def clean_greeting_text(text: str) -> str:
    """Strip semua simbol — hanya huruf, angka, dan spasi."""
    cleaned = re.sub(r'[^\w\s]', '', text)
    return ' '.join(cleaned.split())


def _parse_greeting_response(raw: str) -> List[str]:
    """
    Parse respons Gemini menjadi list 10 string.
    Coba JSON array dulu, fallback ke parse per-baris.
    """
    raw = raw.strip()

    # Coba JSON array
    try:
        # Hapus markdown code fence jika ada
        if raw.startswith('```'):
            lines = raw.split('\n')
            raw = '\n'.join(lines[1:-1])
        data = json.loads(raw)
        if isinstance(data, list):
            greetings = [clean_greeting_text(str(g)) for g in data if str(g).strip()]
            if len(greetings) >= 5:
                return greetings[:10]
    except (json.JSONDecodeError, Exception):
        pass

    # Fallback: parse per-baris, ambil baris yang tidak kosong
    lines = [line.strip() for line in raw.split('\n') if line.strip()]
    greetings = []
    for line in lines:
        # Hapus prefix nomor seperti "1." atau "1)"
        line = re.sub(r'^\d+[\.\)]\s*', '', line)
        # Hapus tanda kutip di awal/akhir
        line = line.strip('"\'')
        cleaned = clean_greeting_text(line)
        if cleaned and len(cleaned) > 5:
            greetings.append(cleaned)

    return greetings[:10] if len(greetings) >= 5 else []


def generate_greetings_with_ai(retry_on_fail: bool = True) -> List[str]:
    """
    Generate 10 teks sapaan unik via Gemini.
    Gunakan user_context dari settings sebagai konteks.
    Return list 10 string plain text (tanpa tanda baca).
    Jika gagal, return FALLBACK_GREETINGS.
    """
    api_key = config_manager.get("api_keys", {}).get("GEMINI_API_KEY", "")
    if not api_key:
        logger.warning("[GREETING_AI] Tidak ada API key Gemini, pakai fallback greetings")
        return FALLBACK_GREETINGS.copy()

    user_context = config_manager.get("user_context", "").strip()
    context_line = f"Sesuai konteks berikut: {user_context}" if user_context else "untuk live streaming jualan online Indonesia"

    prompt = (
        f"Buatkan 10 variasi sapaan untuk live streaming TikTok {context_line}\n"
        "Syarat ketat:\n"
        "- Setiap sapaan 1 sampai 2 kalimat natural dan percakapan\n"
        "- Semua 10 sapaan berbeda satu sama lain dalam variasi kata gaya dan panjang\n"
        "- JANGAN gunakan tanda baca apapun termasuk titik koma tanda seru tanda tanya tanda kutip\n"
        "- JANGAN gunakan simbol markdown seperti bintang garis bawah pagar atau tanda kurung\n"
        "- Hanya huruf biasa dan spasi\n"
        'Format respons: JSON array dengan tepat 10 string\n'
        '["sapaan1", "sapaan2", "sapaan3", ...]'
    )

    headers = {
        "x-goog-api-key": api_key,
        "Content-Type": "application/json",
    }
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"maxOutputTokens": 600, "temperature": 0.9},
    }

    models = [GEMINI_MODEL, GEMINI_FALLBACK]
    for model in models:
        try:
            url = f"{GEMINI_API_BASE}/{model}:generateContent"
            resp = requests.post(url, headers=headers, json=payload, timeout=20)

            if resp.status_code == 200:
                data = resp.json()
                raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
                greetings = _parse_greeting_response(raw_text)

                if len(greetings) >= 5:
                    # Pad ke 10 jika kurang
                    while len(greetings) < 10:
                        greetings.append(greetings[len(greetings) % len(greetings)])
                    logger.info(f"[GREETING_AI] ✅ Generated {len(greetings)} greetings via {model}")
                    return greetings[:10]
                else:
                    logger.warning(f"[GREETING_AI] Response terlalu sedikit ({len(greetings)} item), coba model berikutnya")
                    continue

            elif resp.status_code == 403:
                logger.warning(f"[GREETING_AI] 403 pada {model}, coba fallback model")
                continue
            else:
                logger.error(f"[GREETING_AI] API error {resp.status_code}: {resp.text[:200]}")

        except requests.exceptions.Timeout:
            logger.warning(f"[GREETING_AI] Timeout pada {model}")
        except Exception as e:
            logger.error(f"[GREETING_AI] Error pada {model}: {e}")

    # Retry sekali setelah 30 detik jika diminta
    if retry_on_fail:
        logger.warning("[GREETING_AI] Semua model gagal, retry dalam 30 detik...")
        time.sleep(30)
        return generate_greetings_with_ai(retry_on_fail=False)

    logger.warning("[GREETING_AI] Gagal generate, pakai fallback greetings")
    return FALLBACK_GREETINGS.copy()
```

- [ ] **Step 2: Verifikasi manual — jalankan snippet di terminal**

```bash
cd "D:/VIBE CODING VERSION/STREAMMATE AI SELLER/vocalive"
python -c "
from modules_client.greeting_ai_generator import clean_greeting_text, generate_greetings_with_ai
# Test clean_greeting_text
assert clean_greeting_text('Halo **semua**!') == 'Halo semua'
assert clean_greeting_text('Selamat datang, guys!') == 'Selamat datang guys'
print('clean_greeting_text: OK')
# Test generate
results = generate_greetings_with_ai()
print(f'Generated {len(results)} greetings:')
for i, g in enumerate(results, 1):
    print(f'  {i}. {g}')
"
```

Expected: 10 baris sapaan tanpa tanda baca.

- [ ] **Step 3: Commit**

```bash
git add modules_client/greeting_ai_generator.py
git commit -m "feat: tambah greeting_ai_generator — generate 10 sapaan via Gemini"
```

---

## Task 2: Extend greeting_tts_cache.py — Batch Pre-render & Atomic Swap

**Files:**
- Modify: `modules_client/greeting_tts_cache.py` (tambah 4 method baru di akhir class, sebelum `get_cache_stats`)

- [ ] **Step 1: Tambah 4 method ke class `GreetingTTSCache`**

Sisipkan method-method ini **sebelum** method `get_cache_stats` (sekitar baris 296):

```python
    def prerender_batch(self, texts: list, voice_name: str, language_code: str, batch_id: str) -> list:
        """
        Pre-render list teks ke file audio dengan prefix batch_id.
        Return list path file yang berhasil di-render.
        Teks yang gagal di-skip (tidak crash).
        """
        successful_files = []

        for i, text in enumerate(texts):
            if not text or not text.strip():
                continue

            text = text.strip()
            is_gemini = voice_name and voice_name.startswith('Gemini-')
            extension = ".wav" if is_gemini else ".mp3"
            filename = f"greeting_ai_{batch_id}_{i:02d}{extension}"
            file_path = self.cache_dir / filename

            try:
                from modules_server import tts_engine
                from pathlib import Path
                import shutil

                temp_dir = Path("temp")
                temp_dir.mkdir(exist_ok=True)
                before_files = set(temp_dir.glob("*.*"))

                success = tts_engine.speak(
                    text=text,
                    voice_name=voice_name,
                    language_code=language_code,
                    force_google_tts=True
                )

                if success:
                    after_files = set(temp_dir.glob("*.*"))
                    new_files = after_files - before_files
                    audio_file = next(
                        (f for f in new_files if f.suffix.lower() in ['.mp3', '.wav']),
                        None
                    )
                    if audio_file and audio_file.exists():
                        shutil.copy2(str(audio_file), str(file_path))
                        successful_files.append(str(file_path))
                        print(f"[TTS_CACHE] ✅ Batch render {i+1}/10: {filename}")
                    else:
                        print(f"[TTS_CACHE] ⚠️ Slot {i+1} render OK tapi file tidak ditemukan, skip")
                else:
                    print(f"[TTS_CACHE] ⚠️ Slot {i+1} TTS gagal, skip")

            except Exception as e:
                print(f"[TTS_CACHE] ⚠️ Slot {i+1} error: {e}, skip")

        print(f"[TTS_CACHE] Batch '{batch_id}': {len(successful_files)}/{len(texts)} slot berhasil")
        return successful_files

    def swap_batch(self, old_batch_id: str, new_files: list) -> list:
        """
        Atomic swap: ganti referensi active_files ke new_files.
        Hapus file dengan prefix old_batch_id setelah swap.
        Return new_files yang dipakai.
        """
        # Hapus file lama setelah swap
        if old_batch_id:
            self.cleanup_batch(old_batch_id)
        print(f"[TTS_CACHE] Atomic swap selesai — {len(new_files)} file aktif")
        return new_files

    def cleanup_batch(self, batch_id: str):
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
```

- [ ] **Step 2: Verifikasi manual**

```bash
python -c "
from modules_client.greeting_tts_cache import get_greeting_cache
cache = get_greeting_cache()
# Pastikan 4 method ada
assert hasattr(cache, 'prerender_batch'), 'prerender_batch missing'
assert hasattr(cache, 'swap_batch'), 'swap_batch missing'
assert hasattr(cache, 'cleanup_batch'), 'cleanup_batch missing'
assert hasattr(cache, 'get_files_for_batch'), 'get_files_for_batch missing'
# Test cleanup_batch tidak crash untuk batch yang tidak ada
cache.cleanup_batch('nonexistent_batch')
print('greeting_tts_cache extensions: OK')
"
```

Expected: `greeting_tts_cache extensions: OK`

- [ ] **Step 3: Commit**

```bash
git add modules_client/greeting_tts_cache.py
git commit -m "feat: tambah batch prerender dan atomic swap ke greeting_tts_cache"
```

---

## Task 3: Refactor sequential_greeting_manager.py

**Files:**
- Modify: `modules_client/sequential_greeting_manager.py`

Ini penulisan ulang penuh file. Semua logika lama dipertahankan (pause/resume untuk trigger, state machine) tapi sumber slot diganti dari config ke AI generator.

- [ ] **Step 1: Tulis ulang file**

```python
# modules_client/sequential_greeting_manager.py - AI-Powered Greeting System

import time
import threading
import random
from datetime import datetime
from enum import Enum
from pathlib import Path

from modules_client.config_manager import ConfigManager

REGEN_INTERVAL_SECONDS = 7200  # 2 jam, tidak bisa diubah user


class GreetingState(Enum):
    IDLE            = "idle"
    PREPARING       = "preparing"   # Sedang generate AI + render TTS
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
    - TTS pre-render semua ke file audio
    - Putar acak dengan interval bervariasi (±25%)
    - Jika AI gagal, tetap pakai audio lama
    """

    def __init__(self):
        self.cfg = ConfigManager()

        self.state = GreetingState.IDLE
        self.is_enabled = False

        # Active audio files (list of paths)
        self.active_files = []
        self.active_batch_id = None
        self.files_lock = threading.Lock()

        # Threading
        self.playback_timer = None
        self.regen_timer = None
        self.should_stop = False
        self.thread_lock = threading.Lock()

        # Playback interval (dari settings, bisa diubah user)
        self.greeting_interval = 180

        # Trigger coordination (pause saat ada reply aktif)
        self.trigger_active = False
        self.pending_resume_timer = None
        self.resume_delay = 3

        # Status callback untuk update UI (di-set dari luar)
        self.status_callback = None

        print("[GREETING_AI] Manager initialized")

    # ─── Public API ───────────────────────────────────────────────

    def start(self):
        """Start Greeting AI — generate + prerender, lalu mulai playback."""
        with self.thread_lock:
            if self.state != GreetingState.IDLE:
                print("[GREETING_AI] Already running")
                return

            self.is_enabled = self.cfg.get("greeting_ai_enabled", False)
            if not self.is_enabled:
                print("[GREETING_AI] Disabled in settings")
                return

            self.greeting_interval = self.cfg.get("sequential_greeting_interval", 180)
            self.should_stop = False
            self.state = GreetingState.PREPARING

        self._notify_status("preparing", "Sedang menyiapkan sapaan AI...")

        # Generate + prerender di background thread agar UI tidak freeze
        prep_thread = threading.Thread(target=self._prepare_and_start, daemon=True)
        prep_thread.start()

    def stop(self):
        """Stop semua timer dan playback."""
        with self.thread_lock:
            if self.state == GreetingState.IDLE:
                return

            print("[GREETING_AI] Stopping...")
            self.should_stop = True
            self.state = GreetingState.IDLE

            for t in [self.playback_timer, self.regen_timer, self.pending_resume_timer]:
                if t:
                    t.cancel()
            self.playback_timer = None
            self.regen_timer = None
            self.pending_resume_timer = None

        self._notify_status("idle", "Greeting AI tidak aktif")
        print("[GREETING_AI] Stopped")

    def on_trigger_start(self):
        """Pause greeting saat trigger reply sedang diproses."""
        with self.thread_lock:
            if self.state == GreetingState.ACTIVE:
                self.state = GreetingState.PAUSED
                self.trigger_active = True
                if self.pending_resume_timer:
                    self.pending_resume_timer.cancel()
                    self.pending_resume_timer = None
                print("[GREETING_AI] Paused for trigger reply")

    def on_trigger_complete(self):
        """Resume greeting setelah trigger reply selesai (delay 3 detik)."""
        with self.thread_lock:
            if self.state == GreetingState.PAUSED:
                self.state = GreetingState.WAITING_RESUME
                self.trigger_active = False
                self.pending_resume_timer = threading.Timer(
                    self.resume_delay, self._resume_after_trigger
                )
                self.pending_resume_timer.start()
                print(f"[GREETING_AI] Trigger done, resume in {self.resume_delay}s")

    def set_greeting_interval(self, seconds: float):
        """Update interval dari UI (Cohost Tab)."""
        self.greeting_interval = max(10, seconds)
        self.cfg.set("sequential_greeting_interval", self.greeting_interval)
        print(f"[GREETING_AI] Interval set to {self.greeting_interval}s")

    def set_play_mode(self, mode: str):
        """Placeholder untuk backward compat — sistem ini selalu random."""
        pass

    def force_regenerate(self):
        """Manual trigger regenerasi dari tombol UI."""
        print("[GREETING_AI] Manual regenerate triggered")
        regen_thread = threading.Thread(target=self._regenerate, daemon=True)
        regen_thread.start()

    def get_status(self) -> dict:
        with self.files_lock:
            file_count = len(self.active_files)
        last_updated = self.cfg.get("greeting_ai_last_updated", None)
        return {
            "state": self.state.value,
            "enabled": self.is_enabled,
            "active_files": file_count,
            "interval_seconds": self.greeting_interval,
            "last_updated": last_updated,
        }

    # ─── Internal ─────────────────────────────────────────────────

    def _prepare_and_start(self):
        """Background thread: generate AI + prerender TTS, lalu mulai playback."""
        try:
            greetings = self._generate_greetings()
            new_files = self._prerender(greetings)

            if self.should_stop:
                return

            with self.files_lock:
                old_batch = self.active_batch_id
                new_batch = datetime.now().strftime("%Y%m%d%H%M%S")
                self.active_files = new_files
                self.active_batch_id = new_batch

            # Hapus batch lama jika ada
            if old_batch:
                from modules_client.greeting_tts_cache import get_greeting_cache
                get_greeting_cache().cleanup_batch(old_batch)

            self._save_last_updated()

            with self.thread_lock:
                if not self.should_stop:
                    self.state = GreetingState.ACTIVE

            active_count = len(new_files)
            self._notify_status("active", f"Aktif — {active_count} sapaan tersedia")
            self._schedule_next_playback()
            self._schedule_next_regen()

            print(f"[GREETING_AI] ✅ Started with {active_count} greetings")

        except Exception as e:
            print(f"[GREETING_AI] ❌ Prepare failed: {e}")
            import traceback
            traceback.print_exc()
            with self.thread_lock:
                self.state = GreetingState.IDLE
            self._notify_status("error", f"Gagal menyiapkan sapaan: {e}")

    def _generate_greetings(self) -> list:
        """Panggil AI generator, return list 10 teks."""
        from modules_client.greeting_ai_generator import generate_greetings_with_ai
        print("[GREETING_AI] Generating greetings via Gemini...")
        return generate_greetings_with_ai()

    def _prerender(self, texts: list) -> list:
        """Prerender semua teks ke file audio, return list path."""
        from modules_client.greeting_tts_cache import get_greeting_cache

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

        batch_id = datetime.now().strftime("%Y%m%d%H%M%S")
        cache = get_greeting_cache()
        return cache.prerender_batch(texts, voice_name, language_code, batch_id)

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
        print(f"[GREETING_AI] Next playback in {jittered:.1f}s")

    def _play_random_greeting(self):
        """Pilih file acak dan putar."""
        with self.files_lock:
            if not self.active_files:
                print("[GREETING_AI] No active files to play")
                self._schedule_next_playback()
                return
            chosen = random.choice(self.active_files)

        try:
            from modules_client.greeting_tts_cache import get_greeting_cache
            engine_module = get_greeting_cache()
            from modules_server.tts_engine import get_tts_engine
            engine = get_tts_engine()
            result = engine._play_audio_file(chosen, 5.0)
            success = result.get('success', False) if isinstance(result, dict) else bool(result)
            print(f"[GREETING_AI] {'✅' if success else '❌'} Played: {Path(chosen).name}")
        except Exception as e:
            print(f"[GREETING_AI] ❌ Playback error: {e}")

        if not self.should_stop and self.state == GreetingState.ACTIVE:
            self._schedule_next_playback()

    def _schedule_next_regen(self):
        """Schedule regenerasi AI berikutnya (2 jam)."""
        if self.should_stop:
            return

        self.regen_timer = threading.Timer(REGEN_INTERVAL_SECONDS, self._regenerate)
        self.regen_timer.daemon = True
        self.regen_timer.start()
        print(f"[GREETING_AI] Next regen in {REGEN_INTERVAL_SECONDS/3600:.1f} jam")

    def _regenerate(self):
        """Generate 10 teks baru + prerender ke batch baru + atomic swap."""
        if self.should_stop:
            return

        print("[GREETING_AI] 🔄 Starting regeneration...")
        self._notify_status("regenerating", "Memperbarui sapaan AI...")

        try:
            greetings = self._generate_greetings()
            new_files = self._prerender(greetings)

            if self.should_stop:
                return

            with self.files_lock:
                old_batch = self.active_batch_id
                self.active_batch_id = datetime.now().strftime("%Y%m%d%H%M%S")
                self.active_files = new_files

            if old_batch:
                from modules_client.greeting_tts_cache import get_greeting_cache
                get_greeting_cache().cleanup_batch(old_batch)

            self._save_last_updated()

            count = len(new_files)
            self._notify_status("active", f"Aktif — {count} sapaan diperbarui")
            print(f"[GREETING_AI] ✅ Regeneration done — {count} new files")

        except Exception as e:
            print(f"[GREETING_AI] ❌ Regeneration failed: {e}")
            self._notify_status("active", "Aktif — pakai sapaan sebelumnya")

        # Schedule regen berikutnya
        if not self.should_stop:
            self._schedule_next_regen()

    def _resume_after_trigger(self):
        """Resume playback setelah jeda trigger selesai."""
        with self.thread_lock:
            if self.state == GreetingState.WAITING_RESUME and not self.should_stop:
                self.state = GreetingState.ACTIVE
                print("[GREETING_AI] Resumed after trigger")
                self._schedule_next_playback()

    def _save_last_updated(self):
        """Simpan timestamp update terakhir ke settings."""
        ts = datetime.now().strftime("%H:%M")
        self.cfg.set("greeting_ai_last_updated", ts)

    def _notify_status(self, state: str, message: str):
        """Panggil callback UI jika ada."""
        if self.status_callback and callable(self.status_callback):
            try:
                self.status_callback(state, message)
            except Exception as e:
                print(f"[GREETING_AI] Status callback error: {e}")


# Global instance
_sequential_greeting_manager = None


def get_sequential_greeting_manager():
    global _sequential_greeting_manager
    if _sequential_greeting_manager is None:
        _sequential_greeting_manager = SequentialGreetingManager()
    return _sequential_greeting_manager
```

- [ ] **Step 2: Verifikasi import tidak error**

```bash
python -c "
from modules_client.sequential_greeting_manager import get_sequential_greeting_manager, get_jittered_interval
mgr = get_sequential_greeting_manager()
print('State:', mgr.state.value)
# Test jitter
intervals = [get_jittered_interval(180) for _ in range(5)]
print('Jittered intervals:', [f'{i:.1f}' for i in intervals])
assert all(135 <= i <= 225 for i in intervals), 'Jitter out of range!'
print('sequential_greeting_manager: OK')
"
```

Expected: intervals berbeda-beda antara 135–225.

- [ ] **Step 3: Commit**

```bash
git add modules_client/sequential_greeting_manager.py
git commit -m "feat: refactor sequential_greeting_manager — AI-generated greetings + jitter + 2h regen"
```

---

## Task 4: Update UI config_tab.py

**Files:**
- Modify: `ui/config_tab.py`

Ada dua perubahan: (a) ganti `create_viewer_greeting_section()` isinya, (b) update method handler.

- [ ] **Step 1: Ganti isi `create_viewer_greeting_section()` (baris 541–703)**

Cari method `create_viewer_greeting_section` dan ganti seluruh isinya (dari baris setelah `def create_viewer_greeting_section(self, layout):` hingga sebelum method berikutnya `create_sales_template_section`):

```python
    def create_viewer_greeting_section(self, layout):
        """Greeting AI System — ON/OFF toggle + status indicator"""
        try:
            from ui.theme import (PRIMARY, SECONDARY, ACCENT, BG_BASE, BG_SURFACE,
                                   BG_ELEVATED, TEXT_PRIMARY, TEXT_MUTED, SUCCESS,
                                   WARNING, ERROR, BORDER, btn_primary, btn_success,
                                   btn_danger, btn_ghost, CARD_STYLE)
            BORDER_COLOR = BORDER
        except ImportError:
            PRIMARY = "#2563EB"; ACCENT = "#60A5FA"; BG_SURFACE = "#162032"
            BG_ELEVATED = "#1E2A3B"; TEXT_PRIMARY = "#F0F6FF"; TEXT_MUTED = "#94A3B8"
            SUCCESS = "#10B981"; WARNING = "#F59E0B"; ERROR = "#EF4444"
            BORDER_COLOR = "#1E3A5F"
            def btn_success(extra=""): return f"background-color:{SUCCESS};color:white;border:none;border-radius:6px;padding:6px 14px;{extra}"
            def btn_danger(extra=""): return f"background-color:{ERROR};color:white;border:none;border-radius:6px;padding:6px 14px;{extra}"

        from PyQt6.QtWidgets import (QGroupBox, QVBoxLayout, QHBoxLayout,
                                      QLabel, QPushButton, QCheckBox, QFrame)
        from PyQt6.QtCore import Qt

        group = QGroupBox("🤖 Greeting AI")
        group_layout = QVBoxLayout(group)
        group_layout.setSpacing(12)

        # Deskripsi
        desc = QLabel(
            "AI generate 10 sapaan unik setiap 2 jam menggunakan konteks dari tab Knowledge.\n"
            "Audio fingerprint berubah otomatis — lebih aman dari deteksi spam TikTok."
        )
        desc.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px; padding: 4px; line-height: 1.5;")
        desc.setWordWrap(True)
        group_layout.addWidget(desc)

        # Toggle ON/OFF
        self.greeting_ai_cb = QCheckBox("🤖 Aktifkan Greeting AI")
        self.greeting_ai_cb.setStyleSheet(f"""
            QCheckBox {{
                color: {TEXT_PRIMARY};
                font-size: 13px;
                font-weight: bold;
                padding: 5px;
            }}
            QCheckBox::indicator {{
                width: 18px; height: 18px;
            }}
            QCheckBox::indicator:checked {{
                background-color: {PRIMARY};
                border: 2px solid {PRIMARY};
                border-radius: 3px;
            }}
            QCheckBox::indicator:unchecked {{
                background-color: {BG_SURFACE};
                border: 2px solid {BORDER_COLOR};
                border-radius: 3px;
            }}
        """)
        greeting_ai_enabled = self.cfg.get("greeting_ai_enabled", False)
        self.greeting_ai_cb.setChecked(greeting_ai_enabled)
        self.greeting_ai_cb.stateChanged.connect(self.on_greeting_ai_enabled_changed)
        group_layout.addWidget(self.greeting_ai_cb)

        # Status frame
        status_frame = QFrame()
        status_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_ELEVATED};
                border: 1px solid {BORDER_COLOR};
                border-radius: 8px;
                padding: 12px;
            }}
        """)
        status_layout = QVBoxLayout(status_frame)
        status_layout.setSpacing(6)

        # Status label
        self.greeting_ai_status_label = QLabel("⚪ Tidak aktif")
        self.greeting_ai_status_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 13px; font-weight: bold;")
        status_layout.addWidget(self.greeting_ai_status_label)

        # Last updated label
        last_updated = self.cfg.get("greeting_ai_last_updated", None)
        last_text = f"Terakhir diperbarui: {last_updated}" if last_updated else "Belum pernah diperbarui"
        self.greeting_ai_updated_label = QLabel(last_text)
        self.greeting_ai_updated_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px; font-style: italic;")
        status_layout.addWidget(self.greeting_ai_updated_label)

        group_layout.addWidget(status_frame)

        # Tombol regenerasi manual
        regen_btn_layout = QHBoxLayout()
        self.greeting_ai_regen_btn = QPushButton("🔄 Generate Ulang Sekarang")
        self.greeting_ai_regen_btn.setStyleSheet(btn_success() if callable(btn_success) else btn_success)
        self.greeting_ai_regen_btn.setEnabled(greeting_ai_enabled)
        self.greeting_ai_regen_btn.clicked.connect(self.on_greeting_ai_regen_clicked)
        regen_btn_layout.addWidget(self.greeting_ai_regen_btn)
        regen_btn_layout.addStretch()
        group_layout.addLayout(regen_btn_layout)

        # Info interval
        info = QLabel("💡 Interval putaran diatur di Cohost Tab. Sapaan diperbarui otomatis setiap 2 jam.")
        info.setStyleSheet(f"color: {WARNING}; font-size: 11px; font-style: italic; padding: 6px; background-color: {BG_ELEVATED}; border-radius: 4px;")
        info.setWordWrap(True)
        group_layout.addWidget(info)

        layout.addWidget(group)
```

- [ ] **Step 2: Tambah 3 method handler baru ke class ConfigTab**

Tambahkan setelah method `on_custom_greeting_enabled_changed` (sekitar baris 1749):

```python
    def on_greeting_ai_enabled_changed(self):
        """Handle Greeting AI toggle ON/OFF."""
        try:
            enabled = self.greeting_ai_cb.isChecked()
            self.cfg.set("greeting_ai_enabled", enabled)
            # Backward compat — sequential manager cek key ini juga
            self.cfg.set("sequential_greeting_enabled", enabled)
            self.cfg.set("custom_greeting_enabled", enabled)

            if hasattr(self, 'greeting_ai_regen_btn'):
                self.greeting_ai_regen_btn.setEnabled(enabled)

            if not enabled:
                self.update_greeting_ai_status("idle", "Tidak aktif")

            print(f"[CONFIG] Greeting AI: {'ON' if enabled else 'OFF'}")
        except Exception as e:
            print(f"[CONFIG] Error on_greeting_ai_enabled_changed: {e}")

    def on_greeting_ai_regen_clicked(self):
        """Trigger manual regenerasi greeting AI."""
        try:
            from modules_client.sequential_greeting_manager import get_sequential_greeting_manager
            mgr = get_sequential_greeting_manager()
            mgr.force_regenerate()
            self.update_greeting_ai_status("regenerating", "Memperbarui sapaan AI...")
        except Exception as e:
            print(f"[CONFIG] Error on_greeting_ai_regen_clicked: {e}")

    def update_greeting_ai_status(self, state: str, message: str):
        """Update status label di UI (dipanggil dari greeting manager via callback)."""
        try:
            if not hasattr(self, 'greeting_ai_status_label'):
                return

            state_icons = {
                "idle":         "⚪",
                "preparing":    "⏳",
                "active":       "✅",
                "paused":       "⏸️",
                "regenerating": "🔄",
                "error":        "❌",
            }
            icon = state_icons.get(state, "⚪")
            self.greeting_ai_status_label.setText(f"{icon} {message}")

            if state == "active":
                last_updated = self.cfg.get("greeting_ai_last_updated", "—")
                self.greeting_ai_updated_label.setText(f"Terakhir diperbarui: {last_updated}")

        except Exception as e:
            print(f"[CONFIG] Error update_greeting_ai_status: {e}")
```

- [ ] **Step 3: Verifikasi tidak ada syntax error**

```bash
python -c "
import sys
sys.path.insert(0, '.')
import ast
with open('ui/config_tab.py', 'r', encoding='utf-8') as f:
    source = f.read()
try:
    ast.parse(source)
    print('config_tab.py syntax: OK')
except SyntaxError as e:
    print(f'SYNTAX ERROR: {e}')
"
```

Expected: `config_tab.py syntax: OK`

- [ ] **Step 4: Commit**

```bash
git add ui/config_tab.py
git commit -m "feat: ganti 10 slot manual dengan Greeting AI toggle + status UI di config_tab"
```

---

## Task 5: Update settings_default.json + Wire Status Callback

**Files:**
- Modify: `config/settings_default.json`
- Modify: `ui/cohost_tab_basic.py` (2 baris saja)

- [ ] **Step 1: Tambah field ke settings_default.json**

Buka `config/settings_default.json` dan tambah dua field setelah `"user_context": ""`:

```json
{
  "platform": "TikTok",
  "paket": "basic",
  "ai_provider": "gemini",
  "output_language": "Indonesia",
  "debug_mode": false,
  "tiktok_nickname": "",
  "trigger_words": ["bro", "bang", "min"],
  "cohost_cooldown": 2,
  "viewer_cooldown_minutes": 3,
  "cohost_max_queue": 4,
  "sequential_greeting_interval": 180,
  "greeting_play_mode": "random",
  "tts_voice": "Gemini-Puck (MALE)",
  "tts_key_type": "",
  "google_tts_api_key": "",
  "api_keys": {
    "GEMINI_API_KEY": "",
    "DEEPSEEK_API_KEY": ""
  },
  "user_context": "",
  "greeting_ai_enabled": false,
  "greeting_ai_last_updated": null
}
```

- [ ] **Step 2: Wire status callback di cohost_tab_basic.py**

Cari baris di `cohost_tab_basic.py` tempat `self.sequential_greeting_manager` di-assign (sekitar baris 646–647):

```python
        from modules_client.sequential_greeting_manager import get_sequential_greeting_manager
        self.sequential_greeting_manager = get_sequential_greeting_manager()
```

Tambahkan 3 baris setelahnya untuk wire callback:

```python
        from modules_client.sequential_greeting_manager import get_sequential_greeting_manager
        self.sequential_greeting_manager = get_sequential_greeting_manager()
        # Wire status callback ke config tab jika ada
        if hasattr(self, 'parent') and hasattr(self.parent(), 'config_tab'):
            config_tab = self.parent().config_tab
            if hasattr(config_tab, 'update_greeting_ai_status'):
                self.sequential_greeting_manager.status_callback = config_tab.update_greeting_ai_status
```

> **Catatan:** Jika `self.parent().config_tab` tidak accessible dari sini, wire callback ini bisa dilakukan dari `main_window.py` setelah semua tab dibuat. Cek dengan `print(dir(self.parent()))` untuk memastikan. Jika tidak ketemu, skip langkah wire callback — sistem tetap bekerja, hanya status UI tidak auto-update (masih bisa update manual via `force_regenerate()`).

- [ ] **Step 3: Verifikasi syntax cohost_tab_basic.py**

```bash
python -c "
import ast
with open('ui/cohost_tab_basic.py', 'r', encoding='utf-8') as f:
    source = f.read()
try:
    ast.parse(source)
    print('cohost_tab_basic.py syntax: OK')
except SyntaxError as e:
    print(f'SYNTAX ERROR: {e}')
"
```

- [ ] **Step 4: Commit**

```bash
git add config/settings_default.json ui/cohost_tab_basic.py
git commit -m "feat: tambah greeting_ai fields ke settings_default + wire status callback"
```

---

## Task 6: Integrasi Test — Jalankan Aplikasi

- [ ] **Step 1: Jalankan aplikasi dan cek startup**

```bash
python main.py
```

Perhatikan console output:
- `[GREETING_AI] Manager initialized` — harus muncul
- Tidak ada traceback saat startup

- [ ] **Step 2: Test Greeting AI ON**

1. Buka tab **Konfigurasi**
2. Scroll ke section **🤖 Greeting AI**
3. Centang toggle **Aktifkan Greeting AI**
4. Buka tab **Cohost** → klik **Mulai Live**
5. Di console harus muncul:
   - `[GREETING_AI] Generating greetings via Gemini...`
   - `[GREETING_AI] ✅ Generated 10 greetings`
   - `[TTS_CACHE] ✅ Batch render 1/10:` ... hingga `10/10`
   - `[GREETING_AI] ✅ Started with N greetings`
   - `[GREETING_AI] Next playback in XXX.Xs` — angka bervariasi

- [ ] **Step 3: Test jitter interval**

Di console, perhatikan baris `Next playback in` — angkanya harus **tidak sama persis** antar baris. Contoh:
```
[GREETING_AI] Next playback in 167.3s
[GREETING_AI] Next playback in 211.8s
[GREETING_AI] Next playback in 143.5s
```

- [ ] **Step 4: Test tombol Generate Ulang**

1. Pastikan Greeting AI ON dan live sedang berjalan
2. Klik **🔄 Generate Ulang Sekarang**
3. Console harus menampilkan `[GREETING_AI] 🔄 Starting regeneration...`
4. Setelah selesai: `[GREETING_AI] ✅ Regeneration done`

- [ ] **Step 5: Test fallback jika Gemini error**

1. Sementara ubah API key Gemini di settings menjadi `"invalid_key_test"`
2. Hidupkan Greeting AI → Mulai Live
3. Harus muncul warning `[GREETING_AI] Gagal generate, pakai fallback greetings`
4. Aplikasi **tidak crash** — sistem tetap jalan dengan fallback
5. Kembalikan API key yang benar

- [ ] **Step 6: Final commit jika semua test lulus**

```bash
git add -A
git commit -m "test: verifikasi manual Greeting AI System — semua skenario OK"
```

---

## Checklist Akhir vs Spec

| Kriteria Spec | Task |
|---------------|------|
| Toggle ON/OFF berfungsi, state tersimpan | Task 4 + 5 |
| Saat ON, Gemini generate 10 teks dalam 15 detik | Task 1 + 3 |
| Semua 10 teks ter-render tanpa simbol | Task 1 (`clean_greeting_text`) |
| Playback acak dengan interval bervariasi | Task 3 (`get_jittered_interval`) |
| Setelah 2 jam, swap tanpa crash | Task 3 (`_regenerate` + atomic swap) |
| Tombol Generate Ulang berfungsi | Task 4 + 3 (`force_regenerate`) |
| Jika Gemini gagal, tidak crash | Task 1 (fallback + retry) |
| Status UI update realtime | Task 4 (`update_greeting_ai_status`) |
