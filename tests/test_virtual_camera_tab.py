"""UI widget tests untuk VirtualCameraTab menggunakan pytest-qt.

Fokus: regression test setelah hapus tombol Download UnityCapture (v1.0.14)
dan verifikasi behavior driver panel visibility.

i18n di-load dari i18n/id.json agar UI strings sesuai dengan yang dirender user.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from PyQt6.QtWidgets import QPushButton

pytest.importorskip("pytestqt")


@pytest.fixture(autouse=True)
def _i18n_load_id(monkeypatch):
    """Load real id.json translations sebelum setiap test agar t() return string ID."""
    from modules_client import i18n

    i18n_path = Path(__file__).parent.parent / "i18n" / "id.json"
    translations = json.loads(i18n_path.read_text(encoding="utf-8"))
    monkeypatch.setattr(i18n, "_current_lang", "id")
    monkeypatch.setattr(i18n, "_translations", translations)
    monkeypatch.setattr(i18n, "_reference_translations", translations)


@pytest.fixture
def tab(qtbot):
    """Instantiate VirtualCameraTab tanpa manager (manager=None)."""
    from ui.virtual_camera_tab import VirtualCameraTab

    widget = VirtualCameraTab(manager=None)
    qtbot.addWidget(widget)
    return widget


@pytest.fixture
def tab_with_mock_manager(qtbot):
    """Instantiate VirtualCameraTab dengan MagicMock sebagai manager."""
    from ui.virtual_camera_tab import VirtualCameraTab

    mock_manager = MagicMock()
    mock_manager.playlist = []
    mock_manager.detect_backend = MagicMock(return_value=None)
    mock_manager.get_play_mode = MagicMock(return_value="sequential")

    widget = VirtualCameraTab(manager=mock_manager)
    qtbot.addWidget(widget)
    return widget, mock_manager


class TestInstantiation:
    """Smoke tests: widget bisa dibuat tanpa error."""

    def test_tab_instantiates_without_manager(self, qtbot):
        from ui.virtual_camera_tab import VirtualCameraTab

        widget = VirtualCameraTab(manager=None)
        qtbot.addWidget(widget)

        assert widget is not None
        assert widget.manager is None

    def test_tab_instantiates_with_manager(self, qtbot):
        from ui.virtual_camera_tab import VirtualCameraTab

        mock_manager = MagicMock()
        mock_manager.playlist = []
        mock_manager.detect_backend = MagicMock(return_value="obs")
        mock_manager.get_play_mode = MagicMock(return_value="sequential")

        widget = VirtualCameraTab(manager=mock_manager)
        qtbot.addWidget(widget)

        assert widget is not None
        assert widget.manager is mock_manager


class TestDownloadUnityCaptureButtonRemoved:
    """Regression tests untuk perubahan v1.0.14.

    Tombol 'Download UnityCapture' sengaja dihapus karena membingungkan user.
    Kalau nanti ada yang tidak sengaja menambahkannya kembali, test ini akan fail.
    """

    def test_no_download_unitycapture_button(self, tab):
        buttons = tab.findChildren(QPushButton)
        button_texts = [b.text() for b in buttons]

        assert "Download UnityCapture" not in button_texts, (
            "Tombol 'Download UnityCapture' sengaja dihapus di v1.0.14. "
            "Kalau perlu ditambah lagi, update test ini dan CLAUDE.md."
        )

    def test_no_download_related_button(self, tab):
        buttons = tab.findChildren(QPushButton)
        button_texts_lower = [b.text().lower() for b in buttons]

        for text in button_texts_lower:
            assert "download" not in text, (
                f"Tombol dengan teks 'download' ditemukan: {text}. "
                "Tab Virtual Camera tidak perlu tombol download driver."
            )

    def test_open_driver_download_method_removed(self, tab):
        assert not hasattr(tab, "_open_driver_download"), (
            "Method _open_driver_download() sudah dihapus bersama tombol. "
            "Jangan tambahkan kembali."
        )


class TestDriverPanel:
    """Verify behavior driver_panel visibility."""

    def test_driver_panel_exists(self, tab):
        assert hasattr(tab, "driver_panel")

    def test_driver_panel_hidden_without_manager(self, tab):
        assert tab.driver_panel.isVisible() is False

    def test_driver_panel_visible_when_no_backend(self, tab_with_mock_manager):
        from modules_client.i18n import t

        widget, mock_manager = tab_with_mock_manager
        mock_manager.detect_backend.return_value = None

        widget.show()
        widget._detect_backend_on_init()

        assert widget.driver_panel.isVisible() is True
        assert widget.backend_indicator.text() == t("camera.status.none")

    def test_driver_panel_hidden_when_backend_detected(self, tab_with_mock_manager):
        widget, mock_manager = tab_with_mock_manager
        mock_manager.detect_backend.return_value = "obs"

        widget._detect_backend_on_init()

        assert widget.driver_panel.isVisible() is False
        # Backend id adalah nilai teknis, ditampilkan uppercase apa adanya
        assert widget.backend_indicator.text() == "OBS"


class TestRequiredButtons:
    """Verifikasi tombol utama yang harus selalu ada."""

    def test_tambah_video_button_exists(self, tab):
        from modules_client.i18n import t

        buttons = tab.findChildren(QPushButton)
        texts = [b.text() for b in buttons]

        assert t("camera.btn.add_video") in texts, (
            "Tombol 'Tambah Video' harus ada — main CTA untuk tab ini."
        )

    def test_tambah_video_button_is_enabled(self, tab):
        assert tab.btn_add_video.isEnabled()
