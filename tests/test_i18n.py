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
