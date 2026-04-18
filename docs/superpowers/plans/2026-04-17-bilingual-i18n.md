# VocaLive Bilingual i18n Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Menjadikan VocaLive bilingual (Indonesia / English) tanpa mengubah fitur atau behavior existing — murni additive translation layer.

**Architecture:** JSON dict-based translation manager (`modules_client/i18n.py`) dengan dua file locale (`i18n/id.json`, `i18n/en.json`). UI language independen dari `output_language` AI. Deteksi OS locale untuk fresh install, migrasi eksplisit ke `"id"` untuk user existing. Switcher di Config Tab dengan restart-required.

**Tech Stack:** Python 3.11, PyQt6, JSON, pytest, pytest-qt, pytest-mock. Target build: PyInstaller EXE untuk Windows 10/11.

**Reference:** Design spec di `docs/superpowers/specs/2026-04-17-bilingual-i18n-design.md`

**Branch:** `feat/i18n-bilingual-support` (sudah dibuat)

**Target version:** v1.0.15

---

## Conventions (Apply Throughout)

- **Semua import `t`**: `from modules_client.i18n import t`
- **Semua key**: flat dotted keys lowercase. Pattern `<area>.<component>.<element>`
- **Emoji dipertahankan** di string translated (bagian dari identitas visual)
- **Logger tetap bahasa asli** — internal developer log tidak di-translate (konsisten untuk Sentry/MCP debugging)
- **User data tidak di-translate** — greeting text, product names, trigger_words, user_context, voice IDs
- **TDD**: test dulu (FAIL), implementasi (PASS), commit. Tiap task harus tinggalkan pytest hijau
- **Commit format**: `<type>: <deskripsi Indonesia>` sesuai CLAUDE.md (`feat fix refactor style docs chore`)

---

## Task 1: i18n Module — OS Locale Detection

**Files:**
- Create: `modules_client/i18n.py`
- Create: `tests/test_i18n.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_i18n.py`:

```python
"""Tests untuk modules_client/i18n.py - translation manager."""
import locale
import pytest


class TestDetectOSLocale:
    """Test deteksi OS locale → 'id' atau 'en'."""

    def test_indonesian_locale_returns_id(self, monkeypatch):
        from modules_client import i18n
        monkeypatch.setattr(locale, "getdefaultlocale", lambda: ("id_ID", "cp1252"))
        assert i18n._detect_os_locale() == "id"

    def test_malaysian_locale_returns_id(self, monkeypatch):
        """Malaysia di-map ke 'id' karena pengalaman pengguna mirip."""
        from modules_client import i18n
        monkeypatch.setattr(locale, "getdefaultlocale", lambda: ("ms_MY", "cp1252"))
        assert i18n._detect_os_locale() == "id"

    def test_english_locale_returns_en(self, monkeypatch):
        from modules_client import i18n
        monkeypatch.setattr(locale, "getdefaultlocale", lambda: ("en_US", "cp1252"))
        assert i18n._detect_os_locale() == "en"

    def test_british_english_returns_en(self, monkeypatch):
        from modules_client import i18n
        monkeypatch.setattr(locale, "getdefaultlocale", lambda: ("en_GB", "utf-8"))
        assert i18n._detect_os_locale() == "en"

    def test_unknown_locale_fallback_to_id(self, monkeypatch):
        """Locale tidak dikenal → fallback 'id' (safer default untuk app Indonesia-first)."""
        from modules_client import i18n
        monkeypatch.setattr(locale, "getdefaultlocale", lambda: ("fr_FR", "utf-8"))
        assert i18n._detect_os_locale() == "id"

    def test_none_locale_fallback_to_id(self, monkeypatch):
        from modules_client import i18n
        monkeypatch.setattr(locale, "getdefaultlocale", lambda: (None, None))
        assert i18n._detect_os_locale() == "id"

    def test_exception_fallback_to_id(self, monkeypatch):
        """locale.getdefaultlocale() throws → log warning + fallback 'id'."""
        from modules_client import i18n
        def raising():
            raise OSError("locale not available")
        monkeypatch.setattr(locale, "getdefaultlocale", raising)
        assert i18n._detect_os_locale() == "id"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_i18n.py -v`
Expected: FAIL dengan `ModuleNotFoundError: No module named 'modules_client.i18n'`.

- [ ] **Step 3: Create minimal `modules_client/i18n.py`**

```python
"""VocaLive i18n — JSON dict-based translation manager.

Public API:
    init(fresh_install: bool = False) -> None
    t(key: str, **kwargs) -> str
    current_language() -> str
    set_language(lang: str) -> None
"""
import json
import locale as _locale
import logging
import sys
from pathlib import Path
from typing import Any

logger = logging.getLogger("VocaLive")

_SUPPORTED_LANGS = ("id", "en")
_REFERENCE_LANG = "id"
_DEFAULT_LANG = "id"

_current_lang: str = _DEFAULT_LANG
_translations: dict[str, str] = {}
_reference_translations: dict[str, str] = {}


def _detect_os_locale() -> str:
    """Return 'id' untuk Windows id-ID/ms-MY, 'en' untuk en-*, default 'id' lainnya."""
    try:
        lang_tuple = _locale.getdefaultlocale()
        if lang_tuple and lang_tuple[0]:
            lang = lang_tuple[0].lower()
            if lang.startswith(("id", "ms")):
                return "id"
            if lang.startswith("en"):
                return "en"
    except Exception as e:
        logger.warning(f"[i18n] OS locale detection failed: {e}")
    return _DEFAULT_LANG
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_i18n.py -v`
Expected: 7 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add modules_client/i18n.py tests/test_i18n.py
git commit -m "feat(i18n): deteksi OS locale untuk bilingual support"
```

---

## Task 2: i18n Module — `t()` Lookup with Fallback Chain

**Files:**
- Modify: `modules_client/i18n.py`
- Modify: `tests/test_i18n.py`

- [ ] **Step 1: Write the failing tests**

Append ke `tests/test_i18n.py`:

```python
class TestTranslation:
    """Test fungsi t() dengan fallback chain."""

    def test_t_returns_translation(self, monkeypatch):
        from modules_client import i18n
        monkeypatch.setattr(i18n, "_current_lang", "en")
        monkeypatch.setattr(i18n, "_translations", {"cohost.btn.start": "Start"})
        monkeypatch.setattr(i18n, "_reference_translations", {"cohost.btn.start": "Mulai"})
        assert i18n.t("cohost.btn.start") == "Start"

    def test_t_fallback_to_reference_when_missing_in_current(self, monkeypatch):
        """Key tidak ada di EN → fallback ke ID (reference)."""
        from modules_client import i18n
        monkeypatch.setattr(i18n, "_current_lang", "en")
        monkeypatch.setattr(i18n, "_translations", {})
        monkeypatch.setattr(i18n, "_reference_translations", {"cohost.btn.start": "Mulai"})
        assert i18n.t("cohost.btn.start") == "Mulai"

    def test_t_fallback_to_key_when_missing_both(self, monkeypatch):
        """Key tidak ada di manapun → return raw key string (tidak crash)."""
        from modules_client import i18n
        monkeypatch.setattr(i18n, "_current_lang", "en")
        monkeypatch.setattr(i18n, "_translations", {})
        monkeypatch.setattr(i18n, "_reference_translations", {})
        assert i18n.t("unknown.key") == "unknown.key"

    def test_t_format_placeholder(self, monkeypatch):
        """kwargs disubstitusi via str.format()."""
        from modules_client import i18n
        monkeypatch.setattr(i18n, "_current_lang", "id")
        monkeypatch.setattr(i18n, "_translations", {"err.api.timeout": "Timeout setelah {seconds} detik"})
        monkeypatch.setattr(i18n, "_reference_translations", {})
        assert i18n.t("err.api.timeout", seconds=30) == "Timeout setelah 30 detik"

    def test_t_format_missing_placeholder_returns_raw(self, monkeypatch):
        """Kalau format() gagal (kwargs tidak match), return string unformatted.
        Prevent crash di runtime karena typo nama placeholder."""
        from modules_client import i18n
        monkeypatch.setattr(i18n, "_current_lang", "id")
        monkeypatch.setattr(i18n, "_translations", {"err.x": "Timeout {seconds}"})
        monkeypatch.setattr(i18n, "_reference_translations", {})
        # kwargs nama salah (typo): wrong→seconds
        result = i18n.t("err.x", wrong=30)
        assert "{seconds}" in result or result == "Timeout {seconds}"

    def test_current_language(self, monkeypatch):
        from modules_client import i18n
        monkeypatch.setattr(i18n, "_current_lang", "en")
        assert i18n.current_language() == "en"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_i18n.py::TestTranslation -v`
Expected: FAIL dengan `AttributeError: module 'modules_client.i18n' has no attribute 't'`.

- [ ] **Step 3: Implement `t()` and `current_language()`**

Append ke `modules_client/i18n.py`:

```python
def t(key: str, **kwargs: Any) -> str:
    """Lookup terjemahan untuk key.

    Fallback chain:
        1. _translations (current_lang)
        2. _reference_translations (id.json — reference locale)
        3. raw key string itu sendiri

    kwargs di-substitusi via str.format() jika ada placeholder.
    Format error di-swallow (return string unformatted) untuk anti-crash.
    """
    text = _translations.get(key)
    if text is None:
        text = _reference_translations.get(key)
    if text is None:
        text = key

    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, IndexError, ValueError) as e:
            logger.warning(f"[i18n] format() failed for key={key!r}: {e}")

    return text


