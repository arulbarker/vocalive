"""
Tests untuk modules_client/setup_validator.py

Covers:
- SetupValidator(root_dir=str)
- validate_all() → (is_valid, errors, warnings)
"""

import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration

from modules_client.setup_validator import SetupValidator

# ===========================================================================
# test_validate_valid_setup
# ===========================================================================

def test_validate_valid_setup(tmp_path):
    """
    Setup valid: config dir ada, settings.json valid, file pendukung ada.
    Harus mengembalikan is_valid=True tanpa errors kritis terkait file/JSON.
    """
    # Buat struktur config yang valid
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
            "GEMINI_API_KEY": "test-gemini-key",
            "DEEPSEEK_API_KEY": "sk-testkey123",
        },
        "user_context": "Toko online fashion",
    }
    (config_dir / "settings.json").write_text(
        json.dumps(settings, indent=2), encoding="utf-8"
    )
    (config_dir / "settings_default.json").write_text(
        json.dumps(settings, indent=2), encoding="utf-8"
    )
    (config_dir / "voices.json").write_text(
        json.dumps({"gtts_standard": [], "chirp3": [], "gemini_flash": []}),
        encoding="utf-8",
    )

    validator = SetupValidator(root_dir=str(tmp_path))
    is_valid, errors, warnings = validator.validate_all()

    # Tidak boleh ada error — hanya warnings yang mungkin muncul (misal API key)
    assert is_valid is True, f"Unexpected errors: {errors}"
    # Tidak ada error terkait MISSING file atau JSON syntax
    for err in errors:
        assert "MISSING" not in err
        assert "INVALID JSON" not in err


# ===========================================================================
# test_validate_missing_config_dir
# ===========================================================================

def test_validate_missing_config_dir(tmp_path):
    """
    Jika config directory tidak ada, validate_all() harus mengembalikan is_valid=False.
    Note: SetupValidator mencoba membuat dir; kita pakai subdir agar dia tidak bisa buat
    atau kita cek bahwa minimal ada error yang dilaporkan sebelum/sesudah auto-create.
    """
    # Arahkan ke direktori kosong tanpa sub-folder config sama sekali
    empty_root = tmp_path / "empty_project"
    empty_root.mkdir()

    validator = SetupValidator(root_dir=str(empty_root))
    is_valid, errors, warnings = validator.validate_all()

    # Config dir tidak ada → harus invalid ATAU ada warning/error tentang dir/file yang hilang.
    # SetupValidator akan coba buat dir; setelah itu settings.json masih tidak ada → error.
    assert is_valid is False
    # Harus ada pesan yang menyebut file yang hilang (settings.json)
    combined = " ".join(errors)
    assert "settings.json" in combined or "MISSING" in combined or "Config directory" in combined


# ===========================================================================
# test_validate_malformed_json
# ===========================================================================

def test_validate_malformed_json(tmp_path):
    """
    Jika settings.json berisi JSON tidak valid, validate_all() harus
    mengembalikan is_valid=False dengan pesan error tentang JSON syntax.
    """
    config_dir = tmp_path / "config"
    config_dir.mkdir()

    # Tulis JSON yang rusak
    (config_dir / "settings.json").write_text(
        '{"platform": "TikTok", INVALID_JSON !!!}', encoding="utf-8"
    )

    validator = SetupValidator(root_dir=str(tmp_path))
    is_valid, errors, warnings = validator.validate_all()

    assert is_valid is False
    combined = " ".join(errors)
    # Harus ada referensi ke JSON error di settings.json
    assert "settings.json" in combined
    assert "INVALID JSON" in combined or "JSON" in combined
