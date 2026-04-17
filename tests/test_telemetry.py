"""
Tests untuk modules_client/telemetry.py

Covers:
- _read_device_id()          → baca dari file / fallback "anonymous"
- init()                     → set _initialized, _device_id, _app_version
- capture()                  → no-op sebelum init, panggil posthog.capture setelah init
- close()                    → no-op sebelum init, tidak crash
"""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

pytestmark = pytest.mark.integration

import modules_client.telemetry as t

# ---------------------------------------------------------------------------
# Autouse fixture — reset module-level globals between tests
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_telemetry_state():
    """Reset module state sebelum dan sesudah setiap test."""
    t._initialized = False
    t._device_id = "anonymous"
    t._app_version = "unknown"
    yield
    t._initialized = False
    t._device_id = "anonymous"
    t._app_version = "unknown"


# ---------------------------------------------------------------------------
# Helper — buat mock modul sentry_sdk dan posthog
# ---------------------------------------------------------------------------

def _make_sdk_mocks():
    """Kembalikan (mock_sentry, mock_posthog) yang siap dimasukkan ke sys.modules."""
    mock_sentry = MagicMock()
    mock_posthog = MagicMock()
    return mock_sentry, mock_posthog


# ===========================================================================
# TestReadDeviceId
# ===========================================================================

class TestReadDeviceId:

    def test_read_device_id(self, tmp_path):
        """Jika device_id.dat ada dan berisi id, harus mengembalikan nilai tersebut."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        device_id_file = config_dir / "device_id.dat"
        device_id_file.write_text(json.dumps({"id": "test-123"}), encoding="utf-8")

        with patch.object(t, "_get_app_root", return_value=tmp_path):
            result = t._read_device_id()

        assert result == "test-123"

    def test_read_device_id_missing_file(self, tmp_path):
        """Jika device_id.dat tidak ada, harus mengembalikan 'anonymous'."""
        with patch.object(t, "_get_app_root", return_value=tmp_path):
            result = t._read_device_id()

        assert result == "anonymous"


# ===========================================================================
# TestInit
# ===========================================================================

class TestInit:

    def test_init_sets_state(self, tmp_path):
        """init() harus set _initialized=True, _device_id, dan _app_version dengan benar."""
        # Siapkan device_id.dat agar _read_device_id() mengembalikan nilai nyata
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        (config_dir / "device_id.dat").write_text(
            json.dumps({"id": "device-abc"}), encoding="utf-8"
        )

        mock_sentry, mock_posthog = _make_sdk_mocks()

        with patch.object(t, "_get_app_root", return_value=tmp_path), \
             patch.dict(sys.modules, {"sentry_sdk": mock_sentry, "posthog": mock_posthog}):
            t.init("phc_testkey", "https://sentry.test/dsn", "9.9.9")

        assert t._initialized is True
        assert t._device_id == "device-abc"
        assert t._app_version == "9.9.9"


# ===========================================================================
# TestCapture
# ===========================================================================

class TestCapture:

    def test_capture_before_init(self):
        """capture() sebelum init harus menjadi no-op — tidak crash, tidak memanggil posthog."""
        mock_posthog = MagicMock()

        with patch.dict(sys.modules, {"posthog": mock_posthog}):
            # _initialized masih False — tidak boleh ada side effect
            t.capture("some_event", {"key": "value"})

        mock_posthog.capture.assert_not_called()

    def test_capture_after_init(self, tmp_path):
        """capture() setelah init harus memanggil posthog.capture dengan event yang benar."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        (config_dir / "device_id.dat").write_text(
            json.dumps({"id": "dev-xyz"}), encoding="utf-8"
        )

        mock_sentry, mock_posthog = _make_sdk_mocks()

        with patch.object(t, "_get_app_root", return_value=tmp_path), \
             patch.dict(sys.modules, {"sentry_sdk": mock_sentry, "posthog": mock_posthog}):
            t.init("phc_testkey", "https://sentry.test/dsn", "1.2.3")
            t.capture("app_launched", {"platform": "windows"})

        # posthog.capture harus dipanggil dengan event dan distinct_id yang tepat
        mock_posthog.capture.assert_called_once()
        call_kwargs = mock_posthog.capture.call_args
        # Argumen posisional pertama adalah event name (SDK v7+)
        assert call_kwargs.args[0] == "app_launched"
        assert call_kwargs.kwargs["distinct_id"] == "dev-xyz"
        assert call_kwargs.kwargs["properties"]["platform"] == "windows"
        assert call_kwargs.kwargs["properties"]["app"] == "vocalive"
        assert call_kwargs.kwargs["properties"]["version"] == "1.2.3"


# ===========================================================================
# TestClose
# ===========================================================================

class TestClose:

    def test_close_before_init(self):
        """close() sebelum init harus menjadi no-op — tidak crash, tidak memanggil SDK apapun."""
        mock_sentry, mock_posthog = _make_sdk_mocks()

        with patch.dict(sys.modules, {"sentry_sdk": mock_sentry, "posthog": mock_posthog}):
            # _initialized masih False
            t.close()  # tidak boleh raise exception apapun

        mock_posthog.shutdown.assert_not_called()
        mock_sentry.flush.assert_not_called()
