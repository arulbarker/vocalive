"""
ProductPopupWindow - Frameless always-on-top window untuk overlay video produk.
TikTok Live Studio menangkap window ini sebagai "Window Capture" source.
"""

import os
import threading
import logging

from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import Qt, QUrl, pyqtSignal, pyqtSlot
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget

logger = logging.getLogger('VocaLive')

WINDOW_TITLE = "VocaLive Product Display"


class ProductPopupWindow(QWidget):
    """
    Window overlay vertikal untuk menampilkan video produk saat streaming.

    Setup TikTok Live Studio (sekali):
      Window Capture → pilih "VocaLive Product Display" → taruh di layer atas kamera.

    Usage:
      popup.show_product(video_path)  # tampilkan + play video
      # window auto-hide setelah TTS selesai
    """

    _hide_requested = pyqtSignal()  # signal thread-safe untuk hide dari watcher thread

    def __init__(self, width: int = 608, height: int = 1080):
        super().__init__(None)  # no parent → top-level window
        self.setWindowTitle(WINDOW_TITLE)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool  # tidak muncul di taskbar
        )
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)  # tidak steal focus
        self.setStyleSheet("background-color: black;")
        self.resize(width, height)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._video_widget = QVideoWidget(self)
        self._video_widget.setStyleSheet("background-color: black;")
        layout.addWidget(self._video_widget)

        self._player = QMediaPlayer()
        self._audio_output = QAudioOutput()
        self._player.setAudioOutput(self._audio_output)
        self._player.setVideoOutput(self._video_widget)
        self._audio_output.setVolume(0.0)  # mute — audio dari TTS pygame

        # Loop video: saat selesai, restart dari awal
        self._player.mediaStatusChanged.connect(self._on_media_status)

        # Thread-safe hide dari watcher thread
        self._hide_requested.connect(self._do_hide)

        self._stop_event = threading.Event()
        self._watcher_thread: threading.Thread | None = None

    def _on_media_status(self, status: QMediaPlayer.MediaStatus):
        """Loop video saat EndOfMedia."""
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            source = self._player.source()
            if source and source.isValid():
                self._player.setPosition(0)
                self._player.play()

    def show_product(self, video_path: str):
        """
        Tampilkan window dan putar video produk.
        HARUS dipanggil dari Qt main thread.
        """
        if not os.path.exists(video_path):
            logger.warning(f"ProductPopupWindow: file tidak ditemukan: {video_path}")
            return

        # Stop watcher sebelumnya dan tunggu exit
        self._stop_event.set()
        if self._watcher_thread and self._watcher_thread.is_alive():
            self._watcher_thread.join(timeout=1.0)
        self._stop_event.clear()

        # Load dan play video
        self._player.stop()
        self._player.setSource(QUrl.fromLocalFile(os.path.abspath(video_path)))
        self.show()
        self._player.play()

        # Start TTS watcher
        self._start_tts_watcher()

    def _start_tts_watcher(self):
        """Background thread yang deteksi TTS selesai lalu hide window."""
        def watch():
            import time
            time.sleep(0.5)
            try:
                import pygame
                while not self._stop_event.is_set():
                    if not pygame.mixer.music.get_busy():
                        break
                    time.sleep(0.2)
            except Exception as e:
                logger.warning(f"ProductPopupWindow watcher error: {e}")
                return  # jangan hide jika ada error pygame

            if not self._stop_event.is_set():
                self._hide_requested.emit()  # thread-safe: emit ke main thread

        self._watcher_thread = threading.Thread(target=watch, daemon=True)
        self._watcher_thread.start()

    @pyqtSlot()
    def _do_hide(self):
        """Hide window dan stop player. Dipanggil dari main thread via signal."""
        self._player.stop()
        self.hide()

    def closeEvent(self, event):
        """Cleanup saat window ditutup."""
        self._stop_event.set()
        self._player.stop()
        super().closeEvent(event)

    def resize_popup(self, width: int, height: int):
        """Update ukuran window (dipanggil dari ProductSceneTab saat user ubah size)."""
        self.resize(width, min(height, 1080))
