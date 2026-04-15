# Virtual Camera Tab — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Menambahkan tab Virtual Camera yang memutar playlist video sebagai virtual webcam device untuk TikTok Live Studio.

**Architecture:** `VirtualCameraManager` (QThread) membaca frame video via OpenCV dan mengirim ke virtual camera device via `pyvirtualcam`. UI tab mengelola playlist dan kontrol playback. Backend auto-detect OBS Virtual Camera (primary) → UnityCapture (fallback) → dialog install driver.

**Tech Stack:** PyQt6, pyvirtualcam, opencv-python-headless, OpenCV VideoCapture

---

### Task 1: Tambah Dependencies

**Files:**
- Modify: `requirements.txt` (akhir file)

- [ ] **Step 1: Tambah pyvirtualcam dan opencv-python-headless ke requirements.txt**

Tambahkan di akhir `requirements.txt`:

```
# Virtual Camera
pyvirtualcam>=0.15.0
opencv-python-headless>=4.8.0
```

- [ ] **Step 2: Install dependencies**

Run: `pip install pyvirtualcam opencv-python-headless`

- [ ] **Step 3: Verify import works**

Run: `python -c "import pyvirtualcam; import cv2; print('OK:', pyvirtualcam.__version__, cv2.__version__)"`
Expected: OK dengan versi library

- [ ] **Step 4: Commit**

```bash
git add requirements.txt
git commit -m "chore: tambah pyvirtualcam dan opencv-python-headless untuk virtual camera"
```

---

### Task 2: VirtualCameraManager — Core Logic

**Files:**
- Create: `modules_client/virtual_camera_manager.py`
- Create: `tests/test_virtual_camera_manager.py`

- [ ] **Step 1: Write failing tests untuk VirtualCameraManager**

Create `tests/test_virtual_camera_manager.py`:

