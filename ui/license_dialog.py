#!/usr/bin/env python3
"""
VocaLive - Login Dialog (AppScript Edition)
User login dengan email pembelian (Lynk.id / Whop).
"""

import sys
import os
import time
import logging
from typing import Optional, Tuple

from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QProgressBar, QTextEdit, QFrame, QApplication, QGraphicsDropShadowEffect
)
from PyQt6.QtGui import QFont, QColor

logger = logging.getLogger('VocaLive.LicenseDialog')

try:
    from modules_client.license_manager import LicenseManager
except ImportError:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'modules_client'))
    from license_manager import LicenseManager

# Ocean Blue palette (dari CLAUDE.md)
C_BG       = "#0F1623"
C_SURFACE  = "#162032"
C_ELEVATED = "#1E2A3B"
C_PRIMARY  = "#2563EB"
C_ACCENT   = "#60A5FA"
C_SECONDARY= "#1E3A5F"
C_TEXT     = "#F0F6FF"
C_MUTED    = "#8BAED0"
C_SUCCESS  = "#22C55E"
C_DANGER   = "#EF4444"
RADIUS     = "10px"


class LoginWorker(QThread):
    """Worker thread — login via AppScript di background agar UI tidak freeze."""

    done = pyqtSignal(bool, str, dict)   # success, message, data
    progress = pyqtSignal(str)

    def __init__(self, email: str, license_manager: LicenseManager):
        super().__init__()
        self.email = email
        self.license_manager = license_manager

    def run(self):
        try:
            self.progress.emit("Menghubungi server lisensi...")
            time.sleep(0.4)

            is_valid, message, data = self.license_manager.validate_license_online(self.email)

            if is_valid:
                self.progress.emit("Menyimpan sesi...")
                time.sleep(0.3)
                if self.license_manager.save_license_data(self.email, data):
                    self.done.emit(True, message, data)
                else:
                    self.done.emit(False, "Gagal menyimpan data sesi.", {})
            else:
                self.done.emit(False, message, {})

        except Exception as e:
            self.done.emit(False, f"Error: {str(e)}", {})


