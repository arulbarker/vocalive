"""
Tests untuk modules_client/updater.py

Covers:
- _parse_version()
- check_for_update()
"""

from unittest.mock import MagicMock, patch

import pytest

pytestmark = pytest.mark.unit

# ---------------------------------------------------------------------------
# PyQt6 guard — updater imports QThread at module level; mock it before import
# ---------------------------------------------------------------------------
import sys
from unittest.mock import MagicMock

# Stub PyQt6 so the module can be imported in a headless test environment
_qt_mock = MagicMock()
_qt_mock.QtCore.QThread = object  # use plain object as base class stub
for _mod in (
    "PyQt6",
    "PyQt6.QtCore",
    "PyQt6.QtWidgets",
    "PyQt6.QtGui",
    "PyQt6.QtMultimedia",
):
    if _mod not in sys.modules:
        sys.modules[_mod] = MagicMock()

# Now safe to import
from modules_client.updater import CURRENT_VERSION, _parse_version, check_for_update

# ===========================================================================
# TestParseVersion
# ===========================================================================

class TestParseVersion:

    def test_basic(self):
        """'1.2.3' harus menghasilkan tuple (1, 2, 3)."""
        assert _parse_version("1.2.3") == (1, 2, 3)

    def test_v_prefix(self):
        """'v2.0.1' (dengan prefix v) harus menghasilkan (2, 0, 1)."""
        assert _parse_version("v2.0.1") == (2, 0, 1)

    def test_invalid(self):
        """String tidak valid harus mengembalikan (0,) tanpa raise."""
        result = _parse_version("not-a-version")
        assert result == (0,)

    def test_comparison(self):
        """Versi tuple bisa dibandingkan secara leksikografik yang benar."""
        assert _parse_version("1.0.13") > _parse_version("1.0.9")
        assert _parse_version("2.0.0") > _parse_version("1.9.9")
        assert _parse_version("1.0.0") == _parse_version("v1.0.0")


# ===========================================================================
# TestCheckForUpdate
# ===========================================================================

class TestCheckForUpdate:

    def test_update_available(self):
        """Jika server mengembalikan versi lebih baru, harus return (True, info)."""
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {
            "latest": "99.0.0",
            "notes": "Big release",
            "url": "https://example.com/VocaLive-v99.0.0.zip",
        }

        with patch("modules_client.updater.requests.get", return_value=mock_resp):
            has_update, info = check_for_update()

        assert has_update is True
        assert info is not None
        assert info["latest"] == "99.0.0"

    def test_no_update(self):
        """Jika server mengembalikan versi lebih lama, harus return (False, None)."""
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {
            "latest": "0.0.1",
            "notes": "",
            "url": "",
        }

        with patch("modules_client.updater.requests.get", return_value=mock_resp):
            has_update, info = check_for_update()

        assert has_update is False
        assert info is None

    def test_network_error(self):
        """Jika terjadi network error, harus return (False, None) tanpa raise."""
        import requests as req_lib

        with patch(
            "modules_client.updater.requests.get",
            side_effect=req_lib.exceptions.ConnectionError("no network"),
        ):
            has_update, info = check_for_update()

        assert has_update is False
        assert info is None