def current_language() -> str:
    return _current_lang
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_i18n.py -v`
Expected: 13 tests PASS (7 dari Task 1 + 6 baru).

- [ ] **Step 5: Commit**

```bash
git add modules_client/i18n.py tests/test_i18n.py
git commit -m "feat(i18n): implementasi t() dengan fallback chain dan format placeholder"
```

---

## Task 3: i18n Module — `init()` dengan Fresh Install Migration

**Files:**
- Modify: `modules_client/i18n.py`
- Create: `i18n/id.json` (minimal content)
- Create: `i18n/en.json` (minimal content)
- Modify: `tests/test_i18n.py`

- [ ] **Step 1: Create minimal JSON files**

Create `i18n/id.json`:

```json
{
  "common.ok": "OK"
}
```

Create `i18n/en.json`:

```json
{
  "common.ok": "OK"
}
```

- [ ] **Step 2: Write the failing tests**

Append ke `tests/test_i18n.py`:

```python
class TestInit:
    """Test inisialisasi i18n — load JSON, migrasi, persistence."""

    def test_init_fresh_install_saves_detected_locale(self, tmp_path, monkeypatch):
        """Fresh install Windows en-US → detect 'en' + save ke config."""
        from modules_client import i18n

        # Mock config path ke tmp
        fake_settings = tmp_path / "settings.json"
        fake_settings.write_text('{"platform": "TikTok"}', encoding="utf-8")

        # Mock ConfigManager yang dipakai i18n
        saved = {}
        class FakeCfg:
            def get(self, key, default=None):
                return json.loads(fake_settings.read_text()).get(key, default)
            def set(self, key, value):
                data = json.loads(fake_settings.read_text())
                data[key] = value
                fake_settings.write_text(json.dumps(data), encoding="utf-8")
                saved[key] = value
                return True

        monkeypatch.setattr(i18n, "_get_config_manager", lambda: FakeCfg())
        monkeypatch.setattr(i18n, "_detect_os_locale", lambda: "en")
        monkeypatch.setattr(i18n, "_load_json_file", lambda lang: {"common.ok": "OK"})

        i18n.init(fresh_install=True)

        assert saved.get("ui_language") == "en"
        assert i18n.current_language() == "en"

    def test_init_existing_user_forces_id_migration(self, tmp_path, monkeypatch):
        """User existing (field ui_language belum ada) → force 'id', TIDAK deteksi OS."""
        import json
        from modules_client import i18n

        fake_settings = tmp_path / "settings.json"
        fake_settings.write_text('{"platform": "TikTok"}', encoding="utf-8")

        saved = {}
        class FakeCfg:
            def get(self, key, default=None):
                return json.loads(fake_settings.read_text()).get(key, default)
            def set(self, key, value):
                data = json.loads(fake_settings.read_text())
                data[key] = value
                fake_settings.write_text(json.dumps(data), encoding="utf-8")
                saved[key] = value
                return True

        # Monkeypatch detect_os_locale yang SEHARUSNYA tidak dipanggil
        detect_called = []
        def never_call():
            detect_called.append(True)
            return "en"
        monkeypatch.setattr(i18n, "_get_config_manager", lambda: FakeCfg())
        monkeypatch.setattr(i18n, "_detect_os_locale", never_call)
        monkeypatch.setattr(i18n, "_load_json_file", lambda lang: {"common.ok": "OK"})

        i18n.init(fresh_install=False)

        assert saved.get("ui_language") == "id"
        assert not detect_called, "detect_os_locale should NOT be called for existing user"
        assert i18n.current_language() == "id"

    def test_init_respects_existing_ui_language(self, tmp_path, monkeypatch):
        """User sudah punya ui_language='en' → pakai nilai existing, tidak override."""
        import json
        from modules_client import i18n

        fake_settings = tmp_path / "settings.json"
        fake_settings.write_text('{"ui_language": "en"}', encoding="utf-8")

        class FakeCfg:
            def get(self, key, default=None):
                return json.loads(fake_settings.read_text()).get(key, default)
            def set(self, key, value):
                pass  # should not be called

        monkeypatch.setattr(i18n, "_get_config_manager", lambda: FakeCfg())
        monkeypatch.setattr(i18n, "_load_json_file", lambda lang: {"common.ok": "OK"})

        i18n.init(fresh_install=False)

        assert i18n.current_language() == "en"

    def test_init_invalid_value_falls_back_to_id(self, tmp_path, monkeypatch):
        """ui_language='fr' (invalid) → log warning + fallback 'id'."""
        import json
        from modules_client import i18n

        fake_settings = tmp_path / "settings.json"
        fake_settings.write_text('{"ui_language": "fr"}', encoding="utf-8")

        class FakeCfg:
            def get(self, key, default=None):
                return json.loads(fake_settings.read_text()).get(key, default)
            def set(self, key, value):
                pass

        monkeypatch.setattr(i18n, "_get_config_manager", lambda: FakeCfg())
        monkeypatch.setattr(i18n, "_load_json_file", lambda lang: {"common.ok": "OK"})

        i18n.init(fresh_install=False)

        assert i18n.current_language() == "id"

    def test_set_language_persists(self, tmp_path, monkeypatch):
        import json
        from modules_client import i18n

        fake_settings = tmp_path / "settings.json"
        fake_settings.write_text('{"ui_language": "id"}', encoding="utf-8")

        saved = {}
        class FakeCfg:
            def get(self, key, default=None):
                return json.loads(fake_settings.read_text()).get(key, default)
            def set(self, key, value):
                saved[key] = value
                return True

        monkeypatch.setattr(i18n, "_get_config_manager", lambda: FakeCfg())

        i18n.set_language("en")

        assert saved.get("ui_language") == "en"
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `python -m pytest tests/test_i18n.py::TestInit -v`
Expected: FAIL dengan `AttributeError: module ... has no attribute 'init'`.

- [ ] **Step 4: Implement `init()`, `set_language()`, helpers**

Append ke `modules_client/i18n.py`:

```python
def _i18n_dir() -> Path:
    """Return path folder i18n/ — bekerja di dev mode dan frozen EXE."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent / "i18n"
    return Path(__file__).parent.parent / "i18n"


def _load_json_file(lang: str) -> dict[str, str]:
    """Load i18n/<lang>.json. Return empty dict kalau file tidak ada."""
    path = _i18n_dir() / f"{lang}.json"
    if not path.exists():
        logger.error(f"[i18n] File tidak ditemukan: {path}")
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"[i18n] Failed to load {path}: {e}")
        return {}


def _get_config_manager():
    """Indirection supaya bisa di-mock dalam test."""
    from modules_client.config_manager import ConfigManager
    return ConfigManager()


def init(fresh_install: bool = False) -> None:
    """Inisialisasi i18n state. Panggil SEKALI di main.py setelah setup_validator.

    fresh_install=True  → kalau ui_language belum diset, deteksi OS locale lalu save.
    fresh_install=False → kalau ui_language belum diset, FORCE 'id' (migrasi user lama).

    Invalid value (bukan 'id'/'en') selalu fallback ke 'id'.
    """
    global _current_lang, _translations, _reference_translations

    cfg = _get_config_manager()
    ui_lang = cfg.get("ui_language")

    if ui_lang is None:
        if fresh_install:
            ui_lang = _detect_os_locale()
            logger.info(f"[i18n] Fresh install: detected OS locale = {ui_lang!r}")
        else:
            ui_lang = _DEFAULT_LANG
            logger.info(f"[i18n] Existing user migration: force ui_language={ui_lang!r}")
        cfg.set("ui_language", ui_lang)

    if ui_lang not in _SUPPORTED_LANGS:
        logger.warning(f"[i18n] Invalid ui_language={ui_lang!r}, fallback to {_DEFAULT_LANG!r}")
        ui_lang = _DEFAULT_LANG

    _current_lang = ui_lang
    _translations = _load_json_file(ui_lang)
    _reference_translations = _load_json_file(_REFERENCE_LANG) if ui_lang != _REFERENCE_LANG else _translations

    logger.info(f"[i18n] Initialized: lang={ui_lang}, keys_loaded={len(_translations)}")


def set_language(lang: str) -> None:
    """Persist pilihan bahasa baru. User harus restart untuk apply."""
    if lang not in _SUPPORTED_LANGS:
        logger.error(f"[i18n] set_language: invalid lang={lang!r}")
        return
    cfg = _get_config_manager()
    cfg.set("ui_language", lang)
    logger.info(f"[i18n] Language preference saved: {lang} (restart required)")
```

- [ ] **Step 5: Run all i18n tests**

Run: `python -m pytest tests/test_i18n.py -v`
Expected: 18 tests PASS.

- [ ] **Step 6: Run full suite — no regression**

Run: `python -m pytest tests/ -v --tb=short`
Expected: semua existing tests + 18 baru PASS.

- [ ] **Step 7: Commit**

```bash
git add modules_client/i18n.py tests/test_i18n.py i18n/id.json i18n/en.json
git commit -m "feat(i18n): init() dengan fresh install detection dan migrasi user existing"
```

---

## Task 4: Wire `i18n.init()` ke `main.py`

**Files:**
- Modify: `main.py`
- Modify: `config/settings_default.json`

- [ ] **Step 1: Read `main.py` untuk cari insertion point**

Run: `grep -n "setup_validator\|LicenseManager\|is_license_valid\|telemetry.init" main.py`

Identifikasi blok sekitar `setup_validator` dan sebelum `LicenseManager.is_license_valid()`.

- [ ] **Step 2: Tambah field `ui_language` ke `settings_default.json`**

Edit `config/settings_default.json`, tambah field SETELAH `output_language`:

```json
{
  "platform": "TikTok",
  "paket": "basic",
  "ai_provider": "gemini",
  "output_language": "Indonesia",
  "ui_language": "id",
  "debug_mode": false,
  ...
}
```

- [ ] **Step 3: Modify `main.py` — capture `is_fresh_install` + call `i18n.init()`**

Cari section setelah UTF-8 fix, sebelum license check. Pattern umum:

```python
# Before — contoh struktur yang ada
setup_validator = SetupValidator()
setup_validator.ensure_settings_exists()

license_mgr = LicenseManager()
if not license_mgr.is_license_valid():
    ...
```

Ganti dengan:

```python
# After — tambah is_fresh_install capture + i18n.init
from pathlib import Path

# Capture fresh install status SEBELUM setup_validator bikin settings.json
_app_root = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).parent
_settings_path = _app_root / "config" / "settings.json"
is_fresh_install = not _settings_path.exists()

setup_validator = SetupValidator()
setup_validator.ensure_settings_exists()

# Initialize i18n SEBELUM license dialog (supaya dialog bilingual)
from modules_client import i18n
i18n.init(fresh_install=is_fresh_install)

license_mgr = LicenseManager()
if not license_mgr.is_license_valid():
    ...
```

- [ ] **Step 4: Smoke test — app masih jalan normal**

Run: `python main.py`

Expected: app start normal, no error. Periksa `logs/system.log` untuk baris:
```
[i18n] Existing user migration: force ui_language='id'
[i18n] Initialized: lang=id, keys_loaded=1
```

(Kalau Anda user existing, settings.json sudah ada → migration path triggered.)

Quit app.

- [ ] **Step 5: Verify `ui_language` ditulis ke settings.json**

Run: `grep "ui_language" config/settings.json`
Expected: `"ui_language": "id",`

- [ ] **Step 6: Run full pytest suite**

Run: `python -m pytest tests/ -v --tb=short`
Expected: semua PASS (termasuk `test_setup_validator` mungkin perlu update karena settings_default punya field baru — fix kalau fail).

- [ ] **Step 7: Commit**

```bash
git add main.py config/settings_default.json
git commit -m "feat(i18n): hook i18n.init() ke main.py startup sequence"
```

---

## Task 5: Update Build Script untuk Include JSON Files

**Files:**
- Modify: `build_production_exe_fixed.py`

- [ ] **Step 1: Cari blok `datas` di spec**

Run: `grep -n "datas\s*=\|datas\.append" build_production_exe_fixed.py`

- [ ] **Step 2: Tambah `i18n/*.json` ke `datas`**

Edit `build_production_exe_fixed.py`, di blok `datas = [...]` atau blok spec_content string, tambahkan:

```python
# i18n translation files — WAJIB include untuk bilingual support
('i18n/id.json', 'i18n'),
('i18n/en.json', 'i18n'),
```

Format tuple `(source, dest_folder)` — confirm dengan existing entry (misal `config/settings_default.json`).

- [ ] **Step 3: Verify dengan dry-run**

Kalau build script punya dry-run mode, jalankan. Kalau tidak, cek patch di git diff:

```bash
git diff build_production_exe_fixed.py
```

Expected: tambahan 2 baris untuk JSON files di blok datas.

- [ ] **Step 4: Commit (tanpa full build — full build di Phase 8)**

```bash
git add build_production_exe_fixed.py
git commit -m "chore: include i18n/*.json ke PyInstaller datas"
```

---

## Task 6: Common Keys + Language Switcher di Config Tab + Key Coverage Test

**Files:**
- Modify: `i18n/id.json`
- Modify: `i18n/en.json`
- Modify: `ui/config_tab.py`
- Modify: `tests/test_i18n.py`
- Modify: `tests/test_config_tab.py`

- [ ] **Step 1: Isi `common.*` keys di kedua JSON**

Edit `i18n/id.json`:

