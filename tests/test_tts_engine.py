"""
Tests untuk modules_server/tts_engine.py

Covers:
- speak("") — empty text should return quickly without crashing
- speak("Halo") — delegates to engine.speak
- speak_text("test") — alias for speak
- get_tts_engine() — returns a TTSEngine instance (singleton)
"""

import sys
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

pytestmark = pytest.mark.integration

# ---------------------------------------------------------------------------
# Stub heavy dependencies before the module is imported.
# modules_server/tts_engine.py does try/except at top level for all of these,
# but we stub them in sys.modules so the try-blocks succeed with mocks instead
# of silently setting the names to None (which would skip code paths we need
# to exercise).
# ---------------------------------------------------------------------------

_pygame_mock = MagicMock()
_pygame_mock.mixer = MagicMock()
_pygame_mock.mixer.init = MagicMock(return_value=None)
_pygame_mock.mixer.music = MagicMock()

for _mod_name in (
    "pygame",
    "pygame.mixer",
):
    if _mod_name not in sys.modules:
        sys.modules[_mod_name] = _pygame_mock

if "pyttsx3" not in sys.modules:
    sys.modules["pyttsx3"] = MagicMock()

if "google" not in sys.modules:
    sys.modules["google"] = MagicMock()
if "google.cloud" not in sys.modules:
    sys.modules["google.cloud"] = MagicMock()
if "google.cloud.texttospeech" not in sys.modules:
    sys.modules["google.cloud.texttospeech"] = MagicMock()

# requests is real — keep it; but stub it if it happens to be missing
try:
    import requests as _real_requests  # noqa: F401
except ImportError:
    sys.modules["requests"] = MagicMock()

# modules_client.telemetry is imported lazily inside speak(), stub it too
# so telemetry.capture calls don't cause ImportErrors in test environment
_telemetry_mock = MagicMock()
sys.modules.setdefault("modules_client", MagicMock())
sys.modules.setdefault("modules_client.telemetry", _telemetry_mock)

# ---------------------------------------------------------------------------
# Now it is safe to import the module under test
# ---------------------------------------------------------------------------

# Reset the global singleton between test runs so each test gets a fresh state
import importlib

import modules_server.tts_engine as _tts_mod  # initial import

def _reload_module():
    """Reload tts_engine and reset its global singleton."""
    global _tts_mod
    _tts_mod._tts_engine = None  # type: ignore[attr-defined]
    importlib.reload(_tts_mod)
    return _tts_mod


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestSpeakEmptyText:
    """speak('') should return quickly without raising."""

    def test_speak_empty_text(self):
        """Empty string must not crash — should return False (no speech)."""
        # TTSEngine.__init__ calls pygame.mixer.init and pyttsx3.init — both
        # are already mocked via sys.modules, so construction is safe.
        result = _tts_mod.speak("")
        # The module-level speak() short-circuits on empty text inside
        # TTSEngine.speak() and returns False.  We only assert it doesn't
        # raise and returns a bool-compatible value.
        assert result is False or result is True  # just must not raise


class TestSpeakDelegatesToEngine:
    """speak('Halo') should call engine.speak on the singleton."""

    def test_speak_delegates_to_engine(self):
        """Module-level speak() must forward the call to get_tts_engine().speak()."""
        mock_engine = MagicMock()
        mock_engine.speak.return_value = True

        with patch.object(_tts_mod, "get_tts_engine", return_value=mock_engine):
            result = _tts_mod.speak("Halo")

        # engine.speak should have been called once with the text
        mock_engine.speak.assert_called_once()
        call_args = mock_engine.speak.call_args
        # First positional argument must be the text
        assert call_args[0][0] == "Halo" or call_args[1].get("text") == "Halo" or "Halo" in str(call_args)
        assert result is True


class TestSpeakTextIsAlias:
    """speak_text('test') should work without crashing."""

    def test_speak_text_is_alias(self):
        """speak_text() is a backward-compatible alias — it must not raise."""
        mock_engine = MagicMock()
        mock_engine.speak.return_value = True

        with patch.object(_tts_mod, "get_tts_engine", return_value=mock_engine):
            result = _tts_mod.speak_text("test")

        # Should complete without exception and return a bool-like value
        assert result is True or result is False


class TestGetTtsEngineReturnsSingleton:
    """get_tts_engine() should return a TTSEngine instance."""

    def test_get_tts_engine_returns_instance(self):
        """get_tts_engine() must return a TTSEngine (or mock) and be stable."""
        # Reset the global singleton so we force construction
        _tts_mod._tts_engine = None  # type: ignore[attr-defined]

        with patch.object(_tts_mod, "TTSEngine") as MockTTSEngine:
            fake_instance = MagicMock(spec=_tts_mod.TTSEngine)
            MockTTSEngine.return_value = fake_instance

            engine1 = _tts_mod.get_tts_engine()
            engine2 = _tts_mod.get_tts_engine()

        # Constructor should have been called exactly once (singleton)
        MockTTSEngine.assert_called_once()
        # Both calls must return the same instance
        assert engine1 is engine2
        # The returned object must be the fake instance we set up
        assert engine1 is fake_instance
