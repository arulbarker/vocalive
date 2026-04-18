# ui/user_management_tab.py
"""
User Management Tab - Mengelola blacklist dan whitelist username
Fitur: tambah/hapus, search/filter real-time, import/export CSV
"""

import csv
import logging

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from modules_client.i18n import t

logger = logging.getLogger("VocaLive.UserManagement")

try:
    from modules_client.user_list_manager import get_user_list_manager
    USER_LIST_AVAILABLE = True
except ImportError:
    USER_LIST_AVAILABLE = False
    logger.warning("User list manager not available")

try:
    from ui.theme import (
        ACCENT,
        BG_BASE,
        BG_ELEVATED,
        BG_SURFACE,
        BORDER,
        BORDER_GOLD,
        ERROR,
        INFO,
        PRIMARY,
        RADIUS,
        RADIUS_SM,
        SECONDARY,
        SUCCESS,
        TEXT_DIM,
        TEXT_MUTED,
        TEXT_PRIMARY,
        WARNING,
        btn_danger,
        btn_ghost,
        btn_primary,
        btn_success,
        label_title,
    )
except ImportError:
    PRIMARY = "#2563EB"; BG_BASE = "#0F1623"; BG_SURFACE = "#162032"; BG_ELEVATED = "#1E2A3B"
    TEXT_PRIMARY = "#F0F6FF"; TEXT_MUTED = "#93C5FD"; TEXT_DIM = "#4B7BBA"
    ERROR = "#EF4444"; SUCCESS = "#22C55E"; WARNING = "#F59E0B"; INFO = "#38BDF8"
    BORDER_GOLD = "#1E4585"; BORDER = "#1A2E4A"; ACCENT = "#60A5FA"
    SECONDARY = "#1E3A5F"; RADIUS = "10px"; RADIUS_SM = "6px"
    def btn_success(extra=""): return f"QPushButton {{ background-color: {SUCCESS}; color: white; border: none; border-radius: 6px; padding: 8px 18px; font-weight: 700; {extra} }}"
    def btn_danger(extra=""): return f"QPushButton {{ background-color: {ERROR}; color: white; border: none; border-radius: 6px; padding: 8px 18px; font-weight: 700; {extra} }}"
    def btn_ghost(extra=""): return f"QPushButton {{ background-color: {BG_ELEVATED}; color: {TEXT_MUTED}; border: 1px solid {BORDER}; border-radius: 6px; padding: 7px 18px; {extra} }}"
    def btn_primary(extra=""): return f"QPushButton {{ background-color: {PRIMARY}; color: white; border: none; border-radius: 6px; padding: 8px 18px; font-weight: 700; {extra} }}"
    def label_title(size=16): return f"font-size: {size}pt; font-weight: 700; color: {PRIMARY}; background: transparent;"

_INPUT_STYLE = lambda border_color: f"""
    QLineEdit {{
        background-color: {BG_SURFACE};
        color: {TEXT_PRIMARY};
        border: 1px solid {border_color};
        border-radius: 4px;
        padding: 7px;
    }}
"""

_LIST_STYLE = lambda sel_color: f"""
    QListWidget {{
        background-color: {BG_ELEVATED};
        color: {TEXT_PRIMARY};
        border: 1px solid {BORDER_GOLD};
        border-radius: 4px;
    }}
    QListWidget::item {{
        padding: 7px 10px;
        border-bottom: 1px solid {BORDER};
    }}
    QListWidget::item:selected {{
        background-color: {sel_color};
        color: white;
    }}
"""


