# modules_client/virtual_camera_manager.py - Virtual Camera Manager
# Manages video playlist playback through a virtual camera device (OBS/UnityCapture)

import logging
import os
import random
import time

try:
    import pyvirtualcam
except ImportError:
    pyvirtualcam = None

try:
    import cv2
except ImportError:
    cv2 = None

try:
    import numpy as np
except ImportError:
    np = None

from PyQt6.QtCore import QThread, pyqtSignal

logger = logging.getLogger('VocaLive')

MAX_PLAYLIST_SIZE = 10
SUPPORTED_BACKENDS = ["obs", "unitycapture"]


class VirtualCameraManager(QThread):
    """
    QThread yang membaca frame video via OpenCV dan mengirimnya
    ke virtual camera device via pyvirtualcam.
    Mendukung playlist hingga 10 video dengan mode sequential atau random.
    """

    statusChanged = pyqtSignal(str)
    errorOccurred = pyqtSignal(str)
    videoChanged = pyqtSignal(int, str)   # index, filename
    playbackStopped = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.playlist: list = []
        self.play_mode: str = "sequential"   # "sequential" | "random"
        self.is_playing: bool = False
        self.current_index: int = 0
        self._cam = None
        self._stop_requested: bool = False
        self._skip_requested: bool = False

    # -----------------------------------------------------------------
    # Playlist management
    # -----------------------------------------------------------------

    def set_playlist(self, paths: list) -> None:
        """Set playlist video (max 10 items). Reset index ke 0."""
        if not isinstance(paths, list):
            return
        self.playlist = paths[:MAX_PLAYLIST_SIZE]
        self.current_index = 0
        logger.info(f"Virtual camera playlist set: {len(self.playlist)} videos")

    def set_play_mode(self, mode: str) -> None:
        """Set mode playback: 'sequential' atau 'random'. Mode invalid diabaikan."""
        if mode in ("sequential", "random"):
            self.play_mode = mode
            logger.info(f"Virtual camera play mode: {mode}")

    def get_next_video(self) -> str | None:
        """
        Ambil path video berikutnya sesuai play_mode.
        Sequential: loop dari awal setelah habis.
        Random: pilih acak dari playlist.
        Returns None jika playlist kosong.
        """
        if not self.playlist:
            return None

        if self.play_mode == "random":
            path = random.choice(self.playlist)
            self.current_index = self.playlist.index(path)
            return path

        # Sequential: ambil current_index, lalu increment (loop)
        path = self.playlist[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.playlist)
        return path

    # -----------------------------------------------------------------
    # Playback control
    # -----------------------------------------------------------------

    def skip_to_next(self) -> None:
        """Set flag untuk skip ke video berikutnya."""
        self._skip_requested = True

    def request_stop(self) -> None:
        """Set flag untuk menghentikan playback."""
        self._stop_requested = True

    # -----------------------------------------------------------------
    # Backend detection
    # -----------------------------------------------------------------

    def detect_backend(self) -> str | None:
        """
        Deteksi backend virtual camera yang tersedia.
        Coba 'obs' dulu, lalu 'unitycapture'. Return None jika tidak ada.
        """
        if pyvirtualcam is None:
            logger.warning("pyvirtualcam not installed — cannot detect backend")
            return None

        for backend in SUPPORTED_BACKENDS:
            try:
                # Coba buka virtual camera dengan resolusi minimal untuk test
                cam = pyvirtualcam.Camera(width=640, height=480, fps=30, backend=backend)
                cam.close()
                logger.info(f"Virtual camera backend detected: {backend}")
                return backend
            except Exception:
                continue

        logger.warning("No virtual camera backend detected")
        return None

    # -----------------------------------------------------------------
    # Video info
    # -----------------------------------------------------------------

    def _get_video_info(self, path: str) -> tuple | None:
        """
        Baca info video: (width, height, fps) via cv2.VideoCapture.
        Returns None jika file tidak bisa dibuka.
        """
        if cv2 is None:
            return None

        cap = cv2.VideoCapture(path)
        if not cap.isOpened():
            cap.release()
            return None

        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)

        cap.release()

        if width <= 0 or height <= 0 or fps <= 0:
            return None

        return (width, height, fps)

    # -----------------------------------------------------------------
    # Main thread loop
    # -----------------------------------------------------------------

    def run(self) -> None:
        """Main QThread loop: detect backend, open camera, loop playlist."""
        self._stop_requested = False
        self._skip_requested = False
        self.is_playing = True

        if pyvirtualcam is None:
            self.errorOccurred.emit("pyvirtualcam not installed")
            self.is_playing = False
            self.playbackStopped.emit()
            return

        if cv2 is None:
            self.errorOccurred.emit("OpenCV (cv2) not installed")
            self.is_playing = False
            self.playbackStopped.emit()
            return

        if not self.playlist:
            self.errorOccurred.emit("Playlist kosong")
            self.is_playing = False
            self.playbackStopped.emit()
            return

        # Detect backend
        backend = self.detect_backend()
        if backend is None:
            self.errorOccurred.emit("Tidak ada virtual camera backend (OBS/UnityCapture)")
            self.is_playing = False
            self.playbackStopped.emit()
            return

        # Get video info from first available video to determine camera dimensions
        cam_width, cam_height, cam_fps = 1280, 720, 30  # defaults
        for path in self.playlist:
            info = self._get_video_info(path)
            if info:
                cam_width, cam_height, cam_fps = info
                break

        try:
            self._cam = pyvirtualcam.Camera(
                width=cam_width, height=cam_height,
                fps=int(cam_fps), backend=backend
            )
            self.statusChanged.emit(f"Virtual camera aktif ({cam_width}x{cam_height} @ {int(cam_fps)}fps)")
            logger.info(f"Virtual camera opened: {cam_width}x{cam_height} @ {int(cam_fps)}fps, backend={backend}")

            # Main playback loop
            while not self._stop_requested:
                video_path = self.get_next_video()
                if video_path is None:
                    break

                filename = os.path.basename(video_path)
                idx = self.playlist.index(video_path) if video_path in self.playlist else 0
                self.videoChanged.emit(idx, filename)

                self._play_single_video(self._cam, video_path, cam_fps)

        except Exception as e:
            logger.error(f"Virtual camera error: {e}")
            self.errorOccurred.emit(str(e))
        finally:
            if self._cam is not None:
                try:
                    self._cam.close()
                except Exception:
                    pass
                self._cam = None

            self.is_playing = False
            self.statusChanged.emit("Virtual camera stopped")
            self.playbackStopped.emit()
            logger.info("Virtual camera playback stopped")

    def _play_single_video(self, cam, path: str, fps: float) -> None:
        """
        Putar satu video: baca frame, konversi BGR→RGB, kirim ke virtual camera.
        Berhenti jika _stop_requested atau _skip_requested.
        """
        if cv2 is None or np is None:
            return

        cap = cv2.VideoCapture(path)
        if not cap.isOpened():
            logger.warning(f"Cannot open video: {path}")
            return

        try:
            while cap.isOpened() and not self._stop_requested and not self._skip_requested:
                ret, frame = cap.read()
                if not ret:
                    break  # Video selesai

                # Resize frame jika dimensi tidak sesuai camera
                h, w = frame.shape[:2]
                if w != cam.width or h != cam.height:
                    frame = cv2.resize(frame, (cam.width, cam.height))

                # Convert BGR (OpenCV) → RGB (pyvirtualcam)
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                cam.send(rgb_frame)
                cam.sleep_until_next_frame()

        finally:
            cap.release()
            # Reset skip flag setelah video selesai/diskip
            self._skip_requested = False
