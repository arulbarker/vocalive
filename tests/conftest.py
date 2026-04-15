"""Shared fixtures untuk VocaLive test suite."""

import json
import sys
import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Tambah root project ke sys.path agar import modules_client/ bisa
ROOT_DIR = Path(__file__).parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


@pytest.fixture
def tmp_config(tmp_path):
    """Buat config directory + settings.json sementara."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    settings = {
        "platform": "TikTok",
        "ai_provider": "gemini",
        "tts_voice": "Gemini-Puck (MALE)",
        "tts_key_type": "gemini",
        "google_tts_api_key": "",
        "output_language": "Indonesia",
        "api_keys": {
            "GEMINI_API_KEY": "test-key-123",
            "DEEPSEEK_API_KEY": ""
        },
        "user_context": "Toko online fashion hijab",
        "trigger_words": ["bro", "bang", "min"],
        "viewer_cooldown_minutes": 3,
        "cohost_cooldown": 2,
    }
    settings_file = config_dir / "settings.json"
    settings_file.write_text(json.dumps(settings, indent=2), encoding="utf-8")
    return tmp_path


@pytest.fixture
def tmp_settings_file(tmp_config):
    """Return path to temporary settings.json."""
    return tmp_config / "config" / "settings.json"


@pytest.fixture
def tmp_product_scenes(tmp_path):
    """Buat product_scenes.json sementara dengan sample data."""
    config_dir = tmp_path / "config"
    config_dir.mkdir(exist_ok=True)
    scenes = {
        "popup_width": 608,
        "popup_height": 1080,
        "enabled": True,
        "scenes": [
            {"id": 1, "name": "Hijab Voal Premium", "video_path": "videos/hijab.mp4"},
            {"id": 2, "name": "Gamis Syari Set", "video_path": "videos/gamis.mp4"},
        ]
    }
    scene_file = config_dir / "product_scenes.json"
    scene_file.write_text(json.dumps(scenes, indent=2), encoding="utf-8")
    return str(scene_file)


@pytest.fixture
def tmp_user_lists(tmp_path):
    """Buat user_lists.json sementara."""
    config_dir = tmp_path / "config"
    config_dir.mkdir(exist_ok=True)
    lists = {
        "blacklist": ["spammer1", "troll_user"],
        "whitelist": ["vip_buyer", "reseller_01"]
    }
    lists_file = config_dir / "user_lists.json"
    lists_file.write_text(json.dumps(lists, indent=2), encoding="utf-8")
    return str(lists_file)


@pytest.fixture
def tmp_analytics_dir(tmp_path):
    """Buat analytics directory sementara."""
    analytics_dir = tmp_path / "analytics"
    analytics_dir.mkdir()
    return analytics_dir


@pytest.fixture
def mock_pygame():
    """Mock pygame untuk test yang butuh audio playback."""
    with patch.dict("sys.modules", {"pygame": MagicMock(), "pygame.mixer": MagicMock()}):
        yield


@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset semua singleton sebelum setiap test."""
    yield
    # Reset UserListManager singleton
    try:
        from modules_client.user_list_manager import UserListManager
        UserListManager._instance = None
    except ImportError:
        pass
    # Reset analytics singleton
    try:
        import modules_client.analytics_manager as am
        am._analytics_manager = None
    except ImportError:
        pass