```python
"""
Tests untuk VirtualCameraManager — playlist logic, mode switching, backend detection.
Tier 2: mocked pyvirtualcam & cv2 — test logic tanpa hardware.
"""

import sys
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, PropertyMock

ROOT_DIR = Path(__file__).parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

pytestmark = pytest.mark.integration


@pytest.fixture
def manager():
    """Create VirtualCameraManager with mocked Qt."""
    with patch("modules_client.virtual_camera_manager.QThread.__init__", return_value=None):
        from modules_client.virtual_camera_manager import VirtualCameraManager
        obj = VirtualCameraManager.__new__(VirtualCameraManager)
        obj.playlist = []
        obj.play_mode = "sequential"
        obj.is_playing = False
        obj.current_index = 0
        obj._cam = None
        obj._stop_requested = False
        return obj


class TestPlaylist:
    """Test playlist management."""

    def test_set_playlist(self, manager):
        manager.set_playlist(["a.mp4", "b.mp4", "c.mp4"])
        assert manager.playlist == ["a.mp4", "b.mp4", "c.mp4"]
        assert manager.current_index == 0

    def test_set_playlist_resets_index(self, manager):
        manager.current_index = 5
        manager.set_playlist(["x.mp4"])
        assert manager.current_index == 0

    def test_set_playlist_max_10(self, manager):
        videos = [f"v{i}.mp4" for i in range(15)]
        manager.set_playlist(videos)
        assert len(manager.playlist) == 10

    def test_empty_playlist(self, manager):
        manager.set_playlist([])
        assert manager.playlist == []


class TestPlayMode:
    """Test play mode switching."""

    def test_set_sequential(self, manager):
        manager.set_play_mode("sequential")
        assert manager.play_mode == "sequential"

    def test_set_random(self, manager):
        manager.set_play_mode("random")
        assert manager.play_mode == "random"

    def test_invalid_mode_ignored(self, manager):
        manager.set_play_mode("sequential")
        manager.set_play_mode("invalid")
        assert manager.play_mode == "sequential"


class TestGetNextVideo:
    """Test next video selection logic."""

    def test_sequential_order(self, manager):
        manager.set_playlist(["a.mp4", "b.mp4", "c.mp4"])
        manager.play_mode = "sequential"
        assert manager.get_next_video() == "a.mp4"
        assert manager.get_next_video() == "b.mp4"
        assert manager.get_next_video() == "c.mp4"

    def test_sequential_loops(self, manager):
        manager.set_playlist(["a.mp4", "b.mp4"])
        manager.play_mode = "sequential"
        manager.get_next_video()  # a
        manager.get_next_video()  # b
        result = manager.get_next_video()  # loop → a
        assert result == "a.mp4"

    def test_random_returns_from_playlist(self, manager):
        manager.set_playlist(["a.mp4", "b.mp4", "c.mp4"])
        manager.play_mode = "random"
        for _ in range(20):
            result = manager.get_next_video()
            assert result in ["a.mp4", "b.mp4", "c.mp4"]

    def test_empty_playlist_returns_none(self, manager):
        manager.set_playlist([])
        assert manager.get_next_video() is None


class TestDetectBackend:
    """Test backend detection — OBS primary, UnityCapture fallback."""

    @patch("modules_client.virtual_camera_manager.pyvirtualcam")
    def test_obs_detected(self, mock_pvc, manager):
        mock_cam = MagicMock()
        mock_pvc.Camera.return_value.__enter__ = MagicMock(return_value=mock_cam)
        mock_pvc.Camera.return_value.__exit__ = MagicMock(return_value=False)

        # Simulate OBS backend works
        def camera_factory(*args, **kwargs):
            if kwargs.get("backend") == "obs":
                return MagicMock()
            raise RuntimeError("not found")

        mock_pvc.Camera.side_effect = camera_factory
        result = manager.detect_backend()
        assert result == "obs"

    @patch("modules_client.virtual_camera_manager.pyvirtualcam")
    def test_unitycapture_fallback(self, mock_pvc, manager):
        def camera_factory(*args, **kwargs):
            if kwargs.get("backend") == "obs":
                raise RuntimeError("OBS not installed")
            if kwargs.get("backend") == "unitycapture":
                return MagicMock()
            raise RuntimeError("not found")

        mock_pvc.Camera.side_effect = camera_factory
        result = manager.detect_backend()
        assert result == "unitycapture"

    @patch("modules_client.virtual_camera_manager.pyvirtualcam")
    def test_no_backend(self, mock_pvc, manager):
        mock_pvc.Camera.side_effect = RuntimeError("no driver")
        result = manager.detect_backend()
        assert result is None


class TestStopCleanup:
    """Test stop behavior."""

    def test_request_stop(self, manager):
        manager.is_playing = True
        manager.request_stop()
        assert manager._stop_requested is True
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_virtual_camera_manager.py -v --tb=short`
Expected: FAIL — module not found

- [ ] **Step 3: Create VirtualCameraManager implementation**

Create `modules_client/virtual_camera_manager.py`:

