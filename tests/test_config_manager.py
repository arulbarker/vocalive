"""Tests untuk modules_client/config_manager.py."""

import json
import pytest
from pathlib import Path

from modules_client.config_manager import ConfigManager

pytestmark = pytest.mark.integration


# ---------------------------------------------------------------------------
# 1. test_load_settings_from_file
# ---------------------------------------------------------------------------
def test_load_settings_from_file(tmp_settings_file):
    """load_settings() harus mengembalikan dict dengan platform == 'TikTok'."""
    cm = ConfigManager(config_file=str(tmp_settings_file))
    settings = cm.load_settings()

    assert isinstance(settings, dict)
    assert settings.get("platform") == "TikTok"


# ---------------------------------------------------------------------------
# 2. test_get_returns_value
# ---------------------------------------------------------------------------
def test_get_returns_value(tmp_settings_file):
    """get('platform') harus mengembalikan 'TikTok'."""
    cm = ConfigManager(config_file=str(tmp_settings_file))

    assert cm.get("platform") == "TikTok"


# ---------------------------------------------------------------------------
# 3. test_get_returns_default_for_missing_key
# ---------------------------------------------------------------------------
def test_get_returns_default_for_missing_key(tmp_settings_file):
    """get() harus mengembalikan default jika key tidak ada; None jika no default."""
    cm = ConfigManager(config_file=str(tmp_settings_file))

    assert cm.get("nonexistent_key", "fallback") == "fallback"
    assert cm.get("nonexistent_key") is None


# ---------------------------------------------------------------------------
# 4. test_set_persists_value
# ---------------------------------------------------------------------------
def test_set_persists_value(tmp_settings_file):
    """set() harus menulis ke file sehingga ConfigManager baru bisa membacanya."""
    cm = ConfigManager(config_file=str(tmp_settings_file))
    result = cm.set("new_setting", "hello_world")

    assert result is True

    # Baca ulang pakai instance baru
    cm2 = ConfigManager(config_file=str(tmp_settings_file))
    assert cm2.get("new_setting") == "hello_world"


# ---------------------------------------------------------------------------
# 5. test_get_api_key_top_level
# ---------------------------------------------------------------------------
def test_get_api_key_top_level(tmp_settings_file):
    """get_api_key() harus menemukan nilai dari key top-level."""
    cm = ConfigManager(config_file=str(tmp_settings_file))

    # "platform" ada di top-level settings.json
    assert cm.get_api_key("platform") == "TikTok"


# ---------------------------------------------------------------------------
# 6. test_get_api_key_nested
# ---------------------------------------------------------------------------
def test_get_api_key_nested(tmp_settings_file):
    """get_api_key() harus menemukan nilai dari nested api_keys dict."""
    cm = ConfigManager(config_file=str(tmp_settings_file))

    assert cm.get_api_key("GEMINI_API_KEY") == "test-key-123"


# ---------------------------------------------------------------------------
# 7. test_get_api_key_not_found
# ---------------------------------------------------------------------------
def test_get_api_key_not_found(tmp_settings_file):
    """get_api_key() harus mengembalikan None jika key tidak ditemukan di mana pun."""
    cm = ConfigManager(config_file=str(tmp_settings_file))

    assert cm.get_api_key("TOTALLY_MISSING_KEY") is None


# ---------------------------------------------------------------------------
# 8. test_load_settings_missing_file
# ---------------------------------------------------------------------------
def test_load_settings_missing_file(tmp_path):
    """load_settings() harus mengembalikan {} jika file tidak ada."""
    nonexistent = tmp_path / "config" / "does_not_exist.json"
    cm = ConfigManager(config_file=str(nonexistent))

    settings = cm.load_settings()

    assert settings == {}


# ---------------------------------------------------------------------------
# 9. test_load_settings_malformed_json
# ---------------------------------------------------------------------------
def test_load_settings_malformed_json(tmp_path):
    """load_settings() harus mengembalikan {} jika JSON tidak valid."""
    bad_file = tmp_path / "bad_settings.json"
    bad_file.write_text("{this is not valid json!!!", encoding="utf-8")

    cm = ConfigManager(config_file=str(bad_file))
    settings = cm.load_settings()

    assert settings == {}
