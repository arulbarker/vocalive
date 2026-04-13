"""
ProductPopupWindow - Frameless always-on-top window untuk overlay video produk.
TikTok Live Studio menangkap window ini sebagai "Window Capture" source.

Rendering video menggunakan QVideoSink + QLabel (bukan QVideoWidget) agar
video frame lewat GDI/DWM pipeline dan bisa di-capture oleh TikTok Live Studio.

Mode Preview  : Chroma green — apply Chroma Key filter di TikTok Live Studio
Mode Video    : Video frame dirender ke QLabel, ter-capture normal
"""

import os
import threading
import logging

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, QUrl, QPoint, QRect, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QPainter, QPen, QColor, QFont, QPixmap
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput, QVideoSink, QVideoFrame

logger = logging.getLogger('VocaLive')

WINDOW_TITLE = "VocaLive Product Display"
RESIZE_MARGIN = 10
MIN_WIDTH = 200
MIN_HEIGHT = 300
TITLE_H = 36


class ProductPopupWindow(QWidget):
    """
    Window overlay vertikal untuk menampilkan video produk saat streaming.

    Setup TikTok Live Studio (sekali):
      1. Buka preview → posisikan window di layar
      2. Di TikTok LS: Window Capture → "VocaLive Product Display"
      3. Apply filter Chroma Key (warna hijau #00B140)
      4. Selesai — video otomatis muncul saat produk disebut

    Usage:
      popup.show_preview()            # tampilkan chroma green untuk setup
      popup.show_product(video_path)  # tampilkan + play video
    """

    _hide_requested = pyqtSignal()
    _frame_ready = pyqtSignal(QPixmap)  # thread-safe frame update ke QLabel

    def __init__(self, width: int = 608, height: int = 1080):
        super().__init__(None)
        self.setWindowTitle(WINDOW_TITLE)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setAutoFillBackground(False)
        self.setStyleSheet("background-color: black;")
        self.setMouseTracking(True)
        self.resize(width, height)

        # State drag & resize
        self._drag_pos: QPoint | None = None
        self._resize_edge: str | None = None
        self._resize_start_pos: QPoint | None = None
        self._resize_start_geom: QRect | None = None
        self._is_playing = False

        # Telemetry — scene info
        self._tel_scene_id = 0
        self._tel_scene_name = ""

        # ── Video label — render frame via GDI (ter-capture TikTok Live Studio) ──
        self._video_label = QLabel(self)
        self._video_label.setStyleSheet("background-color: black;")
        self._video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._video_label.setScaledContents(True)
        self._video_label.hide()

        # ── Title bar — solid gelap, hanya tampil saat preview ───────────────
        self._title_bar = QWidget(self)
        self._title_bar.setStyleSheet(
            "QWidget { background-color: rgba(14, 22, 35, 220); "
            "border-bottom: 1px solid #1E3A5F; }"
        )
        tb_layout = QHBoxLayout(self._title_bar)
        tb_layout.setContentsMargins(10, 0, 6, 0)
        tb_layout.setSpacing(0)
        lbl = QLabel("🎬  VocaLive Product Display", self._title_bar)
        lbl.setStyleSheet(
            "color: #60A5FA; font-size: 11px; font-weight: 600; "
            "background: transparent; border: none;"
        )
        tb_layout.addWidget(lbl)
        tb_layout.addStretch()

        # ── Close button — selalu tampil di pojok kanan atas ─────────────────
        self._btn_close = QPushButton("✕", self)
        self._btn_close.setFixedSize(32, 28)
        self._btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_close.setStyleSheet(
            "QPushButton { background-color: rgba(14,22,35,210); color: #93C5FD; "
            "border: 1px solid #1E3A5F; font-size: 14px; font-weight: bold; border-radius: 4px; }"
            "QPushButton:hover { background-color: #EF4444; color: white; border-color: #EF4444; }"
        )
        self._btn_close.clicked.connect(self._close_window)

        # ── Media player dengan QVideoSink (bukan QVideoWidget) ──────────────
        self._player = QMediaPlayer()
        self._audio_output = QAudioOutput()
        self._player.setAudioOutput(self._audio_output)
        self._audio_output.setVolume(0.0)  # mute — audio dari TTS pygame

        self._video_sink = QVideoSink()
        self._player.setVideoSink(self._video_sink)

        # Frame dari decoder → convert ke QPixmap → update QLabel (thread-safe via signal)
        self._video_sink.videoFrameChanged.connect(self._on_video_frame)
        self._frame_ready.connect(self._apply_frame)

        self._player.mediaStatusChanged.connect(self._on_media_status)
        self._hide_requested.connect(self._do_hide)

        self._stop_event = threading.Event()
        self._watcher_thread: threading.Thread | None = None

        self._reposition_children(width, height)

    # ── Positioning ───────────────────────────────────────────────────────────

    def _reposition_children(self, w: int, h: int):
        self._title_bar.setGeometry(0, 0, w, TITLE_H)
        self._video_label.setGeometry(0, 0, w, h)
        self._btn_close.move(w - 38, 4)
        self._btn_close.raise_()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._reposition_children(self.width(), self.height())

    def showEvent(self, event):
        super().showEvent(event)
        self._reposition_children(self.width(), self.height())

    # ── Paint: chroma green saat preview ─────────────────────────────────────

    def paintEvent(self, event):
        if self._is_playing:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Background hijau chroma key
        painter.fillRect(
            QRect(0, TITLE_H, self.width(), self.height() - TITLE_H),
            QColor(0, 177, 64)
        )

        # Border putih tipis
        painter.setPen(QPen(QColor(255, 255, 255, 180), 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(1, 1, self.width() - 3, self.height() - 3)

        # Corner handles putih
        handle = 14
        white = QColor(255, 255, 255, 200)
        for rx, ry in [
            (0, 0), (self.width() - handle, 0),
            (0, self.height() - handle), (self.width() - handle, self.height() - handle),
        ]:
            painter.fillRect(rx, ry, handle, handle, white)

        painter.end()

    # ── Video frame pipeline ──────────────────────────────────────────────────

    @pyqtSlot(QVideoFrame)
    def _on_video_frame(self, frame: QVideoFrame):
        """Dipanggil tiap frame dari decoder — convert ke QPixmap via signal."""
        if not self._is_playing or not frame.isValid():
            return
        image = frame.toImage()
        if not image.isNull():
            self._frame_ready.emit(QPixmap.fromImage(image))

    @pyqtSlot(QPixmap)
    def _apply_frame(self, pixmap: QPixmap):
        """Update QLabel dengan frame terbaru (main thread)."""
        if self._is_playing:
            self._video_label.setPixmap(pixmap)

    # ── Mouse: drag & resize ──────────────────────────────────────────────────

    def _get_resize_edge(self, pos: QPoint) -> str | None:
        m = RESIZE_MARGIN
        w, h = self.width(), self.height()
        x, y = pos.x(), pos.y()
        left, right = x <= m, x >= w - m
        top, bottom = y <= m, y >= h - m
        if top and left:     return "top-left"
        if top and right:    return "top-right"
        if bottom and left:  return "bottom-left"
        if bottom and right: return "bottom-right"
        if top:    return "top"
        if bottom: return "bottom"
        if left:   return "left"
        if right:  return "right"
        return None

    _CURSOR_MAP = {
        "top-left": Qt.CursorShape.SizeFDiagCursor,
        "bottom-right": Qt.CursorShape.SizeFDiagCursor,
        "top-right": Qt.CursorShape.SizeBDiagCursor,
        "bottom-left": Qt.CursorShape.SizeBDiagCursor,
        "top": Qt.CursorShape.SizeVerCursor,
        "bottom": Qt.CursorShape.SizeVerCursor,
        "left": Qt.CursorShape.SizeHorCursor,
        "right": Qt.CursorShape.SizeHorCursor,
    }

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position().toPoint()
            edge = self._get_resize_edge(pos)
            if edge:
                self._resize_edge = edge
                self._resize_start_pos = event.globalPosition().toPoint()
                self._resize_start_geom = QRect(self.geometry())
            elif pos.y() <= TITLE_H:
                self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        pos = event.position().toPoint()
        if event.buttons() == Qt.MouseButton.LeftButton:
            if self._resize_edge and self._resize_start_pos and self._resize_start_geom:
                self._do_resize(event.globalPosition().toPoint())
            elif self._drag_pos is not None:
                self.move(event.globalPosition().toPoint() - self._drag_pos)
        else:
            edge = self._get_resize_edge(pos)
            self.setCursor(self._CURSOR_MAP.get(edge, Qt.CursorShape.ArrowCursor))
        event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        self._resize_edge = None
        self._resize_start_pos = None
        self._resize_start_geom = None

    def _do_resize(self, global_pos: QPoint):
        delta = global_pos - self._resize_start_pos
        geom = QRect(self._resize_start_geom)
        edge = self._resize_edge
        if "right" in edge:  geom.setRight(geom.right() + delta.x())
        if "left" in edge:   geom.setLeft(geom.left() + delta.x())
        if "bottom" in edge: geom.setBottom(geom.bottom() + delta.y())
        if "top" in edge:    geom.setTop(geom.top() + delta.y())
        if geom.width() < MIN_WIDTH:
            geom.setLeft(geom.right() - MIN_WIDTH) if "left" in edge else geom.setRight(geom.left() + MIN_WIDTH)
        if geom.height() < MIN_HEIGHT:
            geom.setTop(geom.bottom() - MIN_HEIGHT) if "top" in edge else geom.setBottom(geom.top() + MIN_HEIGHT)
        self.setGeometry(geom)

    # ── Keyboard ──────────────────────────────────────────────────────────────

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self._close_window()
        else:
            super().keyPressEvent(event)

    # ── Video control ─────────────────────────────────────────────────────────

    def _on_media_status(self, status: QMediaPlayer.MediaStatus):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            source = self._player.source()
            if source and source.isValid():
                self._player.setPosition(0)
                self._player.play()

    def show_preview(self):
        """Tampilkan chroma green untuk setup posisi di TikTok Live Studio."""
        self._stop_event.clear()
        self._is_playing = False
        self._player.stop()
        self._video_label.hide()
        self._video_label.clear()
        self._title_bar.show()
        self.show()
        self.raise_()
        self.update()

    def show_product(self, video_path: str):
        """Tampilkan video produk. HARUS dipanggil dari Qt main thread."""
        # Telemetry — scene_triggered event
        try:
            from modules_client.telemetry import capture as _tel_capture
            _tel_capture("scene_triggered", {
                "scene_id": getattr(self, '_tel_scene_id', 0),
                "scene_name": getattr(self, '_tel_scene_name', ''),
            })
        except Exception:
            pass

        if not os.path.exists(video_path):
            logger.warning(f"ProductPopupWindow: file tidak ditemukan: {video_path}")
            return

        self._stop_event.set()
        if self._watcher_thread and self._watcher_thread.is_alive():
            self._watcher_thread.join(timeout=1.0)
        self._stop_event.clear()

        self._is_playing = True
        self._title_bar.hide()
        self._video_label.clear()
        self._video_label.setGeometry(0, 0, self.width(), self.height())
        self._video_label.show()

        self._player.stop()
        self._player.setSource(QUrl.fromLocalFile(os.path.abspath(video_path)))
        self.show()
        self._player.play()
        self._start_tts_watcher()

    def _start_tts_watcher(self):
        """Deteksi TTS selesai → hide. Jika mixer belum init, user tutup manual."""
        def watch():
            import time
            time.sleep(1.0)
            try:
                import pygame
                if not pygame.mixer.get_init():
                    return
                while not self._stop_event.is_set():
                    if not pygame.mixer.music.get_busy():
                        break
                    time.sleep(0.2)
            except Exception:
                return
            if not self._stop_event.is_set():
                self._hide_requested.emit()

        self._watcher_thread = threading.Thread(target=watch, daemon=True)
        self._watcher_thread.start()

    @pyqtSlot()
    def _do_hide(self):
        self._player.stop()
        self._is_playing = False
        self._video_label.hide()
        self._video_label.clear()
        self._title_bar.show()
        self.hide()
        self.update()

    def _close_window(self):
        # Telemetry — scene_dismissed event
        try:
            from modules_client.telemetry import capture as _tel_capture
            _tel_capture("scene_dismissed", {
                "scene_id": getattr(self, '_tel_scene_id', 0),
            })
        except Exception:
            pass

        self._stop_event.set()
        self._player.stop()
        self._is_playing = False
        self._video_label.hide()
        self._video_label.clear()
        self._title_bar.show()
        self.hide()
        self.update()

    def closeEvent(self, event):
        # Telemetry — scene_dismissed event
        try:
            from modules_client.telemetry import capture as _tel_capture
            _tel_capture("scene_dismissed", {
                "scene_id": getattr(self, '_tel_scene_id', 0),
            })
        except Exception:
            pass

        self._stop_event.set()
        self._player.stop()
        super().closeEvent(event)

    def resize_popup(self, width: int, height: int):
        self.resize(width, min(height, 1080))