```python
"""
VirtualCameraManager — putar playlist video sebagai virtual camera device.

Membaca video frame-by-frame via OpenCV, kirim ke virtual camera via pyvirtualcam.
Backend: OBS Virtual Camera (primary) → UnityCapture (fallback).
"""

import logging
import random

from PyQt6.QtCore import QThread, pyqtSignal

logger = logging.getLogger('VocaLive')

try:
    import pyvirtualcam
except ImportError:
    pyvirtualcam = None

try:
    import cv2
except ImportError:
    cv2 = None

MAX_PLAYLIST = 10


class VirtualCameraManager(QThread):
    """Manage video playlist playback to virtual camera device."""

    statusChanged = pyqtSignal(str)
    errorOccurred = pyqtSignal(str)
    videoChanged = pyqtSignal(int, str)  # index, filename
    playbackStopped = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.playlist: list = []
        self.play_mode: str = "sequential"
        self.is_playing: bool = False
        self.current_index: int = 0
        self._cam = None
        self._stop_requested = False

    def set_playlist(self, paths: list):
        """Set video playlist, max 10 items."""
        self.playlist = list(paths[:MAX_PLAYLIST])
        self.current_index = 0

    def set_play_mode(self, mode: str):
        """Set play mode: 'sequential' or 'random'."""
        if mode in ("sequential", "random"):
            self.play_mode = mode

    def get_next_video(self) -> str | None:
        """Get next video path based on play mode."""
        if not self.playlist:
            return None

        if self.play_mode == "random":
            path = random.choice(self.playlist)
            return path

        # Sequential with loop
        path = self.playlist[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.playlist)
        return path

    def skip_to_next(self):
        """Signal to skip current video and play next."""
        self._skip_requested = True

    def request_stop(self):
        """Request playback stop from any thread."""
        self._stop_requested = True

    def detect_backend(self) -> str | None:
        """Detect available virtual camera backend.
        
        Returns 'obs', 'unitycapture', or None.
        """
        if pyvirtualcam is None:
            return None

        # Try OBS first (primary)
        for backend in ("obs", "unitycapture"):
            try:
                cam = pyvirtualcam.Camera(width=640, height=480, fps=30, backend=backend)
                cam.close()
                return backend
            except Exception:
                continue

        return None

    def _get_video_info(self, path: str) -> tuple | None:
        """Read video resolution and FPS. Returns (width, height, fps) or None."""
        if cv2 is None:
            return None
        cap = cv2.VideoCapture(path)
        if not cap.isOpened():
            return None
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        cap.release()
        if w <= 0 or h <= 0:
            return None
        return (w, h, fps if fps > 0 else 30.0)

    def run(self):
        """Main playback loop — runs in QThread."""
        self._stop_requested = False
        self._skip_requested = False
        self.is_playing = True

        if not self.playlist:
            self.errorOccurred.emit("Playlist kosong — tambahkan video dulu")
            self.is_playing = False
            self.playbackStopped.emit()
            return

        if pyvirtualcam is None or cv2 is None:
            self.errorOccurred.emit("Library pyvirtualcam atau opencv belum terinstall")
            self.is_playing = False
            self.playbackStopped.emit()
            return

        # Detect backend
        backend = self.detect_backend()
        if backend is None:
            self.errorOccurred.emit("no_driver")
            self.is_playing = False
            self.playbackStopped.emit()
            return

        self.statusChanged.emit(f"Backend: {backend}")
        logger.info("[VCAM] Using backend: %s", backend)

        # Get resolution from first video
        info = self._get_video_info(self.playlist[0])
        if info is None:
            self.errorOccurred.emit(f"Gagal baca video: {self.playlist[0]}")
            self.is_playing = False
            self.playbackStopped.emit()
            return

        width, height, fps = info
        logger.info("[VCAM] Camera: %dx%d @ %.1f fps", width, height, fps)

        try:
            with pyvirtualcam.Camera(width, height, fps, backend=backend) as cam:
                self._cam = cam
                self.statusChanged.emit(f"Streaming {width}x{height} @ {int(fps)}fps via {backend}")

                while not self._stop_requested:
                    video_path = self.get_next_video()
                    if video_path is None:
                        break

                    idx = self.playlist.index(video_path) + 1 if video_path in self.playlist else 0
                    filename = video_path.replace("\\", "/").split("/")[-1]
                    self.videoChanged.emit(idx, filename)
                    self.statusChanged.emit(f"Playing {idx}/{len(self.playlist)} — {filename}")

                    self._play_single_video(cam, video_path, fps)

        except Exception as e:
            logger.error("[VCAM] Error: %s", e)
            self.errorOccurred.emit(str(e))
        finally:
            self._cam = None
            self.is_playing = False
            self.playbackStopped.emit()
            logger.info("[VCAM] Playback stopped")

    def _play_single_video(self, cam, path: str, fps: float):
        """Play one video file, sending frames to virtual camera."""
        self._skip_requested = False
        cap = cv2.VideoCapture(path)

        if not cap.isOpened():
            logger.warning("[VCAM] Skipping unreadable video: %s", path)
            return

        try:
            while not self._stop_requested and not self._skip_requested:
                ret, frame = cap.read()
                if not ret:
                    break  # Video finished

                # OpenCV BGR → pyvirtualcam RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                cam.send(frame_rgb)
                cam.sleep_until_next_frame()
        finally:
            cap.release()
```

- [ ] **Step 4: Run tests**

