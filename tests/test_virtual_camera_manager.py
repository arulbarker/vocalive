"""
Tests untuk modules_client/virtual_camera_manager.py

Covers:
- Playlist management (set_playlist, max 10, reset index)
- Play mode setting (sequential/random, invalid rejected)
- get_next_video() logic (sequential loop, random, empty)
- detect_backend() (OBS, UnityCapture fallback, no backend)
- request_stop / skip_to_next flags
"""

import sys
from unittest.mock import MagicMock, patch

import pytest

pytestmark = pytest.mark.integration

# ---------------------------------------------------------------------------
# PyQt6 guard — mock Qt modules before importing the manager
# ---------------------------------------------------------------------------
for _mod in (
    "PyQt6",
    "PyQt6.QtCore",
    "PyQt6.QtWidgets",
    "PyQt6.QtGui",
    "PyQt6.QtMultimedia",
):
    if _mod not in sys.modules:
        sys.modules[_mod] = MagicMock()


# ---------------------------------------------------------------------------
# Fixture: create VirtualCameraManager without real QThread init
# ---------------------------------------------------------------------------
@pytest.fixture
def manager():
    with patch("modules_client.virtual_camera_manager.QThread.__init__", return_value=None):
        from modules_client.virtual_camera_manager import VirtualCameraManager
        obj = VirtualCameraManager.__new__(VirtualCameraManager)
        obj.playlist = []
        obj.play_mode = "sequential"
        obj.is_playing = False
        obj.current_index = 0
        obj._cam = None
        obj._stop_requested = False
        obj._skip_requested = False
        return obj


# ===========================================================================
# TestPlaylist
# ===========================================================================

class TestPlaylist:

    def test_set_playlist_basic(self, manager):
        """set_playlist menyimpan list path."""
        paths = ["video1.mp4", "video2.mp4", "video3.mp4"]
        manager.set_playlist(paths)
        assert manager.playlist == paths

    def test_set_playlist_max_10(self, manager):
        """set_playlist membatasi max 10 items."""
        paths = [f"video{i}.mp4" for i in range(15)]
        manager.set_playlist(paths)
        assert len(manager.playlist) == 10
        assert manager.playlist == paths[:10]

    def test_set_playlist_resets_index(self, manager):
        """set_playlist selalu reset current_index ke 0."""
        manager.current_index = 5
        manager.set_playlist(["a.mp4", "b.mp4"])
        assert manager.current_index == 0

    def test_set_playlist_empty(self, manager):
        """set_playlist dengan list kosong menghasilkan playlist kosong."""
        manager.set_playlist(["a.mp4"])
        manager.set_playlist([])
        assert manager.playlist == []
        assert manager.current_index == 0

    def test_set_playlist_invalid_type(self, manager):
        """set_playlist dengan non-list tidak mengubah playlist."""
        manager.set_playlist(["a.mp4"])
        manager.set_playlist("not_a_list")
        assert manager.playlist == ["a.mp4"]

    def test_set_playlist_exactly_10(self, manager):
        """set_playlist dengan tepat 10 items diterima semua."""
        paths = [f"video{i}.mp4" for i in range(10)]
        manager.set_playlist(paths)
        assert len(manager.playlist) == 10


# ===========================================================================
# TestPlayMode
# ===========================================================================

class TestPlayMode:

    def test_set_sequential(self, manager):
        """set_play_mode('sequential') diterima."""
        manager.set_play_mode("sequential")
        assert manager.play_mode == "sequential"

    def test_set_random(self, manager):
        """set_play_mode('random') diterima."""
        manager.set_play_mode("random")
        assert manager.play_mode == "random"

    def test_invalid_mode_ignored(self, manager):
        """Mode invalid tidak mengubah play_mode."""
        manager.play_mode = "sequential"
        manager.set_play_mode("shuffle")
        assert manager.play_mode == "sequential"

    def test_empty_mode_ignored(self, manager):
        """String kosong tidak mengubah play_mode."""
        manager.play_mode = "random"
        manager.set_play_mode("")
        assert manager.play_mode == "random"


