"""
ProductSceneTab - Tab UI untuk kelola daftar produk video overlay.
User mendaftarkan nama produk + file video MP4 lokal.
"""

import os
import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog,
    QSpinBox, QFrame, QMessageBox, QAbstractItemView,
    QDialog, QLineEdit, QDialogButtonBox
)
from PyQt6.QtCore import Qt, pyqtSlot

try:
    from ui.theme import (
        PRIMARY, BG_BASE, BG_SURFACE, BG_ELEVATED, TEXT_PRIMARY, TEXT_MUTED,
        BORDER, BORDER_GOLD, SUCCESS, ERROR, WARNING, RADIUS,
        btn_success, btn_danger, btn_ghost, btn_secondary,
        label_title, label_subtitle, CARD_STYLE
    )
except ImportError:
    PRIMARY = "#2563EB"; BG_BASE = "#0F1623"; BG_SURFACE = "#162032"
    BG_ELEVATED = "#1E2A3B"; TEXT_PRIMARY = "#F0F6FF"; TEXT_MUTED = "#93C5FD"
    BORDER = "#1A2E4A"; BORDER_GOLD = "#1E4585"; SUCCESS = "#22C55E"
    ERROR = "#EF4444"; WARNING = "#F59E0B"; RADIUS = "10px"
    CARD_STYLE = f"QFrame {{ background-color: {BG_SURFACE}; border: 1px solid {BORDER}; border-radius: 10px; }}"
    def btn_success(e=""): return f"QPushButton {{ background-color: {SUCCESS}; color: white; border: none; border-radius: 6px; padding: 8px 16px; font-weight: 700; {e} }}"
    def btn_danger(e=""): return f"QPushButton {{ background-color: {ERROR}; color: white; border: none; border-radius: 6px; padding: 8px 16px; font-weight: 700; {e} }}"
    def btn_ghost(e=""): return f"QPushButton {{ background-color: {BG_ELEVATED}; color: {TEXT_MUTED}; border: 1px solid {BORDER}; border-radius: 6px; padding: 7px 16px; {e} }}"
    def btn_secondary(e=""): return f"QPushButton {{ background-color: transparent; color: {PRIMARY}; border: 1px solid {PRIMARY}; border-radius: 6px; padding: 7px 16px; font-weight: 600; {e} }}"
    def label_title(s=16): return f"font-size: {s}pt; font-weight: 700; color: {PRIMARY}; background: transparent;"
    def label_subtitle(s=11): return f"font-size: {s}px; color: {TEXT_MUTED}; background: transparent;"

logger = logging.getLogger('VocaLive.ProductSceneTab')

from modules_client.product_scene_manager import ProductSceneManager