class LicenseDialog(QDialog):
    """Dialog login email VocaLive — Ocean Blue theme."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.license_manager = LicenseManager()
        self.worker = None
        self._entered_email = ""

        self.setWindowTitle("VocaLive — Aktivasi Lisensi")
        self.setFixedSize(480, 560)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowCloseButtonHint)
        self.setModal(True)

        self.setStyleSheet(f"""
            QDialog {{
                background-color: {C_BG};
            }}
            QLabel {{
                color: {C_TEXT};
            }}
        """)

        self._build_ui()
        self._center()
        self.email_input.setFocus()

    # ------------------------------------------------------------------
    # UI Build
    # ------------------------------------------------------------------

    def _build_ui(self):
        root = QVBoxLayout()
        root.setContentsMargins(36, 32, 36, 28)
        root.setSpacing(20)

        root.addWidget(self._header())
        root.addWidget(self._input_card())
        root.addWidget(self._progress_section())
        root.addWidget(self._status_section())
        root.addWidget(self._buttons())

        self.setLayout(root)

    def _header(self) -> QFrame:
        f = QFrame()
        lay = QVBoxLayout(f)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.setSpacing(8)

        icon = QLabel("🎙️")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet("font-size: 44px;")
        lay.addWidget(icon)

        title = QLabel("VocaLive")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {C_ACCENT}; letter-spacing: 1px;")
        lay.addWidget(title)

        sub = QLabel("Masukkan email yang digunakan saat pembelian")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setFont(QFont("Segoe UI", 9))
        sub.setStyleSheet(f"color: {C_MUTED};")
        sub.setWordWrap(True)
        lay.addWidget(sub)

        return f

    def _input_card(self) -> QFrame:
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {C_SURFACE};
                border-radius: {RADIUS};
                padding: 4px;
            }}
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(16)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 100))
        card.setGraphicsEffect(shadow)

        lay = QVBoxLayout(card)
        lay.setSpacing(10)
        lay.setContentsMargins(20, 18, 20, 18)

        lbl = QLabel("Email Pembelian")
        lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.Medium))
        lbl.setStyleSheet(f"color: {C_ACCENT};")
        lay.addWidget(lbl)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("contoh@email.com")
        self.email_input.setMinimumHeight(44)
        self.email_input.setFont(QFont("Segoe UI", 11))
        self.email_input.setStyleSheet(f"""
            QLineEdit {{
                background: {C_ELEVATED};
                border: 2px solid {C_SECONDARY};
                border-radius: 8px;
                padding: 10px 14px;
                color: {C_TEXT};
            }}
            QLineEdit:focus {{
                border: 2px solid {C_PRIMARY};
            }}
        """)
        self.email_input.returnPressed.connect(self._start_login)
        lay.addWidget(self.email_input)

        hint = QLabel("💡 Email harus sama dengan yang dipakai di Lynk.id / Whop saat pembelian")
        hint.setFont(QFont("Segoe UI", 8))
        hint.setStyleSheet(f"color: {C_MUTED};")
        hint.setWordWrap(True)
        lay.addWidget(hint)

        return card

    def _progress_section(self) -> QFrame:
        self.progress_frame = QFrame()
        self.progress_frame.hide()
        lay = QVBoxLayout(self.progress_frame)
        lay.setSpacing(8)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setMaximumHeight(6)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                border-radius: 3px;
                background: {C_ELEVATED};
            }}
            QProgressBar::chunk {{
                border-radius: 3px;
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {C_PRIMARY}, stop:1 {C_ACCENT});
            }}
        """)
        lay.addWidget(self.progress_bar)

        self.progress_label = QLabel("Menghubungi server...")
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_label.setFont(QFont("Segoe UI", 9))
        self.progress_label.setStyleSheet(f"color: {C_MUTED};")
        lay.addWidget(self.progress_label)

        return self.progress_frame

    def _status_section(self) -> QFrame:
        self.status_frame = QFrame()
        self.status_frame.hide()
        lay = QVBoxLayout(self.status_frame)

        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(90)
        self.status_text.setReadOnly(True)
        self.status_text.setFont(QFont("Consolas", 9))
        self.status_text.setStyleSheet(f"""
            QTextEdit {{
                background: {C_ELEVATED};
                border: 1px solid {C_SECONDARY};
                border-radius: 6px;
                padding: 8px;
                color: {C_TEXT};
            }}
        """)
        lay.addWidget(self.status_text)
        return self.status_frame

    def _buttons(self) -> QFrame:
        f = QFrame()
        lay = QHBoxLayout(f)
        lay.setSpacing(12)

        self.btn_cancel = QPushButton("Batal")
        self.btn_cancel.setAutoDefault(False)
        self.btn_cancel.setMinimumHeight(42)
        self.btn_cancel.setFont(QFont("Segoe UI", 10))
        self.btn_cancel.setStyleSheet(f"""
            QPushButton {{
                background: {C_ELEVATED};
                border: 1px solid {C_SECONDARY};
                border-radius: 8px;
                color: {C_MUTED};
                padding: 10px 18px;
            }}
            QPushButton:hover {{ background: {C_SECONDARY}; color: {C_TEXT}; }}
        """)
        self.btn_cancel.clicked.connect(self.reject)
        lay.addWidget(self.btn_cancel)

        self.btn_login = QPushButton("Login")
        self.btn_login.setMinimumHeight(42)
        self.btn_login.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.btn_login.setStyleSheet(f"""
            QPushButton {{
                background: {C_PRIMARY};
                border: none;
                border-radius: 8px;
                color: white;
                padding: 10px 24px;
            }}
            QPushButton:hover {{ background: #1D4FD8; }}
            QPushButton:pressed {{ background: #1A44C0; }}
            QPushButton:disabled {{ background: {C_SECONDARY}; color: {C_MUTED}; }}
        """)
        self.btn_login.setDefault(True)
        self.btn_login.clicked.connect(self._start_login)
        lay.addWidget(self.btn_login)

        return f

    # ------------------------------------------------------------------
    # Logic
    # ------------------------------------------------------------------

    def _center(self):
        if self.parent():
            pg = self.parent().geometry()
            self.move(pg.x() + (pg.width() - self.width()) // 2,
                      pg.y() + (pg.height() - self.height()) // 2)
        else:
            screen = QApplication.primaryScreen().geometry()
            self.move((screen.width() - self.width()) // 2,
                      (screen.height() - self.height()) // 2)

    def _start_login(self):
        email = self.email_input.text().strip()
        if not email or "@" not in email:
            self._show_error("Masukkan email yang valid.")
            return

        self._entered_email = email
        self.email_input.setEnabled(False)
        self.btn_login.setEnabled(False)
        self.progress_frame.show()
        self.status_frame.show()
        self.status_text.clear()

        self.worker = LoginWorker(email, self.license_manager)
        self.worker.done.connect(self._on_done)
        self.worker.progress.connect(self._on_progress)
        self.worker.start()

    def _on_progress(self, msg: str):
        self.progress_label.setText(msg)
        self.status_text.append(f"• {msg}")
        self._scroll_status()

    def _on_done(self, success: bool, message: str, data: dict):
        self.progress_frame.hide()
        self.email_input.setEnabled(True)
        self.btn_login.setEnabled(True)

        if success:
            nama = data.get("nama", "")
            exp = data.get("expired_date", "")
            self.status_text.append(f"\n✅ Login berhasil! Selamat datang{', ' + nama if nama else ''}.")
            if exp:
                self.status_text.append(f"   Aktif hingga: {exp}")
            self._scroll_status()
            QTimer.singleShot(1400, self.accept)
        else:
            self._show_error(message)

    def _show_error(self, msg: str):
        self.status_frame.show()
        self.status_text.append(f"\n❌ {msg}")
        self._scroll_status()
        # Flash border merah
        orig = self.email_input.styleSheet()
        err = orig.replace(f"border: 2px solid {C_SECONDARY};", "border: 2px solid #EF4444;")
        self.email_input.setStyleSheet(err)
        QTimer.singleShot(1000, lambda: self.email_input.setStyleSheet(orig))

    def _scroll_status(self):
        cur = self.status_text.textCursor()
        cur.movePosition(cur.MoveOperation.End)
        self.status_text.setTextCursor(cur)

    def keyPressEvent(self, event):
        """Pastikan Enter selalu trigger login, tidak close dialog."""
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if self.btn_login.isEnabled():
                self._start_login()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()
        event.accept()


def show_license_dialog(parent=None) -> Tuple[bool, Optional[str]]:
    """Entry point dari main.py. Return (success, email)."""
    dialog = LicenseDialog(parent)
    result = dialog.exec()
    if result == QDialog.DialogCode.Accepted:
        return True, dialog._entered_email
    return False, None


# Quick test
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    ok, email = show_license_dialog()
    logger.info("[LicenseDialog] Result: ok=%s, email=%s", ok, email[:3] + "***" if email else "")