```json
{
  "common.ok": "OK",
  "common.cancel": "Batal",
  "common.yes": "Ya",
  "common.no": "Tidak",
  "common.apply": "Terapkan",
  "common.save": "Simpan",
  "common.delete": "Hapus",
  "common.close": "Tutup",
  "common.error": "Error",
  "common.warning": "Peringatan",
  "common.info": "Informasi",
  "common.loading": "Memuat...",
  "common.success": "Berhasil",
  "common.confirm": "Konfirmasi",
  "common.add": "Tambah",
  "common.edit": "Ubah",
  "common.refresh": "Refresh",
  "common.back": "Kembali",
  "common.next": "Lanjut",
  "common.browse": "Pilih File",
  "config.label.ui_language": "UI Language / Bahasa Antarmuka:",
  "config.info.restart_required": "Bahasa UI akan diterapkan setelah aplikasi di-restart."
}
```

Edit `i18n/en.json`:

```json
{
  "common.ok": "OK",
  "common.cancel": "Cancel",
  "common.yes": "Yes",
  "common.no": "No",
  "common.apply": "Apply",
  "common.save": "Save",
  "common.delete": "Delete",
  "common.close": "Close",
  "common.error": "Error",
  "common.warning": "Warning",
  "common.info": "Info",
  "common.loading": "Loading...",
  "common.success": "Success",
  "common.confirm": "Confirm",
  "common.add": "Add",
  "common.edit": "Edit",
  "common.refresh": "Refresh",
  "common.back": "Back",
  "common.next": "Next",
  "common.browse": "Browse",
  "config.label.ui_language": "UI Language / Bahasa Antarmuka:",
  "config.info.restart_required": "UI language will apply after restarting the application."
}
```

- [ ] **Step 2: Add key coverage test**

Append ke `tests/test_i18n.py`:

```python
import re
from pathlib import Path


class TestKeyCoverage:
    """Pastikan semua key yang dipakai di source ada di JSON, dan sebaliknya."""

    PROJECT_ROOT = Path(__file__).parent.parent
    KEY_PATTERN = re.compile(r"""\bt\(\s*["']([a-zA-Z_][\w.]*)["']""")

    def _scan_keys_used(self) -> set[str]:
        """Scan semua .py di ui/ dan modules_client/ untuk pemanggilan t("key")."""
        used = set()
        for folder in ["ui", "modules_client"]:
            for pyfile in (self.PROJECT_ROOT / folder).glob("*.py"):
                try:
                    content = pyfile.read_text(encoding="utf-8")
                except Exception:
                    continue
                used.update(self.KEY_PATTERN.findall(content))
        # Scan sales_templates.py juga
        st = self.PROJECT_ROOT / "sales_templates.py"
        if st.exists():
            used.update(self.KEY_PATTERN.findall(st.read_text(encoding="utf-8")))
        return used

    def _load_json_keys(self, filename: str) -> set[str]:
        import json
        path = self.PROJECT_ROOT / "i18n" / filename
        return set(json.loads(path.read_text(encoding="utf-8")).keys())

    def test_all_used_keys_exist_in_id_json(self):
        used = self._scan_keys_used()
        id_keys = self._load_json_keys("id.json")
        missing = used - id_keys
        assert not missing, f"Keys dipakai di source tapi hilang di id.json: {sorted(missing)}"

    def test_all_used_keys_exist_in_en_json(self):
        used = self._scan_keys_used()
        en_keys = self._load_json_keys("en.json")
        missing = used - en_keys
        assert not missing, f"Keys dipakai di source tapi hilang di en.json: {sorted(missing)}"

    def test_id_and_en_have_identical_keys(self):
        """Kedua locale file wajib punya key yang sama persis."""
        id_keys = self._load_json_keys("id.json")
        en_keys = self._load_json_keys("en.json")
        only_id = id_keys - en_keys
        only_en = en_keys - id_keys
        assert not only_id and not only_en, (
            f"Key mismatch:\n"
            f"  Only in id.json: {sorted(only_id)}\n"
            f"  Only in en.json: {sorted(only_en)}"
        )

    def test_placeholders_consistent_between_locales(self):
        """Kalau 'err.x' di id pakai {seconds}, di en juga HARUS pakai {seconds}."""
        import json
        id_data = json.loads((self.PROJECT_ROOT / "i18n" / "id.json").read_text(encoding="utf-8"))
        en_data = json.loads((self.PROJECT_ROOT / "i18n" / "en.json").read_text(encoding="utf-8"))
        placeholder_re = re.compile(r"\{(\w+)\}")
        mismatches = []
        for key in id_data:
            if key not in en_data:
                continue
            id_ph = set(placeholder_re.findall(id_data[key]))
            en_ph = set(placeholder_re.findall(en_data[key]))
            if id_ph != en_ph:
                mismatches.append((key, id_ph, en_ph))
        assert not mismatches, f"Placeholder mismatch:\n" + "\n".join(
            f"  {k}: id={sorted(i)}, en={sorted(e)}" for k, i, e in mismatches
        )
```

- [ ] **Step 3: Run coverage test — expect PASS (no t() calls yet in code)**

Run: `python -m pytest tests/test_i18n.py::TestKeyCoverage -v`
Expected: 4 tests PASS (belum ada `t()` calls di source, jadi used set kosong → no missing keys).

- [ ] **Step 4: Add UI language combo ke Config Tab**

Cari section "Umum" atau area dekat `language_combo` existing di `ui/config_tab.py`. Pattern: cari `self.language_combo = QComboBox()` dan `addItems(["Indonesia", "Malaysia", "English"])`.

Tambah SETELAH blok output_language combo:

```python
from modules_client import i18n
from modules_client.i18n import t

# ===== UI Language (bilingual UI support) =====
ui_lang_label = QLabel(t("config.label.ui_language"))
layout.addWidget(ui_lang_label)

self.ui_lang_combo = QComboBox()
self.ui_lang_combo.addItem("Bahasa Indonesia", "id")
self.ui_lang_combo.addItem("English", "en")
self.ui_lang_combo.setCurrentIndex(0 if i18n.current_language() == "id" else 1)
self.ui_lang_combo.currentIndexChanged.connect(self.on_ui_language_changed)
layout.addWidget(self.ui_lang_combo)
```

Tambah handler di class yang sama:

```python
def on_ui_language_changed(self, idx):
    """Handle perubahan UI language — save ke config + tampilkan restart prompt."""
    new_lang = self.ui_lang_combo.itemData(idx)
    if new_lang == i18n.current_language():
        return
    i18n.set_language(new_lang)
    QMessageBox.information(
        self,
        t("common.info"),
        t("config.info.restart_required"),
    )
```

- [ ] **Step 5: Add test untuk ui_lang_combo**

Append ke `tests/test_config_tab.py` (atau buat section baru):

```python
class TestUILanguageCombo:
    """Test UI language switcher di Config Tab."""

    def test_ui_lang_combo_exists(self, qtbot, mocker):
        mocker.patch("modules_client.i18n.current_language", return_value="id")
        from ui.config_tab import ConfigTab
        mocker.patch("modules_client.config_manager.ConfigManager")
        tab = ConfigTab()
        qtbot.addWidget(tab)
        assert hasattr(tab, "ui_lang_combo")
        assert tab.ui_lang_combo.count() == 2

    def test_ui_lang_combo_reflects_current_language(self, qtbot, mocker):
        mocker.patch("modules_client.i18n.current_language", return_value="en")
        mocker.patch("modules_client.config_manager.ConfigManager")
        from ui.config_tab import ConfigTab
        tab = ConfigTab()
        qtbot.addWidget(tab)
        assert tab.ui_lang_combo.itemData(tab.ui_lang_combo.currentIndex()) == "en"

    def test_ui_lang_change_calls_set_language(self, qtbot, mocker):
        mocker.patch("modules_client.i18n.current_language", return_value="id")
        mocker.patch("modules_client.config_manager.ConfigManager")
        set_lang = mocker.patch("modules_client.i18n.set_language")
        mocker.patch("ui.config_tab.QMessageBox.information")
        from ui.config_tab import ConfigTab
        tab = ConfigTab()
        qtbot.addWidget(tab)
        # Switch ke index EN
        tab.ui_lang_combo.setCurrentIndex(1)
        set_lang.assert_called_once_with("en")
```

- [ ] **Step 6: Run all tests**

Run: `python -m pytest tests/ -v --tb=short`
Expected: all PASS.

- [ ] **Step 7: Smoke test UI**

Run: `python main.py`

Buka Config Tab → scroll ke section Umum → verify "UI Language / Bahasa Antarmuka:" combo ada dengan 2 opsi. Pilih "English" → modal "UI language will apply after restarting" muncul. Close app, check `config/settings.json` → `"ui_language": "en"`.

**Restore ke "id"** sebelum commit (supaya test suite default):
Edit `config/settings.json` → `"ui_language": "id"`.

- [ ] **Step 8: Commit**

```bash
git add i18n/id.json i18n/en.json ui/config_tab.py tests/test_i18n.py tests/test_config_tab.py
git commit -m "feat(i18n): tambah common keys dan UI language switcher di Config Tab"
```

---

## Task 7: Translate License Dialog

**Files:**
- Modify: `ui/license_dialog.py`
- Modify: `i18n/id.json`
- Modify: `i18n/en.json`
- Modify: `tests/test_license_dialog.py`

- [ ] **Step 1: Inventory semua string di `ui/license_dialog.py`**

Run: `grep -nE 'QLabel\(|QPushButton\(|QLineEdit\(|setPlaceholderText|setWindowTitle|QMessageBox\.(warning|information|critical)|QMessageBox\(' ui/license_dialog.py`

Tulis daftar semua string literal user-facing (contoh: "Email:", "🔑 Login VocaLive", "Masuk", "Batal", "Email tidak valid", dll.) — **ignore string untuk logger**.

- [ ] **Step 2: Tambah key `license.*` di kedua JSON**

Edit `i18n/id.json`, tambah section `license.*`:

```json
  "license.dialog.title": "🔑 Login VocaLive",
  "license.label.email": "Email:",
  "license.placeholder.email": "contoh@gmail.com",
  "license.btn.login": "Masuk",
  "license.btn.cancel": "Batal",
  "license.msg.checking": "Memverifikasi lisensi...",
  "license.err.email_invalid": "Format email tidak valid",
  "license.err.email_empty": "Email tidak boleh kosong",
  "license.err.connection": "Tidak bisa terhubung ke server lisensi. Cek koneksi internet.",
  "license.err.not_found": "Email tidak terdaftar. Hubungi admin untuk registrasi.",
  "license.err.expired": "Lisensi sudah expired. Silakan perpanjang.",
  "license.err.unknown": "Terjadi kesalahan: {detail}",
  "license.msg.success": "Lisensi valid, selamat datang!"
```

Edit `i18n/en.json`:

```json
  "license.dialog.title": "🔑 VocaLive Login",
  "license.label.email": "Email:",
  "license.placeholder.email": "example@gmail.com",
  "license.btn.login": "Sign In",
  "license.btn.cancel": "Cancel",
  "license.msg.checking": "Verifying license...",
  "license.err.email_invalid": "Invalid email format",
  "license.err.email_empty": "Email cannot be empty",
  "license.err.connection": "Cannot connect to license server. Check your internet.",
  "license.err.not_found": "Email not registered. Contact admin for registration.",
  "license.err.expired": "License expired. Please renew.",
  "license.err.unknown": "An error occurred: {detail}",
  "license.msg.success": "License valid, welcome!"
```

- [ ] **Step 3: Refactor `ui/license_dialog.py`**

Pattern: untuk setiap string literal user-facing yang di-identify di Step 1, ganti:

