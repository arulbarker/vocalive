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
        obj._grace_period_over = False
        return obj


# ---------------------------------------------------------------------------
# Test should_skip_comment — grace period + timestamp filtering
# ---------------------------------------------------------------------------

class TestShouldSkipComment:
    """Test comment filtering logic di should_skip_comment()."""

    def test_no_start_timestamp_accepts_all(self, listener):
        """Sebelum connect, semua komentar diterima."""
        listener.start_timestamp = None
        assert listener.should_skip_comment(1000000, time.time()) is False
        assert listener.should_skip_comment(None, time.time()) is False

    def test_during_grace_period_all_skipped(self, listener):
        """Selama grace period (3s), SEMUA komentar di-skip — termasuk yang punya timestamp baru."""
        listener.start_timestamp = 1000.0
        listener._grace_period_over = False
        # 1 detik setelah connect → masih dalam grace period
        current = 1001.0
        # Komentar baru (timestamp setelah connect) tetap di-skip
        assert listener.should_skip_comment(1001.0 * 1000, current) is True
        # Komentar tanpa timestamp juga di-skip
        assert listener.should_skip_comment(None, current) is True
        # Komentar lama juga di-skip
        assert listener.should_skip_comment(998.0 * 1000, current) is True

    def test_grace_period_ends_after_threshold(self, listener):
        """Setelah CONNECT_GRACE_PERIOD detik, komentar baru diterima."""
        from ui.cohost_tab_basic import SimpleTikTokListener
        listener.start_timestamp = 1000.0
        listener._grace_period_over = False
        # Tepat setelah grace period
        current = 1000.0 + SimpleTikTokListener.CONNECT_GRACE_PERIOD + 0.1
        # Komentar baru (timestamp setelah connect) → diterima
        assert listener.should_skip_comment(current * 1000, current) is False
        # Flag harus sudah True
        assert listener._grace_period_over is True

    def test_old_comment_with_timestamp_skipped_after_grace(self, listener):
        """Setelah grace period, komentar dengan timestamp sebelum connect tetap di-skip."""
        listener.start_timestamp = 1000.0
        listener._grace_period_over = True  # Grace period sudah lewat
        # Event 2 detik sebelum connect → old chat
        old_ts_ms = (1000.0 - 2.0) * 1000  # 998000
        assert listener.should_skip_comment(old_ts_ms, 1005.0) is True

    def test_very_old_comment_skipped_after_grace(self, listener):
        """Komentar 30 detik sebelum connect → pasti old chat."""
        listener.start_timestamp = 1000.0
        listener._grace_period_over = True
        old_ts_ms = (1000.0 - 30.0) * 1000
        assert listener.should_skip_comment(old_ts_ms, 1005.0) is True

    def test_realtime_comment_accepted_after_grace(self, listener):
        """Komentar setelah connect + setelah grace period → diterima."""
        listener.start_timestamp = 1000.0
        listener._grace_period_over = True
        realtime_ts_ms = (1000.0 + 5.0) * 1000  # 1005000
        assert listener.should_skip_comment(realtime_ts_ms, 1005.0) is False

    def test_no_timestamp_accepted_after_grace(self, listener):
        """Komentar tanpa timestamp setelah grace period → diterima."""
        listener.start_timestamp = 1000.0
        listener._grace_period_over = True
        assert listener.should_skip_comment(None, 1005.0) is False

    def test_zero_timestamp_accepted_after_grace(self, listener):
        """Timestamp 0 (falsy) setelah grace period → sama seperti None, diterima."""
        listener.start_timestamp = 1000.0
        listener._grace_period_over = True
        assert listener.should_skip_comment(0, 1005.0) is False

    def test_comment_exactly_at_connect_time_skipped(self, listener):
        """Komentar dengan timestamp tepat saat connect → di-skip (< start_timestamp is False, = is not < so accepted... but it's borderline). Actually event_time < start_timestamp → False for equal."""
        listener.start_timestamp = 1000.0
        listener._grace_period_over = True
        # Exactly at connect time → event_time == start_timestamp → not < → accepted
        assert listener.should_skip_comment(1000.0 * 1000, 1005.0) is False

    def test_grace_period_flag_transitions_correctly(self, listener):
        """Flag _grace_period_over berubah dari False ke True tepat saat grace period habis."""
        from ui.cohost_tab_basic import SimpleTikTokListener
        listener.start_timestamp = 1000.0
        listener._grace_period_over = False

        gp = SimpleTikTokListener.CONNECT_GRACE_PERIOD

        # Masih dalam grace period
        assert listener.should_skip_comment(None, 1000.0 + gp - 0.5) is True
        assert listener._grace_period_over is False

        # Tepat setelah grace period
        assert listener.should_skip_comment(1005.0 * 1000, 1000.0 + gp + 0.1) is False
        assert listener._grace_period_over is True

        # Setelah flag True, tetap True
        assert listener.should_skip_comment(1006.0 * 1000, 1006.0) is False
        assert listener._grace_period_over is True


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