# ===========================================================================
# TestGetNextVideo
# ===========================================================================

class TestGetNextVideo:

    def test_empty_playlist_returns_none(self, manager):
        """Playlist kosong → None."""
        assert manager.get_next_video() is None

    def test_sequential_returns_in_order(self, manager):
        """Sequential: video dikembalikan berurutan."""
        manager.set_playlist(["a.mp4", "b.mp4", "c.mp4"])
        assert manager.get_next_video() == "a.mp4"
        assert manager.get_next_video() == "b.mp4"
        assert manager.get_next_video() == "c.mp4"

    def test_sequential_loops_back(self, manager):
        """Sequential: setelah habis, kembali ke awal."""
        manager.set_playlist(["a.mp4", "b.mp4"])
        manager.get_next_video()  # a
        manager.get_next_video()  # b
        result = manager.get_next_video()  # kembali ke a
        assert result == "a.mp4"

    def test_sequential_single_video_loops(self, manager):
        """Sequential: satu video terus berulang."""
        manager.set_playlist(["only.mp4"])
        assert manager.get_next_video() == "only.mp4"
        assert manager.get_next_video() == "only.mp4"
        assert manager.get_next_video() == "only.mp4"

    def test_random_returns_from_list(self, manager):
        """Random: video yang dikembalikan ada di playlist."""
        paths = ["a.mp4", "b.mp4", "c.mp4"]
        manager.set_playlist(paths)
        manager.set_play_mode("random")
        for _ in range(20):
            result = manager.get_next_video()
            assert result in paths

    def test_random_with_single_video(self, manager):
        """Random: satu video selalu dikembalikan."""
        manager.set_playlist(["solo.mp4"])
        manager.set_play_mode("random")
        assert manager.get_next_video() == "solo.mp4"


# ===========================================================================
# TestDetectBackend
# ===========================================================================

class TestDetectBackend:

    def test_obs_detected(self, manager):
        """Jika OBS berhasil, return 'obs'."""
        mock_cam = MagicMock()
        mock_pyvirtualcam = MagicMock()
        mock_pyvirtualcam.Camera.return_value = mock_cam

        with patch("modules_client.virtual_camera_manager.pyvirtualcam", mock_pyvirtualcam):
            result = manager.detect_backend()
        assert result == "obs"
        mock_cam.close.assert_called_once()

    def test_unitycapture_fallback(self, manager):
        """Jika OBS gagal tapi UnityCapture berhasil, return 'unitycapture'."""
        mock_cam = MagicMock()
        mock_pyvirtualcam = MagicMock()

        def side_effect(width, height, fps, backend):
            if backend == "obs":
                raise RuntimeError("OBS not available")
            return mock_cam

        mock_pyvirtualcam.Camera.side_effect = side_effect

        with patch("modules_client.virtual_camera_manager.pyvirtualcam", mock_pyvirtualcam):
            result = manager.detect_backend()
        assert result == "unitycapture"

    def test_no_backend_returns_none(self, manager):
        """Jika semua backend gagal, return None."""
        mock_pyvirtualcam = MagicMock()
        mock_pyvirtualcam.Camera.side_effect = RuntimeError("no backend")

        with patch("modules_client.virtual_camera_manager.pyvirtualcam", mock_pyvirtualcam):
            result = manager.detect_backend()
        assert result is None

    def test_pyvirtualcam_not_installed(self, manager):
        """Jika pyvirtualcam is None, return None."""
        with patch("modules_client.virtual_camera_manager.pyvirtualcam", None):
            result = manager.detect_backend()
        assert result is None


# ===========================================================================
# TestStopCleanup
# ===========================================================================