```python
# SEBELUM
self.setWindowTitle("🔑 Login VocaLive")
email_label = QLabel("Email:")
self.email_input.setPlaceholderText("contoh@gmail.com")
self.login_btn = QPushButton("Masuk")
...
QMessageBox.warning(self, "Error", "Format email tidak valid")

# SESUDAH
from modules_client.i18n import t

self.setWindowTitle(t("license.dialog.title"))
email_label = QLabel(t("license.label.email"))
self.email_input.setPlaceholderText(t("license.placeholder.email"))
self.login_btn = QPushButton(t("license.btn.login"))
...
QMessageBox.warning(self, t("common.error"), t("license.err.email_invalid"))
```

Untuk error message dengan detail dinamis:

```python
# SEBELUM
QMessageBox.critical(self, "Error", f"Terjadi kesalahan: {e}")
# SESUDAH
QMessageBox.critical(self, t("common.error"), t("license.err.unknown", detail=str(e)))
```

- [ ] **Step 4: Update test_license_dialog.py**

Cari test yang assert raw string (contoh: `assert dialog.windowTitle() == "🔑 Login VocaLive"`). Update ke pattern yang support kedua bahasa:

```python
def test_dialog_title_shown(self, qtbot, mocker):
    # Force UI lang ke 'id' untuk test deterministik
    mocker.patch("modules_client.i18n.current_language", return_value="id")
    mocker.patch("modules_client.i18n._translations", {"license.dialog.title": "🔑 Login VocaLive"})
    mocker.patch("modules_client.i18n._reference_translations", {})
    from ui.license_dialog import LicenseDialog
    dialog = LicenseDialog()
    qtbot.addWidget(dialog)
    assert "Login" in dialog.windowTitle() or "🔑" in dialog.windowTitle()
```

(Longgar-kan assertion supaya tidak strict check raw string — kita cek ada keyword atau emoji saja.)

- [ ] **Step 5: Run tests**

Run: `python -m pytest tests/test_license_dialog.py tests/test_i18n.py -v`
Expected: all PASS. `test_all_used_keys_exist_in_id_json` dan `test_all_used_keys_exist_in_en_json` sekarang aktif catch key missing.

- [ ] **Step 6: Smoke test UI**

Run dari clean state: delete `config/license.enc` dulu supaya trigger login dialog.

```bash
rm config/license.enc  # backup dulu kalau perlu
python main.py
```

License dialog muncul — verify title + labels tampil sesuai `ui_language` aktif. Tutup app tanpa login (batal).

Restore license.enc kalau perlu.

- [ ] **Step 7: Commit**

```bash
git add ui/license_dialog.py i18n/id.json i18n/en.json tests/test_license_dialog.py
git commit -m "feat(i18n): translate License Dialog"
```

---

## Task 8: Translate Update Dialog

**Files:**
- Modify: `ui/update_dialog.py`
- Modify: `i18n/id.json`
- Modify: `i18n/en.json`

- [ ] **Step 1: Inventory strings**

Run: `grep -nE 'QLabel\(|QPushButton\(|setWindowTitle|QMessageBox' ui/update_dialog.py`

- [ ] **Step 2: Tambah key `update.*` di kedua JSON**

`i18n/id.json`:

```json
  "update.dialog.title": "⬆️ Update Tersedia",
  "update.label.version": "Versi baru: {version}",
  "update.label.current": "Versi Anda: {version}",
  "update.label.changelog": "Perubahan:",
  "update.btn.update_now": "Update Sekarang",
  "update.btn.later": "Nanti Saja",
  "update.msg.downloading": "Mengunduh... {progress}%",
  "update.msg.installing": "Menginstall update...",
  "update.msg.done": "Update selesai. Buka VocaLive.exe secara manual.",
  "update.err.download": "Download gagal: {reason}",
  "update.err.install": "Install gagal: {reason}"
```

`i18n/en.json`:

```json
  "update.dialog.title": "⬆️ Update Available",
  "update.label.version": "New version: {version}",
  "update.label.current": "Your version: {version}",
  "update.label.changelog": "Changelog:",
  "update.btn.update_now": "Update Now",
  "update.btn.later": "Later",
  "update.msg.downloading": "Downloading... {progress}%",
  "update.msg.installing": "Installing update...",
  "update.msg.done": "Update complete. Please open VocaLive.exe manually.",
  "update.err.download": "Download failed: {reason}",
  "update.err.install": "Install failed: {reason}"
```

- [ ] **Step 3: Refactor `ui/update_dialog.py`**

Apply pattern yang sama seperti Task 7: semua string user-facing → `t("update.*")`.

- [ ] **Step 4: Run tests**

Run: `python -m pytest tests/ -v --tb=short`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add ui/update_dialog.py i18n/id.json i18n/en.json
git commit -m "feat(i18n): translate Update Dialog"
```

---

## Task 9: Translate Main Window Chrome

**Files:**
- Modify: `ui/main_window.py`
- Modify: `i18n/id.json`
- Modify: `i18n/en.json`

- [ ] **Step 1: Inventory — focus pada chrome saja (window title, tab names, toolbar)**

Run: `grep -nE 'setWindowTitle|addTab\(|setText\("|QAction\(' ui/main_window.py`

**Identifikasi:**
- Window title
- Tab names: "CoHost", "Config", "Product Scene", "Analytics", "User Management", "Virtual Camera"
- Toolbar buttons: "🔄 Cek Update", "⬆️ Update Tersedia!", dll.
- Menu items kalau ada
- Status bar messages yang user-facing

- [ ] **Step 2: Tambah key `main.*`**

`i18n/id.json`:

```json
  "main.window.title": "VocaLive v{version}",
  "main.tab.cohost": "CoHost",
  "main.tab.config": "Konfigurasi",
  "main.tab.product": "Scene Produk",
  "main.tab.analytics": "Analytics",
  "main.tab.users": "Manajemen User",
  "main.tab.camera": "Virtual Camera",
  "main.btn.check_update": "🔄 Cek Update",
  "main.btn.update_available": "⬆️ Update Tersedia!",
  "main.status.ready": "Siap",
  "main.status.connecting": "Menghubungkan...",
  "main.status.connected": "Terhubung",
  "main.status.disconnected": "Terputus",
  "main.msg.license_checking": "Memverifikasi lisensi...",
  "main.msg.license_expired": "Lisensi expired. Silakan login ulang."
```

`i18n/en.json`:

```json
  "main.window.title": "VocaLive v{version}",
  "main.tab.cohost": "CoHost",
  "main.tab.config": "Settings",
  "main.tab.product": "Product Scenes",
  "main.tab.analytics": "Analytics",
  "main.tab.users": "User Management",
  "main.tab.camera": "Virtual Camera",
  "main.btn.check_update": "🔄 Check Update",
  "main.btn.update_available": "⬆️ Update Available!",
  "main.status.ready": "Ready",
  "main.status.connecting": "Connecting...",
  "main.status.connected": "Connected",
  "main.status.disconnected": "Disconnected",
  "main.msg.license_checking": "Verifying license...",
  "main.msg.license_expired": "License expired. Please sign in again."
```

- [ ] **Step 3: Refactor `ui/main_window.py`**

Contoh:

```python
# SEBELUM
self.setWindowTitle(f"VocaLive v{VERSION}")
self.tabs.addTab(cohost_tab, "CoHost")
self.check_update_btn = QPushButton("🔄 Cek Update")

# SESUDAH
from modules_client.i18n import t

self.setWindowTitle(t("main.window.title", version=VERSION))
self.tabs.addTab(cohost_tab, t("main.tab.cohost"))
self.check_update_btn = QPushButton(t("main.btn.check_update"))
```

- [ ] **Step 4: Run tests + smoke**

Run: `python -m pytest tests/ -v --tb=short`
Run: `python main.py` — verify window title + tab names sesuai ui_language aktif.

- [ ] **Step 5: Commit**

```bash
git add ui/main_window.py i18n/id.json i18n/en.json
git commit -m "feat(i18n): translate Main Window chrome (title, tabs, toolbar)"
```

---

## Task 10: Translate Config Tab (Full)

**Files:**
- Modify: `ui/config_tab.py`
- Modify: `i18n/id.json`
- Modify: `i18n/en.json`

- [ ] **Step 1: Inventory semua string di Config Tab**

Run: `grep -cE 'QLabel\(|QPushButton\(|QCheckBox\(|QGroupBox\(|setPlaceholderText|QMessageBox' ui/config_tab.py`
Expected: ~40-50 hits.

Buat list string-by-string menggunakan:
```bash
grep -nE 'QLabel\("[^"]+"|QPushButton\("[^"]+"' ui/config_tab.py | head -50
```

- [ ] **Step 2: Tambah key `config.*` di kedua JSON**

Minimal set (expand sesuai inventory):

`i18n/id.json`:

```json
  "config.section.general": "Pengaturan Umum",
  "config.section.ai": "Pengaturan AI",
  "config.section.tts": "Pengaturan TTS",
  "config.section.tiktok": "TikTok Live",
  "config.label.ai_provider": "AI Provider:",
  "config.label.output_language": "Bahasa Output AI:",
  "config.label.tiktok_nickname": "Username TikTok:",
  "config.label.gemini_key": "API Key Gemini:",
  "config.label.deepseek_key": "API Key DeepSeek:",
  "config.label.tts_voice": "Suara TTS:",
  "config.label.trigger_words": "Trigger Words (pisah koma):",
  "config.label.user_context": "Konteks Jualan:",
  "config.label.cohost_cooldown": "Cooldown CoHost (detik):",
  "config.label.viewer_cooldown": "Cooldown per Viewer (menit):",
  "config.btn.detect_tts_key": "🔍 Deteksi API Key",
  "config.btn.test_tts": "🔊 Test Suara",
  "config.btn.save": "💾 Simpan Pengaturan",
  "config.msg.saved": "Pengaturan berhasil disimpan",
  "config.msg.detect_gemini": "Terdeteksi: Google AI Studio key (Gemini)",
  "config.msg.detect_cloud": "Terdeteksi: Google Cloud TTS key",
  "config.msg.detect_both": "Terdeteksi: Gemini + Google Cloud",
  "config.msg.detect_none": "Tidak terdeteksi key valid",
  "config.msg.test_tts_ok": "Test suara berhasil",
  "config.err.tts_key_invalid": "API Key TTS tidak valid atau tidak diizinkan",
  "config.err.save_failed": "Gagal menyimpan pengaturan: {reason}"
```

`i18n/en.json`:

```json
  "config.section.general": "General Settings",
  "config.section.ai": "AI Settings",
  "config.section.tts": "TTS Settings",
  "config.section.tiktok": "TikTok Live",
  "config.label.ai_provider": "AI Provider:",
  "config.label.output_language": "AI Output Language:",
  "config.label.tiktok_nickname": "TikTok Username:",
  "config.label.gemini_key": "Gemini API Key:",
  "config.label.deepseek_key": "DeepSeek API Key:",
  "config.label.tts_voice": "TTS Voice:",
  "config.label.trigger_words": "Trigger Words (comma-separated):",
  "config.label.user_context": "Sales Context:",
  "config.label.cohost_cooldown": "CoHost Cooldown (seconds):",
  "config.label.viewer_cooldown": "Per-Viewer Cooldown (minutes):",
  "config.btn.detect_tts_key": "🔍 Detect API Key",
  "config.btn.test_tts": "🔊 Test Voice",
  "config.btn.save": "💾 Save Settings",
  "config.msg.saved": "Settings saved successfully",
  "config.msg.detect_gemini": "Detected: Google AI Studio key (Gemini)",
  "config.msg.detect_cloud": "Detected: Google Cloud TTS key",
  "config.msg.detect_both": "Detected: Gemini + Google Cloud",
  "config.msg.detect_none": "No valid key detected",
  "config.msg.test_tts_ok": "Voice test successful",
  "config.err.tts_key_invalid": "TTS API Key invalid or not authorized",
  "config.err.save_failed": "Failed to save settings: {reason}"