Run: `python -m pytest tests/test_virtual_camera_manager.py -v --tb=short`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add modules_client/virtual_camera_manager.py tests/test_virtual_camera_manager.py
git commit -m "feat: tambah VirtualCameraManager — playlist video ke virtual camera device"
```

---

### Task 3: Config Persistence — virtual_camera.json

**Files:**
- Modify: `modules_client/virtual_camera_manager.py`
- Add to: `tests/test_virtual_camera_manager.py`

- [ ] **Step 1: Write failing tests for config load/save**

Append to `tests/test_virtual_camera_manager.py`:

```python
class TestConfigPersistence:
    """Test save/load config to virtual_camera.json."""

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
        config_path.write_text(json.dumps({
            "playlist": ["x.mp4", "y.mp4"],
            "play_mode": "sequential"
        }), encoding="utf-8")

        manager.load_config(str(config_path))
        assert manager.playlist == ["x.mp4", "y.mp4"]
        assert manager.play_mode == "sequential"

    def test_load_missing_file(self, manager, tmp_path):
        config_path = tmp_path / "nonexistent.json"
        manager.load_config(str(config_path))
        assert manager.playlist == []
        assert manager.play_mode == "sequential"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_virtual_camera_manager.py::TestConfigPersistence -v --tb=short`
Expected: FAIL — `save_config`/`load_config` not defined

- [ ] **Step 3: Add save_config and load_config to VirtualCameraManager**

Add these methods to the `VirtualCameraManager` class in `modules_client/virtual_camera_manager.py`:

```python
    def save_config(self, path: str = None):
        """Save playlist and settings to JSON."""
        import json
        if path is None:
            from pathlib import Path
            path = str(Path(__file__).parent.parent / "config" / "virtual_camera.json")
        data = {
            "playlist": self.playlist,
            "play_mode": self.play_mode,
        }
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error("[VCAM] Failed to save config: %s", e)

    def load_config(self, path: str = None):
        """Load playlist and settings from JSON."""
        import json
        if path is None:
            from pathlib import Path
            path = str(Path(__file__).parent.parent / "config" / "virtual_camera.json")
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.set_playlist(data.get("playlist", []))
            self.set_play_mode(data.get("play_mode", "sequential"))
        except FileNotFoundError:
            pass
        except Exception as e:
            logger.error("[VCAM] Failed to load config: %s", e)
```

- [ ] **Step 4: Run tests**

Run: `python -m pytest tests/test_virtual_camera_manager.py -v --tb=short`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add modules_client/virtual_camera_manager.py tests/test_virtual_camera_manager.py
git commit -m "feat: tambah save/load config virtual camera ke JSON"
```

---

### Task 4: VirtualCameraTab — UI

**Files:**
- Create: `ui/virtual_camera_tab.py`

- [ ] **Step 1: Create VirtualCameraTab UI**

Create `ui/virtual_camera_tab.py`:

