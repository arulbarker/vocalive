"""
Tests untuk modules_client/greeting_ai_generator.py

Covers:
- clean_greeting_text()
- _parse_greeting_response()
- generate_greetings_with_ai()
"""

import pytest
from unittest.mock import patch, MagicMock

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Helpers — import target module
# ---------------------------------------------------------------------------

from modules_client.greeting_ai_generator import (
    clean_greeting_text,
    _parse_greeting_response,
    generate_greetings_with_ai,
    FALLBACK_GREETINGS,
)


# ===========================================================================
# TestCleanGreetingText
# ===========================================================================

class TestCleanGreetingText:

    def test_basic_clean(self):
        """Plain text tanpa simbol dikembalikan utuh (whitespace dinormalkan)."""
        assert clean_greeting_text("Halo semuanya") == "Halo semuanya"

    def test_punctuation_stripped(self):
        """Tanda baca harus dihapus semua."""
        result = clean_greeting_text("Halo, semuanya! Selamat datang.")
        assert "," not in result
        assert "!" not in result
        assert "." not in result
        assert "Halo" in result
        assert "semuanya" in result

    def test_markdown_bold_stripped(self):
        """**bold** harus menghasilkan teks tanpa bintang."""
        result = clean_greeting_text("**Selamat** datang!")
        assert "*" not in result
        assert "Selamat" in result
        assert "datang" in result

    def test_whitespace_collapse(self):
        """Spasi ganda / tab harus diciutkan menjadi satu spasi."""
        result = clean_greeting_text("Halo   semuanya\t\tguy")
        assert "  " not in result
        assert result == "Halo semuanya guy"

    def test_empty_string(self):
        """String kosong harus mengembalikan string kosong."""
        assert clean_greeting_text("") == ""

    def test_only_symbols(self):
        """String berisi hanya simbol harus menghasilkan string kosong."""
        result = clean_greeting_text("!@#$%^&*()")
        assert result == ""


# ===========================================================================
# TestParseGreetingResponse
# ===========================================================================

class TestParseGreetingResponse:

    def test_json_array_10_items(self):
        """JSON array valid dengan 10 item harus mengembalikan 10 item."""
        items = [f"Sapaan ke {i} untuk live streaming kita" for i in range(10)]
        import json
        raw = json.dumps(items)
        result = _parse_greeting_response(raw)
        assert len(result) == 10

    def test_json_with_code_fence(self):
        """JSON array dibungkus ```code fence``` harus di-parse dengan benar."""
        import json
        items = [f"Halo ini sapaan nomor {i} untuk semua penonton" for i in range(10)]
        raw = "```json\n" + json.dumps(items) + "\n```"
        result = _parse_greeting_response(raw)
        assert len(result) == 10

    def test_numbered_lines_5_items(self):
        """Fallback numbered lines dengan 5 item harus mengembalikan 5 item."""
        raw = (
            "1. Halo semuanya selamat datang di live kita\n"
            "2. Hai guys makasih udah mampir ke sini\n"
            "3. Selamat datang di live streaming kita hari ini\n"
            "4. Halo teman teman senang banget ada kalian di sini\n"
            "5. Hai hai welcome di live kita semuanya"
        )
        result = _parse_greeting_response(raw)
        assert len(result) == 5

    def test_strips_quotes(self):
        """Tanda kutip di awal/akhir baris harus dihapus."""
        raw = (
            '"Halo semuanya selamat datang di sini"\n'
            '"Hai guys makasih udah join live kita"\n'
            '"Selamat datang dan selamat menyaksikan"\n'
            '"Halo teman teman senang kalian hadir"\n'
            '"Welcome semua penonton setia kita disini"'
        )
        result = _parse_greeting_response(raw)
        # Tidak ada tanda kutip tersisa di item manapun
        for item in result:
            assert '"' not in item
            assert "'" not in item

    def test_too_few_returns_empty(self):
        """Kurang dari 5 item setelah parse harus mengembalikan list kosong."""
        raw = (
            "1. Halo\n"
            "2. Hai semuanya"
        )
        result = _parse_greeting_response(raw)
        assert result == []

    def test_filters_short_lines(self):
        """Baris yang setelah clean_greeting_text panjangnya <= 5 harus dibuang."""
        raw = (
            "1. Hi\n"                                          # terlalu pendek
            "2. Halo semuanya selamat datang di live kita\n"
            "3. Hai guys makasih udah mampir ke sini\n"
            "4. Selamat datang di live streaming kita hari ini\n"
            "5. Halo teman teman senang banget ada kalian di sini\n"
            "6. Hai hai welcome di live kita semuanya ya"
        )
        result = _parse_greeting_response(raw)
        # Semua item yang lolos harus panjang > 5 chars
        for item in result:
            assert len(item) > 5


# ===========================================================================
# TestGenerateGreetingsWithAI
# ===========================================================================

class TestGenerateGreetingsWithAI:

    def test_no_api_key_returns_fallback(self):
        """Jika tidak ada GEMINI_API_KEY, harus mengembalikan FALLBACK_GREETINGS."""
        with patch(
            "modules_client.greeting_ai_generator.config_manager"
        ) as mock_cfg:
            mock_cfg.get.return_value = {}  # api_keys kosong
            result = generate_greetings_with_ai(retry_on_fail=False)

        assert result == FALLBACK_GREETINGS
        assert len(result) == 10
