"""UI widget tests untuk LicenseDialog menggunakan pytest-qt.

Fokus: critical auth flow — email validation, button states, initial UI state.
Tidak test network call sebenarnya (LoginWorker di-mock).
"""

from unittest.mock import MagicMock, patch

import pytest
from PyQt6.QtCore import Qt

pytest.importorskip("pytestqt")


@pytest.fixture
def dialog(qtbot):
    """Instantiate LicenseDialog dengan LicenseManager di-mock."""
    with patch("ui.license_dialog.LicenseManager") as MockLM:
        MockLM.return_value = MagicMock()
        from ui.license_dialog import LicenseDialog

        d = LicenseDialog()
        qtbot.addWidget(d)
        yield d


class TestInstantiation:
    """Smoke tests."""

    def test_dialog_instantiates(self, dialog):
        assert dialog is not None

    def test_window_title_set(self, dialog):
        assert "VocaLive" in dialog.windowTitle()
        assert "Lisensi" in dialog.windowTitle() or "License" in dialog.windowTitle()

    def test_dialog_is_modal(self, dialog):
        assert dialog.isModal() is True

    def test_fixed_size(self, dialog):
        assert dialog.minimumSize() == dialog.maximumSize()


class TestRequiredWidgets:
    """Verifikasi widget UI yang critical harus ada."""

    def test_email_input_exists(self, dialog):
        assert hasattr(dialog, "email_input")
        assert dialog.email_input is not None

    def test_login_button_exists(self, dialog):
        assert hasattr(dialog, "btn_login")
        assert dialog.btn_login.text() == "Login"

    def test_cancel_button_exists(self, dialog):
        assert hasattr(dialog, "btn_cancel")
        assert dialog.btn_cancel.text() == "Batal"

    def test_login_button_is_default(self, dialog):
        assert dialog.btn_login.isDefault()

    def test_cancel_button_not_autodefault(self, dialog):
        """Cancel tidak boleh autoDefault — mencegah Enter trigger Cancel."""
        assert dialog.btn_cancel.autoDefault() is False


class TestInitialState:
    """State awal dialog sebelum user interaksi."""

    def test_email_input_empty(self, dialog):
        assert dialog.email_input.text() == ""

    def test_email_input_has_placeholder(self, dialog):
        assert dialog.email_input.placeholderText() != ""

    def test_progress_frame_hidden(self, dialog):
        assert dialog.progress_frame.isHidden() is True

    def test_status_frame_hidden(self, dialog):
        assert dialog.status_frame.isHidden() is True

    def test_login_button_enabled(self, dialog):
        assert dialog.btn_login.isEnabled()

    def test_email_input_enabled(self, dialog):
        assert dialog.email_input.isEnabled()


class TestEmailValidation:
    """Critical auth flow: validasi email sebelum dikirim."""

    def test_empty_email_shows_error(self, dialog, qtbot):
        dialog.email_input.setText("")

        dialog._start_login()

        assert dialog.status_frame.isHidden() is False
        assert "valid" in dialog.status_text.toPlainText().lower()

    def test_email_without_at_shows_error(self, dialog, qtbot):
        dialog.email_input.setText("invalidEmail")

        dialog._start_login()

        assert dialog.status_frame.isHidden() is False
        assert "valid" in dialog.status_text.toPlainText().lower()

    def test_email_with_only_whitespace_rejected(self, dialog, qtbot):
        dialog.email_input.setText("   ")

        dialog._start_login()

        assert dialog.status_frame.isHidden() is False
        assert dialog.email_input.isEnabled()

    def test_invalid_email_does_not_disable_input(self, dialog, qtbot):
        """Setelah error, user harus bisa edit email lagi."""
        dialog.email_input.setText("no-at-sign")

        dialog._start_login()

        assert dialog.email_input.isEnabled()
        assert dialog.btn_login.isEnabled()


class TestLoginFlow:
    """Flow login dengan email valid → trigger worker."""

    def test_valid_email_starts_worker(self, dialog, qtbot):
        """Email valid → LoginWorker dibuat dan dimulai."""
        dialog.email_input.setText("test@example.com")

        with patch("ui.license_dialog.LoginWorker") as MockWorker:
            worker_instance = MagicMock()
            MockWorker.return_value = worker_instance

            dialog._start_login()

            MockWorker.assert_called_once()
            worker_instance.start.assert_called_once()

    def test_valid_email_disables_input_during_login(self, dialog):
        dialog.email_input.setText("test@example.com")

        with patch("ui.license_dialog.LoginWorker"):
            dialog._start_login()

        assert dialog.email_input.isEnabled() is False
        assert dialog.btn_login.isEnabled() is False

    def test_valid_email_shows_progress(self, dialog):
        dialog.email_input.setText("test@example.com")

        with patch("ui.license_dialog.LoginWorker"):
            dialog._start_login()

        assert dialog.progress_frame.isHidden() is False

    def test_entered_email_stored(self, dialog):
        """_entered_email harus tersimpan untuk return value dari show_license_dialog."""
        dialog.email_input.setText("  user@domain.com  ")

        with patch("ui.license_dialog.LoginWorker"):
            dialog._start_login()

        assert dialog._entered_email == "user@domain.com"  # stripped


class TestKeyboardInteraction:
    """Enter key behavior — must trigger login, not close dialog."""

    def test_enter_key_triggers_login(self, dialog, qtbot):
        dialog.email_input.setText("test@example.com")

        with patch("ui.license_dialog.LoginWorker") as MockWorker:
            worker_instance = MagicMock()
            MockWorker.return_value = worker_instance

            qtbot.keyClick(dialog, Qt.Key.Key_Return)

            MockWorker.assert_called_once()

    def test_enter_key_ignored_when_login_disabled(self, dialog, qtbot):
        """Kalau btn_login sudah disabled (sedang login), Enter tidak trigger lagi."""
        dialog.btn_login.setEnabled(False)

        with patch("ui.license_dialog.LoginWorker") as MockWorker:
            qtbot.keyClick(dialog, Qt.Key.Key_Return)

            MockWorker.assert_not_called()
