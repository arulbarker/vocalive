#!/usr/bin/env python3
"""
VocaLive - Update Dialog
Dialog download & install update dengan progress bar.
"""

import os
import sys
import tempfile
from typing import Optional

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QTextEdit, QFrame, QApplication
)
from PyQt6.QtGui import QFont

try:
    from modules_client.updater import DownloadThread, install_update, CURRENT_VERSION
except ImportError:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from modules_client.updater import DownloadThread, install_update, CURRENT_VERSION

# Ocean Blue palette
C_BG       = "#0F1623"
C_SURFACE  = "#162032"
C_ELEVATED = "#1E2A3B"
C_PRIMARY  = "#2563EB"
C_ACCENT   = "#60A5FA"
C_SECONDARY= "#1E3A5F"
C_TEXT     = "#F0F6FF"
C_MUTED    = "#8BAED0"
C_SUCCESS  = "#22C55E"
RADIUS     = "10px"


class UpdateDialog(QDialog):
    """Dialog update VocaLive — download + install."""

    def __init__(self, update_info: dict, parent=None):
        super().__init__(parent)
        self.update_info = update_info
        self.download_thread: Optional[DownloadThread] = None
        self.zip_path: Optional[str] = None

        self.setWindowTitle("VocaLive — Update Tersedia")
        self.setFixedSize(480, 420)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowCloseButtonHint)
        self.setModal(True)
        self.setStyleSheet(f"QDialog {{ background-color: {C_BG}; }} QLabel {{ color: {C_TEXT}; }}")

        self._build_ui()
        self._center()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(16)

        # Header card
        header = QFrame()
        header.setStyleSheet(f"QFrame {{ background: {C_SURFACE}; border-radius: {RADIUS}; }}")
        hl = QVBoxLayout(header)
        hl.setContentsMargins(16, 14, 16, 14)
        hl.setSpacing(6)

        top_row = QHBoxLayout()
        icon = QLabel("⬆️")
        icon.setStyleSheet("font-size: 28px;")
        top_row.addWidget(icon)

        ver_col = QVBoxLayout()
        ver_col.setSpacing(2)
        ver_title = QLabel("Update Tersedia!")
        ver_title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        ver_title.setStyleSheet(f"color: {C_ACCENT};")
        ver_col.addWidget(ver_title)

        latest = self.update_info.get("latest", "?")
        ver_sub = QLabel(f"v{CURRENT_VERSION}  →  v{latest}")
        ver_sub.setFont(QFont("Segoe UI", 10))
        ver_sub.setStyleSheet(f"color: {C_MUTED};")
        ver_col.addWidget(ver_sub)

        top_row.addLayout(ver_col)
        top_row.addStretch()
        hl.addLayout(top_row)

        notes_lbl = QLabel("Apa yang baru:")
        notes_lbl.setFont(QFont("Segoe UI", 9, QFont.Weight.Medium))
        notes_lbl.setStyleSheet(f"color: {C_MUTED}; margin-top: 4px;")
        hl.addWidget(notes_lbl)

        notes = QTextEdit()
        notes.setReadOnly(True)
        notes.setMaximumHeight(90)
        notes.setFont(QFont("Segoe UI", 9))
        notes.setPlainText(self.update_info.get("notes", "-"))
        notes.setStyleSheet(f"""
            QTextEdit {{
                background: {C_ELEVATED};
                border: 1px solid {C_SECONDARY};
                border-radius: 6px;
                padding: 6px;
                color: {C_TEXT};
            }}
        """)
        hl.addWidget(notes)
        root.addWidget(header)

        # Progress (hidden awalnya)
        self.progress_frame = QFrame()
        self.progress_frame.setStyleSheet(
            f"QFrame {{ background: {C_SURFACE}; border-radius: {RADIUS}; }}"
        )
        pl = QVBoxLayout(self.progress_frame)
        pl.setContentsMargins(16, 12, 16, 12)
        pl.setSpacing(6)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximumHeight(8)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: none; border-radius: 4px; background: {C_ELEVATED};
            }}
            QProgressBar::chunk {{
                border-radius: 4px;
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {C_PRIMARY}, stop:1 {C_ACCENT});
            }}
        """)
        pl.addWidget(self.progress_bar)

        self.progress_label = QLabel("Mengunduh update...")
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_label.setFont(QFont("Segoe UI", 9))
        self.progress_label.setStyleSheet(f"color: {C_MUTED};")
        pl.addWidget(self.progress_label)

        self.progress_frame.hide()
        root.addWidget(self.progress_frame)

        root.addStretch()

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self.btn_later = QPushButton("Nanti Saja")
        self.btn_later.setMinimumHeight(40)
        self.btn_later.setFont(QFont("Segoe UI", 10))
        self.btn_later.setStyleSheet(f"""
            QPushButton {{
                background: {C_ELEVATED}; border: 1px solid {C_SECONDARY};
                border-radius: 8px; color: {C_MUTED}; padding: 8px 16px;
            }}
            QPushButton:hover {{ background: {C_SECONDARY}; color: {C_TEXT}; }}
        """)
        self.btn_later.clicked.connect(self.reject)
        btn_row.addWidget(self.btn_later)

        self.btn_update = QPushButton("⬇️  Update Sekarang")
        self.btn_update.setMinimumHeight(40)
        self.btn_update.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.btn_update.setStyleSheet(f"""
            QPushButton {{
                background: {C_PRIMARY}; border: none;
                border-radius: 8px; color: white; padding: 8px 20px;
            }}
            QPushButton:hover {{ background: #1D4FD8; }}
            QPushButton:pressed {{ background: #1A44C0; }}
            QPushButton:disabled {{ background: {C_SECONDARY}; color: {C_MUTED}; }}
        """)
        self.btn_update.clicked.connect(self._start_download)
        btn_row.addWidget(self.btn_update)

        root.addLayout(btn_row)

    def _center(self):
        if self.parent():
            pg = self.parent().geometry()
            self.move(pg.x() + (pg.width() - self.width()) // 2,
                      pg.y() + (pg.height() - self.height()) // 2)
        else:
            screen = QApplication.primaryScreen().geometry()
            self.move((screen.width() - self.width()) // 2,
                      (screen.height() - self.height()) // 2)

    def _start_download(self):
        url = self.update_info.get("url", "")
        if not url:
            self._set_status("URL download tidak tersedia.", error=True)
            return

        self.btn_update.setEnabled(False)
        self.btn_later.setEnabled(False)
        self.progress_frame.show()
        self.setFixedSize(480, 460)

        fd, self.zip_path = tempfile.mkstemp(suffix=".zip", prefix="vocalive_update_")
        os.close(fd)

        self.download_thread = DownloadThread(url, self.zip_path)
        self.download_thread.progress.connect(self._on_progress)
        self.download_thread.finished.connect(self._on_download_done)
        self.download_thread.error.connect(self._on_error)
        self.download_thread.start()

    def _on_progress(self, pct: int):
        self.progress_bar.setValue(pct)
        self.progress_label.setText(f"Mengunduh... {pct}%")

    def _on_download_done(self, zip_path: str):
        self.progress_label.setText("Download selesai. Menginstall...")
        self.progress_bar.setValue(100)
        ok = install_update(zip_path)
        if ok:
            self.progress_label.setText("Update siap! Aplikasi akan restart otomatis.")
            self.progress_label.setStyleSheet(f"color: {C_SUCCESS}; font-weight: bold;")
            QTimer.singleShot(1500, self._quit_for_update)
        else:
            self._set_status("Gagal install. Coba jalankan sebagai Administrator.", error=True)
            self.btn_later.setEnabled(True)

    def _on_error(self, msg: str):
        self._set_status(f"Error: {msg}", error=True)
        self.btn_update.setEnabled(True)
        self.btn_later.setEnabled(True)

    def _set_status(self, msg: str, error: bool = False):
        self.progress_label.setText(msg)
        color = "#EF4444" if error else C_SUCCESS
        self.progress_label.setStyleSheet(f"color: {color};")
        self.progress_frame.show()

    def _quit_for_update(self):
        self.accept()
        QApplication.instance().quit()

    def closeEvent(self, event):
        if self.download_thread and self.download_thread.isRunning():
            self.download_thread.terminate()
            self.download_thread.wait()
        event.accept()


def show_update_dialog(update_info: dict, parent=None) -> None:
    dialog = UpdateDialog(update_info, parent)
    dialog.exec()