```python
"""
VirtualCameraTab — Tab UI untuk mengelola playlist video sebagai virtual camera.
User masukkan video, pilih mode (sequential/random), klik Play.
"""

import os
import logging
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog,
    QFrame, QRadioButton, QButtonGroup, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSlot

try:
    from ui.theme import (
        PRIMARY, BG_BASE, BG_SURFACE, BG_ELEVATED, TEXT_PRIMARY, TEXT_MUTED,
        BORDER, SUCCESS, ERROR, WARNING, ACCENT, RADIUS,
        btn_primary, btn_success, btn_danger, btn_ghost, btn_secondary,
        label_title, label_subtitle, status_badge,
        CARD_STYLE, HEADER_FRAME_STYLE
    )
except ImportError:
    PRIMARY = "#2563EB"; BG_BASE = "#0F1623"; BG_SURFACE = "#162032"
    BG_ELEVATED = "#1E2A3B"; TEXT_PRIMARY = "#F0F6FF"; TEXT_MUTED = "#93C5FD"
    BORDER = "#1A2E4A"; SUCCESS = "#22C55E"; ERROR = "#EF4444"
    WARNING = "#F59E0B"; ACCENT = "#60A5FA"; RADIUS = "10px"
    CARD_STYLE = f"QFrame {{ background-color: {BG_SURFACE}; border: 1px solid {BORDER}; border-radius: 10px; }}"
    HEADER_FRAME_STYLE = f"QFrame {{ background-color: {BG_ELEVATED}; border-bottom: 2px solid {PRIMARY}; border-radius: 10px 10px 0 0; padding: 12px; }}"
    def btn_primary(e=""): return f"QPushButton {{ background-color: {PRIMARY}; color: white; border: none; border-radius: 6px; padding: 8px 16px; font-weight: 700; {e} }}"
    def btn_success(e=""): return f"QPushButton {{ background-color: {SUCCESS}; color: white; border: none; border-radius: 6px; padding: 8px 16px; font-weight: 700; {e} }}"
    def btn_danger(e=""): return f"QPushButton {{ background-color: {ERROR}; color: white; border: none; border-radius: 6px; padding: 8px 16px; font-weight: 700; {e} }}"
    def btn_ghost(e=""): return f"QPushButton {{ background-color: {BG_ELEVATED}; color: {TEXT_MUTED}; border: 1px solid {BORDER}; border-radius: 6px; padding: 7px 16px; {e} }}"
    def btn_secondary(e=""): return f"QPushButton {{ background-color: transparent; color: {PRIMARY}; border: 1px solid {PRIMARY}; border-radius: 6px; padding: 7px 16px; font-weight: 600; {e} }}"
    def label_title(s=16): return f"font-size: {s}pt; font-weight: 700; color: {PRIMARY}; background: transparent;"
    def label_subtitle(s=11): return f"font-size: {s}px; color: {TEXT_MUTED}; background: transparent;"
    def status_badge(color=None, size=11): return f"font-size: {size}px; color: {color or TEXT_MUTED}; font-weight: 600; background: transparent;"

from modules_client.virtual_camera_manager import VirtualCameraManager

logger = logging.getLogger('VocaLive')

UNITY_CAPTURE_URL = "https://github.com/schellingb/UnityCapture/releases"
VIDEO_FILTER = "Video Files (*.mp4 *.avi *.mkv *.mov *.wmv);;All Files (*)"
MAX_PLAYLIST = 10


class VirtualCameraTab(QWidget):
    """Tab untuk mengelola virtual camera — playlist video sebagai webcam."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.manager = VirtualCameraManager()
        self.manager.load_config()
        self._setup_signals()
        self._init_ui()
        self._load_playlist_to_table()

    def _setup_signals(self):
        """Connect manager signals."""
        self.manager.statusChanged.connect(self._on_status_changed)
        self.manager.errorOccurred.connect(self._on_error)
        self.manager.videoChanged.connect(self._on_video_changed)
        self.manager.playbackStopped.connect(self._on_playback_stopped)

    def _init_ui(self):
        """Build the tab UI."""
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # === Header ===
        header = QFrame()
        header.setStyleSheet(HEADER_FRAME_STYLE)
        header_layout = QVBoxLayout(header)

        title = QLabel("Virtual Camera")
        title.setStyleSheet(label_title(14))
        header_layout.addWidget(title)

        subtitle = QLabel("Putar video sebagai virtual webcam untuk TikTok Live Studio")
        subtitle.setStyleSheet(label_subtitle())
        header_layout.addWidget(subtitle)

        layout.addWidget(header)

        # === Status Card ===
        status_card = QFrame()
        status_card.setStyleSheet(CARD_STYLE)
        status_layout = QHBoxLayout(status_card)

        self.status_indicator = QLabel("Stopped")
        self.status_indicator.setStyleSheet(status_badge(ERROR, size=13))
        status_layout.addWidget(self.status_indicator)

        status_layout.addStretch()

        self.backend_label = QLabel("Backend: detecting...")
        self.backend_label.setStyleSheet(label_subtitle())
        status_layout.addWidget(self.backend_label)

        layout.addWidget(status_card)

        # === Driver Install Panel (hidden by default) ===
        self.driver_panel = QFrame()
        self.driver_panel.setStyleSheet(
            f"QFrame {{ background-color: #1E1A0F; border: 1px solid {WARNING}; border-radius: {RADIUS}; padding: 12px; }}"
        )
        driver_layout = QVBoxLayout(self.driver_panel)

        driver_msg = QLabel(
            "Virtual camera driver belum terinstall.\n"
            "Install OBS (sudah include virtual camera) atau download UnityCapture driver."
        )
        driver_msg.setStyleSheet(f"color: {WARNING}; font-size: 12px; background: transparent;")
        driver_msg.setWordWrap(True)
        driver_layout.addWidget(driver_msg)

        btn_download = QPushButton("Download UnityCapture Driver")
        btn_download.setStyleSheet(btn_secondary("font-size: 12px;"))
        btn_download.clicked.connect(self._open_driver_download)
        driver_layout.addWidget(btn_download)

        restart_msg = QLabel("Setelah install driver, restart VocaLive.")
        restart_msg.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px; background: transparent;")
        driver_layout.addWidget(restart_msg)

        self.driver_panel.setVisible(False)
        layout.addWidget(self.driver_panel)

        # === Playlist Section ===
        playlist_card = QFrame()
        playlist_card.setStyleSheet(CARD_STYLE)
        playlist_layout = QVBoxLayout(playlist_card)

        pl_header = QHBoxLayout()
        pl_title = QLabel("Playlist")
        pl_title.setStyleSheet(label_title(12))
        pl_header.addWidget(pl_title)

        self.playlist_count = QLabel("0/10 video")
        self.playlist_count.setStyleSheet(label_subtitle())
        pl_header.addStretch()
        pl_header.addWidget(self.playlist_count)
        playlist_layout.addLayout(pl_header)

        # Table
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["No", "Video", ""])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 40)
        self.table.setColumnWidth(2, 70)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet(
            f"QTableWidget {{ background-color: {BG_BASE}; color: {TEXT_PRIMARY}; "
            f"border: 1px solid {BORDER}; border-radius: 6px; gridline-color: {BORDER}; }}"
            f"QHeaderView::section {{ background-color: {BG_ELEVATED}; color: {TEXT_MUTED}; "
            f"border: none; padding: 6px; font-weight: 600; }}"
        )
        playlist_layout.addWidget(self.table)

        # Add button
        btn_add = QPushButton("+ Tambah Video")
        btn_add.setStyleSheet(btn_ghost("font-size: 12px;"))
        btn_add.clicked.connect(self._add_videos)
        playlist_layout.addWidget(btn_add)

        layout.addWidget(playlist_card)

        # === Mode Selection ===
        mode_card = QFrame()
        mode_card.setStyleSheet(CARD_STYLE)
        mode_layout = QHBoxLayout(mode_card)

        mode_label = QLabel("Mode:")
        mode_label.setStyleSheet(f"color: {TEXT_PRIMARY}; font-weight: 600; background: transparent;")
        mode_layout.addWidget(mode_label)

        self.radio_sequential = QRadioButton("Berurutan")
        self.radio_random = QRadioButton("Acak")
        self.radio_sequential.setStyleSheet(f"color: {TEXT_PRIMARY}; background: transparent;")
        self.radio_random.setStyleSheet(f"color: {TEXT_PRIMARY}; background: transparent;")

        self.mode_group = QButtonGroup(self)
        self.mode_group.addButton(self.radio_sequential)
        self.mode_group.addButton(self.radio_random)

        if self.manager.play_mode == "random":
            self.radio_random.setChecked(True)
        else:
            self.radio_sequential.setChecked(True)

        self.radio_sequential.toggled.connect(self._on_mode_changed)

        mode_layout.addWidget(self.radio_sequential)
        mode_layout.addWidget(self.radio_random)
        mode_layout.addStretch()

        layout.addWidget(mode_card)

        # === Control Buttons ===
        ctrl_layout = QHBoxLayout()

        self.btn_play = QPushButton("Play")
        self.btn_play.setStyleSheet(btn_success("font-size: 14px; padding: 10px 24px;"))
        self.btn_play.clicked.connect(self._on_play)
        ctrl_layout.addWidget(self.btn_play)

        self.btn_stop = QPushButton("Stop")
        self.btn_stop.setStyleSheet(btn_danger("font-size: 14px; padding: 10px 24px;"))
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self._on_stop)
        ctrl_layout.addWidget(self.btn_stop)

        self.btn_next = QPushButton("Next")
        self.btn_next.setStyleSheet(btn_primary("font-size: 14px; padding: 10px 24px;"))
        self.btn_next.setEnabled(False)
        self.btn_next.clicked.connect(self._on_next)
        ctrl_layout.addWidget(self.btn_next)

        layout.addLayout(ctrl_layout)

        layout.addStretch()
        self.setLayout(layout)

        # Detect backend on init
        self._detect_backend_async()

    # === Slots ===

    def _detect_backend_async(self):
        """Detect virtual camera backend."""
        backend = self.manager.detect_backend()
        if backend:
            self.backend_label.setText(f"Backend: {backend}")
            self.driver_panel.setVisible(False)
        else:
            self.backend_label.setText("Backend: tidak terdeteksi")
            self.driver_panel.setVisible(True)

    def _load_playlist_to_table(self):
        """Populate table from manager playlist."""
        self.table.setRowCount(0)
        for i, path in enumerate(self.manager.playlist):
            self._add_row(i, path)
        self._update_count()

    def _add_row(self, index: int, path: str):
        """Add one row to playlist table."""
        row = self.table.rowCount()
        self.table.insertRow(row)

        # No
        num_item = QTableWidgetItem(str(index + 1))
        num_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(row, 0, num_item)

        # Filename
        filename = os.path.basename(path)
        name_item = QTableWidgetItem(filename)
        name_item.setToolTip(path)
        self.table.setItem(row, 1, name_item)

        # Delete button
        btn_del = QPushButton("Hapus")
        btn_del.setStyleSheet(btn_danger("font-size: 11px; padding: 4px 8px;"))
        btn_del.clicked.connect(lambda checked, r=row: self._remove_video(r))
        self.table.setCellWidget(row, 2, btn_del)

    def _update_count(self):
        """Update playlist count label."""
        count = len(self.manager.playlist)
        self.playlist_count.setText(f"{count}/{MAX_PLAYLIST} video")

    @pyqtSlot()
    def _add_videos(self):
        """Open file dialog to add videos."""
        remaining = MAX_PLAYLIST - len(self.manager.playlist)
        if remaining <= 0:
            QMessageBox.information(self, "Playlist Penuh", f"Maksimal {MAX_PLAYLIST} video.")
            return

        files, _ = QFileDialog.getOpenFileNames(
            self, "Pilih Video", "", VIDEO_FILTER
        )

        if not files:
            return

        files = files[:remaining]
        new_playlist = self.manager.playlist + files
        self.manager.set_playlist(new_playlist)
        self.manager.save_config()

        self._load_playlist_to_table()

    def _remove_video(self, row: int):
        """Remove video from playlist by row index."""
        if 0 <= row < len(self.manager.playlist):
            self.manager.playlist.pop(row)
            self.manager.save_config()
            self._load_playlist_to_table()

    @pyqtSlot()
    def _on_mode_changed(self):
        """Handle mode radio button change."""
        mode = "sequential" if self.radio_sequential.isChecked() else "random"
        self.manager.set_play_mode(mode)
        self.manager.save_config()

    @pyqtSlot()
    def _on_play(self):
        """Start virtual camera playback."""
        if not self.manager.playlist:
            QMessageBox.warning(self, "Playlist Kosong", "Tambahkan minimal 1 video dulu.")
            return

        self.btn_play.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.btn_next.setEnabled(True)
        self.status_indicator.setText("Starting...")
        self.status_indicator.setStyleSheet(status_badge(WARNING, size=13))

        self.manager.start()

    @pyqtSlot()
    def _on_stop(self):
        """Stop virtual camera playback."""
        self.manager.request_stop()
        self.status_indicator.setText("Stopping...")

    @pyqtSlot()
    def _on_next(self):
        """Skip to next video."""
        self.manager.skip_to_next()

    @pyqtSlot(str)
    def _on_status_changed(self, message: str):
        """Update status display."""
        self.status_indicator.setText(message)
        self.status_indicator.setStyleSheet(status_badge(SUCCESS, size=13))

    @pyqtSlot(str)
    def _on_error(self, message: str):
        """Handle error from manager."""
        if message == "no_driver":
            self.driver_panel.setVisible(True)
            self.status_indicator.setText("Driver tidak terdeteksi")
        else:
            self.status_indicator.setText(f"Error: {message}")
        self.status_indicator.setStyleSheet(status_badge(ERROR, size=13))
        self.btn_play.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.btn_next.setEnabled(False)

    @pyqtSlot(int, str)
    def _on_video_changed(self, index: int, filename: str):
        """Highlight current video in table."""
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item:
                if row == index - 1:
                    item.setText(f">{index}")
                else:
                    item.setText(str(row + 1))

    @pyqtSlot()
    def _on_playback_stopped(self):
        """Reset UI when playback stops."""
        self.btn_play.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.btn_next.setEnabled(False)
        self.status_indicator.setText("Stopped")
        self.status_indicator.setStyleSheet(status_badge(ERROR, size=13))

        # Reset table highlighting
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item:
                item.setText(str(row + 1))

    def _open_driver_download(self):
        """Open UnityCapture download page in browser."""
        import webbrowser
        webbrowser.open(UNITY_CAPTURE_URL)
```

