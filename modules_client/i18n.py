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
    """Return 'id' untuk Windows id-ID/ms-MY, 'en' untuk en-*, default 'id' lainnya.

    Note: menggunakan `locale.getdefaultlocale()` yang deprecated di Python 3.11+
    tapi tetap dipakai karena `locale.getlocale()` (penggantinya) TIDAK membaca
    Windows user UI language preference — hanya current C locale yang biasanya None.
    Revisit ketika Python 3.15 menghapus API ini (pakai ctypes.windll.kernel32.GetUserDefaultUILanguage).
    """
    import warnings
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
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


def _i18n_dir() -> Path:
    """Return path folder i18n/. Handles dev mode, PyInstaller onefile, dan onedir.

    Kritis: PyInstaller onefile extract bundled data ke sys._MEIPASS (temp dir),
    BUKAN ke Path(sys.executable).parent (folder EXE). Sebelumnya assume onedir
    → JSON tidak ketemu di onefile build → UI tampilkan raw keys.
    """
    if getattr(sys, "frozen", False):
        # 1. PyInstaller onefile: sys._MEIPASS adalah temp extraction dir
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            candidate = Path(meipass) / "i18n"
            if candidate.exists():
                return candidate
        # 2. Onedir mode (atau fallback): folder EXE
        exe_dir_candidate = Path(sys.executable).parent / "i18n"
        if exe_dir_candidate.exists():
            return exe_dir_candidate
        # 3. Last resort: return _MEIPASS path anyway (log akan tell us kalau missing)
        if meipass:
            return Path(meipass) / "i18n"
        return exe_dir_candidate
    # Dev mode: project root
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
