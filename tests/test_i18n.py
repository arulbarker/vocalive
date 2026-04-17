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
