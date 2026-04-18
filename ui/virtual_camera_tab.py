# ui/virtual_camera_tab.py — Virtual Camera Tab UI
"""
Tab UI untuk mengelola virtual camera: playlist video, mode playback,
dan kontrol start/stop streaming ke virtual camera device.
"""

import logging
import os

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QButtonGroup,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QRadioButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from modules_client.i18n import t

try:
    from ui.theme import (
        ACCENT,
        BG_BASE,
        BG_ELEVATED,
        BG_SURFACE,
        BORDER,
        CARD_STYLE,
        ERROR,
        HEADER_FRAME_STYLE,
        PRIMARY,
        RADIUS,
        SUCCESS,
        TEXT_MUTED,
        TEXT_PRIMARY,
        WARNING,
        btn_danger,
        btn_ghost,
        btn_primary,
        btn_secondary,
        btn_success,
        label_subtitle,
        label_title,
        status_badge,
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

logger = logging.getLogger("VocaLive")

MAX_PLAYLIST = 10


class VirtualCameraTab(QWidget):
    """Tab untuk mengelola virtual camera playlist dan streaming."""

    def __init__(self, manager=None, parent=None):
        super().__init__(parent)
        self.manager = manager
        self._init_ui()
        self._connect_signals()
        self._detect_backend_on_init()

    # -----------------------------------------------------------------
    # UI setup
    # -----------------------------------------------------------------

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # -- Header --
        header_frame = QFrame()
        header_frame.setStyleSheet(HEADER_FRAME_STYLE)
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(16, 12, 16, 12)

        title = QLabel(t("camera.title"))
        title.setStyleSheet(label_title(16))
        header_layout.addWidget(title)

        subtitle = QLabel(t("camera.subtitle"))
        subtitle.setStyleSheet(label_subtitle(11))
        header_layout.addWidget(subtitle)

        layout.addWidget(header_frame)

        # -- Status card --
        status_card = QFrame()
        status_card.setStyleSheet(CARD_STYLE)
        status_layout = QHBoxLayout(status_card)
        status_layout.setContentsMargins(16, 12, 16, 12)

        status_label = QLabel(t("camera.label.status"))
        status_label.setStyleSheet(f"color: {TEXT_MUTED}; font-weight: 600; background: transparent;")
        status_layout.addWidget(status_label)

        self.status_indicator = QLabel(t("camera.status.stopped"))
        self.status_indicator.setStyleSheet(status_badge(TEXT_MUTED, size=13))
        status_layout.addWidget(self.status_indicator)

        status_layout.addStretch()

        backend_label = QLabel(t("camera.label.backend"))
        backend_label.setStyleSheet(f"color: {TEXT_MUTED}; font-weight: 600; background: transparent;")
        status_layout.addWidget(backend_label)

        self.backend_indicator = QLabel(t("camera.status.detecting"))
        self.backend_indicator.setStyleSheet(status_badge(ACCENT, size=13))
        status_layout.addWidget(self.backend_indicator)

        layout.addWidget(status_card)

        # -- Driver install panel (hidden by default) --
        self.driver_panel = QFrame()
        self.driver_panel.setStyleSheet(
            f"QFrame {{ background-color: {BG_ELEVATED}; border: 1px solid {WARNING}; border-radius: 10px; }}"
        )
        driver_layout = QVBoxLayout(self.driver_panel)
        driver_layout.setContentsMargins(16, 12, 16, 12)

        driver_title = QLabel(t("camera.driver.title"))
        driver_title.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {WARNING}; background: transparent;")
        driver_layout.addWidget(driver_title)

        driver_desc = QLabel(t("camera.driver.desc"))
        driver_desc.setStyleSheet(f"font-size: 11px; color: {TEXT_MUTED}; background: transparent;")
        driver_desc.setWordWrap(True)
        driver_layout.addWidget(driver_desc)

        self.driver_panel.setVisible(False)
        layout.addWidget(self.driver_panel)

        # -- Playlist table --
        playlist_card = QFrame()
        playlist_card.setStyleSheet(CARD_STYLE)
        playlist_layout = QVBoxLayout(playlist_card)
        playlist_layout.setContentsMargins(12, 12, 12, 12)

        playlist_header = QHBoxLayout()
        playlist_title = QLabel(t("camera.playlist.title"))
        playlist_title.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {TEXT_PRIMARY}; background: transparent;")
        playlist_header.addWidget(playlist_title)

        playlist_header.addStretch()

        self.btn_add_video = QPushButton(t("camera.btn.add_video"))
        self.btn_add_video.setStyleSheet(btn_primary("font-size: 12px;"))
        self.btn_add_video.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_add_video.clicked.connect(self._add_videos)
        playlist_header.addWidget(self.btn_add_video)

        playlist_layout.addLayout(playlist_header)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels([
            t("camera.table.col.no"),
            t("camera.table.col.video"),
            t("camera.table.col.remove"),
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 40)
        self.table.setColumnWidth(2, 70)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet(
            f"QTableWidget {{ background-color: {BG_SURFACE}; color: {TEXT_PRIMARY}; "
            f"border: 1px solid {BORDER}; border-radius: 6px; gridline-color: {BORDER}; }}"
            f"QHeaderView::section {{ background-color: {BG_ELEVATED}; color: {TEXT_MUTED}; "
            f"border: none; padding: 6px; font-weight: 600; }}"
        )
        playlist_layout.addWidget(self.table)

        layout.addWidget(playlist_card)

        # -- Mode selection --
        mode_layout = QHBoxLayout()
        mode_label = QLabel(t("camera.label.play_mode"))
        mode_label.setStyleSheet(f"color: {TEXT_MUTED}; font-weight: 600; background: transparent;")
        mode_layout.addWidget(mode_label)

        self.radio_sequential = QRadioButton(t("camera.mode.sequential"))
        self.radio_sequential.setChecked(True)
        self.radio_sequential.setStyleSheet(f"QRadioButton {{ color: {TEXT_PRIMARY}; background: transparent; }}")
        mode_layout.addWidget(self.radio_sequential)

        self.radio_random = QRadioButton(t("camera.mode.random"))
        self.radio_random.setStyleSheet(f"QRadioButton {{ color: {TEXT_PRIMARY}; background: transparent; }}")
        mode_layout.addWidget(self.radio_random)

        self.mode_group = QButtonGroup(self)
        self.mode_group.addButton(self.radio_sequential)
        self.mode_group.addButton(self.radio_random)
        self.mode_group.buttonClicked.connect(self._on_mode_changed)

        mode_layout.addStretch()
        layout.addLayout(mode_layout)

        # -- Control buttons --
        ctrl_layout = QHBoxLayout()

        self.btn_play = QPushButton(t("camera.btn.play"))
        self.btn_play.setStyleSheet(btn_success("font-size: 13px; padding: 10px 24px;"))
        self.btn_play.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_play.clicked.connect(self._on_play)
        ctrl_layout.addWidget(self.btn_play)

        self.btn_stop = QPushButton(t("camera.btn.stop"))
        self.btn_stop.setStyleSheet(btn_danger("font-size: 13px; padding: 10px 24px;"))
        self.btn_stop.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self._on_stop)
        ctrl_layout.addWidget(self.btn_stop)

        self.btn_next = QPushButton(t("camera.btn.next"))
        self.btn_next.setStyleSheet(btn_primary("font-size: 13px; padding: 10px 24px;"))
        self.btn_next.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_next.setEnabled(False)
        self.btn_next.clicked.connect(self._on_next)
        ctrl_layout.addWidget(self.btn_next)

        ctrl_layout.addStretch()
        layout.addLayout(ctrl_layout)

        layout.addStretch()

    # -----------------------------------------------------------------
    # Signal connections
    # -----------------------------------------------------------------

    def _connect_signals(self):
        if self.manager is None:
            return
        self.manager.statusChanged.connect(self._on_status_changed)
        self.manager.errorOccurred.connect(self._on_error)
        self.manager.videoChanged.connect(self._on_video_changed)
        self.manager.playbackStopped.connect(self._on_playback_stopped)

    # -----------------------------------------------------------------
    # Backend detection
    # -----------------------------------------------------------------

    def _detect_backend_on_init(self):
        if self.manager is None:
            self.backend_indicator.setText(t("camera.status.no_manager"))
            return
        backend = self.manager.detect_backend()
        if backend:
            # Backend id (internal: "obs"/"unity") displayed uppercase — technical value, not translated
            self.backend_indicator.setText(backend.upper())
            self.backend_indicator.setStyleSheet(status_badge(SUCCESS, size=13))
            self.driver_panel.setVisible(False)
        else:
            self.backend_indicator.setText(t("camera.status.none"))
            self.backend_indicator.setStyleSheet(status_badge(ERROR, size=13))
            self.driver_panel.setVisible(True)

    # -----------------------------------------------------------------
    # Table refresh
    # -----------------------------------------------------------------

    def _refresh_table(self):
        if self.manager is None:
            return
        playlist = self.manager.playlist
        self.table.setRowCount(len(playlist))
        for i, path in enumerate(playlist):
            # No column
            no_item = QTableWidgetItem(str(i + 1))
            no_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(i, 0, no_item)

            # Filename column
            filename = os.path.basename(path)
            self.table.setItem(i, 1, QTableWidgetItem(filename))

            # Delete button
            btn_del = QPushButton(t("camera.btn.remove"))
            btn_del.setStyleSheet(btn_danger("font-size: 11px; padding: 4px 8px;"))
            btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_del.clicked.connect(lambda checked, idx=i: self._remove_video(idx))
            self.table.setCellWidget(i, 2, btn_del)

    # -----------------------------------------------------------------
    # Slot handlers
    # -----------------------------------------------------------------

    def _on_status_changed(self, status: str):
        # Status string di-emit manager (bahasa internal, belum lewat i18n).
        # Substring check berdasarkan keyword internal — aman meski string diterjemahkan
        # di masa depan karena label tetap menampilkan raw status text dari manager.
        self.status_indicator.setText(status)
        lower = status.lower()
        if "aktif" in lower or "streaming" in lower or "running" in lower:
            self.status_indicator.setStyleSheet(status_badge(SUCCESS, size=13))
        elif "stop" in lower:
            self.status_indicator.setStyleSheet(status_badge(TEXT_MUTED, size=13))
        else:
            self.status_indicator.setStyleSheet(status_badge(ACCENT, size=13))

    def _on_error(self, error_msg: str):
        self.status_indicator.setText(t("camera.status.error", message=error_msg))
        self.status_indicator.setStyleSheet(status_badge(ERROR, size=13))
        if "no_driver" in error_msg.lower() or "backend" in error_msg.lower():
            self.driver_panel.setVisible(True)

    def _on_video_changed(self, index: int, filename: str):
        """Highlight current row in table."""
        for row in range(self.table.rowCount()):
            for col in range(2):  # skip button column
                item = self.table.item(row, col)
                if item:
                    if row == index:
                        item.setBackground(Qt.GlobalColor.transparent)
                        item.setForeground(Qt.GlobalColor.white)
                    else:
                        item.setForeground(Qt.GlobalColor.white)
        self.table.selectRow(index)

    def _on_playback_stopped(self):
        self.btn_play.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.btn_next.setEnabled(False)
        self.status_indicator.setText(t("camera.status.stopped"))
        self.status_indicator.setStyleSheet(status_badge(TEXT_MUTED, size=13))

    def _on_play(self):
        if self.manager is None:
            return
        self.btn_play.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.btn_next.setEnabled(True)
        self.manager.start()

    def _on_stop(self):
        if self.manager is None:
            return
        self.manager.request_stop()

    def _on_next(self):
        if self.manager is None:
            return
        self.manager.skip_to_next()

    def _add_videos(self):
        if self.manager is None:
            return
        current_count = len(self.manager.playlist)
        remaining = MAX_PLAYLIST - current_count
        if remaining <= 0:
            return

        files, _ = QFileDialog.getOpenFileNames(
            self, t("camera.dialog.pick_video"), "", t("camera.dialog.video_filter")
        )
        if not files:
            return

        new_playlist = self.manager.playlist + files[:remaining]
        self.manager.set_playlist(new_playlist)
        self.manager.save_config()
        self._refresh_table()

    def _remove_video(self, index: int):
        if self.manager is None:
            return
        playlist = list(self.manager.playlist)
        if 0 <= index < len(playlist):
            playlist.pop(index)
            self.manager.set_playlist(playlist)
            self.manager.save_config()
            self._refresh_table()

    def _on_mode_changed(self, button):
        if self.manager is None:
            return
        if button == self.radio_sequential:
            self.manager.set_play_mode("sequential")
        else:
            self.manager.set_play_mode("random")
        self.manager.save_config()