- [ ] **Step 2: Verify import works**

Run: `python -c "from ui.virtual_camera_tab import VirtualCameraTab; print('OK')"`
Expected: OK (atau ImportError dari Qt jika tidak ada display — acceptable di CI)

- [ ] **Step 3: Commit**

```bash
git add ui/virtual_camera_tab.py
git commit -m "feat: tambah VirtualCameraTab UI — playlist, mode, kontrol play/stop/next"
```

---

### Task 5: Wire Tab ke MainWindow

**Files:**
- Modify: `ui/main_window.py:227-234` (import section)
- Modify: `ui/main_window.py:879` (after Product Scene tab)

- [ ] **Step 1: Add import di main_window.py**

Setelah block import ProductSceneTab (line ~234), tambahkan:

```python
# Import VirtualCameraTab
try:
    from ui.virtual_camera_tab import VirtualCameraTab
    VIRTUAL_CAMERA_TAB_AVAILABLE = True
    logger.info("VirtualCameraTab imported successfully")
except ImportError as e:
    VIRTUAL_CAMERA_TAB_AVAILABLE = False
    logger.warning(f"VirtualCameraTab not available: {e}")
```

- [ ] **Step 2: Add tab di _create_main_tabs()**

Setelah block Product Scene tab (line ~879), tambahkan:

