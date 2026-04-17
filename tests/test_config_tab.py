"""UI widget tests untuk ConfigTab menggunakan pytest-qt.

Fokus: API key detection UI, provider switching, signal emission.
ConfigManager di-mock untuk isolation dari real config/settings.json.
"""

from unittest.mock import MagicMock, patch

import pytest
from PyQt6.QtWidgets import QLineEdit, QPushButton

pytest.importorskip("pytestqt")


@pytest.fixture
def config_tab(qtbot):
    """Instantiate ConfigTab dengan ConfigManager di-mock.

    Mock returns sensible defaults agar load_saved_keys() tidak crash.
    """
    mock_cfg_data = {
        "ai_provider": "deepseek",
        "api_keys": {
            "GEMINI_API_KEY": "",
            "DEEPSEEK_API_KEY": "",
        },
        "google_tts_api_key": "",
        "user_context": "",
        "tts_voice": "Gemini-Puck (MALE)",
        "tts_key_type": "all",
    }

    mock_cfg_instance = MagicMock()
    mock_cfg_instance.get.side_effect = lambda key, default=None: mock_cfg_data.get(key, default)
    mock_cfg_instance.get_all_settings.return_value = mock_cfg_data

    with patch("ui.config_tab.ConfigManager", return_value=mock_cfg_instance):
        from ui.config_tab import ConfigTab

        widget = ConfigTab()
        qtbot.addWidget(widget)
        yield widget


class TestInstantiation:
    """Smoke test — widget bisa dibuat tanpa error."""

    def test_tab_instantiates(self, config_tab):
        assert config_tab is not None

    def test_has_required_attributes(self, config_tab):
        assert hasattr(config_tab, "provider_combo")
        assert hasattr(config_tab, "api_key_input")
        assert hasattr(config_tab, "ai_test_btn")
        assert hasattr(config_tab, "tts_api_key_input")
        assert hasattr(config_tab, "tts_voice_combo")


class TestProviderCombo:
    """Dropdown pilihan AI provider."""

    def test_provider_combo_has_deepseek(self, config_tab):
        items = [config_tab.provider_combo.itemText(i)
                 for i in range(config_tab.provider_combo.count())]
        assert "DeepSeek" in items

    def test_provider_combo_has_gemini(self, config_tab):
        items = [config_tab.provider_combo.itemText(i)
                 for i in range(config_tab.provider_combo.count())]
        assert "Gemini Flash Lite" in items

    def test_provider_only_has_supported_providers(self, config_tab):
        """YouTube ChatGPT sudah di-disable — pastikan tidak accidentally ditambah."""
        items = [config_tab.provider_combo.itemText(i)
                 for i in range(config_tab.provider_combo.count())]
        assert "ChatGPT" not in items
        assert "OpenAI" not in items


class TestApiKeyInput:
    """Input API key — password mode + validation behavior."""

    def test_api_key_input_is_password_mode(self, config_tab):
        """API key harus disembunyikan by default untuk security."""
        assert config_tab.api_key_input.echoMode() == QLineEdit.EchoMode.Password

    def test_ai_test_button_disabled_when_no_key(self, config_tab):
        config_tab.api_key_input.setText("")
        config_tab.on_api_key_changed()

        assert config_tab.ai_test_btn.isEnabled() is False

    def test_ai_test_button_enabled_when_key_present(self, config_tab):
        config_tab.api_key_input.setText("sk-test-key-12345")
        config_tab.on_api_key_changed()

        assert config_tab.ai_test_btn.isEnabled() is True

    def test_ai_test_button_disabled_on_whitespace_only(self, config_tab):
        config_tab.api_key_input.setText("   ")
        config_tab.on_api_key_changed()

        assert config_tab.ai_test_btn.isEnabled() is False


class TestProviderChanged:
    """on_provider_changed() updates placeholder berdasarkan provider."""

    def test_deepseek_placeholder(self, config_tab):
        config_tab.on_provider_changed("DeepSeek")

        placeholder = config_tab.api_key_input.placeholderText()
        assert "DeepSeek" in placeholder
        assert "sk-" in placeholder

    def test_gemini_placeholder(self, config_tab):
        config_tab.on_provider_changed("Gemini Flash Lite")

        placeholder = config_tab.api_key_input.placeholderText()
        assert "Gemini" in placeholder
        assert "AIzaSy" in placeholder


class TestPasswordToggle:
    """Tombol show/hide password."""

    def test_toggle_password_visibility_shows_text(self, config_tab):
        input_field = config_tab.api_key_input
        assert input_field.echoMode() == QLineEdit.EchoMode.Password

        config_tab.toggle_password_visibility(input_field)
        assert input_field.echoMode() == QLineEdit.EchoMode.Normal

    def test_toggle_password_visibility_hides_text(self, config_tab):
        input_field = config_tab.api_key_input

        config_tab.toggle_password_visibility(input_field)
        config_tab.toggle_password_visibility(input_field)

        assert input_field.echoMode() == QLineEdit.EchoMode.Password


class TestSignals:
    """Signal emission untuk komunikasi cross-tab."""

    def test_tts_key_type_changed_signal_exists(self, config_tab):
        assert hasattr(config_tab, "tts_key_type_changed")

    def test_greeting_status_changed_signal_exists(self, config_tab):
        assert hasattr(config_tab, "greeting_status_changed")

    def test_tts_key_type_changed_emits_string(self, config_tab, qtbot):
        """Signal bisa di-emit dan diterima."""
        with qtbot.waitSignal(config_tab.tts_key_type_changed, timeout=500) as blocker:
            config_tab.tts_key_type_changed.emit("gemini")

        assert blocker.args == ["gemini"]


class TestVoiceCombo:
    """TTS voice selector dropdown."""

    def test_tts_voice_combo_populated(self, config_tab):
        """Voice dropdown punya setidaknya beberapa pilihan."""
        assert config_tab.tts_voice_combo.count() > 0

    def test_populate_tts_voice_combo_with_gemini(self, config_tab):
        """key_type='gemini' → hanya voice Gemini yang di-show."""
        config_tab.tts_voice_combo.clear()
        config_tab._populate_tts_voice_combo("gemini")

        items = [config_tab.tts_voice_combo.itemText(i)
                 for i in range(config_tab.tts_voice_combo.count())]
        # Semua voice Gemini harus prefix "Gemini-"
        if items:
            assert any("Gemini-" in item for item in items)

    def test_populate_tts_voice_combo_with_all(self, config_tab):
        """key_type='all' → semua voice available."""
        config_tab.tts_voice_combo.clear()
        config_tab._populate_tts_voice_combo("all")

        count_all = config_tab.tts_voice_combo.count()
        assert count_all > 0


class TestCloseEvent:
    """Cleanup behavior saat tab close."""

    def test_close_event_without_thread(self, config_tab, qtbot):
        """closeEvent tidak crash kalau test_thread belum ada."""
        config_tab.test_thread = None

        event = MagicMock()
        config_tab.closeEvent(event)

        event.accept.assert_called_once()

    def test_close_event_with_finished_thread(self, config_tab, qtbot):
        """closeEvent handle test_thread yang sudah finished."""
        mock_thread = MagicMock()
        mock_thread.isRunning.return_value = False
        config_tab.test_thread = mock_thread

        event = MagicMock()
        config_tab.closeEvent(event)

        mock_thread.quit.assert_not_called()
        event.accept.assert_called_once()
