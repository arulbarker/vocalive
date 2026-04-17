"""
Tests untuk modules_client/api.py — routing dan JSON parsing generate_reply_with_scene.

Semua test di-mark sebagai integration karena melibatkan import modul client
dan mocking di level yang membutuhkan dependency modules_client.
"""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Pastikan root project ada di sys.path
ROOT_DIR = Path(__file__).parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

pytestmark = pytest.mark.integration


# ---------------------------------------------------------------------------
# Helpers — buat mock ConfigManager yang mengembalikan setting tertentu
# ---------------------------------------------------------------------------

def _make_cfg_mock(ai_provider: str = "gemini", gemini_key: str = "fake-key", deepseek_key: str = ""):
    """Return MagicMock yang mensimulasikan ConfigManager.get()."""
    cfg_instance = MagicMock()

    def _cfg_get(key, default=None):
        mapping = {
            "ai_provider": ai_provider,
            "api_keys": {
                "GEMINI_API_KEY": gemini_key,
                "DEEPSEEK_API_KEY": deepseek_key,
            },
        }
        return mapping.get(key, default)

    cfg_instance.get.side_effect = _cfg_get
    return cfg_instance


# ---------------------------------------------------------------------------
# Test 1 — parse valid JSON dengan scene_id = 1
# ---------------------------------------------------------------------------

def test_parse_valid_scene_response():
    """
    generate_reply_with_scene harus return scene_id=1 ketika AI merespons
    dengan JSON {"reply": "...", "scene_id": 1}.

    ProductSceneManager diimport secara lazy di dalam fungsi, sehingga patch
    harus dilakukan di modules_client.product_scene_manager, bukan
    modules_client.api.
    """
    fake_ai_response = '{"reply": "Hijab premium 89rb kak", "scene_id": 1}'

    cfg_mock = _make_cfg_mock(ai_provider="gemini", gemini_key="fake-key")

    with patch("modules_client.api.ConfigManager", return_value=cfg_mock), \
         patch(
             "modules_client.product_scene_manager.ProductSceneManager"
         ) as MockPSM, \
         patch("modules_client.gemini_ai.generate_reply", return_value=fake_ai_response):

        # ProductSceneManager.build_product_context() harus return non-empty
        # agar jalur JSON parsing aktif (bukan jalur no-product fallback)
        psm_instance = MagicMock()
        psm_instance.build_product_context.return_value = "scene_id=1 : Hijab Premium"
        MockPSM.return_value = psm_instance

        from modules_client.api import generate_reply_with_scene

        reply, scene_id = generate_reply_with_scene("Berapa harga hijab?")

    assert scene_id == 1
    assert "Hijab premium 89rb kak" in reply


# ---------------------------------------------------------------------------
# Test 2 — parse valid JSON dengan scene_id = 0
# ---------------------------------------------------------------------------

def test_parse_scene_id_zero():
    """
    generate_reply_with_scene harus return scene_id=0 ketika AI merespons
    dengan JSON {"reply": "...", "scene_id": 0} (tidak ada produk relevan).
    """
    fake_ai_response = '{"reply": "Halo selamat datang", "scene_id": 0}'

    cfg_mock = _make_cfg_mock(ai_provider="gemini", gemini_key="fake-key")

    with patch("modules_client.api.ConfigManager", return_value=cfg_mock), \
         patch("modules_client.product_scene_manager.ProductSceneManager") as MockPSM, \
         patch("modules_client.gemini_ai.generate_reply", return_value=fake_ai_response):

        psm_instance = MagicMock()
        psm_instance.build_product_context.return_value = "scene_id=1 : Hijab Premium"
        MockPSM.return_value = psm_instance

        from modules_client.api import generate_reply_with_scene

        reply, scene_id = generate_reply_with_scene("Halo!")

    assert scene_id == 0
    assert "Halo selamat datang" in reply


# ---------------------------------------------------------------------------
# Test 3 — fallback ke (raw_text, 0) ketika respons AI bukan JSON
# ---------------------------------------------------------------------------

def test_non_json_response_fallback():
    """
    Ketika AI mengembalikan teks biasa (bukan JSON), generate_reply_with_scene
    harus return (raw_text, 0) sebagai fallback — bukan raise exception.
    """
    plain_text = "Halo kak"

    cfg_mock = _make_cfg_mock(ai_provider="gemini", gemini_key="fake-key")

    with patch("modules_client.api.ConfigManager", return_value=cfg_mock), \
         patch("modules_client.product_scene_manager.ProductSceneManager") as MockPSM, \
         patch("modules_client.gemini_ai.generate_reply", return_value=plain_text):

        psm_instance = MagicMock()
        psm_instance.build_product_context.return_value = "scene_id=1 : Hijab Premium"
        MockPSM.return_value = psm_instance

        from modules_client.api import generate_reply_with_scene

        reply, scene_id = generate_reply_with_scene("Halo!")

    assert scene_id == 0
    assert reply == plain_text


# ---------------------------------------------------------------------------
# Test 4 — test_api_connection() harus return dict
# ---------------------------------------------------------------------------

def test_api_connection_returns_dict():
    """
    test_api_connection() harus selalu return dict tanpa melempar exception,
    bahkan ketika semua koneksi jaringan gagal.

    api_bridge sudah ter-instantiate saat module di-import, sehingga kita
    patch atribut session langsung pada objek global yang sudah ada.
    """
    import requests.exceptions

    cfg_mock = _make_cfg_mock(ai_provider="deepseek", deepseek_key="")

    # Simulasikan koneksi gagal dengan exception yang di-handle oleh fungsi
    conn_error = requests.exceptions.ConnectionError("Network unavailable")
    mock_session = MagicMock()
    mock_session.get.side_effect = conn_error

    with patch("modules_client.api.ConfigManager", return_value=cfg_mock):
        import modules_client.api as api_module

        original_session = api_module.api_bridge.session
        api_module.api_bridge.session = mock_session
        try:
            result = api_module.test_api_connection()
        finally:
            api_module.api_bridge.session = original_session

    assert isinstance(result, dict)
    # Kunci wajib ada
    assert "ai_provider" in result
    assert "local_server" in result
