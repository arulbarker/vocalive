"""
Tests untuk modules_client/api.py — routing dan JSON parsing generate_reply_with_scene.

Catatan penting untuk mocking:
- api.py melakukan LOCAL IMPORT di dalam fungsi (baris 372, 393, 403).
  Karena itu, patch harus di-target ke SUMBER module:
    - modules_client.config_manager.ConfigManager (bukan api.ConfigManager)
    - modules_client.gemini_ai.generate_reply (bukan api.gemini_gen)
    - modules_client.deepseek_ai.generate_reply
- ConfigManager singleton tidak cukup di-patch constructor-nya — kita harus
  memastikan instance.get() return nilai yang diinginkan.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

ROOT_DIR = Path(__file__).parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

pytestmark = pytest.mark.integration


@pytest.fixture(autouse=True)
def _i18n_id_loaded(monkeypatch):
    """Load real id.json translations agar t() di api.py return nilai asli,
    bukan raw key. Tanpa ini, err.api.* key akan di-return as-is."""
    import json

    from modules_client import i18n

    i18n_path = Path(__file__).parent.parent / "i18n" / "id.json"
    translations = json.loads(i18n_path.read_text(encoding="utf-8"))
    monkeypatch.setattr(i18n, "_current_lang", "id")
    monkeypatch.setattr(i18n, "_translations", translations)
    monkeypatch.setattr(i18n, "_reference_translations", translations)


def _make_cfg_mock(ai_provider: str = "gemini", gemini_key: str = "fake-key", deepseek_key: str = "fake-key"):
    """Return MagicMock yang mensimulasikan ConfigManager class.

    Penting: return value dari ConfigManager() harus punya .get() method yang
    return nilai yang di-hardcode sesuai parameter.
    """
    instance = MagicMock()

    def _get(key, default=None):
        data = {
            "ai_provider": ai_provider,
            "api_keys": {
                "GEMINI_API_KEY": gemini_key,
                "DEEPSEEK_API_KEY": deepseek_key,
            },
        }
        return data.get(key, default)

    instance.get.side_effect = _get

    cls_mock = MagicMock(return_value=instance)
    return cls_mock


def _patch_psm(context_str: str = "scene_id=1 : Hijab Premium"):
    """Return context manager yang mem-patch ProductSceneManager."""
    psm_class = MagicMock()
    psm_instance = MagicMock()
    psm_instance.build_product_context.return_value = context_str
    psm_class.return_value = psm_instance
    return patch("modules_client.product_scene_manager.ProductSceneManager", psm_class)


def test_parse_valid_scene_response():
    """AI merespons JSON {"reply": "...", "scene_id": 1} → scene_id=1."""
    fake_ai_response = '{"reply": "Hijab premium 89rb kak", "scene_id": 1}'
    cfg_cls_mock = _make_cfg_mock(ai_provider="gemini")

    with patch("modules_client.config_manager.ConfigManager", cfg_cls_mock), \
         _patch_psm(), \
         patch("modules_client.gemini_ai.generate_reply", return_value=fake_ai_response) as gem_mock:
        from modules_client.api import generate_reply_with_scene

        reply, scene_id = generate_reply_with_scene("Berapa harga hijab?")

    assert gem_mock.called, "Gemini generate_reply seharusnya dipanggil"
    assert scene_id == 1
    assert "Hijab premium 89rb kak" in reply


def test_parse_scene_id_zero():
    """AI merespons JSON dengan scene_id=0 → reply tanpa popup."""
    fake_ai_response = '{"reply": "Halo selamat datang", "scene_id": 0}'
    cfg_cls_mock = _make_cfg_mock(ai_provider="gemini")

    with patch("modules_client.config_manager.ConfigManager", cfg_cls_mock), \
         _patch_psm(), \
         patch("modules_client.gemini_ai.generate_reply", return_value=fake_ai_response):
        from modules_client.api import generate_reply_with_scene

        reply, scene_id = generate_reply_with_scene("Halo!")

    assert scene_id == 0
    assert "Halo selamat datang" in reply


def test_non_json_response_fallback():
    """AI mengembalikan plain text (bukan JSON) → (raw_text, 0) fallback."""
    plain_text = "Halo kak"
    cfg_cls_mock = _make_cfg_mock(ai_provider="gemini")

    with patch("modules_client.config_manager.ConfigManager", cfg_cls_mock), \
         _patch_psm(), \
         patch("modules_client.gemini_ai.generate_reply", return_value=plain_text):
        from modules_client.api import generate_reply_with_scene

        reply, scene_id = generate_reply_with_scene("Halo!")

    assert scene_id == 0
    assert reply == plain_text


def test_deepseek_provider_routing():
    """ai_provider='deepseek' → deepseek_ai.generate_reply dipanggil, bukan gemini."""
    fake_ai_response = '{"reply": "Dari DeepSeek", "scene_id": 2}'
    cfg_cls_mock = _make_cfg_mock(ai_provider="deepseek")

    with patch("modules_client.config_manager.ConfigManager", cfg_cls_mock), \
         _patch_psm(), \
         patch("modules_client.gemini_ai.generate_reply") as gem_mock, \
         patch("modules_client.deepseek_ai.generate_reply", return_value=fake_ai_response) as ds_mock:
        from modules_client.api import generate_reply_with_scene

        reply, scene_id = generate_reply_with_scene("Test")

    assert ds_mock.called, "DeepSeek seharusnya dipanggil"
    assert not gem_mock.called, "Gemini seharusnya TIDAK dipanggil untuk provider=deepseek"
    assert scene_id == 2
    assert "Dari DeepSeek" in reply


def test_missing_gemini_key_returns_error():
    """Kalau GEMINI_API_KEY kosong → error message, tidak panggil AI."""
    cfg_cls_mock = _make_cfg_mock(ai_provider="gemini", gemini_key="")

    with patch("modules_client.config_manager.ConfigManager", cfg_cls_mock), \
         _patch_psm(), \
         patch("modules_client.gemini_ai.generate_reply") as gem_mock:
        from modules_client.api import generate_reply_with_scene

        reply, scene_id = generate_reply_with_scene("Test")

    assert not gem_mock.called
    assert scene_id == 0
    assert "GEMINI_API_KEY" in reply


def test_empty_product_context_uses_plain_reply():
    """Kalau tidak ada produk terdaftar → jatuh ke generate_reply biasa."""
    cfg_cls_mock = _make_cfg_mock(ai_provider="gemini")

    with patch("modules_client.config_manager.ConfigManager", cfg_cls_mock), \
         _patch_psm(context_str=""), \
         patch("modules_client.api.generate_reply", return_value="Halo tanpa produk") as plain_mock:
        from modules_client.api import generate_reply_with_scene

        reply, scene_id = generate_reply_with_scene("Test")

    assert plain_mock.called
    assert scene_id == 0
    assert reply == "Halo tanpa produk"


def test_api_connection_returns_dict():
    """test_api_connection() selalu return dict, bahkan saat network error."""
    import requests.exceptions

    cfg_cls_mock = _make_cfg_mock(ai_provider="deepseek", deepseek_key="")

    conn_error = requests.exceptions.ConnectionError("Network unavailable")
    mock_session = MagicMock()
    mock_session.get.side_effect = conn_error

    with patch("modules_client.config_manager.ConfigManager", cfg_cls_mock):
        import modules_client.api as api_module

        original_session = api_module.api_bridge.session
        api_module.api_bridge.session = mock_session
        try:
            result = api_module.test_api_connection()
        finally:
            api_module.api_bridge.session = original_session

    assert isinstance(result, dict)
    assert "ai_provider" in result
    assert "local_server" in result