class TestStopCleanup:

    def test_request_stop_sets_flag(self, manager):
        """request_stop() set _stop_requested = True."""
        assert manager._stop_requested is False
        manager.request_stop()
        assert manager._stop_requested is True

    def test_skip_to_next_sets_flag(self, manager):
        """skip_to_next() set _skip_requested = True."""
        assert manager._skip_requested is False
        manager.skip_to_next()
        assert manager._skip_requested is True

    def test_initial_flags_are_false(self, manager):
        """Flag awal semuanya False."""
        assert manager._stop_requested is False
        assert manager._skip_requested is False
        assert manager.is_playing is False


# ===========================================================================
# TestGetVideoInfo
# ===========================================================================

class TestGetVideoInfo:

    def test_valid_video(self, manager):
        """Video valid mengembalikan (width, height, fps)."""
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.get.side_effect = lambda prop: {
            3: 1920.0,   # CAP_PROP_FRAME_WIDTH
            4: 1080.0,   # CAP_PROP_FRAME_HEIGHT
            5: 30.0,     # CAP_PROP_FPS
        }.get(prop, 0.0)

        mock_cv2 = MagicMock()
        mock_cv2.VideoCapture.return_value = mock_cap
        mock_cv2.CAP_PROP_FRAME_WIDTH = 3
        mock_cv2.CAP_PROP_FRAME_HEIGHT = 4
        mock_cv2.CAP_PROP_FPS = 5

        with patch("modules_client.virtual_camera_manager.cv2", mock_cv2):
            result = manager._get_video_info("test.mp4")
        assert result == (1920, 1080, 30.0)
        mock_cap.release.assert_called_once()

    def test_invalid_video(self, manager):
        """Video yang tidak bisa dibuka mengembalikan None."""
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = False

        mock_cv2 = MagicMock()
        mock_cv2.VideoCapture.return_value = mock_cap

        with patch("modules_client.virtual_camera_manager.cv2", mock_cv2):
            result = manager._get_video_info("nonexistent.mp4")
        assert result is None

    def test_cv2_not_installed(self, manager):
        """cv2 is None → return None."""
        with patch("modules_client.virtual_camera_manager.cv2", None):
            result = manager._get_video_info("test.mp4")
        assert result is None

    def test_zero_dimensions(self, manager):
        """Video dengan dimensi 0 mengembalikan None."""
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.get.return_value = 0.0

        mock_cv2 = MagicMock()
        mock_cv2.VideoCapture.return_value = mock_cap
        mock_cv2.CAP_PROP_FRAME_WIDTH = 3
        mock_cv2.CAP_PROP_FRAME_HEIGHT = 4
        mock_cv2.CAP_PROP_FPS = 5

        with patch("modules_client.virtual_camera_manager.cv2", mock_cv2):
            result = manager._get_video_info("bad.mp4")
        assert result is None
        mock_cap.release.assert_called_once()


# ===========================================================================
# TestConfigPersistence
# ===========================================================================

class TestConfigPersistence:

    def test_save_config(self, manager, tmp_path):
        config_path = tmp_path / "virtual_camera.json"
        manager.set_playlist(["a.mp4", "b.mp4"])
        manager.set_play_mode("random")
        manager.save_config(str(config_path))
        import json
        data = json.loads(config_path.read_text(encoding="utf-8"))
        assert data["playlist"] == ["a.mp4", "b.mp4"]
        assert data["play_mode"] == "random"

    def test_load_config(self, manager, tmp_path):
        config_path = tmp_path / "virtual_camera.json"
        import json
        config_path.write_text(json.dumps({"playlist": ["x.mp4", "y.mp4"], "play_mode": "sequential"}), encoding="utf-8")
        manager.load_config(str(config_path))
        assert manager.playlist == ["x.mp4", "y.mp4"]
        assert manager.play_mode == "sequential"

    def test_load_missing_file(self, manager, tmp_path):
        manager.load_config(str(tmp_path / "nonexistent.json"))
        assert manager.playlist == []
        assert manager.play_mode == "sequential"