```

(Expand kalau inventory di Step 1 menemukan string tambahan — pastikan semua ter-cover.)

- [ ] **Step 3: Refactor `ui/config_tab.py`**

Ganti setiap string literal user-facing → `t("config.*")`. Kelompok:
- Section titles (GroupBox) → `config.section.*`
- Input labels → `config.label.*`
- Buttons → `config.btn.*`
- Success messages → `config.msg.*`
- Errors → `config.err.*`

**JANGAN ubah:**
- Nilai di `output_language` combo (`["Indonesia", "Malaysia", "English"]`) — ini literal value yang disimpan ke settings.json
- Nilai di voice dropdown (`id-ID-Chirp3-...`) — technical IDs
- Placeholder trigger_words default (`"bro, bang, min"`) — user data

- [ ] **Step 4: Run tests + smoke**

Run: `python -m pytest tests/ -v --tb=short`

Expected PASS. Coverage test sekarang validate semua ~30 key config.* ada di kedua JSON.

Run: `python main.py` → buka Config Tab → verify semua label bilingual switchable.

- [ ] **Step 5: Commit**

```bash
git add ui/config_tab.py i18n/id.json i18n/en.json
git commit -m "feat(i18n): translate Config Tab (full)"
```

---

## Task 11: Translate Cohost Tab

**Files:**
- Modify: `ui/cohost_tab_basic.py`
- Modify: `i18n/id.json`
- Modify: `i18n/en.json`

- [ ] **Step 1: Inventory**

Run: `grep -cE 'QLabel\(|QPushButton\(|QCheckBox\(|QGroupBox\(|setWindowTitle' ui/cohost_tab_basic.py`
Expected: ~28+. Inventory full list.

- [ ] **Step 2: Tambah key `cohost.*` dan `err.*`**

Minimum set (expand sesuai inventory):

`i18n/id.json`:

```json
  "cohost.btn.start": "🚀 Mulai",
  "cohost.btn.stop": "⏹ Stop",
  "cohost.btn.clear_log": "🗑 Clear Log",
  "cohost.label.platform": "Platform:",
  "cohost.label.status": "Status:",
  "cohost.label.greeting_interval": "Interval Greeting (detik):",
  "cohost.label.greeting_mode": "Mode Greeting:",
  "cohost.mode.random": "Acak",
  "cohost.mode.sequential": "Berurutan",
  "cohost.status.idle": "Idle",
  "cohost.status.connecting": "Menghubungkan ke TikTok Live...",
  "cohost.status.listening": "Mendengarkan komentar...",
  "cohost.status.stopped": "Dihentikan",
  "cohost.log.user_joined": "{user} bergabung",
  "cohost.log.reply_generated": "AI: {reply}",
  "cohost.log.tts_playing": "🔊 Memutar TTS...",
  "cohost.log.blacklisted": "⛔ User {user} di-blacklist",
  "cohost.log.spam_filtered": "🚫 Spam tersaring dari {user}",
  "cohost.err.tiktok_connect": "Gagal terhubung TikTok: {reason}",
  "cohost.err.tts_failed": "TTS gagal: {reason}",
  "cohost.err.ai_failed": "AI gagal membalas: {reason}",
  "cohost.msg.nickname_empty": "Username TikTok belum diisi. Buka tab Konfigurasi."
```

`i18n/en.json`:

```json
  "cohost.btn.start": "🚀 Start",
  "cohost.btn.stop": "⏹ Stop",
  "cohost.btn.clear_log": "🗑 Clear Log",
  "cohost.label.platform": "Platform:",
  "cohost.label.status": "Status:",
  "cohost.label.greeting_interval": "Greeting Interval (sec):",
  "cohost.label.greeting_mode": "Greeting Mode:",
  "cohost.mode.random": "Random",
  "cohost.mode.sequential": "Sequential",
  "cohost.status.idle": "Idle",
  "cohost.status.connecting": "Connecting to TikTok Live...",
  "cohost.status.listening": "Listening to comments...",
  "cohost.status.stopped": "Stopped",
  "cohost.log.user_joined": "{user} joined",
  "cohost.log.reply_generated": "AI: {reply}",
  "cohost.log.tts_playing": "🔊 Playing TTS...",
  "cohost.log.blacklisted": "⛔ User {user} blacklisted",
  "cohost.log.spam_filtered": "🚫 Spam filtered from {user}",
  "cohost.err.tiktok_connect": "TikTok connection failed: {reason}",
  "cohost.err.tts_failed": "TTS failed: {reason}",
  "cohost.err.ai_failed": "AI reply failed: {reason}",
  "cohost.msg.nickname_empty": "TikTok username is empty. Open Settings tab."
```

- [ ] **Step 3: Refactor `ui/cohost_tab_basic.py`**

Pattern seperti sebelumnya. **Perhatian khusus:**
- Log viewer: pesan yang ditampilkan di log UI widget adalah user-facing → translate. Tapi `logger.info(...)` internal tetap bahasa original.
- Status indicator text (misal "Connected" dengan icon 🟢) → translate.

- [ ] **Step 4: Run tests + smoke**

Run: `python -m pytest tests/ -v --tb=short`

Smoke: `python main.py` → Cohost Tab → ganti UI lang via Config Tab → restart → verify Cohost Tab sekarang English.

- [ ] **Step 5: Commit**

```bash
git add ui/cohost_tab_basic.py i18n/id.json i18n/en.json
git commit -m "feat(i18n): translate Cohost Tab"
```

---

## Task 12: Translate Product Scene Tab

**Files:**
- Modify: `ui/product_scene_tab.py`
- Modify: `i18n/id.json`
- Modify: `i18n/en.json`

- [ ] **Step 1: Inventory (~20 strings)**

Run: `grep -nE 'QLabel\(|QPushButton\(|setWindowTitle|QMessageBox|QFileDialog' ui/product_scene_tab.py`

- [ ] **Step 2: Tambah key `product.*`**

`i18n/id.json`:

```json
  "product.title": "Kelola Scene Produk",
  "product.label.scene_name": "Nama Scene:",
  "product.label.video_path": "Path Video:",
  "product.label.description": "Deskripsi (untuk AI):",
  "product.btn.add": "➕ Tambah Scene",
  "product.btn.browse_video": "📁 Pilih Video",
  "product.btn.remove": "🗑 Hapus",
  "product.btn.test_popup": "👁 Test Popup",
  "product.header.id": "ID",
  "product.header.name": "Nama",
  "product.header.video": "Video",
  "product.msg.added": "Scene berhasil ditambahkan",
  "product.msg.removed": "Scene dihapus",
  "product.err.name_empty": "Nama scene tidak boleh kosong",
  "product.err.video_missing": "File video tidak ditemukan: {path}",
  "product.confirm.delete": "Hapus scene '{name}'?"
```

`i18n/en.json`:

```json
  "product.title": "Manage Product Scenes",
  "product.label.scene_name": "Scene Name:",
  "product.label.video_path": "Video Path:",
  "product.label.description": "Description (for AI):",
  "product.btn.add": "➕ Add Scene",
  "product.btn.browse_video": "📁 Choose Video",
  "product.btn.remove": "🗑 Remove",
  "product.btn.test_popup": "👁 Test Popup",
  "product.header.id": "ID",
  "product.header.name": "Name",
  "product.header.video": "Video",
  "product.msg.added": "Scene added successfully",
  "product.msg.removed": "Scene removed",
  "product.err.name_empty": "Scene name cannot be empty",
  "product.err.video_missing": "Video file not found: {path}",
  "product.confirm.delete": "Delete scene '{name}'?"
```

- [ ] **Step 3: Refactor + test + commit**

```bash
git add ui/product_scene_tab.py i18n/id.json i18n/en.json
git commit -m "feat(i18n): translate Product Scene Tab"
```

---

## Task 13: Translate Analytics Tab

**Files:**
- Modify: `ui/analytics_tab.py`
- Modify: `i18n/id.json`
- Modify: `i18n/en.json`

- [ ] **Step 1: Inventory (~25 strings)**

Run: `grep -nE 'QLabel\(|QPushButton\(|setWindowTitle|setText\("' ui/analytics_tab.py`

- [ ] **Step 2: Tambah key `analytics.*`**

`i18n/id.json`:

```json
  "analytics.title": "Analytics & Laporan",
  "analytics.label.total_comments": "Total Komentar:",
  "analytics.label.total_replies": "Total Reply AI:",
  "analytics.label.top_keywords": "Keyword Terbanyak:",
  "analytics.label.session_duration": "Durasi Sesi:",
  "analytics.label.unique_viewers": "Viewer Unik:",
  "analytics.label.date_range": "Rentang Tanggal:",
  "analytics.btn.refresh": "🔄 Refresh",
  "analytics.btn.export_csv": "📁 Export CSV",
  "analytics.btn.clear_data": "🗑 Hapus Data",
  "analytics.msg.no_data": "Belum ada data untuk ditampilkan",
  "analytics.msg.exported": "Data berhasil diekspor ke {path}",
  "analytics.confirm.clear": "Yakin hapus semua data analytics? Tindakan ini tidak dapat dibatalkan."
```

`i18n/en.json`:

```json
  "analytics.title": "Analytics & Reports",
  "analytics.label.total_comments": "Total Comments:",
  "analytics.label.total_replies": "Total AI Replies:",
  "analytics.label.top_keywords": "Top Keywords:",
  "analytics.label.session_duration": "Session Duration:",
  "analytics.label.unique_viewers": "Unique Viewers:",
  "analytics.label.date_range": "Date Range:",
  "analytics.btn.refresh": "🔄 Refresh",
  "analytics.btn.export_csv": "📁 Export CSV",
  "analytics.btn.clear_data": "🗑 Clear Data",
  "analytics.msg.no_data": "No data to display yet",
  "analytics.msg.exported": "Data exported to {path}",
  "analytics.confirm.clear": "Clear all analytics data? This cannot be undone."
```

- [ ] **Step 3: Refactor + test + commit**

```bash
git add ui/analytics_tab.py i18n/id.json i18n/en.json
git commit -m "feat(i18n): translate Analytics Tab"
```

---

## Task 14: Translate User Management Tab

**Files:**
- Modify: `ui/user_management_tab.py`
- Modify: `i18n/id.json`
- Modify: `i18n/en.json`

- [ ] **Step 1: Inventory (~15 strings)**

Run: `grep -nE 'QLabel\(|QPushButton\(|QMessageBox' ui/user_management_tab.py`

- [ ] **Step 2: Tambah key `users.*`**

`i18n/id.json`:

```json
  "users.title": "Manajemen User TikTok",
  "users.tab.blacklist": "Blacklist",
  "users.tab.whitelist": "Whitelist",
  "users.label.username": "Username:",
  "users.label.reason": "Alasan:",
  "users.btn.add": "➕ Tambah",
  "users.btn.remove": "➖ Hapus Pilihan",
  "users.btn.clear": "🗑 Clear Semua",
  "users.msg.added": "User {user} ditambahkan ke {list_type}",
  "users.msg.removed": "User dihapus dari daftar",
  "users.err.username_empty": "Username tidak boleh kosong",
  "users.err.already_exists": "User {user} sudah ada di daftar {list_type}",
  "users.confirm.clear": "Hapus semua user dari {list_type}?"
