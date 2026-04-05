# ui/user_management_tab.py
"""
User Management Tab - Mengelola blacklist dan whitelist username
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QTextEdit, QListWidget, QListWidgetItem, QLineEdit,
    QMessageBox, QFrame, QSplitter, QAbstractItemView
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor
import logging

logger = logging.getLogger("VocaLive.UserManagement")

# Try to import user list manager
try:
    from modules_client.user_list_manager import get_user_list_manager
    USER_LIST_AVAILABLE = True
except ImportError:
    USER_LIST_AVAILABLE = False
    logger.warning("User list manager not available")

try:
    from ui.theme import (PRIMARY, SECONDARY, ACCENT, BG_BASE, BG_SURFACE, BG_ELEVATED,
        TEXT_PRIMARY, TEXT_MUTED, TEXT_DIM, BORDER_GOLD, BORDER,
        SUCCESS, ERROR, WARNING, INFO, RADIUS, RADIUS_SM,
        btn_success, btn_danger, btn_ghost, btn_primary, label_title)
except ImportError:
    PRIMARY = "#2563EB"; BG_BASE = "#0F1623"; BG_SURFACE = "#162032"; BG_ELEVATED = "#1E2A3B"
    TEXT_PRIMARY = "#F0F6FF"; TEXT_MUTED = "#93C5FD"; TEXT_DIM = "#4B7BBA"
    ERROR = "#EF4444"; SUCCESS = "#22C55E"; WARNING = "#F59E0B"; INFO = "#38BDF8"
    BORDER_GOLD = "#1E4585"; BORDER = "#1A2E4A"; ACCENT = "#60A5FA"
    SECONDARY = "#1E3A5F"; RADIUS = "10px"; RADIUS_SM = "6px"
    def btn_success(extra=""): return f"QPushButton {{ background-color: {SUCCESS}; color: white; border: none; border-radius: 6px; padding: 8px 18px; font-weight: 700; {extra} }}"
    def btn_danger(extra=""): return f"QPushButton {{ background-color: {ERROR}; color: white; border: none; border-radius: 6px; padding: 8px 18px; font-weight: 700; {extra} }}"
    def btn_ghost(extra=""): return f"QPushButton {{ background-color: {BG_ELEVATED}; color: {TEXT_MUTED}; border: 1px solid {BORDER}; border-radius: 6px; padding: 7px 18px; {extra} }}"
    def btn_primary(extra=""): return f"QPushButton {{ background-color: {PRIMARY}; color: {BG_BASE}; border: none; border-radius: 6px; padding: 8px 18px; font-weight: 700; {extra} }}"
    def label_title(size=16): return f"font-size: {size}pt; font-weight: 700; color: {PRIMARY}; background: transparent;"


class UserManagementTab(QWidget):
    """Tab untuk mengelola blacklist dan whitelist users"""
    
    # Signal when lists are updated
    listsUpdated = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        
        # Get user list manager
        if USER_LIST_AVAILABLE:
            self.user_manager = get_user_list_manager()
        else:
            self.user_manager = None
        
        self._setup_ui()
        self._load_lists()
    
    def _setup_ui(self):
        """Setup user interface"""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # ===== HEADER =====
        header = self._create_header()
        main_layout.addWidget(header)
        
        # Check if module available
        if not USER_LIST_AVAILABLE:
            error_label = QLabel("⚠️ User List Manager module tidak tersedia")
            error_label.setStyleSheet(f"color: {ERROR}; font-size: 14px; padding: 20px;")
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            main_layout.addWidget(error_label)
            self.setLayout(main_layout)
            return
        
        # ===== INFO SECTION =====
        info_frame = QFrame()
        info_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_ELEVATED};
                border-radius: 8px;
                padding: 10px;
                border: 1px solid {BORDER_GOLD};
            }}
        """)
        info_layout = QVBoxLayout()
        
        info_title = QLabel("ℹ️ Cara Kerja:")
        info_title.setStyleSheet(f"color: {ACCENT}; font-weight: bold; font-size: 12px;")
        info_layout.addWidget(info_title)
        
        info_text = QLabel(
            "• 🚫 <b>Blacklist</b>: User di blacklist akan DIABAIKAN sepenuhnya (tidak di-reply)\n"
            "• ⭐ <b>Whitelist (VIP)</b>: User VIP akan SELALU dijawab (bypass cooldown)"
        )
        info_text.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
        info_text.setWordWrap(True)
        info_layout.addWidget(info_text)
        
        info_frame.setLayout(info_layout)
        main_layout.addWidget(info_frame)
        
        # ===== MAIN CONTENT - SPLITTER =====
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # LEFT: Blacklist
        blacklist_widget = self._create_list_section(
            "🚫 Blacklist (Blokir)",
            "Pengguna yang diblokir tidak akan mendapat reply",
            ERROR,
            is_blacklist=True
        )
        splitter.addWidget(blacklist_widget)

        # RIGHT: Whitelist
        whitelist_widget = self._create_list_section(
            "⭐ Whitelist (VIP)",
            "Pengguna VIP selalu dijawab, bypass cooldown",
            SUCCESS,
            is_blacklist=False
        )
        splitter.addWidget(whitelist_widget)
        
        # Equal split
        splitter.setSizes([1, 1])
        main_layout.addWidget(splitter)
        
        # ===== STATS =====
        stats_frame = self._create_stats_section()
        main_layout.addWidget(stats_frame)
        
        self.setLayout(main_layout)
    
    def _create_header(self):
        """Create header section"""
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
        
        # Title
        title = QLabel("👥 User Management")
        title.setStyleSheet(label_title())
        layout.addWidget(title)
        
        layout.addStretch()
        
        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self._load_lists)
        refresh_btn.setStyleSheet(btn_ghost())
        layout.addWidget(refresh_btn)
        
        header.setLayout(layout)
        return header
    
    def _create_list_section(self, title, description, color, is_blacklist=True):
        """Create a list section (blacklist or whitelist)"""
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
        desc_label = QLabel(description)
        desc_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px; font-weight: normal;")
        layout.addWidget(desc_label)
        
        # Input area
        input_layout = QHBoxLayout()
        
        if is_blacklist:
            self.blacklist_input = QLineEdit()
            self.blacklist_input.setPlaceholderText("Masukkan username...")
            self.blacklist_input.setStyleSheet(f"""
                QLineEdit {{
                    background-color: {BG_SURFACE};
                    color: {TEXT_PRIMARY};
                    border: 1px solid {ERROR};
                    border-radius: 4px;
                    padding: 8px;
                }}
            """)
            self.blacklist_input.returnPressed.connect(self._add_to_blacklist)
            input_layout.addWidget(self.blacklist_input)
            
            add_btn = QPushButton("+ Tambah")
            add_btn.clicked.connect(self._add_to_blacklist)
            add_btn.setStyleSheet(btn_danger())
            input_layout.addWidget(add_btn)
        else:
            self.whitelist_input = QLineEdit()
            self.whitelist_input.setPlaceholderText("Masukkan username VIP...")
            self.whitelist_input.setStyleSheet(f"""
                QLineEdit {{
                    background-color: {BG_SURFACE};
                    color: {TEXT_PRIMARY};
                    border: 1px solid {SUCCESS};
                    border-radius: 4px;
                    padding: 8px;
                }}
            """)
            self.whitelist_input.returnPressed.connect(self._add_to_whitelist)
            input_layout.addWidget(self.whitelist_input)
            
            add_btn = QPushButton("+ Tambah VIP")
            add_btn.clicked.connect(self._add_to_whitelist)
            add_btn.setStyleSheet(btn_success())
            input_layout.addWidget(add_btn)
        
        layout.addLayout(input_layout)
        
        # List widget
        if is_blacklist:
            self.blacklist_widget = QListWidget()
            self.blacklist_widget.setStyleSheet(f"""
                QListWidget {{
                    background-color: {BG_ELEVATED};
                    color: {TEXT_PRIMARY};
                    border: 1px solid {BORDER_GOLD};
                    border-radius: 4px;
                }}
                QListWidget::item {{
                    padding: 8px;
                    border-bottom: 1px solid {BORDER};
                }}
                QListWidget::item:selected {{
                    background-color: {ERROR};
                    color: white;
                }}
            """)
            self.blacklist_widget.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
            layout.addWidget(self.blacklist_widget)
            
            # Remove button
            remove_btn = QPushButton("🗑️ Hapus")
            remove_btn.clicked.connect(self._remove_from_blacklist)
            remove_btn.setStyleSheet(btn_danger())
            layout.addWidget(remove_btn)
        else:
            self.whitelist_widget = QListWidget()
            self.whitelist_widget.setStyleSheet(f"""
                QListWidget {{
                    background-color: {BG_ELEVATED};
                    color: {TEXT_PRIMARY};
                    border: 1px solid {BORDER_GOLD};
                    border-radius: 4px;
                }}
                QListWidget::item {{
                    padding: 8px;
                    border-bottom: 1px solid {BORDER};
                }}
                QListWidget::item:selected {{
                    background-color: {SUCCESS};
                    color: white;
                }}
            """)
            self.whitelist_widget.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
            layout.addWidget(self.whitelist_widget)
            
            # Remove button
            remove_btn = QPushButton("🗑️ Hapus VIP")
            remove_btn.clicked.connect(self._remove_from_whitelist)
            remove_btn.setStyleSheet(btn_ghost())
            layout.addWidget(remove_btn)
        
        group.setLayout(layout)
        return group
    
    def _create_stats_section(self):
        """Create statistics section"""
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
        
        # Blacklist count
        self.blacklist_count_label = QLabel("🚫 Blacklist: 0 users")
        self.blacklist_count_label.setStyleSheet(f"color: {ERROR}; font-weight: bold;")
        layout.addWidget(self.blacklist_count_label)
        
        layout.addStretch()
        
        # Whitelist count
        self.whitelist_count_label = QLabel("⭐ Whitelist: 0 users")
        self.whitelist_count_label.setStyleSheet(f"color: {SUCCESS}; font-weight: bold;")
        layout.addWidget(self.whitelist_count_label)
        
        frame.setLayout(layout)
        return frame
    
    def _load_lists(self):
        """Load lists from manager"""
        if not self.user_manager:
            return
        
        # Load blacklist
        self.blacklist_widget.clear()
        for username in self.user_manager.get_blacklist():
            item = QListWidgetItem(f"🚫 {username}")
            item.setData(Qt.ItemDataRole.UserRole, username)
            self.blacklist_widget.addItem(item)
        
        # Load whitelist
        self.whitelist_widget.clear()
        for username in self.user_manager.get_whitelist():
            item = QListWidgetItem(f"⭐ {username}")
            item.setData(Qt.ItemDataRole.UserRole, username)
            self.whitelist_widget.addItem(item)
        
        # Update stats
        self._update_stats()
    
    def _update_stats(self):
        """Update statistics labels"""
        if not self.user_manager:
            return
        
        stats = self.user_manager.get_stats()
        self.blacklist_count_label.setText(f"🚫 Blacklist: {stats['blacklist_count']} users")
        self.whitelist_count_label.setText(f"⭐ Whitelist: {stats['whitelist_count']} users")
    
    def _add_to_blacklist(self):
        """Add user to blacklist"""
        username = self.blacklist_input.text().strip()
        if not username:
            return
        
        if self.user_manager.add_to_blacklist(username):
            self.blacklist_input.clear()
            self._load_lists()
            self.listsUpdated.emit()
            logger.info(f"Added to blacklist: {username}")
    
    def _remove_from_blacklist(self):
        """Remove selected users from blacklist"""
        selected_items = self.blacklist_widget.selectedItems()
        if not selected_items:
            return
        
        for item in selected_items:
            username = item.data(Qt.ItemDataRole.UserRole)
            self.user_manager.remove_from_blacklist(username)
        
        self._load_lists()
        self.listsUpdated.emit()
    
    def _add_to_whitelist(self):
        """Add user to whitelist (VIP)"""
        username = self.whitelist_input.text().strip()
        if not username:
            return
        
        if self.user_manager.add_to_whitelist(username):
            self.whitelist_input.clear()
            self._load_lists()
            self.listsUpdated.emit()
            logger.info(f"Added to whitelist (VIP): {username}")
    
    def _remove_from_whitelist(self):
        """Remove selected users from whitelist"""
        selected_items = self.whitelist_widget.selectedItems()
        if not selected_items:
            return
        
        for item in selected_items:
            username = item.data(Qt.ItemDataRole.UserRole)
            self.user_manager.remove_from_whitelist(username)
        
        self._load_lists()
        self.listsUpdated.emit()
