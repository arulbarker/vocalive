"""Tests untuk modules_client/config_manager.py."""

import json
import sys
import pytest
from pathlib import Path
from unittest.mock import patch

from modules_client.config_manager import ConfigManager, _get_app_root

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


# ---------------------------------------------------------------------------
# 10. test_get_app_root_dev_mode
# ---------------------------------------------------------------------------
def test_get_app_root_dev_mode():
    """_get_app_root() di dev mode harus return parent dari modules_client/."""
    root = _get_app_root()
    assert (root / "modules_client").exists()


# ---------------------------------------------------------------------------
# 11. test_get_app_root_frozen_mode
# ---------------------------------------------------------------------------
def test_get_app_root_frozen_mode(tmp_path):
    """_get_app_root() di frozen (EXE) mode harus return parent dari executable."""
    fake_exe = tmp_path / "VocaLive.exe"
    fake_exe.touch()
    with patch.object(sys, 'frozen', True, create=True), \
         patch.object(sys, 'executable', str(fake_exe)):
        root = _get_app_root()
        assert root == tmp_path


# ---------------------------------------------------------------------------
# 12. test_config_manager_resolves_relative_path
# ---------------------------------------------------------------------------
def test_config_manager_resolves_relative_path():
    """ConfigManager dengan path relatif harus resolve ke path absolut."""
    cm = ConfigManager("config/settings.json")
    assert cm.config_file.is_absolute()


# ---------------------------------------------------------------------------
# 13. test_config_manager_keeps_absolute_path
# ---------------------------------------------------------------------------
def test_config_manager_keeps_absolute_path(tmp_path):
    """ConfigManager dengan path absolut harus pakai langsung tanpa resolve."""
    abs_path = tmp_path / "my_settings.json"
    cm = ConfigManager(str(abs_path))
    assert cm.config_file == abs_path