```

`i18n/en.json`:

```json
  "users.title": "TikTok User Management",
  "users.tab.blacklist": "Blacklist",
  "users.tab.whitelist": "Whitelist",
  "users.label.username": "Username:",
  "users.label.reason": "Reason:",
  "users.btn.add": "➕ Add",
  "users.btn.remove": "➖ Remove Selected",
  "users.btn.clear": "🗑 Clear All",
  "users.msg.added": "User {user} added to {list_type}",
  "users.msg.removed": "User removed from list",
  "users.err.username_empty": "Username cannot be empty",
  "users.err.already_exists": "User {user} already in {list_type}",
  "users.confirm.clear": "Remove all users from {list_type}?"
```

- [ ] **Step 3: Refactor + test + commit**

```bash
git add ui/user_management_tab.py i18n/id.json i18n/en.json
git commit -m "feat(i18n): translate User Management Tab"
```

---

## Task 15: Translate Virtual Camera Tab

**Files:**
- Modify: `ui/virtual_camera_tab.py`
- Modify: `i18n/id.json`
- Modify: `i18n/en.json`

- [ ] **Step 1: Inventory (~15 strings)**

Run: `grep -nE 'QLabel\(|QPushButton\(|QCheckBox\(|QFileDialog' ui/virtual_camera_tab.py`

- [ ] **Step 2: Tambah key `camera.*`**

`i18n/id.json`:

```json
  "camera.title": "Virtual Camera",
  "camera.label.backend": "Backend:",
  "camera.label.playlist": "Playlist Video:",
  "camera.label.play_mode": "Mode Putar:",
  "camera.mode.sequential": "Berurutan",
  "camera.mode.random": "Acak",
  "camera.btn.add_video": "➕ Tambah Video",
  "camera.btn.remove_selected": "➖ Hapus Pilihan",
  "camera.btn.start_camera": "▶️ Jalankan Virtual Camera",
  "camera.btn.stop_camera": "⏹ Stop",
  "camera.status.no_driver": "⚠️ Driver virtual camera tidak terdeteksi",
  "camera.status.obs": "✅ OBS Virtual Camera terdeteksi",
  "camera.status.unity": "✅ UnityCapture terdeteksi",
  "camera.status.running": "🎥 Virtual camera aktif",
  "camera.err.no_videos": "Playlist kosong. Tambah video dulu.",
  "camera.err.driver_missing": "Driver tidak tersedia. Install OBS atau UnityCapture."
```

`i18n/en.json`:

```json
  "camera.title": "Virtual Camera",
  "camera.label.backend": "Backend:",
  "camera.label.playlist": "Video Playlist:",
  "camera.label.play_mode": "Play Mode:",
  "camera.mode.sequential": "Sequential",
  "camera.mode.random": "Random",
  "camera.btn.add_video": "➕ Add Video",
  "camera.btn.remove_selected": "➖ Remove Selected",
  "camera.btn.start_camera": "▶️ Start Virtual Camera",
  "camera.btn.stop_camera": "⏹ Stop",
  "camera.status.no_driver": "⚠️ No virtual camera driver detected",
  "camera.status.obs": "✅ OBS Virtual Camera detected",
  "camera.status.unity": "✅ UnityCapture detected",
  "camera.status.running": "🎥 Virtual camera running",
  "camera.err.no_videos": "Playlist is empty. Add videos first.",
  "camera.err.driver_missing": "Driver not available. Install OBS or UnityCapture."
```

- [ ] **Step 3: Refactor + test + commit**

```bash
git add ui/virtual_camera_tab.py i18n/id.json i18n/en.json
git commit -m "feat(i18n): translate Virtual Camera Tab"
```

---

## Task 16: Translate Product Popup Window

**Files:**
- Modify: `ui/product_popup_window.py`
- Modify: `i18n/id.json`
- Modify: `i18n/en.json`

- [ ] **Step 1: Inventory (~5 strings — kecil)**

Run: `grep -nE 'QLabel\(|QPushButton\(|setWindowTitle' ui/product_popup_window.py`

- [ ] **Step 2: Tambah key `popup.*`**

`i18n/id.json`:

```json
  "popup.title": "Popup Produk: {name}",
  "popup.label.price": "Harga:",
  "popup.btn.close": "Tutup",
  "popup.hint.drag": "Seret untuk memindahkan",
  "popup.hint.resize": "Tarik sudut untuk ubah ukuran"
```

`i18n/en.json`:

```json
  "popup.title": "Product Popup: {name}",
  "popup.label.price": "Price:",
  "popup.btn.close": "Close",
  "popup.hint.drag": "Drag to move",
  "popup.hint.resize": "Drag corner to resize"
```

- [ ] **Step 3: Refactor + test + commit**

```bash
git add ui/product_popup_window.py i18n/id.json i18n/en.json
git commit -m "feat(i18n): translate Product Popup Window"
```

---

## Task 17: Refactor `sales_templates.py` + Translate Template Content

**Files:**
- Modify: `sales_templates.py`
- Modify: `i18n/id.json`
- Modify: `i18n/en.json`
- Create: `tests/test_sales_templates_i18n.py`

- [ ] **Step 1: Identifikasi semua caller `TEMPLATES`**

Run: `grep -rn "from sales_templates import TEMPLATES\|sales_templates\.TEMPLATES" --include="*.py"`

- [ ] **Step 2: Write failing test untuk `get_templates()`**

Create `tests/test_sales_templates_i18n.py`:

```python
"""Test sales_templates dengan i18n."""
import pytest


class TestSalesTemplatesI18n:
    def test_get_templates_returns_dict_with_keys(self, mocker):
        mocker.patch("modules_client.i18n._translations", {
            "sales_template.general_seller.name": "Penjual Umum",
            "sales_template.general_seller.description": "Template umum",
            "sales_template.general_seller.content": "Kamu adalah asisten live streaming...",
        })
        mocker.patch("modules_client.i18n._reference_translations", {})
        from sales_templates import get_templates
        templates = get_templates()
        assert "general_seller" in templates
        assert templates["general_seller"]["name"] == "Penjual Umum"

    def test_get_templates_reflects_current_language(self, mocker):
        """Ganti _translations → get_templates() return nilai baru."""
        mocker.patch("modules_client.i18n._translations", {
            "sales_template.general_seller.name": "General Seller",
            "sales_template.general_seller.description": "Generic template",
            "sales_template.general_seller.content": "You are a live streaming assistant...",
        })
        mocker.patch("modules_client.i18n._reference_translations", {})
        from sales_templates import get_templates
        templates = get_templates()
        assert templates["general_seller"]["name"] == "General Seller"
```

- [ ] **Step 3: Run test — expect FAIL (function doesn't exist yet)**

Run: `python -m pytest tests/test_sales_templates_i18n.py -v`
Expected: FAIL dengan ImportError atau AttributeError.

- [ ] **Step 4: Refactor `sales_templates.py`**

Replace full file content:

```python
"""Sales Templates for VocaLive CoHost AI — i18n aware.

IMPORTANT: jangan pernah `TEMPLATES = get_templates()` di module level.
Evaluasi top-level mengambil nilai SEBELUM i18n.init() dipanggil, menghasilkan
raw key strings. Semua caller WAJIB panggil get_templates() lazily setiap kali
butuh data template.
"""
from modules_client.i18n import t

TEMPLATE_KEYS = [
    "general_seller",
    "fashion_seller",
    "food_seller",
    "beauty_seller",
    "electronics_seller",
    "household_seller",
    "baby_seller",
    "health_seller",
    "digital_seller",
    "automotive_seller",
]


def get_templates() -> dict:
    """Return dict template dalam UI language aktif. Panggil setiap butuh data fresh."""
    return {
        key: {
            "name": t(f"sales_template.{key}.name"),
            "description": t(f"sales_template.{key}.description"),
            "content": t(f"sales_template.{key}.content"),
        }
        for key in TEMPLATE_KEYS
    }
```

- [ ] **Step 5: Update semua caller dari `TEMPLATES` → `get_templates()`**

Pakai grep dari Step 1. Umumnya di `config_tab.py` atau tempat yang tampilkan dropdown template:

```python
# SEBELUM
from sales_templates import TEMPLATES
self.template_combo.addItems([TEMPLATES[k]["name"] for k in TEMPLATES])