```python
        # Add Virtual Camera tab
        if VIRTUAL_CAMERA_TAB_AVAILABLE:
            try:
                self.virtual_camera_tab = VirtualCameraTab()
                self.main_tabs.addTab(self.virtual_camera_tab, "Virtual Camera")
                logger.info("Virtual Camera tab added successfully")
            except Exception as e:
                logger.error(f"Failed to create Virtual Camera tab: {e}")
                placeholder = QWidget()
                layout = QVBoxLayout()
                layout.addWidget(QLabel(f"Error loading Virtual Camera Tab: {e}"))
                placeholder.setLayout(layout)
                self.main_tabs.addTab(placeholder, "Virtual Camera (Error)")
```

- [ ] **Step 3: Run app to verify tab muncul**

Run: `python main.py`
Expected: Tab "Virtual Camera" muncul di tab bar

- [ ] **Step 4: Run full test suite**

Run: `python -m pytest tests/ -v --tb=short`
Expected: All tests PASS (termasuk test baru dari Task 2 & 3)

- [ ] **Step 5: Commit**

```bash
git add ui/main_window.py
git commit -m "feat: wire VirtualCameraTab ke MainWindow — tab baru muncul di UI"
```

---

### Task 6: Build Config — hiddenimports PyInstaller

**Files:**
- Modify: `build_production_exe_fixed.py` (hiddenimports section)

- [ ] **Step 1: Tambah hiddenimports**

Cari array `hiddenimports` di `build_production_exe_fixed.py` dan tambahkan:

```python
'pyvirtualcam',
'cv2',
```

- [ ] **Step 2: Commit**

```bash
git add build_production_exe_fixed.py
git commit -m "chore: tambah pyvirtualcam dan cv2 ke hiddenimports PyInstaller"
```

---

### Task 7: Final Integration Test

**Files:**
- No new files

- [ ] **Step 1: Run full test suite**

Run: `python -m pytest tests/ -v --tb=short`
Expected: All tests PASS

- [ ] **Step 2: Manual test app**

Run: `python main.py`

Verifikasi:
1. Tab "Virtual Camera" muncul
2. Bisa tambah video ke playlist
3. Mode sequential/random bisa dipilih
4. Playlist tersimpan (restart app, playlist masih ada)
5. Jika tidak ada OBS/UnityCapture → driver panel muncul dengan link download
6. Jika ada driver → klik Play → video streaming ke virtual camera

- [ ] **Step 3: Push to remote**

```bash
git push -u origin feat/virtual-camera-tab
```
