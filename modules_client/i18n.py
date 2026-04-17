"""VocaLive i18n — JSON dict-based translation manager.

Public API:
    init(fresh_install: bool = False) -> None
    t(key: str, **kwargs) -> str
    current_language() -> str
    set_language(lang: str) -> None
"""
import locale as _locale
import logging

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