class UserManagementTab(QWidget):
    """Tab untuk mengelola blacklist dan whitelist users"""

    listsUpdated = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.user_manager = get_user_list_manager() if USER_LIST_AVAILABLE else None
        self._setup_ui()
        self._load_lists()

    # ──────────────────────────────────────────────────────────────
    # UI SETUP
    # ──────────────────────────────────────────────────────────────

    def _setup_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(15, 15, 15, 15)

        main_layout.addWidget(self._create_header())

        if not USER_LIST_AVAILABLE:
            err = QLabel(t("users.err.unavailable"))
            err.setStyleSheet(f"color: {ERROR}; font-size: 14px; padding: 20px;")
            err.setAlignment(Qt.AlignmentFlag.AlignCenter)
            main_layout.addWidget(err)
            self.setLayout(main_layout)
            return

        main_layout.addWidget(self._create_info_section())

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self._create_list_section(is_blacklist=True))
        splitter.addWidget(self._create_list_section(is_blacklist=False))
        splitter.setSizes([1, 1])
        main_layout.addWidget(splitter)

        main_layout.addWidget(self._create_stats_section())
        self.setLayout(main_layout)

    def _create_header(self):
        header = QFrame()
        header.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_ELEVATED};
                border-radius: 8px;
                padding: 10px;
                border: 1px solid {BORDER_GOLD};
            }}
        """)
        layout = QHBoxLayout()

        title = QLabel(t("users.header.title"))
        title.setStyleSheet(label_title())
        layout.addWidget(title)
        layout.addStretch()

        # Import CSV
        import_btn = QPushButton(t("users.btn.import_csv"))
        import_btn.setToolTip(t("users.tooltip.import_csv"))
        import_btn.clicked.connect(self._import_csv)
        import_btn.setStyleSheet(btn_ghost())
        layout.addWidget(import_btn)

        # Export CSV
        export_btn = QPushButton(t("users.btn.export_csv"))
        export_btn.setToolTip(t("users.tooltip.export_csv"))
        export_btn.clicked.connect(self._export_csv)
        export_btn.setStyleSheet(btn_ghost())
        layout.addWidget(export_btn)

        refresh_btn = QPushButton(t("users.btn.refresh"))
        refresh_btn.clicked.connect(self._load_lists)
        refresh_btn.setStyleSheet(btn_ghost())
        layout.addWidget(refresh_btn)

        header.setLayout(layout)
        return header

    def _create_info_section(self):
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_ELEVATED};
                border-radius: 8px;
                padding: 10px;
                border: 1px solid {BORDER_GOLD};
            }}
        """)
        layout = QVBoxLayout()

        title = QLabel(t("users.info.title"))
        title.setStyleSheet(f"color: {ACCENT}; font-weight: bold; font-size: 12px;")
        layout.addWidget(title)

        info = QLabel(t("users.info.body"))
        info.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
        info.setWordWrap(True)
        layout.addWidget(info)

        frame.setLayout(layout)
        return frame

    def _create_list_section(self, is_blacklist: bool):
        if is_blacklist:
            title = t("users.blacklist.title")
            desc  = t("users.blacklist.desc")
            color = ERROR
        else:
            title = t("users.whitelist.title")
            desc  = t("users.whitelist.desc")
            color = SUCCESS

        group = QGroupBox(title)
        group.setStyleSheet(f"""
            QGroupBox {{
                color: {color};
                border: 2px solid {color};
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
                font-size: 13px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
        """)
        layout = QVBoxLayout()

        # Description
        desc_lbl = QLabel(desc)
        desc_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px; font-weight: normal;")
        layout.addWidget(desc_lbl)

        # ── Add input ──
        input_row = QHBoxLayout()
        if is_blacklist:
            self.blacklist_input = QLineEdit()
            self.blacklist_input.setPlaceholderText(t("users.placeholder.blacklist_input"))
            self.blacklist_input.setStyleSheet(_INPUT_STYLE(ERROR))
            self.blacklist_input.returnPressed.connect(self._add_to_blacklist)
            input_row.addWidget(self.blacklist_input)

            add_btn = QPushButton(t("users.btn.add"))
            add_btn.clicked.connect(self._add_to_blacklist)
            add_btn.setStyleSheet(btn_danger())
            input_row.addWidget(add_btn)
        else:
            self.whitelist_input = QLineEdit()
            self.whitelist_input.setPlaceholderText(t("users.placeholder.whitelist_input"))
            self.whitelist_input.setStyleSheet(_INPUT_STYLE(SUCCESS))
            self.whitelist_input.returnPressed.connect(self._add_to_whitelist)
            input_row.addWidget(self.whitelist_input)

            add_btn = QPushButton(t("users.btn.add_vip"))
            add_btn.clicked.connect(self._add_to_whitelist)
            add_btn.setStyleSheet(btn_success())
            input_row.addWidget(add_btn)

        layout.addLayout(input_row)

        # ── Search / filter ──
        search_row = QHBoxLayout()
        search_icon = QLabel("🔍")
        search_row.addWidget(search_icon)

        if is_blacklist:
            self.blacklist_search = QLineEdit()
            self.blacklist_search.setPlaceholderText(t("users.placeholder.search_blacklist"))
            self.blacklist_search.setStyleSheet(_INPUT_STYLE(BORDER))
            self.blacklist_search.textChanged.connect(self._filter_blacklist)
            search_row.addWidget(self.blacklist_search)
        else:
            self.whitelist_search = QLineEdit()
            self.whitelist_search.setPlaceholderText(t("users.placeholder.search_whitelist"))
            self.whitelist_search.setStyleSheet(_INPUT_STYLE(BORDER))
            self.whitelist_search.textChanged.connect(self._filter_whitelist)
            search_row.addWidget(self.whitelist_search)

        layout.addLayout(search_row)

        # ── List widget ──
        if is_blacklist:
            self.blacklist_widget = QListWidget()
            self.blacklist_widget.setStyleSheet(_LIST_STYLE(ERROR))
            self.blacklist_widget.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
            layout.addWidget(self.blacklist_widget)

            remove_btn = QPushButton(t("users.btn.remove_selected"))
            remove_btn.clicked.connect(self._remove_from_blacklist)
            remove_btn.setStyleSheet(btn_danger())
            layout.addWidget(remove_btn)
        else:
            self.whitelist_widget = QListWidget()
            self.whitelist_widget.setStyleSheet(_LIST_STYLE(SUCCESS))
            self.whitelist_widget.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
            layout.addWidget(self.whitelist_widget)

            remove_btn = QPushButton(t("users.btn.remove_vip_selected"))
            remove_btn.clicked.connect(self._remove_from_whitelist)
            remove_btn.setStyleSheet(btn_ghost())
            layout.addWidget(remove_btn)

        group.setLayout(layout)
        return group

    def _create_stats_section(self):
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_ELEVATED};
                border-radius: 8px;
                padding: 10px;
                border: 1px solid {BORDER_GOLD};
            }}
        """)
        layout = QHBoxLayout()

        self.blacklist_count_label = QLabel(t("users.stats.blacklist", count=0))
        self.blacklist_count_label.setStyleSheet(f"color: {ERROR}; font-weight: bold;")
        layout.addWidget(self.blacklist_count_label)

        layout.addStretch()

        self.whitelist_count_label = QLabel(t("users.stats.whitelist", count=0))
        self.whitelist_count_label.setStyleSheet(f"color: {SUCCESS}; font-weight: bold;")
        layout.addWidget(self.whitelist_count_label)

        frame.setLayout(layout)
        return frame

    # ──────────────────────────────────────────────────────────────
    # DATA OPERATIONS
    # ──────────────────────────────────────────────────────────────

    def _load_lists(self):
        if not self.user_manager:
            return

        self.blacklist_widget.clear()
        for username in sorted(self.user_manager.get_blacklist()):
            item = QListWidgetItem(t("users.item.blacklist", username=username))
            item.setData(Qt.ItemDataRole.UserRole, username)
            self.blacklist_widget.addItem(item)

        self.whitelist_widget.clear()
        for username in sorted(self.user_manager.get_whitelist()):
            item = QListWidgetItem(t("users.item.whitelist", username=username))
            item.setData(Qt.ItemDataRole.UserRole, username)
            self.whitelist_widget.addItem(item)

        self._update_stats()
        # Re-apply active search filters after reload
        self._filter_blacklist(self.blacklist_search.text())
        self._filter_whitelist(self.whitelist_search.text())

    def _update_stats(self):
        if not self.user_manager:
            return
        stats = self.user_manager.get_stats()
        self.blacklist_count_label.setText(t("users.stats.blacklist", count=stats['blacklist_count']))
        self.whitelist_count_label.setText(t("users.stats.whitelist", count=stats['whitelist_count']))

    def _add_to_blacklist(self):
        username = self.blacklist_input.text().strip().lstrip("@")
        if not username:
            return
        if self.user_manager.add_to_blacklist(username):
            self.blacklist_input.clear()
            self._load_lists()
            self.listsUpdated.emit()
            logger.info(f"Added to blacklist: {username}")

    def _add_to_whitelist(self):
        username = self.whitelist_input.text().strip().lstrip("@")
        if not username:
            return
        if self.user_manager.add_to_whitelist(username):
            self.whitelist_input.clear()
            self._load_lists()
            self.listsUpdated.emit()
            logger.info(f"Added to VIP: {username}")

    def _remove_from_blacklist(self):
        selected = self.blacklist_widget.selectedItems()
        if not selected:
            return
        for item in selected:
            self.user_manager.remove_from_blacklist(item.data(Qt.ItemDataRole.UserRole))
        self._load_lists()
        self.listsUpdated.emit()

    def _remove_from_whitelist(self):
        selected = self.whitelist_widget.selectedItems()
        if not selected:
            return
        for item in selected:
            self.user_manager.remove_from_whitelist(item.data(Qt.ItemDataRole.UserRole))
        self._load_lists()
        self.listsUpdated.emit()

    # ──────────────────────────────────────────────────────────────
    # SEARCH / FILTER
    # ──────────────────────────────────────────────────────────────

    def _filter_blacklist(self, text: str):
        """Sembunyikan item yang tidak cocok dengan kata kunci pencarian"""
        keyword = text.strip().lower()
        for i in range(self.blacklist_widget.count()):
            item = self.blacklist_widget.item(i)
            username = item.data(Qt.ItemDataRole.UserRole) or ""
            item.setHidden(keyword != "" and keyword not in username.lower())

    def _filter_whitelist(self, text: str):
        keyword = text.strip().lower()
        for i in range(self.whitelist_widget.count()):
            item = self.whitelist_widget.item(i)
            username = item.data(Qt.ItemDataRole.UserRole) or ""
            item.setHidden(keyword != "" and keyword not in username.lower())

    # ──────────────────────────────────────────────────────────────
    # IMPORT / EXPORT CSV
    # ──────────────────────────────────────────────────────────────

    def _export_csv(self):
        """Export blacklist dan whitelist ke CSV — dua kolom: username,list_type"""
        if not self.user_manager:
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            t("users.dialog.export_title"),
            t("users.dialog.export_default_name"),
            t("users.dialog.export_filter"),
        )
        if not file_path:
            return

        try:
            rows = (
                [(u, "blacklist") for u in sorted(self.user_manager.get_blacklist())] +
                [(u, "whitelist") for u in sorted(self.user_manager.get_whitelist())]
            )
            with open(file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["username", "list_type"])
                writer.writerows(rows)

            QMessageBox.information(
                self,
                t("users.msg.export_success_title"),
                t("users.msg.export_success", count=len(rows), path=file_path),
            )
            logger.info(f"Exported {len(rows)} users to {file_path}")

        except Exception as e:
            QMessageBox.warning(
                self,
                t("users.err.export_failed_title"),
                t("users.err.export_failed", reason=str(e)),
            )

    def _import_csv(self):
        """Import username dari CSV — support format: username saja, atau username,list_type"""
        if not self.user_manager:
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            t("users.dialog.import_title"),
            "",
            t("users.dialog.import_filter"),
        )
        if not file_path:
            return

        try:
            added_black = added_white = skipped = 0

            with open(file_path, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                for row in reader:
                    if not row:
                        continue
                    username = row[0].strip().lstrip("@").lower()
                    if not username or username == "username":  # skip header
                        continue

                    # Kolom kedua: "blacklist" atau "whitelist" (opsional, default blacklist)
                    list_type = row[1].strip().lower() if len(row) > 1 else "blacklist"

                    if list_type in ("whitelist", "vip", "white"):
                        if self.user_manager.add_to_whitelist(username):
                            added_white += 1
                        else:
                            skipped += 1
                    else:
                        if self.user_manager.add_to_blacklist(username):
                            added_black += 1
                        else:
                            skipped += 1

            self._load_lists()
            self.listsUpdated.emit()

            QMessageBox.information(
                self,
                t("users.msg.import_success_title"),
                t(
                    "users.msg.import_success",
                    added_black=added_black,
                    added_white=added_white,
                    skipped=skipped,
                ),
            )
            logger.info(f"Imported: {added_black} blacklist, {added_white} whitelist, {skipped} skipped")

        except Exception as e:
            QMessageBox.warning(
                self,
                t("users.err.import_failed_title"),
                t("users.err.import_failed", reason=str(e)),
            )