class AddProductDialog(QDialog):
    """Dialog untuk menambah produk baru — user isi nama manual + pilih file video."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Tambah Produk Baru")
        self.setMinimumWidth(480)
        self.setModal(True)
        self._video_path = ""
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(20, 20, 20, 20)

        # Nama produk
        layout.addWidget(QLabel("Nama Produk:"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Contoh: Celana Jeans Slim Fit Premium")
        self.name_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {BG_SURFACE};
                color: {TEXT_PRIMARY};
                border: 1px solid {BORDER};
                border-radius: 6px;
                padding: 8px 10px;
                font-size: 13px;
            }}
            QLineEdit:focus {{ border-color: {PRIMARY}; }}
        """)
        layout.addWidget(self.name_input)

        # File video
        layout.addWidget(QLabel("File Video:"))
        video_row = QHBoxLayout()
        self.video_label = QLabel("Belum ada file dipilih")
        self.video_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px; padding: 2px;")
        self.video_label.setWordWrap(True)

        btn_browse = QPushButton("📁 Pilih File")
        btn_browse.setStyleSheet(btn_secondary("font-size: 12px; padding: 7px 14px;"))
        btn_browse.clicked.connect(self._browse_video)

        video_row.addWidget(self.video_label, 1)
        video_row.addWidget(btn_browse)
        layout.addLayout(video_row)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Save).setText("Simpan")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Batal")
        buttons.button(QDialogButtonBox.StandardButton.Save).setStyleSheet(btn_success())
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setStyleSheet(btn_ghost())
        buttons.accepted.connect(self._on_save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setStyleSheet(f"QDialog {{ background-color: {BG_BASE}; }} QLabel {{ color: {TEXT_PRIMARY}; font-size: 12px; }}")

    @pyqtSlot()
    def _browse_video(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Pilih File Video Produk", "",
            "Video Files (*.mp4 *.avi *.mov *.mkv *.webm);;All Files (*)"
        )
        if path:
            self._video_path = path
            self.video_label.setText(os.path.basename(path))
            self.video_label.setToolTip(path)
            self.video_label.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 12px; padding: 2px;")

    @pyqtSlot()
    def _on_save(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Nama Kosong", "Nama produk tidak boleh kosong.")
            return
        if not self._video_path:
            QMessageBox.warning(self, "File Belum Dipilih", "Pilih file video terlebih dahulu.")
            return
        self.accept()

    def get_result(self) -> tuple[str, str]:
        """Kembalikan (nama_produk, video_path)."""
        return self.name_input.text().strip(), self._video_path


class ProductSceneTab(QWidget):
    """Tab untuk kelola daftar produk video popup."""

    def __init__(self, popup_window=None, parent=None):
        super().__init__(parent)
        self._psm = ProductSceneManager()
        self._popup_window = popup_window  # ProductPopupWindow reference
        self._build_ui()
        self._load_table()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Header
        title = QLabel("Product Scene Manager")
        title.setStyleSheet(label_title(16))
        subtitle = QLabel(
            "Daftarkan produk dan file video MP4. "
            "AI akan memilih scene yang sesuai saat menjelaskan produk."
        )
        subtitle.setStyleSheet(label_subtitle(11))
        subtitle.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(subtitle)

        # Toolbar
        toolbar = QHBoxLayout()
        self.btn_add = QPushButton("+ Tambah Produk")
        self.btn_add.setStyleSheet(btn_success())
        self.btn_add.clicked.connect(self._add_scene)

        self.btn_remove = QPushButton("Hapus")
        self.btn_remove.setStyleSheet(btn_danger())
        self.btn_remove.clicked.connect(self._remove_selected)

        self.btn_test = QPushButton("▶ Test Tampilkan")
        self.btn_test.setStyleSheet(btn_secondary())
        self.btn_test.clicked.connect(self._test_selected)

        self.btn_preview = QPushButton("Preview Window")
        self.btn_preview.setStyleSheet(btn_ghost())
        self.btn_preview.clicked.connect(self._open_preview)

        # Toggle ON/OFF fitur product popup
        self.btn_toggle = QPushButton()
        self.btn_toggle.setFixedWidth(120)
        self.btn_toggle.clicked.connect(self._toggle_enabled)

        toolbar.addWidget(self.btn_add)
        toolbar.addWidget(self.btn_remove)
        toolbar.addWidget(self.btn_test)
        toolbar.addWidget(self.btn_preview)
        toolbar.addStretch()
        toolbar.addWidget(self.btn_toggle)
        layout.addLayout(toolbar)

        self._refresh_toggle_btn()

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["No", "Nama Produk", "File Video"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked)
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {BG_SURFACE};
                color: {TEXT_PRIMARY};
                border: 1px solid {BORDER_GOLD};
                border-radius: 8px;
                gridline-color: {BORDER};
                font-size: 12px;
            }}
            QTableWidget::item {{ padding: 8px 6px; }}
            QTableWidget::item:selected {{ background-color: {PRIMARY}; color: white; }}
            QHeaderView::section {{
                background-color: {BG_ELEVATED};
                color: {TEXT_MUTED};
                border: none;
                border-bottom: 1px solid {BORDER_GOLD};
                padding: 8px 6px;
                font-weight: 600;
            }}
        """)
        self.table.itemChanged.connect(self._on_cell_edited)
        layout.addWidget(self.table)

        # Popup size settings
        size_frame = QFrame()
        size_frame.setStyleSheet(CARD_STYLE)
        size_layout = QHBoxLayout(size_frame)
        size_layout.setContentsMargins(16, 12, 16, 12)

        size_layout.addWidget(QLabel("Ukuran Popup:"))

        size_layout.addWidget(QLabel("Lebar:"))
        self.spin_width = QSpinBox()
        self.spin_width.setRange(200, 1920)
        self.spin_width.setSuffix(" px")
        self.spin_width.valueChanged.connect(self._on_size_changed)

        size_layout.addWidget(self.spin_width)
        size_layout.addWidget(QLabel("Tinggi (max 1080):"))

        self.spin_height = QSpinBox()
        self.spin_height.setRange(400, 1080)
        self.spin_height.setSuffix(" px")
        self.spin_height.valueChanged.connect(self._on_size_changed)

        size_layout.addWidget(self.spin_height)
        size_layout.addStretch()

        info = QLabel("Setup TikTok Live Studio: Window Capture → 'VocaLive Product Display'")
        info.setStyleSheet(f"color: {WARNING}; font-size: 11px;")
        size_layout.addWidget(info)

        layout.addWidget(size_frame)

        # Load current size
        w, h = self._psm.get_popup_size()
        self.spin_width.blockSignals(True)
        self.spin_height.blockSignals(True)
        self.spin_width.setValue(w)
        self.spin_height.setValue(h)
        self.spin_width.blockSignals(False)
        self.spin_height.blockSignals(False)

    def _load_table(self):
        """Refresh tabel dari ProductSceneManager."""
        self.table.blockSignals(True)
        scenes = self._psm.get_scenes()
        self.table.setRowCount(len(scenes))
        for row, scene in enumerate(scenes):
            self.table.setItem(row, 0, QTableWidgetItem(str(scene["id"])))
            self.table.setItem(row, 1, QTableWidgetItem(scene.get("name", "")))
            path_item = QTableWidgetItem(scene.get("video_path", ""))
            path_item.setToolTip(scene.get("video_path", ""))
            self.table.setItem(row, 2, path_item)
            # Kolom No tidak editable
            no_item = self.table.item(row, 0)
            if no_item:
                no_item.setFlags(no_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.table.blockSignals(False)

    @pyqtSlot()
    def _add_scene(self):
        """Tambah produk baru — dialog user isi nama manual + pilih video."""
        from modules_client.product_scene_manager import ProductSceneManager
        if len(self._psm.get_scenes()) >= ProductSceneManager.MAX_SCENES:
            QMessageBox.warning(
                self, "Batas Maksimal",
                f"Maksimal {ProductSceneManager.MAX_SCENES} produk. Hapus produk lama sebelum menambah baru."
            )
            return
        dialog = AddProductDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        name, video_path = dialog.get_result()
        self._psm.add_scene(name, video_path)
        self._load_table()

    @pyqtSlot()
    def _remove_selected(self):
        """Hapus baris yang dipilih."""
        row = self.table.currentRow()
        if row < 0:
            return
        id_item = self.table.item(row, 0)
        if not id_item:
            return
        try:
            scene_id = int(id_item.text())
        except ValueError:
            return
        reply = QMessageBox.question(
            self, "Konfirmasi Hapus",
            f"Hapus produk ID {scene_id}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._psm.remove_scene(scene_id)
            self._load_table()

    @pyqtSlot()
    def _test_selected(self):
        """Test tampilkan popup dengan video produk yang dipilih."""
        if self._popup_window is None:
            QMessageBox.warning(self, "Error", "Popup window belum diinisialisasi.")
            return
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Info", "Pilih produk dari tabel terlebih dahulu.")
            return
        id_item = self.table.item(row, 0)
        if not id_item:
            return
        try:
            scene_id = int(id_item.text())
        except ValueError:
            return
        scene = self._psm.get_scene_by_id(scene_id)
        if not scene or not scene.get("video_path"):
            QMessageBox.warning(self, "Error", "File video belum dipilih untuk produk ini.")
            return
        self._popup_window.show_product(scene["video_path"])

    @pyqtSlot()
    def _open_preview(self):
        """Buka popup window dalam mode preview — bisa dipanggil berkali-kali."""
        if self._popup_window is None:
            QMessageBox.warning(self, "Error", "Popup window belum diinisialisasi.")
            return
        self._popup_window.show_preview()

    def _refresh_toggle_btn(self):
        """Update tampilan tombol toggle sesuai state enabled."""
        enabled = self._psm.get_enabled()
        if enabled:
            self.btn_toggle.setText("● Popup Aktif")
            self.btn_toggle.setStyleSheet(btn_success("font-size: 12px; font-weight: 700;"))
        else:
            self.btn_toggle.setText("○ Popup Mati")
            self.btn_toggle.setStyleSheet(
                f"QPushButton {{ background-color: {BG_ELEVATED}; color: {TEXT_MUTED}; "
                f"border: 1px solid {BORDER}; border-radius: 6px; padding: 8px 16px; "
                f"font-size: 12px; font-weight: 700; }}"
                f"QPushButton:hover {{ background-color: {SUCCESS}; color: white; }}"
            )

    @pyqtSlot()
    def _toggle_enabled(self):
        """Toggle ON/OFF fitur product popup."""
        new_state = not self._psm.get_enabled()
        self._psm.set_enabled(new_state)
        self._refresh_toggle_btn()

    @pyqtSlot()
    def _on_size_changed(self):
        """Simpan dan apply ukuran popup."""
        w = self.spin_width.value()
        h = self.spin_height.value()
        self._psm.set_popup_size(w, h)
        if self._popup_window is not None:
            self._popup_window.resize_popup(w, h)

    @pyqtSlot(QTableWidgetItem)
    def _on_cell_edited(self, item: QTableWidgetItem):
        """Simpan perubahan nama produk atau path video dari tabel."""
        row = item.row()
        col = item.column()
        id_item = self.table.item(row, 0)
        if not id_item:
            return
        try:
            scene_id = int(id_item.text())
        except ValueError:
            return
        if col == 1:  # Nama produk
            self._psm.update_scene(scene_id, name=item.text())
        elif col == 2:  # Path video
            self._psm.update_scene(scene_id, video_path=item.text())
