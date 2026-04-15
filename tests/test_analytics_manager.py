"""
Tests untuk modules_client/analytics_manager.py — LiveAnalyticsManager.
"""

import csv
import pytest
from pathlib import Path

from modules_client.analytics_manager import LiveAnalyticsManager

pytestmark = pytest.mark.integration


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def make_manager(tmp_analytics_dir):
    """Buat instance LiveAnalyticsManager dengan direktori temp."""
    return LiveAnalyticsManager(data_dir=tmp_analytics_dir)


# ---------------------------------------------------------------------------
# TestKeywordExtraction (5 tests)
# ---------------------------------------------------------------------------

class TestKeywordExtraction:
    """Unit tests untuk _extract_keywords — tidak butuh session aktif."""

    def test_product_keywords(self, tmp_analytics_dir):
        mgr = make_manager(tmp_analytics_dir)
        keywords = mgr._extract_keywords("ada hijab gamis warna hitam?")
        assert "hijab" in keywords
        assert "gamis" in keywords
        assert "hitam" in keywords

    def test_price_mention(self, tmp_analytics_dir):
        mgr = make_manager(tmp_analytics_dir)
        keywords = mgr._extract_keywords("harganya berapa? 150rb aja ya")
        assert "_price_mention" in keywords

    def test_size_mention(self, tmp_analytics_dir):
        mgr = make_manager(tmp_analytics_dir)
        keywords = mgr._extract_keywords("ada size 38 tidak?")
        assert "size_38" in keywords

    def test_no_stopwords(self, tmp_analytics_dir):
        mgr = make_manager(tmp_analytics_dir)
        # Stopwords like 'yang', 'dan', 'atau', 'ini', 'itu' must NOT appear
        stopwords = {"yang", "dan", "atau", "ini", "itu"}
        keywords = mgr._extract_keywords("yang dan atau ini itu")
        extracted_set = set(keywords)
        overlap = extracted_set & stopwords
        assert not overlap, f"Stopwords ditemukan di keywords: {overlap}"

    def test_empty_message(self, tmp_analytics_dir):
        mgr = make_manager(tmp_analytics_dir)
        keywords = mgr._extract_keywords("")
        assert keywords == []


# ---------------------------------------------------------------------------
# TestSessionLifecycle (5 tests)
# ---------------------------------------------------------------------------

class TestSessionLifecycle:
    """Tests untuk siklus hidup session (start → track → end)."""

    def test_start_session(self, tmp_analytics_dir):
        mgr = make_manager(tmp_analytics_dir)
        session_id = mgr.start_session(platform="tiktok")
        assert session_id.startswith("tiktok_")
        stats = mgr.get_current_stats()
        assert stats["is_active"] is True
        assert stats["platform"] == "tiktok"

    def test_end_session(self, tmp_analytics_dir):
        mgr = make_manager(tmp_analytics_dir)
        mgr.start_session(platform="tiktok")
        result = mgr.end_session()
        assert result is True
        stats = mgr.get_current_stats()
        assert stats["is_active"] is False

    def test_end_inactive_session_returns_false(self, tmp_analytics_dir):
        mgr = make_manager(tmp_analytics_dir)
        # Tidak ada session aktif — harus return False
        result = mgr.end_session()
        assert result is False

    def test_track_comment(self, tmp_analytics_dir):
        mgr = make_manager(tmp_analytics_dir)
        mgr.start_session(platform="tiktok")
        mgr.track_comment("user_budi", "ada hijab warna putih?", replied=True)
        stats = mgr.get_current_stats()
        assert stats["total_comments"] == 1
        assert stats["total_comments_replied"] == 1
        assert stats["unique_viewers"] == 1

    def test_track_multiple_viewers(self, tmp_analytics_dir):
        mgr = make_manager(tmp_analytics_dir)
        mgr.start_session(platform="tiktok")
        mgr.track_comment("user_ani", "harga gamis berapa?")
        mgr.track_comment("user_budi", "ada diskon?")
        mgr.track_comment("user_ani", "mau order dong")
        stats = mgr.get_current_stats()
        assert stats["total_comments"] == 3
        assert stats["unique_viewers"] == 2


# ---------------------------------------------------------------------------
# TestTopViewers (1 test)
# ---------------------------------------------------------------------------

class TestTopViewers:
    """Test pengurutan top viewers."""

    def test_sort_by_comments(self, tmp_analytics_dir):
        mgr = make_manager(tmp_analytics_dir)
        mgr.start_session(platform="tiktok")

        # user_a: 3 komentar, user_b: 1 komentar
        for _ in range(3):
            mgr.track_comment("user_a", "stok masih ada?")
        mgr.track_comment("user_b", "size xl ada?")

        top = mgr.get_top_viewers(limit=10, sort_by="total_comments")
        assert len(top) == 2
        assert top[0]["username"] == "user_a"
        assert top[0]["total_comments"] == 3
        assert top[1]["username"] == "user_b"


# ---------------------------------------------------------------------------
# TestExportCSV (2 tests)
# ---------------------------------------------------------------------------

class TestExportCSV:
    """Tests untuk export_to_csv."""

    def test_export_current_session(self, tmp_analytics_dir):
        mgr = make_manager(tmp_analytics_dir)
        mgr.start_session(platform="tiktok")
        mgr.track_comment("user_siti", "gamis ready?", replied=True)

        export_path, message = mgr.export_to_csv()

        assert export_path is not None, f"Export gagal: {message}"
        assert message == "Export successful"
        csv_file = Path(export_path)
        assert csv_file.exists()

        # Verifikasi isi CSV mengandung session info
        content = csv_file.read_text(encoding="utf-8")
        assert "tiktok" in content.lower()

    def test_export_nonexistent_session(self, tmp_analytics_dir):
        mgr = make_manager(tmp_analytics_dir)
        mgr.start_session(platform="tiktok")
        mgr.end_session()  # simpan ke history dulu

        # Session ID yang tidak ada
        path, message = mgr.export_to_csv(session_id="nonexistent_session_id_xyz")
        assert path is None
        assert "not found" in message.lower()


# ---------------------------------------------------------------------------
# test_track_gift
# ---------------------------------------------------------------------------

def test_track_gift(tmp_analytics_dir):
    """Gift dari viewer harus terakumulasi di stats."""
    mgr = make_manager(tmp_analytics_dir)
    mgr.start_session(platform="tiktok")
    mgr.track_gift("user_rahman", "Rose", gift_value=5000)
    mgr.track_gift("user_rahman", "Galaxy", gift_value=10000)
    stats = mgr.get_current_stats()
    assert stats["total_gifts_value"] == 15000

    # Verifikasi data viewer juga ter-update
    top = mgr.get_top_viewers(limit=5, sort_by="gifts_value")
    assert top[0]["username"] == "user_rahman"
    assert top[0]["gifts_sent"] == 2
    assert top[0]["gifts_value"] == 15000


# ---------------------------------------------------------------------------
# test_track_viewer_count_peak
# ---------------------------------------------------------------------------

def test_track_viewer_count_peak(tmp_analytics_dir):
    """track_viewer_count harus update peak_viewers hanya jika count lebih tinggi."""
    mgr = make_manager(tmp_analytics_dir)
    mgr.start_session(platform="tiktok")

    mgr.track_viewer_count(100)
    assert mgr.get_current_stats()["peak_viewers"] == 100

    mgr.track_viewer_count(250)
    assert mgr.get_current_stats()["peak_viewers"] == 250

    # Count lebih rendah — peak tidak berubah
    mgr.track_viewer_count(80)
    assert mgr.get_current_stats()["peak_viewers"] == 250
