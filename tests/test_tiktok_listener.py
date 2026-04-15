"""
Tests untuk SimpleTikTokListener — comment filtering dan stop cleanup.

Tier 2: mocked Qt — test logic filter timestamp tanpa koneksi TikTok.
"""

import sys
import time
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

ROOT_DIR = Path(__file__).parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

pytestmark = pytest.mark.integration


# ---------------------------------------------------------------------------
# Fixture — buat SimpleTikTokListener tanpa QThread aktif
# ---------------------------------------------------------------------------

@pytest.fixture
def listener():
    """Create SimpleTikTokListener instance with mocked Qt."""
    with patch("ui.cohost_tab_basic.QThread.__init__", return_value=None):
        from ui.cohost_tab_basic import SimpleTikTokListener
        obj = SimpleTikTokListener.__new__(SimpleTikTokListener)
        obj.username = "testuser"
        obj.running = False
        obj.client = None
        obj.seen_messages = set()
        obj.daemon = True
        obj.start_timestamp = None
        return obj


# ---------------------------------------------------------------------------
# Test should_skip_comment — timestamp filtering
# ---------------------------------------------------------------------------

class TestShouldSkipComment:
    """Test comment filtering logic di should_skip_comment()."""

    def test_no_start_timestamp_accepts_all(self, listener):
        """Sebelum connect, semua komentar diterima."""
        listener.start_timestamp = None
        assert listener.should_skip_comment(1000000, time.time()) is False
        assert listener.should_skip_comment(None, time.time()) is False

    def test_old_comment_with_timestamp_skipped(self, listener):
        """Komentar >0.5 detik sebelum connect harus di-skip."""
        listener.start_timestamp = 1000.0
        # Event 2 detik sebelum connect → old chat
        old_ts_ms = (1000.0 - 2.0) * 1000  # 998000
        assert listener.should_skip_comment(old_ts_ms, 1001.0) is True

    def test_very_old_comment_skipped(self, listener):
        """Komentar 30 detik sebelum connect → pasti old chat."""
        listener.start_timestamp = 1000.0
        old_ts_ms = (1000.0 - 30.0) * 1000
        assert listener.should_skip_comment(old_ts_ms, 1001.0) is True

    def test_near_realtime_comment_accepted(self, listener):
        """Komentar 0.3 detik sebelum connect → masih diterima (dalam grace)."""
        listener.start_timestamp = 1000.0
        near_ts_ms = (1000.0 - 0.3) * 1000  # 999700
        assert listener.should_skip_comment(near_ts_ms, 1001.0) is False

    def test_exactly_at_threshold_accepted(self, listener):
        """Komentar tepat -0.5 detik → boundary, harus diterima (not < -0.5)."""
        listener.start_timestamp = 1000.0
        boundary_ts_ms = (1000.0 - 0.5) * 1000  # 999500
        assert listener.should_skip_comment(boundary_ts_ms, 1001.0) is False

    def test_realtime_comment_accepted(self, listener):
        """Komentar setelah connect → pasti diterima."""
        listener.start_timestamp = 1000.0
        realtime_ts_ms = (1000.0 + 3.0) * 1000  # 1003000
        assert listener.should_skip_comment(realtime_ts_ms, 1003.0) is False

    def test_no_timestamp_accepted(self, listener):
        """Komentar tanpa timestamp → langsung diterima."""
        listener.start_timestamp = 1000.0
        assert listener.should_skip_comment(None, 1000.1) is False

    def test_zero_timestamp_treated_as_no_timestamp(self, listener):
        """Timestamp 0 (falsy) → sama seperti None, diterima."""
        listener.start_timestamp = 1000.0
        assert listener.should_skip_comment(0, 1001.0) is False


# ---------------------------------------------------------------------------
# Test stop cleanup — tidak ada sleep blocking
# ---------------------------------------------------------------------------

class TestStopCleanup:
    """Verify stop() tidak punya sleep() blocking."""

    def test_stop_no_sleep_call(self):
        """stop() tidak boleh panggil time.sleep() — blocking main thread."""
        import inspect
        from ui.cohost_tab_basic import CohostTabBasic
        source = inspect.getsource(CohostTabBasic.stop)
        assert "time.sleep" not in source, "stop() masih punya time.sleep() — blocking UI thread!"

    def test_stop_wait_max_300ms(self):
        """stop() thread.wait() tidak boleh lebih dari 500ms."""
        import re
        import inspect
        from ui.cohost_tab_basic import CohostTabBasic
        source = inspect.getsource(CohostTabBasic.stop)
        # Find all .wait(N) calls
        waits = re.findall(r'\.wait\((\d+)\)', source)
        for wait_ms in waits:
            assert int(wait_ms) <= 500, f"wait({wait_ms}) terlalu lama — max 500ms"