# SESUDAH
from sales_templates import get_templates
templates = get_templates()
self.template_combo.addItems([templates[k]["name"] for k in templates])
```

- [ ] **Step 6: Tambah content templates ke JSON**

Terjemahkan isi `content` dari existing `TEMPLATES` dict lama (sekarang sudah di git history) ke kedua JSON.

`i18n/id.json` (partial — salin isi original sebagai ID, translate untuk EN):

```json
  "sales_template.general_seller.name": "Penjual Umum",
  "sales_template.general_seller.description": "Template umum untuk jualan produk apapun",
  "sales_template.general_seller.content": "Kamu adalah asisten live streaming yang ramah dan antusias.\nTugasmu membantu menjawab pertanyaan penonton tentang produk yang dijual.\nJawab dengan singkat, jelas, dan persuasif. Gunakan bahasa Indonesia yang santai.\nSelalu dorong penonton untuk segera order karena stok terbatas.\nMaksimal 2-3 kalimat per jawaban.",

  "sales_template.fashion_seller.name": "Penjual Fashion",
  "sales_template.fashion_seller.description": "Template untuk jualan baju, sepatu, aksesoris",
  "sales_template.fashion_seller.content": "Kamu adalah fashion advisor yang stylish dan trendy di live streaming.\nBantu penonton memilih ukuran, warna, dan gaya yang cocok untuk mereka.\nJelaskan material, kualitas, dan keunggulan produk fashion dengan antusias.\nSarankan mix & match outfit yang menarik. Bahasa santai, semangat, dan persuasif.\nMaksimal 2-3 kalimat per jawaban.",

  "sales_template.food_seller.name": "Penjual Kuliner",
  "sales_template.food_seller.description": "Template untuk jualan makanan, minuman, snack",
  "sales_template.food_seller.content": "Kamu adalah food enthusiast yang passionate di live streaming.\nDeskripsikan rasa, tekstur, dan keunikan produk kuliner dengan cara yang menggugah selera.\nJelaskan cara penyajian, bahan-bahan premium, dan manfaat kesehatan jika ada.\nBuat penonton penasaran dan ingin langsung mencoba. Bahasa hangat dan mengundang.\nMaksimal 2-3 kalimat per jawaban.",

  "sales_template.beauty_seller.name": "Penjual Kecantikan",
  "sales_template.beauty_seller.description": "Template untuk jualan skincare, makeup, perawatan",
  "sales_template.beauty_seller.content": "Kamu adalah beauty consultant yang ahli di live streaming.\nBantu penonton memilih produk kecantikan sesuai jenis kulit dan kebutuhan mereka.\nJelaskan kandungan aktif, manfaat, dan cara penggunaan produk dengan detail.\nRekomendasikan rutinitas perawatan yang cocok. Bahasa profesional namun tetap akrab.\nMaksimal 2-3 kalimat per jawaban.",

  "sales_template.electronics_seller.name": "Penjual Elektronik",
  "sales_template.electronics_seller.description": "Template untuk jualan gadget, elektronik, aksesoris",
  "sales_template.electronics_seller.content": "Kamu adalah tech advisor yang menguasai produk elektronik di live streaming.\nJelaskan spesifikasi, fitur unggulan, dan keunggulan produk secara mudah dipahami.\nBantu penonton membandingkan pilihan dan menemukan produk yang sesuai kebutuhan dan budget.\nBerikan tips penggunaan yang berguna. Bahasa informatif dan terpercaya.\nMaksimal 2-3 kalimat per jawaban.",

  "sales_template.household_seller.name": "Penjual Peralatan Rumah Tangga",
  "sales_template.household_seller.description": "Template untuk jualan peralatan rumah, dapur, kebersihan",
  "sales_template.household_seller.content": "Kamu adalah home expert di live streaming yang antusias.\nJelaskan fungsi, kemudahan pakai, dan manfaat praktis peralatan rumah tangga.\nTekankan kualitas material, daya tahan, dan value for money.\nBuat penonton membayangkan betapa mudahnya hidup dengan produk ini.\nMaksimal 2-3 kalimat per jawaban.",

  "sales_template.baby_seller.name": "Penjual Perlengkapan Bayi",
  "sales_template.baby_seller.description": "Template untuk jualan perlengkapan bayi, anak, ibu",
  "sales_template.baby_seller.content": "Kamu adalah parenting advisor yang caring di live streaming.\nJelaskan keamanan, kenyamanan, dan manfaat produk untuk tumbuh kembang anak.\nBantu ibu memilih produk sesuai usia dan kebutuhan bayi/anak.\nBerikan tips parenting yang berguna. Bahasa lembut, hangat, dan meyakinkan.\nMaksimal 2-3 kalimat per jawaban.",

  "sales_template.health_seller.name": "Penjual Kesehatan",
  "sales_template.health_seller.description": "Template untuk jualan suplemen, herbal, alat kesehatan",
  "sales_template.health_seller.content": "Kamu adalah health advisor yang terpercaya di live streaming.\nJelaskan manfaat, kandungan, dan cara konsumsi produk kesehatan dengan akurat.\nTekankan keamanan, sertifikasi, dan pengalaman pengguna lain.\nIngatkan konsultasi dokter untuk kasus khusus. Bahasa informatif dan bijak.\nMaksimal 2-3 kalimat per jawaban.",

  "sales_template.digital_seller.name": "Penjual Produk Digital",
  "sales_template.digital_seller.description": "Template untuk jualan ebook, kursus, software, akun premium",
  "sales_template.digital_seller.content": "Kamu adalah digital consultant yang paham tren di live streaming.\nJelaskan manfaat, fitur, dan value produk digital secara menarik.\nBerikan gambaran konkret tentang hasil yang bisa didapat pembeli.\nTekankan harga spesial live dan akses instan. Bahasa enerjik dan meyakinkan.\nMaksimal 2-3 kalimat per jawaban.",

  "sales_template.automotive_seller.name": "Penjual Otomotif",
  "sales_template.automotive_seller.description": "Template untuk jualan aksesoris motor, mobil, sparepart",
  "sales_template.automotive_seller.content": "Kamu adalah otomotif advisor yang passionate di live streaming.\nJelaskan spesifikasi, kompatibilitas, dan keunggulan produk otomotif.\nBantu penonton memilih aksesoris atau sparepart yang cocok untuk kendaraan mereka.\nBerikan tips perawatan dan instalasi. Bahasa teknis namun tetap mudah dipahami.\nMaksimal 2-3 kalimat per jawaban."
```

`i18n/en.json` — translate semua content ke English. Contoh 1:

```json
  "sales_template.general_seller.name": "General Seller",
  "sales_template.general_seller.description": "General template for selling any product",
  "sales_template.general_seller.content": "You are a friendly and enthusiastic live streaming assistant.\nYour job is to help answer viewer questions about the products being sold.\nRespond concisely, clearly, and persuasively. Use casual, engaging English.\nAlways encourage viewers to order quickly because stock is limited.\nMaximum 2-3 sentences per answer."
```

(Lanjutkan untuk 9 template lain dengan pola yang sama.)

- [ ] **Step 7: Verify TEMPLATE_KEYS list di sales_templates.py matches original TEMPLATES dict keys**

Run: `git show HEAD~10:sales_templates.py | grep -oE '"\w+_seller"' | sort -u`

Bandingkan dengan `TEMPLATE_KEYS` di file baru. Kalau beda, tambah/hapus key yang sesuai.

- [ ] **Step 8: Run all tests**

Run: `python -m pytest tests/ -v --tb=short`
Expected: all PASS. Key coverage test memvalidasi 10 template × 3 field = 30 keys ada di kedua JSON.

- [ ] **Step 9: Smoke test**

Run: `python main.py` → Config Tab → dropdown template → pilih beberapa template → verify name dan content reflects UI lang. Ganti UI lang → restart → template names sekarang bilingual.

- [ ] **Step 10: Commit**

```bash
git add sales_templates.py i18n/id.json i18n/en.json tests/test_sales_templates_i18n.py
# Tambah caller-caller yang di-update di step 5
git add ui/config_tab.py   # atau file lain yg dipakai
git commit -m "feat(i18n): refactor sales_templates ke get_templates() lazy + translate content"
```

---

## Task 18: Translate AI/TTS Error Messages + Greeting AI Generator Special Case

**Files:**
- Modify: `modules_client/gemini_ai.py`
- Modify: `modules_client/deepseek_ai.py`
- Modify: `modules_client/api.py`
- Modify: `modules_server/tts_engine.py`
- Modify: `modules_client/greeting_ai_generator.py`
- Modify: `i18n/id.json`
- Modify: `i18n/en.json`

- [ ] **Step 1: Inventory user-facing errors di AI modules**

Run: `grep -nE 'raise (Exception|ValueError|RuntimeError)\(|QMessageBox' modules_client/gemini_ai.py modules_client/deepseek_ai.py modules_client/api.py`

**Kritis:** pisahkan:
- Exception message yang DI-RAISE → bisa dibaca UI layer (translate)
- `logger.error/warning/info` → developer log (JANGAN translate)

- [ ] **Step 2: Tambah key `err.api.*` dan `err.tts.*`**

`i18n/id.json`:

```json
  "err.api.gemini_key_missing": "API Key Gemini tidak ditemukan di config/settings.json",
  "err.api.deepseek_key_missing": "API Key DeepSeek tidak ditemukan di config/settings.json",
  "err.api.gemini_forbidden": "Gemini 403: Generative Language API belum di-enable di API Key restrictions",
  "err.api.timeout": "Permintaan AI timeout setelah {seconds} detik",
  "err.api.rate_limit": "Rate limit tercapai, coba lagi dalam beberapa menit",
  "err.api.network": "Gagal terhubung ke server AI: {reason}",
  "err.api.invalid_response": "Response AI tidak valid: {detail}",
  "err.api.unknown": "Error AI tidak diketahui: {detail}",
  "err.tts.gemini_failed": "Gemini TTS gagal: {reason}",
  "err.tts.cloud_failed": "Google Cloud TTS gagal: {reason}",
  "err.tts.key_missing": "API Key TTS belum diset",
  "err.tts.no_voice": "Voice tidak dipilih. Buka tab Konfigurasi."
```

`i18n/en.json`:

```json
  "err.api.gemini_key_missing": "Gemini API Key not found in config/settings.json",
  "err.api.deepseek_key_missing": "DeepSeek API Key not found in config/settings.json",
  "err.api.gemini_forbidden": "Gemini 403: Generative Language API not enabled in API Key restrictions",
  "err.api.timeout": "AI request timed out after {seconds} seconds",
  "err.api.rate_limit": "Rate limit reached, please try again in a few minutes",
  "err.api.network": "Failed to connect to AI server: {reason}",
  "err.api.invalid_response": "Invalid AI response: {detail}",
  "err.api.unknown": "Unknown AI error: {detail}",
  "err.tts.gemini_failed": "Gemini TTS failed: {reason}",
  "err.tts.cloud_failed": "Google Cloud TTS failed: {reason}",
  "err.tts.key_missing": "TTS API Key not set",
  "err.tts.no_voice": "No voice selected. Open Settings tab."
```

- [ ] **Step 3: Refactor AI modules**

Pattern:

```python
# SEBELUM (gemini_ai.py)
if not api_key:
    raise Exception("API Key Gemini tidak ditemukan di config/settings.json")

# SESUDAH
from modules_client.i18n import t

if not api_key:
    raise Exception(t("err.api.gemini_key_missing"))
```

Untuk error dengan detail dinamis:

```python
# SEBELUM
raise Exception(f"Gemini timeout setelah {timeout}s")
# SESUDAH
raise Exception(t("err.api.timeout", seconds=timeout))
```

Apply ke semua file di Step 1.

- [ ] **Step 4: Refactor TTS engine error surfacing**

`modules_server/tts_engine.py`:

```python
# Log internal TETAP bahasa asli — jangan translate
logger.error(f"Gemini TTS gagal: {e}")

# Tapi kalau error di-surface ke UI via signal atau exception:
# SEBELUM
raise Exception(f"Gemini TTS gagal: {e}")
# SESUDAH
from modules_client.i18n import t
raise Exception(t("err.tts.gemini_failed", reason=str(e)))
```

- [ ] **Step 5: Greeting AI Generator — special case (output_language, bukan ui_language)**

Edit `modules_client/greeting_ai_generator.py`:

```python
# Cari tempat prompt di-build (sekitar function generate_greetings atau similar)

# SEBELUM
prompt = f"Buat 10 sapaan unik untuk live streaming TikTok dengan nickname {nickname}..."

# SESUDAH
output_lang = cfg.get("output_language", "Indonesia")
prompt_templates = {
    "Indonesia": (
        "Buat 10 sapaan unik dan variatif untuk live streaming TikTok dengan nickname {nickname}. "
        "Format: bullet list dengan tanda '-'. Masing-masing 1 kalimat pendek, ramah, dan enerjik. "
        "Variasikan: menyapa viewer baru, yang sering datang, yang kasih gift, dll."
    ),
    "English": (
        "Generate 10 unique and varied greetings for a TikTok live stream with nickname {nickname}. "
        "Format: bullet list with '-'. Each is a short, friendly, energetic sentence. "
        "Vary: welcoming new viewers, regular viewers, gifters, etc."
    ),
    "Malaysia": (
        "Buatkan 10 sapaan unik dan pelbagai untuk siaran langsung TikTok dengan nickname {nickname} "
        "dalam bahasa Melayu. Format: senarai bullet dengan '-'. Setiap satu ayat pendek, mesra, "
        "dan bertenaga. Pelbagaikan: menyambut penonton baru, tetap, pemberi hadiah, dll."
    ),
}
prompt = prompt_templates.get(output_lang, prompt_templates["Indonesia"]).format(nickname=nickname)
```

**Catatan:** ini BUKAN menggunakan `t()` i18n manager — karena prompt ini harus mengikuti `output_language` (bahasa AI bicara ke viewer), BUKAN `ui_language` (bahasa app UI).

- [ ] **Step 6: Run all tests**

Run: `python -m pytest tests/ -v --tb=short`
Expected: all PASS. Coverage test validate semua error keys exist.

- [ ] **Step 7: Smoke test error paths**

Run: `python main.py` → set Gemini API Key kosong di Config → Save → buka Cohost Tab → klik Start TikTok Live → verify error dialog dalam UI language aktif.

Ganti UI ke English → restart → trigger error lagi → verify English.

- [ ] **Step 8: Commit**

```bash
git add modules_client/gemini_ai.py modules_client/deepseek_ai.py modules_client/api.py \
        modules_server/tts_engine.py modules_client/greeting_ai_generator.py \
        i18n/id.json i18n/en.json
git commit -m "feat(i18n): translate AI/TTS error messages + greeting prompt per output_language"
```

---

## Task 19: Tambah `ui_language` ke Telemetry

**Files:**
- Modify: `main.py`

- [ ] **Step 1: Locate `telemetry.set_user_context` call di main.py**

Run: `grep -n "set_user_context\|telemetry.init" main.py`

- [ ] **Step 2: Tambah `ui_language` ke user context**

```python
# SEBELUM
telemetry.set_user_context({
    "platform": "windows",
    "app_mode": APP_MODE,
})

# SESUDAH
telemetry.set_user_context({
    "platform": "windows",
    "app_mode": APP_MODE,
    "ui_language": i18n.current_language(),
})
```

- [ ] **Step 3: Run pytest**

Run: `python -m pytest tests/ -v --tb=short`
Expected: all PASS.

- [ ] **Step 4: Commit**

```bash
git add main.py
git commit -m "feat(i18n): tambah ui_language property ke telemetry user context"
```

---

## Task 20: Update `CLAUDE.md` dengan Section i18n + Bump Version

**Files:**
- Modify: `CLAUDE.md`
- Modify: `version.py`

- [ ] **Step 1: Tambah section "Internationalization (i18n)" di CLAUDE.md**

Insert SETELAH section "Greeting System" atau di area Architecture:

```markdown
### Internationalization (i18n)

VocaLive support bilingual UI: **Indonesia** dan **English**. UI language terpisah dari `output_language` AI (yang mengontrol bahasa AI ke viewer).

1. **`modules_client/i18n.py`** — JSON dict-based translation manager. API publik: `init()`, `t(key, **kwargs)`, `current_language()`, `set_language(lang)`
2. **`i18n/id.json`** dan **`i18n/en.json`** — flat dotted keys (`<area>.<component>.<element>`)
3. **Detection**: fresh install → deteksi Windows locale (id/ms → ID, en-* → EN). User existing update → force "id" (migrasi cegah kejutan)
4. **Switcher**: di Config Tab, apply setelah restart (bukan hot-reload)
5. **Coverage test**: `tests/test_i18n.py::TestKeyCoverage` memastikan setiap `t("key")` di source ada di kedua JSON

**Pattern refactor string widget:**

```python
from modules_client.i18n import t

# SEBELUM
btn = QPushButton("🚀 Mulai")
# SESUDAH
btn = QPushButton(t("cohost.btn.start"))
```

**Non-UI strings yang di-translate:** sales templates (`sales_templates.py` → `get_templates()` lazy), AI/TTS error messages, license dialog, update dialog.

**Non-UI strings yang TIDAK di-translate:**
- Developer log (`logger.*`) — konsisten untuk Sentry/MCP debugging
- Voice identifier (`Gemini-Puck`, `id-ID-Chirp3-*`)
- User data (greeting slots, product names, trigger_words, user_context, tiktok_nickname)
- `output_language` combo values (tetap literal "Indonesia"/"Malaysia"/"English")

**Special case — Greeting AI Generator prompt:** mengikuti `output_language` (bahasa viewer dengar AI), BUKAN `ui_language` (bahasa app UI). Diimplementasi via dict lookup terpisah di `greeting_ai_generator.py`, bukan lewat `t()`.
```

- [ ] **Step 2: Tambah Bilingual checklist ke Manual QA di CLAUDE.md**

Insert ke section "Manual QA Checklist" SETELAH "📦 Build Output":

```markdown
#### 🌐 Bilingual / i18n
- [ ] Fresh install di Windows id-ID → UI muncul Indonesia
- [ ] Fresh install di Windows en-US → UI muncul English
- [ ] Update dari v1.0.14 → UI tetap Indonesia (migration)
- [ ] Ganti UI lang di Config Tab → restart → semua tab pakai bahasa baru
- [ ] License dialog tampil sesuai UI lang (saat first install sebelum login)
- [ ] Update dialog tampil sesuai UI lang
- [ ] Sales template dropdown: nama dan content sesuai UI lang
- [ ] Template dikirim ke AI sesuai UI lang, tapi AI output tetap ikuti output_language
- [ ] Error TTS ditampilkan dalam UI lang
- [ ] Greeting AI tetap pakai output_language (UI=EN + output=ID → greeting ID)
- [ ] PostHog event `app_launched` menyertakan property `ui_language`
```

- [ ] **Step 3: Update Version History di CLAUDE.md**

Tambah baris baru di tabel Version History:

```markdown
| **v1.0.15** | 2026-04-17 | Bilingual UI support (Indonesia / English), OS locale detection, migration user existing |
```

Update "Versi saat ini: v1.0.15" di bawah tabel.

- [ ] **Step 4: Bump `version.py`**

Edit `version.py`:

```python
VERSION = "1.0.15"
VERSION_WIN = "1.0.15.0"
VERSION_TUPLE = (1, 0, 15, 0)
```

- [ ] **Step 5: Run tests**

Run: `python -m pytest tests/ -v --tb=short`
Expected: all PASS (termasuk `test_version.py` yang validate format).

- [ ] **Step 6: Commit**

```bash
git add CLAUDE.md version.py
git commit -m "docs: dokumentasi i18n + bump ke v1.0.15"
```

---

## Task 21: Final QA, Lint, Build, PR

**Files:**
- Various (final cleanup)

- [ ] **Step 1: Run ruff lint**

Run: `ruff check .`
Expected: ≤ baseline (~107 issue existing). Kalau i18n introduced new issues, fix.

Run: `ruff check --fix . && ruff format .` untuk auto-fix safe issues.

- [ ] **Step 2: Run full pytest dengan coverage**

Run: `python -m pytest tests/ -v --tb=short --cov=modules_client --cov=modules_server --cov=ui --cov-report=term-missing`
Expected: all PASS. Coverage test `test_all_used_keys_exist_in_*_json` dan `test_id_and_en_have_identical_keys` hijau.

- [ ] **Step 3: Manual QA — fresh install simulation**

```bash
# Backup config existing
cp config/settings.json config/settings.json.bak
rm config/settings.json

# Trigger fresh install path
python main.py
```

Expected: setup_validator bikin settings.json baru, i18n.init detect OS locale. Periksa `config/settings.json` → field `ui_language` terset sesuai OS Windows Anda.

Quit app. Restore backup:
```bash
mv config/settings.json.bak config/settings.json
```

- [ ] **Step 4: Manual QA — switch language + restart**

Run `python main.py` → Config Tab → ganti UI language → restart app → verify semua tab (License dialog kalau re-login, CoHost, Config, Product, Analytics, Users, Virtual Camera) sudah pakai bahasa baru. Check CLAUDE.md Bilingual checklist di Task 20 Step 2.

- [ ] **Step 5: Build EXE production**

Run: `python build_production_exe_fixed.py`

Expected: `dist/VocaLive-v1.0.15.zip` dibuat. Size ~236MB (verify tidak ada bloat dari i18n addition — JSON files kecil, max 100KB).

Extract ZIP ke folder test → jalankan `VocaLive.exe` → verify tidak ada DLL error → verify `i18n/id.json` dan `i18n/en.json` ada di folder extracted.

- [ ] **Step 6: Run Manual QA Checklist lengkap dari CLAUDE.md**

Kerjakan semua section checklist existing (Startup, TTS, TikTok Live, Product Popup, Virtual Camera, Auto-Update, Telemetry, Build Output) PLUS section 🌐 Bilingual yang baru.

- [ ] **Step 7: Final commit (kalau ada cleanup)**

```bash
git status
# Kalau ada uncommitted changes dari ruff format atau QA fix:
git add <files>
git commit -m "chore: final cleanup pre-release v1.0.15"
```

- [ ] **Step 8: Push branch dan buka PR**

```bash
git push -u origin feat/i18n-bilingual-support
```

Create PR ke `main` via `gh pr create`:

```bash
gh pr create --title "feat: bilingual UI support (Indonesia / English) — v1.0.15" --body "$(cat <<'EOF'
## Summary

Menambahkan dukungan bilingual UI (Indonesia dan English) ke VocaLive sebagai additive layer — zero perubahan fitur atau behavior.

- JSON dict-based translation manager di `modules_client/i18n.py`
- UI language terpisah dari `output_language` AI (dua konsep independen)
- OS locale detection untuk fresh install, migrasi eksplisit `"id"` untuk user existing
- Switcher di Config Tab, apply setelah restart
- Semua 11 file UI + AI/TTS error messages + sales templates di-translate (~315 keys)
- 15+ test baru termasuk key coverage test yang otomatis catch key missing

Target version: v1.0.15

## Test Plan
- [x] Pytest hijau (~230 tests termasuk 15+ test i18n baru)
- [x] Ruff lint tidak regresi dari baseline
- [x] Fresh install Windows id-ID → UI Indonesia otomatis
- [x] Fresh install Windows en-US → UI English otomatis
- [x] Update dari v1.0.14 → UI tetap Indonesia (migrasi)
- [x] Switch UI lang di Config Tab → restart → semua tab translated
- [x] License dialog + Update dialog bilingual
- [x] Sales templates bilingual
- [x] AI/TTS error messages bilingual
- [x] Greeting AI generator tetap pakai output_language (bukan ui_language) — confirmed
- [x] Build EXE v1.0.15 sukses, size ~236MB (no bloat)
- [x] Manual QA checklist lengkap sesuai CLAUDE.md

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

- [ ] **Step 9: Post-merge release tasks (setelah PR approved & merged)**

Urutan (dari CLAUDE.md "Alur Rilis Versi Baru"):
1. Tag release: `git tag v1.0.15 && git push origin v1.0.15`
2. Upload `dist/VocaLive-v1.0.15.zip` ke GitHub Releases: https://github.com/arulbarker/vocalive-release/releases
3. Update `appscript.txt`: `VERSION_INFO["vocalive"]["latest"] = "1.0.15"`, update URL ke asset ZIP baru → deploy Google Apps Script

---

## Self-Review Summary

**Spec coverage:**
- ✅ Section 2 (Key Decisions) → covered in Tasks 3, 4, 6
- ✅ Section 3 (Arsitektur) → Tasks 1-3 implement i18n.py, Task 5 wires ke build
- ✅ Section 4 (Migration) → Task 3 covers fresh_install + migration force-id
- ✅ Section 5 (Integration Pattern) → Tasks 7-16 apply pattern per UI file
- ✅ Section 6 (Non-UI strings) → Task 17 (sales_templates), Task 18 (AI/TTS errors + greeting special case)
- ✅ Section 7 (Testing) → Task 6 Step 2 creates coverage test yang enforce sepanjang phases berikutnya
- ✅ Section 8 (Phases) → 21 tasks cover phase 0-8
- ✅ Section 9 (Build) → Task 5
- ✅ Section 9.3 (Telemetry `ui_language`) → Task 19
- ✅ Section 12 (Acceptance Criteria) → Task 21 final QA covers semua

**Type consistency:** Semua task pakai import `from modules_client.i18n import t` dan naming `ui_language` config field konsisten.

**No placeholders:** Semua step punya code konkret. Translation content sample lengkap di Tasks 6-18. Task 17 & 18 menyediakan minimum set — masih butuh iterasi kalau inventory Step 1 find string tambahan (acceptable, bukan placeholder).

**Known gap:** Task 17 Step 6 menerjemahkan 10 template EN — sample content diberikan hanya untuk template pertama. Implementer perlu terjemahkan 9 template sisanya mengikuti pola sama. Ini effort yang reasonable dan eksplisit.

---

**Plan complete.** Siap dieksekusi.
