import os
import json
import sys
import time
import logging
import webbrowser
import requests
from pathlib import Path
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QMessageBox, 
    QHBoxLayout, QProgressBar, QFrame, QGroupBox, QGridLayout,
    QSpacerItem, QScrollArea, QSizePolicy, QTextEdit, QComboBox,
    QSpinBox, QInputDialog, QLineEdit, QDialog
)
from PyQt6.QtGui import QFont, QDesktopServices, QColor, QPixmap
from PyQt6.QtCore import QUrl, Qt, QTimer, pyqtSignal
from modules_client.config_manager import ConfigManager
from modules_client.supabase_client import SupabaseClient
import re
import hashlib
import hmac

logger = logging.getLogger('StreamMate')

# ✅ SUPABASE-ONLY MODE DETECTION
def _is_supabase_only_mode() -> bool:
    """Check if system should use Supabase-only mode (no VPS calls)"""
    try:
        supabase_config = Path("config/supabase_config.json")
        if supabase_config.exists():
            return True
        return False
    except:
        return False

def safe_attr_check(obj, attr_name):
    """Safely check if an object has an attribute."""
    try:
        return hasattr(obj, attr_name)
    except Exception:
        return False

# Setup path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Import ConfigManager - UI harus pakai client config manager
# try:
#     from modules_client.config_manager import ConfigManager
# except ImportError:
#     from modules_client.config_manager import ConfigManager

class SubscriptionTab(QWidget):
    # Signal untuk update main window
    package_activated = pyqtSignal(str)
    demo_expired_signal = pyqtSignal()  # Sinyal baru untuk demo berakhir
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.cfg = ConfigManager()  # Client ConfigManager default sudah config/settings.json
        
        # Demo timer system
        self.demo_timer = None
        self.demo_start_time = None
        self.demo_duration_minutes = 30
        self.demo_active = False
        
        # Supabase client
        self.supabase = SupabaseClient()
        
        # TAMBAHKAN background setup seperti login_tab
        self.setup_background()
        
        # Setup UI
        self.setup_ui()
        self.setup_timer()
        
        # Start background monitoring untuk demo
        self.setup_demo_monitoring()
        
        # ✅ TAMBAHAN: Debug parent connection
        print(f"[DEBUG] SubscriptionTab initialized with parent: {type(parent).__name__ if parent else 'None'}")
        if parent and safe_attr_check(parent, 'pilih_paket'):
            print(f"[DEBUG] Parent has pilih_paket method - direct call available")
        else:
            print(f"[DEBUG] Parent missing pilih_paket method - will use signal")
        
        # Setup timer untuk update kredit dan status - OPTIMASI: Interval lebih lambat
        self.credit_timer = QTimer(self)
        self.credit_timer.timeout.connect(self.refresh_credits)
        self.credit_timer.start(180000)  # ✅ OPTIMASI: Ubah dari 30 detik ke 2 menit
        
        # Initial refresh
        self.refresh_credits()
        

    
    def setup_background(self):
        """Setup background gradient yang modern seperti login_tab."""
        self.setStyleSheet("""
            SubscriptionTab {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                            stop:0 #0F1419, stop:0.3 #1a1f2e,
                                            stop:0.7 #2c3e50, stop:1 #34495e);
            }
            QLabel {
                color: white;
            }
            QPushButton {
                color: white;
            }
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: #1a1f2e;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #34495e;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
        
    def setup_ui(self):
        """Setup subscription tab UI yang lengkap dan profesional"""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)
        
        # Create scroll area untuk responsivitas
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        
        # Content widget
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(20)
        
        # ========== HEADER SECTION ==========
        header_widget = self.create_header_section()
        content_layout.addWidget(header_widget)
        
        # ========== STATUS SECTION ==========
        status_widget = self.create_status_section()
        content_layout.addWidget(status_widget)
        
        # ========== QUICK ACTIONS ==========
        quick_actions = self.create_quick_actions()
        content_layout.addWidget(quick_actions)
        
        # ========== ENTER MODE BUTTONS ==========
        mode_buttons_widget = self.create_mode_buttons_section()
        content_layout.addWidget(mode_buttons_widget)
        
        # ========== PACKAGE CARDS ==========
        packages_widget = self.create_packages_section()
        content_layout.addWidget(packages_widget)
        
        # ========== INFO SECTION ==========
        info_widget = self.create_info_section()
        content_layout.addWidget(info_widget)
        
        # Add stretch
        content_layout.addStretch()
        
        # Set content to scroll area
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)
        
    def create_header_section(self):
        """Create header dengan branding"""
        header = QWidget()
        header_layout = QVBoxLayout(header)
        header_layout.setSpacing(10)
        
        # Title
        title = QLabel("💰 StreamMate AI Subscription")
        title.setStyleSheet("""
            QLabel {
                font-size: 28px;
                font-weight: bold;
                color: #1877F2;
            }
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel("Manage your streaming subscription and credits")
        subtitle.setStyleSheet("""
            QLabel {
                font-size: 16px;
                color: #65676B;
            }
        """)
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(subtitle)
        
        return header
        
    def create_status_section(self):
        """Create status section dengan informasi lengkap dan tombol top-up"""
        status_frame = QFrame()
        status_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #E0E0E0;
                border-radius: 12px;
                padding: 20px;
            }
        """)
        
        main_layout = QVBoxLayout(status_frame)
        main_layout.setSpacing(15)
        
        # Top section with Top-up button
        top_section = QHBoxLayout()
        
        # Top-up Credits button - Moved here
        topup_btn = QPushButton("💳 Top-up Credits")
        topup_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
                max-width: 150px;
            }
            QPushButton:hover {
                background-color: #45A049;
            }
        """)
        topup_btn.clicked.connect(self.show_topup_options)
        top_section.addWidget(topup_btn)
        
        top_section.addStretch()
        main_layout.addLayout(top_section)
        
        # Status grid
        status_grid = QWidget()
        layout = QGridLayout(status_grid)
        layout.setSpacing(15)
        
        # Row 1: Status Langganan
        layout.addWidget(self.create_status_label("Status:"), 0, 0)
        self.status_value = QLabel("Checking...")
        self.status_value.setStyleSheet(self.get_value_style())
        layout.addWidget(self.status_value, 0, 1)
        
        # Row 2: Paket Aktif
        layout.addWidget(self.create_status_label("Package:"), 1, 0)
        self.package_value = QLabel("None")
        self.package_value.setStyleSheet(self.get_value_style())
        layout.addWidget(self.package_value, 1, 1)
        
        # Row 3: Total Kredit
        layout.addWidget(self.create_status_label("Total Credits:"), 2, 0)
        self.credits_value = QLabel("0 credits")
        self.credits_value.setStyleSheet(self.get_value_style("#1877F2"))
        layout.addWidget(self.credits_value, 2, 1)
        
        # Row 4: Wallet Credits
        layout.addWidget(self.create_status_label("Wallet Credits:"), 3, 0)
        self.wallet_credits_value = QLabel("0 credits")
        self.wallet_credits_value.setStyleSheet(self.get_value_style("#4CAF50"))
        layout.addWidget(self.wallet_credits_value, 3, 1)
        
        # Row 5: Basic Credits
        layout.addWidget(self.create_status_label("Basic Credits:"), 4, 0)
        self.basic_credits_value = QLabel("0 credits")
        self.basic_credits_value.setStyleSheet(self.get_value_style("#FF9800"))
        layout.addWidget(self.basic_credits_value, 4, 1)
        
        # Row 6: Pro Credits
        layout.addWidget(self.create_status_label("Pro Credits:"), 5, 0)
        self.pro_credits_value = QLabel("0 credits")
        self.pro_credits_value.setStyleSheet(self.get_value_style("#2196F3"))
        layout.addWidget(self.pro_credits_value, 5, 1)
        
        # Row 7: Total Penggunaan
        layout.addWidget(self.create_status_label("Usage:"), 6, 0)
        self.usage_value = QLabel("0 credits")
        self.usage_value.setStyleSheet(self.get_value_style())
        layout.addWidget(self.usage_value, 6, 1)
        
        # Row 8: Expire Date (jika ada)
        self.expire_label = self.create_status_label("Expires:")
        self.expire_value = QLabel("-")
        self.expire_value.setStyleSheet(self.get_value_style())
        layout.addWidget(self.expire_label, 7, 0)
        layout.addWidget(self.expire_value, 7, 1)
        self.expire_label.setVisible(False)
        self.expire_value.setVisible(False)
        
        # Column stretch
        layout.setColumnStretch(1, 1)
        
        main_layout.addWidget(status_grid)
        
        return status_frame
        
    def create_status_label(self, text):
        """Create consistent status label"""
        label = QLabel(text)
        label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #666;
                min-width: 100px;
            }
        """)
        return label
        
    def get_value_style(self, color="#333"):
        """Get style for value labels"""
        return f"""
            QLabel {{
                font-size: 14px;
                font-weight: bold;
                color: {color};
            }}
        """
        
    def create_quick_actions(self):
        """Create quick action buttons"""
        from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton
        
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setSpacing(15)
        
        # Demo button
        self.demo_btn = QPushButton("🎮 Try Demo 30 Minutes")
        self.demo_btn.setStyleSheet("""
            QPushButton {
                background-color: #42B883;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #37A372;
            }
            QPushButton:disabled {
                background-color: #CCCCCC;
            }
        """)
        self.demo_btn.clicked.connect(self.start_demo)
        layout.addWidget(self.demo_btn)
        
        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh Status")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #F0F2F5;
                color: #1877F2;
                border: 1px solid #1877F2;
                padding: 12px 24px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #E8F0FE;
            }
        """)
        refresh_btn.clicked.connect(lambda: self.refresh_credits(force_supabase_sync=True))
        layout.addWidget(refresh_btn)
        
        # Logout button
        logout_btn = QPushButton("🚪 Logout")
        logout_btn.setStyleSheet("""
            QPushButton {
                background-color: #FA383E;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #E8282D;
            }
        """)
        logout_btn.clicked.connect(self.logout)
        layout.addWidget(logout_btn)
        
        layout.addStretch()
        
        return widget
        
    def create_packages_section(self):
        """Create package cards yang dibeli dengan kredit"""
        packages_frame = QFrame()
        packages_frame.setStyleSheet("""
            QFrame {
                background-color: #F8F9FA;
                border-radius: 12px;
                border: 1px solid #E0E0E0;
                padding: 20px;
                margin: 10px 0;
            }
        """)
        
        main_layout = QVBoxLayout(packages_frame)
        
        # Section title
        title = QLabel("📦 Choose Features Package (Paid with Credits)")
        title.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #333;
                margin-bottom: 15px;
            }
        """)
        main_layout.addWidget(title)
        
        # Info label about credit purchases
        info_widget = QFrame()
        info_widget.setStyleSheet("""
            QFrame {
                background-color: #E3F2FD;
                border-radius: 8px;
                border-left: 4px solid #2196F3;
                padding: 15px;
                margin-bottom: 20px;
            }
        """)
        info_layout = QHBoxLayout(info_widget)
        
        info_label = QLabel("💡 Need more credits? Use the 'Top-up Credits' button above to add credits, then purchase packages below")
        info_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #666;
                font-style: italic;
            }
        """)
        info_label.setWordWrap(True)
        info_layout.addWidget(info_label)
        
        main_layout.addWidget(info_widget)
        
        # Cards container
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(20)
        
        # BASIC PACKAGE CARD - Updated for credit purchase
        basic_card = self.create_package_card(
            title="BASIC",
            price="100,000 Credits",  # Changed from money to credits
            credits="One-time purchase",
            features=[
                "✅ Auto-Reply AI (Trigger Mode)",
                "⏳ Voice Translation (Coming Soon)",
                "✅ YouTube & TikTok Support",
                "✅ Basic TTS Voices",
                "✅ Chat Overlay",
                "✅ 24/7 Support"
            ],
            color="#4CAF50",
            package_id="basic",
            is_available=True,
            is_popular=True
        )
        cards_layout.addWidget(basic_card)
        
        # PRO PACKAGE CARD
        pro_card = self.create_package_card(
            title="PRO",
            price="300,000 Credits",
            credits="300,000 Credits",
            features=[
                "✅ All Basic features",
                "🤖 Advanced AI Cohost",
                "📚 RAG Knowledge System",
                "🌐 Advanced Translation",
                "👥 Viewer Management",
                "🎤 Virtual Microphone",
                "🎯 Priority Support"
            ],
            color="#FF9800",
            package_id="pro",
            is_available=True,
            is_popular=True
        )
        cards_layout.addWidget(pro_card)
        
        main_layout.addLayout(cards_layout)
        
        return packages_frame
        
    def create_mode_buttons_section(self):
        """Create section untuk tombol Enter Basic Mode dan Enter Pro Mode"""
        buttons_frame = QFrame()
        buttons_frame.setStyleSheet("""
            QFrame {
                background-color: #F8F9FA;
                border-radius: 12px;
                border: 1px solid #E0E0E0;
                padding: 20px;
                margin: 10px 0;
            }
        """)
        
        main_layout = QVBoxLayout(buttons_frame)
        
        # Section title
        title = QLabel("🚀 Enter Application Mode")
        title.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #333;
                margin-bottom: 15px;
            }
        """)
        main_layout.addWidget(title)
        
        # Buttons container
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(20)
        
        # BASIC MODE BUTTON
        self.basic_mode_btn = QPushButton("🚀 Enter Basic Mode")
        self.basic_mode_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 15px 30px;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
                border: none;
                min-width: 200px;
            }
            QPushButton:hover {
                background-color: #45A049;
            }
            QPushButton:disabled {
                background-color: #CCCCCC;
                color: #666666;
            }
        """)
        self.basic_mode_btn.clicked.connect(self.enter_basic_mode)
        buttons_layout.addWidget(self.basic_mode_btn)
        
        # PRO MODE BUTTON
        self.pro_mode_btn = QPushButton("🚀 Enter Pro Mode")
        self.pro_mode_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                padding: 15px 30px;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
                border: none;
                min-width: 200px;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
            QPushButton:disabled {
                background-color: #CCCCCC;
                color: #666666;
            }
        """)
        self.pro_mode_btn.clicked.connect(self.enter_pro_mode)
        buttons_layout.addWidget(self.pro_mode_btn)
        
        main_layout.addLayout(buttons_layout)
        
        return buttons_frame
        
    def create_package_card(self, title, price, credits, features, color, 
                            package_id, is_available=True, is_popular=False, 
                            is_coming_soon=False):
        """Create attractive package card"""
        card = QFrame()
        card.setMinimumWidth(280)
        card.setMaximumWidth(350)
        
        # Card styling
        if is_available:
            card.setStyleSheet(f"""
                QFrame {{
                    background-color: white;
                    border: 2px solid {color};
                    border-radius: 12px;
                    padding: 0;
                }}
                QFrame:hover {{
                    border: 3px solid {color};
                }}
            """)
        else:
            card.setStyleSheet("""
                QFrame {
                    background-color: #F5F5F5;
                    border: 2px solid #E0E0E0;
                    border-radius: 12px;
                    padding: 0;
                }
            """)
            
        layout = QVBoxLayout(card)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header dengan badge
        header = QWidget()
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(20, 20, 20, 10)
        
        # Badge
        if is_popular:
            badge = QLabel("🔥 MOST POPULAR")
            badge.setStyleSheet(f"""
                QLabel {{
                    background-color: {color};
                    color: white;
                    padding: 4px 12px;
                    border-radius: 12px;
                    font-size: 11px;
                    font-weight: bold;
                }}
            """)
            badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            header_layout.addWidget(badge)
        elif is_coming_soon:
            badge = QLabel("🚀 COMING SOON")
            badge.setStyleSheet("""
                QLabel {
                    background-color: #666;
                    color: white;
                    padding: 4px 12px;
                    border-radius: 12px;
                    font-size: 11px;
                    font-weight: bold;
                }
            """)
            badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            header_layout.addWidget(badge)
            
        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            QLabel {{
                font-size: 24px;
                font-weight: bold;
                color: {color if is_available else '#999'};
                margin: 10px 0;
            }}
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(title_label)
        
        # Price
        price_label = QLabel(price)
        price_label.setStyleSheet(f"""
            QLabel {{
                font-size: 28px;
                font-weight: bold;
                color: {color if is_available else '#999'};
            }}
        """)
        price_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(price_label)
        
        # Credits
        credits_label = QLabel(credits)
        credits_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                color: #666;
                margin-bottom: 15px;
            }
        """)
        credits_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(credits_label)
        
        layout.addWidget(header)
        
        # Features
        features_widget = QWidget()
        features_widget.setStyleSheet("background-color: #FAFAFA;")
        features_layout = QVBoxLayout(features_widget)
        features_layout.setContentsMargins(20, 15, 20, 15)
        
        for feature in features:
            feat_label = QLabel(feature)
            feat_label.setStyleSheet(f"""
                QLabel {{
                    font-size: 13px;
                    color: {'#333' if is_available else '#999'};
                    padding: 3px 0;
                }}
            """)
            features_layout.addWidget(feat_label)
            
        layout.addWidget(features_widget)
        
        # Buy button
        button_widget = QWidget()
        button_layout = QVBoxLayout(button_widget)
        button_layout.setContentsMargins(20, 15, 20, 20)
        
        if is_available:
            # Buy package button
            buy_btn = QPushButton(f"💳 Buy {title} with Credits")
            buy_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    color: white;
                    border: none;
                    padding: 12px;
                    border-radius: 8px;
                    font-size: 16px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {self.darken_color(color)};
                }}
            """)
            buy_btn.clicked.connect(lambda: self.buy_package(package_id))
            button_layout.addWidget(buy_btn)
        else:
            # Coming soon button
            soon_btn = QPushButton("🔒 Coming Soon")
            soon_btn.setStyleSheet("""
                QPushButton {
                    background-color: #E0E0E0;
                    color: #999;
                    border: none;
                    padding: 12px;
                    border-radius: 8px;
                    font-size: 16px;
                    font-weight: bold;
                }
            """)
            soon_btn.setEnabled(False)
            button_layout.addWidget(soon_btn)
            
        layout.addWidget(button_widget)
        
        return card

    def get_demo_status_display(self):
        """Dapatkan status demo untuk ditampilkan dengan warna hitam."""
        try:
            # ✅ PERBAIKAN: Cek demo reset harian sebelum display status
            self._check_demo_daily_reset()
            
            subscription_file = Path("config/subscription_status.json")
            if not subscription_file.exists():
                return {
                    "text": "✅ Demo available - Click to start 30 minutes free",
                    "color": "#000000"  # HITAM
                }
                
            with open(subscription_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            status = data.get("status", "")
            
            # KASUS 1: Demo sedang aktif
            if status == "demo":
                expire_date_str = data.get("expire_date", "")
                if expire_date_str:
                    try:
                        from datetime import datetime, timezone
                        if '+' in expire_date_str or 'Z' in expire_date_str:
                            expire_date = datetime.fromisoformat(expire_date_str.replace('Z', '+00:00'))
                            now_time = datetime.now(timezone.utc)
                        else:
                            expire_date = datetime.fromisoformat(expire_date_str)
                            now_time = datetime.now()
                        
                        if now_time < expire_date:
                            remaining = expire_date - now_time
                            mins_left = int(remaining.total_seconds() / 60)
                            
                            # Batasi maksimal 30 menit untuk display
                            if mins_left > 30:
                                mins_left = 30
                            
                            return {
                                "text": f"⏱️ Demo active - Remaining: {mins_left} minutes",
                                "color": "#000000"  # HITAM
                            }
                        else:
                            # Demo expired, tapi TIDAK mengubah file lokal
                            # Status akan diubah oleh stop_demo_auto() saja
                            return {
                                "text": "⏰ Demo expired - Reset tomorrow at 00:00 WIB",
                                "color": "#000000"  # HITAM
                            }
                    except Exception as e:
                        print(f"[DEBUG] Error parsing demo time: {e}")
                        return {
                            "text": "⚠️ Demo error - Reset tomorrow at 00:00 WIB", 
                            "color": "#000000"
                        }
                else:
                    return {
                        "text": "⚠️ Demo data error - Reset tomorrow at 00:00 WIB",
                        "color": "#000000"
                    }
                
            # KASUS 2: Demo sudah expired atau digunakan hari ini
            elif status == "expired" or data.get("demo_used", False):
                return {
                    "text": "⏰ Demo already used - Reset tomorrow at 00:00 WIB",
                    "color": "#000000"  # HITAM
                }
            
            # KASUS 3: Demo tersedia (belum digunakan)
            else:
                return {
                    "text": "✅ Demo available - 30 minutes free",
                    "color": "#000000"  # HITAM
                }
            
        except Exception as e:
            print(f"[DEBUG] Error in get_demo_status_display: {e}")
            return {
                "text": "⚠️ Demo status not readable",
                "color": "#000000"  # HITAM
            }

    def _check_demo_daily_reset(self):
        """Cek dan reset demo jika sudah lewat jam 00:00 WIB"""
        try:
            print("[DEMO-RESET] Checking if demo needs resetting...")
            
            # ✅ GUNAKAN SUPABASE UNTUK DEMO RESET
            from modules_client.supabase_client import SupabaseClient
            supabase = SupabaseClient()
            
            # Get user email
            email = self.cfg.get("user_data", {}).get("email", "")
            if not email:
                print("[DEMO-RESET] No email found, using local file")
                return self._check_demo_daily_reset_local()
            
            # Cek demo data dari Supabase
            demo_result = supabase._make_request(
                'GET',
                f'/rest/v1/demo_usage?email=eq.{email}',
                use_service_role=True
            )
            
            if not demo_result or len(demo_result) == 0:
                print("[DEMO-RESET] No demo data found in Supabase")
                return False
            
            demo_data = demo_result[0]
            demo_used = demo_data.get("demo_used", False)
            demo_reset_at = demo_data.get("demo_reset_at")
            
            if not demo_used:
                print("[DEMO-RESET] Demo not used yet, no need to reset")
                return False
            
            print(f"[DEMO-RESET] Current demo_used: {demo_used}, reset_at: {demo_reset_at}")
            
            # Cek apakah sudah melewati reset time
            import pytz
            from datetime import datetime, date
            
            wib = pytz.timezone('Asia/Jakarta')
            now_wib = datetime.now(wib)
            
            if demo_reset_at:
                try:
                    reset_datetime = datetime.fromisoformat(demo_reset_at.replace('Z', ''))
                    if reset_datetime.tzinfo is None:
                        reset_datetime = wib.localize(reset_datetime)
                    else:
                        reset_datetime = reset_datetime.astimezone(wib)
                    
                    # Jika sudah lewat reset time, reset demo
                    if now_wib >= reset_datetime:
                        print(f"[DEMO-RESET] RESETTING DEMO - Reset time: {reset_datetime.isoformat()}, Now: {now_wib.isoformat()}")
                        
                        # Update demo data di Supabase
                        update_data = {
                            "demo_used": False,
                            "demo_duration_minutes": 30,
                            "demo_reset_at": (now_wib + timedelta(days=1)).isoformat()
                        }
                        
                        update_result = supabase._make_request(
                            'PATCH',
                            f'/rest/v1/demo_usage?email=eq.{email}',
                            update_data,
                            use_service_role=True
                        )
                        
                        if update_result:
                            print(f"[DEMO-RESET] Demo successfully reset in Supabase")
                            
                            # Update local file juga
                            self._update_local_demo_reset()
                            
                            # Refresh UI button
                            self.update_demo_button()
                            
                            return True
                        else:
                            print(f"[DEMO-RESET] Failed to reset demo in Supabase")
                            return False
                    else:
                        print(f"[DEMO-RESET] No reset needed. Reset time: {reset_datetime.isoformat()}, Now: {now_wib.isoformat()}")
                        return False
                        
                except Exception as e:
                    print(f"[DEMO-RESET] Error parsing reset time: {e}")
                    return False
            
            return False
                
        except Exception as e:
            print(f"[DEMO-RESET] Error checking demo reset from Supabase: {e}")
            # Fallback ke local file
            return self._check_demo_daily_reset_local()
    
    def _check_demo_daily_reset_local(self):
        """Fallback: Cek dan reset demo dari local file"""
        try:
            print("[DEMO-RESET] Using local file fallback...")
            
            subscription_file = Path("config/subscription_status.json")
            if not subscription_file.exists():
                print("[DEMO-RESET] No subscription file found, nothing to reset")
                return False
                
            with open(subscription_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            status = data.get("status", "")
            demo_used = data.get("demo_used", False)
            
            # Hanya cek reset jika status expired atau demo_used = True
            if status != "expired" and not demo_used:
                print("[DEMO-RESET] Demo not used yet, no need to reset")
                return False
            
            print(f"[DEMO-RESET] Current status: {status}, demo_used: {demo_used}")
            
            # Cek apakah sudah melewati jam 00:00 WIB dari tanggal demo terakhir digunakan
            import pytz
            from datetime import datetime, date
            
            wib = pytz.timezone('Asia/Jakarta')
            now_wib = datetime.now(wib)
            today_wib = now_wib.date()
            
            print(f"[DEMO-RESET] Current WIB time: {now_wib.isoformat()}")
            
            # Cek tanggal terakhir demo digunakan
            demo_expired_at = data.get("demo_expired_at", "")
            activated_at = data.get("activated_at", "")
            
            last_demo_date = None
            
            if demo_expired_at:
                try:
                    last_demo_datetime = datetime.fromisoformat(demo_expired_at.replace('Z', ''))
                    # Convert ke WIB jika perlu
                    if last_demo_datetime.tzinfo is None:
                        last_demo_datetime = wib.localize(last_demo_datetime)
                    else:
                        last_demo_datetime = last_demo_datetime.astimezone(wib)
                    last_demo_date = last_demo_datetime.date()
                    print(f"[DEMO-RESET] Last demo expired at: {last_demo_datetime.isoformat()}, date: {last_demo_date}")
                except Exception as e:
                    print(f"[DEMO-RESET] Error parsing demo_expired_at: {e}")
                    pass
            
            if not last_demo_date and activated_at:
                try:
                    activated_datetime = datetime.fromisoformat(activated_at.replace('Z', ''))
                    if activated_datetime.tzinfo is None:
                        activated_datetime = wib.localize(activated_datetime)
                    else:
                        activated_datetime = activated_datetime.astimezone(wib)
                    last_demo_date = activated_datetime.date()
                    print(f"[DEMO-RESET] Last demo activated at: {activated_datetime.isoformat()}, date: {last_demo_date}")
                except Exception as e:
                    print(f"[DEMO-RESET] Error parsing activated_at: {e}")
                    pass
            
            # Jika sudah berbeda hari (lewat jam 00:00 WIB), reset demo
            if last_demo_date and today_wib > last_demo_date:
                print(f"[DEMO-RESET] RESETTING DEMO - Last used: {last_demo_date}, Today: {today_wib}")
                
                # Reset status demo
                data["status"] = "inactive"
                data["demo_used"] = False
                if "demo_expired_at" in data:
                    del data["demo_expired_at"]
                if "expire_date" in data:
                    del data["expire_date"]
                    
                # Simpan file yang sudah direset
                with open(subscription_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                print(f"[DEMO-RESET] Demo successfully reset for new day")
                
                # Refresh UI button
                self.update_demo_button()
                
                return True  # Return True if reset occurred
            else:
                if last_demo_date:
                    print(f"[DEMO-RESET] No reset needed. Last used: {last_demo_date}, Today: {today_wib}")
                else:
                    print("[DEMO-RESET] No reset needed. Could not determine last usage date.")
                return False
                
        except Exception as e:
            print(f"[DEMO-RESET] Error checking demo reset: {e}")
            import traceback
            print(traceback.format_exc())
            return False
    
    def _update_local_demo_reset(self):
        """Update local file setelah reset di Supabase"""
        try:
            subscription_file = Path("config/subscription_status.json")
            if subscription_file.exists():
                with open(subscription_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Reset status demo
                data["status"] = "inactive"
                data["demo_used"] = False
                if "demo_expired_at" in data:
                    del data["demo_expired_at"]
                if "expire_date" in data:
                    del data["expire_date"]
                    
                # Simpan file yang sudah direset
                with open(subscription_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                print(f"[DEMO-RESET] Local file updated after Supabase reset")
                
        except Exception as e:
            print(f"[DEMO-RESET] Error updating local file: {e}")
            return False

    def update_demo_button(self):
        """Update tombol demo berdasarkan status."""
        status_info = self.get_demo_status_display()
        button_text = status_info["text"].lower()
        
        # KASUS 1: Demo sedang aktif
        if "active" in button_text:
            self.demo_btn.setText("⏱️ Demo Currently Active")
            self.demo_btn.setEnabled(False)
            self.demo_btn.setStyleSheet("""
                QPushButton {
                    font-size: 16px;
                    font-weight: bold;
                    padding: 15px 30px;
                    background-color: #6c757d;
                    color: white;
                    border: none;
                    border-radius: 10px;
                    margin: 10px 0;
                }
            """)
            
        # KASUS 2: Demo sudah digunakan/expired (menampilkan notifikasi reset)
        elif "already used" in button_text or "expired" in button_text or "reset" in button_text:
            self.demo_btn.setText("⏰ Demo Reset Tomorrow")
            self.demo_btn.setEnabled(True)  # Enable untuk show notifikasi
            self.demo_btn.setStyleSheet("""
                QPushButton {
                    font-size: 16px;
                    font-weight: bold;
                    padding: 15px 30px;
                    background-color: #dc3545;
                    color: white;
                    border: none;
                    border-radius: 10px;
                    margin: 10px 0;
                }
                QPushButton:hover {
                    background-color: #c82333;
                }
            """)
            # Connect ke method yang hanya menampilkan popup info
            try:
                self.demo_btn.clicked.disconnect()
            except:
                pass
            self.demo_btn.clicked.connect(lambda: QMessageBox.information(
                self,
                "Demo Unavailable",
                "You can try the demo again after 00:00 WIB (midnight) tomorrow.",
                QMessageBox.StandardButton.Ok
            ))
            
        # KASUS 3: Demo tersedia
        else:
            self.demo_btn.setText("🚀 Try Demo 30 Minutes")
            self.demo_btn.setEnabled(True)
            self.demo_btn.setStyleSheet("""
                QPushButton {
                    font-size: 16px;
                    font-weight: bold;
                    padding: 15px 30px;
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                    stop:0 #28a745, stop:1 #1e7e34);
                    color: white;
                    border: none;
                    border-radius: 10px;
                    margin: 10px 0;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                    stop:0 #218838, stop:1 #1c7430);
                }
            """)
            # Connect ke method normal untuk start demo
            try:
                self.demo_btn.clicked.disconnect()
            except:
                pass
            self.demo_btn.clicked.connect(self.start_demo)
        
    def create_info_section(self):
        """Create info section"""
        info_frame = QFrame()
        info_frame.setStyleSheet("""
            QFrame {
                background-color: #E8F4F8;
                border: 1px solid #B8E0F0;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        
        layout = QVBoxLayout(info_frame)
        
        info_text = """
        <style>
            body { font-family: Arial, sans-serif; }
            h3 { color: #1877F2; margin-top: 10px; }
            ul { margin: 5px 0; padding-left: 20px; }
            li { margin: 3px 0; }
        </style>
        
        <h3>ℹ️ Important Information</h3>
        <ul>
            <li style="color: black;"><b>Demo Mode:</b> 30 minutes free to try Basic features (one-time use)</li>
            <li style="color: black;"><b>Payment:</b> Via iPaymu - Bank Transfer, E-Wallet, QRIS</li>
            <li style="color: black;"><b>Activation:</b> Automatic after successful payment</li>
            <li style="color: black;"><b>Credits:</b> Valid for 30 days from purchase</li>
        </ul>
        
        <h3>📞 Need Help?</h3>
        <p style="color: black;">Email: mursalinasrul@gmail.com<br>
        WhatsApp: +62 895-1642-5913</p>
        """
        
        info_widget = QTextEdit()
        info_widget.setHtml(info_text)
        info_widget.setReadOnly(True)
        info_widget.setMaximumHeight(200)
        info_widget.setStyleSheet("""
            QTextEdit {
                background-color: transparent;
                border: none;
                font-size: 12px;
            }
        """)
        
        layout.addWidget(info_widget)
        
        return info_frame
        
    def setup_timer(self):
        """Setup auto refresh timer - DEPRECATED, gunakan credit_timer"""
        pass

    def refresh_credits(self, force_supabase_sync=False):
        """Refresh status dan kredit dari Supabase"""
        try:
            # Check for daily demo reset first
            reset_occurred = self._check_demo_daily_reset()
            if reset_occurred:
                print("[REFRESH] Demo was reset during refresh_credits call")
                
            # 🎯 PERBAIKAN: Selalu ambil data dari Supabase terlebih dahulu
            email = self.cfg.get("user_data", {}).get("email", "")
            supabase_data = None
            
            if email:
                try:
                    print("[REFRESH] Fetching latest data from Supabase...")
                    credit_data = self.supabase.get_credit_balance(email)
                    
                    if credit_data and credit_data.get("status") == "success":
                        data = credit_data.get("data", {})
                        # --- Perbaikan: Gunakan credit_balance/credit_used jika ada ---
                        credit_balance = float(data.get("wallet_balance", 0))
                        credit_used = float(data.get("total_spent", 0))
                        basic_credits = float(data.get("basic_credits", 0))
                        pro_credits = float(data.get("pro_credits", 0))
                        
                        supabase_data = {
                            "status": "paid" if data.get("status") == "active" else "inactive",
                            "package": data.get("tier", "basic"),
                            "credit_balance": credit_balance,
                            "credit_used": credit_used,
                            "basic_credits": basic_credits,
                            "pro_credits": pro_credits,
                            "hours_credit": credit_balance,  # for legacy fallback
                            "hours_used": credit_used,      # for legacy fallback
                            "email": email
                        }
                        print(f"[REFRESH] Supabase data: {supabase_data['credit_balance']:.6f} credits, {supabase_data['credit_used']:.6f} used")
                    else:
                        print(f"[REFRESH] Supabase error: {credit_data}")
                except Exception as e:
                    print(f"[REFRESH] Supabase connection error: {e}")
            
            # Fallback ke subscription file jika Supabase gagal
            if not supabase_data:
                subscription_file = Path("config/subscription_status.json")
                
                if not subscription_file.exists():
                    self.update_status_display({
                        "status": "inactive",
                        "package": "none", 
                        "credit_balance": 0,
                        "credit_used": 0,
                        "basic_credits": 0,
                        "pro_credits": 0,
                        "hours_credit": 0,
                        "hours_used": 0
                    })
                    return
                    
                with open(subscription_file, "r", encoding="utf-8") as f:
                    supabase_data = json.load(f)
                print("[REFRESH] Using local subscription file")
                # --- Perbaikan: Pastikan field credit_balance/credit_used ada ---
                if "credit_balance" not in supabase_data:
                    supabase_data["credit_balance"] = float(supabase_data.get("hours_credit", 0))
                if "credit_used" not in supabase_data:
                    supabase_data["credit_used"] = float(supabase_data.get("hours_used", 0))
                if "basic_credits" not in supabase_data:
                    supabase_data["basic_credits"] = 0
                if "pro_credits" not in supabase_data:
                    supabase_data["pro_credits"] = 0
            
            # Cek status demo lokal sebelum overwrite dengan data server
            subscription_file = Path("config/subscription_status.json")
            if subscription_file.exists():
                with open(subscription_file, "r", encoding="utf-8") as f:
                    local_data = json.load(f)
                local_status = local_data.get("status", "")
                expire_date_str = local_data.get("expire_date", "")
                from datetime import datetime, timezone
                demo_still_active = False
                if local_status == "demo" and expire_date_str:
                    try:
                        if '+' in expire_date_str or 'Z' in expire_date_str:
                            expire_date = datetime.fromisoformat(expire_date_str.replace('Z', '+00:00'))
                            now_time = datetime.now(timezone.utc)
                        else:
                            expire_date = datetime.fromisoformat(expire_date_str)
                            now_time = datetime.now()
                        if now_time < expire_date:
                            demo_still_active = True
                    except Exception as e:
                        print(f"[REFRESH] Error parsing local demo expire_date: {e}")
                if demo_still_active:
                    print("[REFRESH] Local demo still active, ignoring server data overwrite.")
                    self.update_status_display(local_data)
                    self.update_demo_button()
                    return

            self.update_status_display(supabase_data)
            
            # ✅ PERBAIKAN: Log data untuk debugging
            credit_balance = float(supabase_data.get("credit_balance", supabase_data.get("hours_credit", 0)))
            credit_used = float(supabase_data.get("credit_used", supabase_data.get("hours_used", 0)))
            print(f"[REFRESH] Current data: {credit_balance:.1f} credits, {credit_used:.4f} used")
            
            # Update credit display jika ada
            if hasattr(self, 'credit_status_label'):
                if credit_balance < 1.0:
                    self.credit_status_label.setText(f"❌ Credits: {credit_balance:.1f} (Insufficient)")
                    self.credit_status_label.setStyleSheet("color: red; font-weight: bold;")
                elif credit_balance < 5.0:
                    self.credit_status_label.setText(f"⚠️ Credits: {credit_balance:.1f} (Low)")
                    self.credit_status_label.setStyleSheet("color: orange; font-weight: bold;")
                else:
                    self.credit_status_label.setText(f"✅ Credits: {credit_balance:.1f}")
                    self.credit_status_label.setStyleSheet("color: green;")
            
            # Update demo button to reflect current status
            self.update_demo_button()
            
        except Exception as e:
            logger.error(f"Error refreshing credits: {e}")
            self.status_value.setText("Error")

    def update_status_display(self, data):
        """Update status display dengan data terbaru"""
        try:
            status = data.get("status", "inactive")
            package = data.get("package", "none")
            credit_balance = float(data.get("credit_balance", data.get("hours_credit", 0)))
            credit_used = float(data.get("credit_used", data.get("hours_used", 0)))
            basic_credits = float(data.get("basic_credits", 0))
            pro_credits = float(data.get("pro_credits", 0))
            
            # UPDATE STATUS: Aktif hanya jika ada Basic atau Pro credits
            if basic_credits > 0 or pro_credits > 0:
                status = "active"
                self.status_value.setText("✅ Active")
                self.status_value.setStyleSheet(self.get_value_style("#4CAF50"))
            elif status == "demo":
                self.status_value.setText("🎮 Demo Active")
                self.status_value.setStyleSheet(self.get_value_style("#FF9800"))
            else:
                self.status_value.setText("❌ Inactive")
                self.status_value.setStyleSheet(self.get_value_style("#D32F2F"))
            
            # UPDATE PACKAGE: Tampilkan mode yang memiliki credits
            package_display = []
            if basic_credits > 0:
                package_display.append("Basic")
            if pro_credits > 0:
                package_display.append("Pro")
            
            if package_display:
                package_text = ", ".join(package_display)
                self.package_value.setText(package_text)
                self.package_value.setStyleSheet(self.get_value_style("#2196F3"))
            else:
                self.package_value.setText("None")
                self.package_value.setStyleSheet(self.get_value_style("#666666"))
            
            # UPDATE CREDITS: Tampilkan semua jenis kredit
            total_credits = credit_balance + basic_credits + pro_credits
            self.credits_value.setText(f"{total_credits:.1f} credits")
            if total_credits > 0:
                self.credits_value.setStyleSheet(self.get_value_style("#4CAF50"))
            else:
                self.credits_value.setStyleSheet(self.get_value_style("#D32F2F"))
            
            # UPDATE WALLET CREDITS
            self.wallet_credits_value.setText(f"{credit_balance:.1f} credits")
            if credit_balance > 0:
                self.wallet_credits_value.setStyleSheet(self.get_value_style("#4CAF50"))
            else:
                self.wallet_credits_value.setStyleSheet(self.get_value_style("#666666"))
            
            # UPDATE BASIC CREDITS
            self.basic_credits_value.setText(f"{basic_credits:.1f} credits")
            if basic_credits > 0:
                self.basic_credits_value.setStyleSheet(self.get_value_style("#FF9800"))
            else:
                self.basic_credits_value.setStyleSheet(self.get_value_style("#666666"))
            
            # UPDATE PRO CREDITS
            self.pro_credits_value.setText(f"{pro_credits:.1f} credits")
            if pro_credits > 0:
                self.pro_credits_value.setStyleSheet(self.get_value_style("#2196F3"))
            else:
                self.pro_credits_value.setStyleSheet(self.get_value_style("#666666"))
            
            # UPDATE USAGE: Tampilkan sebagai data tracking (bukan batasan)
            if status == "demo":
                # Untuk demo, tampilkan waktu tersisa
                expire_date = data.get("expire_date")
                if expire_date:
                    self.expire_label.setVisible(True)
                    self.expire_value.setVisible(True)
                    try:
                        from datetime import datetime
                        expire_dt = datetime.fromisoformat(expire_date.replace('Z', '+00:00'))
                        remaining = expire_dt - datetime.now(expire_dt.tzinfo or None)
                        if remaining.total_seconds() > 0:
                            mins = int(remaining.total_seconds() / 60)
                            self.usage_value.setText(f"Demo: {mins} minutes remaining")
                        else:
                            self.usage_value.setText("Demo: Expired")
                    except Exception as e:
                        self.usage_value.setText(f"Demo: {expire_date}")
                else:
                    self.usage_value.setText("Demo: 30 minutes")
            else:
                # Untuk mode aktif, tampilkan usage sebagai data tracking
                self.usage_value.setText(f"Usage: {credit_used:.1f} credits used")
                self.usage_value.setStyleSheet(self.get_value_style("#666666"))
            
            # Check if demo was used
            if data.get("demo_used", False):
                self.demo_btn.setEnabled(False)
                self.demo_btn.setText("Demo Already Used")
            else:
                self.demo_btn.setEnabled(True)
                self.demo_btn.setText("🎮 Try Demo 30 Minutes")
                
        except Exception as e:
            logger.error(f"Error updating status display: {e}")
            self.status_value.setText("Error")
            self.status_value.setStyleSheet(self.get_value_style("#D32F2F"))
        
        # UPDATE BASIC MODE BUTTON - BERDASARKAN KREDIT BASIC SAJA
        if hasattr(self, 'basic_mode_btn'):
            # Cek kredit Basic (terpisah dari kredit Pro)
            basic_credits = self._get_basic_credits()
            print(f"[DEBUG] Basic Mode Button Update - Status: {status}, Basic Credits: {basic_credits:.1f}")
            
            if status == "demo":
                # Khusus untuk demo, disable tombol
                self.basic_mode_btn.setEnabled(False)
                self.basic_mode_btn.setText("Basic Mode (Demo Active)")
                self.basic_mode_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #CCCCCC;
                        color: #666666;
                        border: none;
                        padding: 15px 30px;
                        border-radius: 8px;
                        font-size: 16px;
                        font-weight: bold;
                        min-width: 200px;
                    }
                """)
                print(f"[DEBUG] Basic Mode Button: DISABLED (Demo Active)")
            else:
                # Selalu enable tombol Basic mode, tampilkan real credits
                self.basic_mode_btn.setEnabled(True)
                self.basic_mode_btn.setText(f"🚀 Enter Basic Mode ({basic_credits:.1f} credits)")
                self.basic_mode_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #4CAF50;
                        color: white;
                        border: none;
                        padding: 15px 30px;
                        border-radius: 8px;
                        font-size: 16px;
                        font-weight: bold;
                        min-width: 200px;
                    }
                    QPushButton:hover {
                        background-color: #45A049;
                    }
                """)
                print(f"[DEBUG] Basic Mode Button: ENABLED (Basic Credits: {basic_credits:.1f})")
        
        # UPDATE PRO MODE BUTTON - BERDASARKAN KREDIT PRO SAJA
        if hasattr(self, 'pro_mode_btn'):
            # Cek kredit Pro (terpisah dari kredit Basic)
            pro_credits = self._get_pro_credits()
            print(f"[DEBUG] Pro Mode Button Update - Status: {status}, Pro Credits: {pro_credits:.1f}")
            
            if status == "demo":
                # Khusus untuk demo, disable tombol
                self.pro_mode_btn.setEnabled(False)
                self.pro_mode_btn.setText("Pro Mode (Demo Active)")
                self.pro_mode_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #CCCCCC;
                        color: #666666;
                        border: none;
                        padding: 15px 30px;
                        border-radius: 8px;
                        font-size: 16px;
                        font-weight: bold;
                        min-width: 200px;
                    }
                """)
                print(f"[DEBUG] Pro Mode Button: DISABLED (Demo Active)")
            else:
                # Selalu enable tombol Pro mode, tampilkan real credits
                self.pro_mode_btn.setEnabled(True)
                self.pro_mode_btn.setText(f"🚀 Enter Pro Mode ({pro_credits:,.0f} credits)")
                self.pro_mode_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #FF9800;
                        color: white;
                        border: none;
                        padding: 15px 30px;
                        border-radius: 8px;
                        font-size: 16px;
                        font-weight: bold;
                        min-width: 200px;
                    }
                    QPushButton:hover {
                        background-color: #F57C00;
                    }
                """)
                print(f"[DEBUG] Pro Mode Button: ENABLED (Pro Credits: {pro_credits:.1f})")

    def buy_package(self, package_name):
        """Proses pembelian paket dengan kredit yang sudah dimiliki."""
        print("\n=== DEBUG CREDIT PURCHASE START ===")
        print(f"DEBUG: Package name: {package_name}")
        
        # Handle Basic package purchase with credits
        if package_name == "basic":
            self.buy_basic_package_with_credits()
            return
            
        # Handle Pro package purchase with credits
        if package_name == "pro":
            self.buy_pro_package_with_credits()
            return
            
        # For other packages, show coming soon
        QMessageBox.information(
            self, "Coming Soon", 
            f"{package_name.capitalize()} package will be available soon!"
        )
        print("=== DEBUG CREDIT PURCHASE END ===\n")
        
    def buy_pro_package_with_credits(self):
        """Handle Pro package purchase with credits via Supabase"""
        try:
            email = self.cfg.get("user_data", {}).get("email", "")
            if not email:
                QMessageBox.warning(self, "Login Required", "Please login first to purchase Pro package")
                return
            
            # Check current credit balance from Supabase
            try:
                credit_data = self.supabase.get_credit_balance(email)
                if not credit_data or credit_data.get("status") != "success":
                    QMessageBox.warning(self, "Error", "Failed to get credit balance from Supabase")
                    return
                
                data = credit_data.get("data", {})
                current_balance = float(data.get("wallet_balance", 0))
                required_credits = 100000  # 100,000 credits for Pro (consistent with Credit Wallet)
                
                if current_balance < required_credits:
                    QMessageBox.warning(
                        self, "Insufficient Credits",
                        f"Pro package requires {required_credits:,} credits.\n"
                        f"Your current balance: {current_balance:,} credits\n\n"
                        "Please top-up more credits first."
                    )
                    return
                
                # Allow multiple Pro credit purchases for top-up
                # Removed active status check to enable continuous credit purchases
                # Users should be able to buy Pro credits multiple times to top-up
                
                # Define subscription file for later use
                subscription_file = Path("config/subscription_status.json")
                
                # Confirm purchase
                reply = QMessageBox.question(
                    self, "Confirm Purchase",
                    f"🚀 CoHost Pro Package\n\n"
                    f"Price: {required_credits:,} credits\n"
                    f"Includes:\n"
                    f"• All Basic features\n"
                    f"• Sequential & Delay Mode\n"
                    f"• Premium Google Chirp3 TTS\n"
                    f"• Virtual Microphone\n"
                    f"• Viewer Management\n"
                    f"• Advanced Analytics\n"
                    f"• Priority Support\n\n"
                    f"Your balance after purchase: {current_balance - required_credits:,} credits\n\n"
                    f"Proceed with purchase?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if reply != QMessageBox.StandardButton.Yes:
                    return
                
                # Purchase via Supabase
                purchase_result = self.supabase.purchase_mode_credits(
                    email=email,
                    mode="pro",
                    credits_needed=required_credits
                )
                
                if not purchase_result or purchase_result.get("status") != "success":
                    QMessageBox.critical(self, "Purchase Failed", "Failed to purchase Pro package via Supabase")
                    return
                
                # Update local subscription data
                if subscription_file.exists():
                    with open(subscription_file, 'r', encoding='utf-8') as f:
                        sub_data = json.load(f)
                else:
                    sub_data = {}
                
                # Add Pro package data
                sub_data["pro"] = {
                    "active": True,
                    "purchased_at": datetime.now().isoformat(),
                    "email": email,
                    "package": "pro"
                }
                
                # Save updated subscription data
                with open(subscription_file, 'w', encoding='utf-8') as f:
                    json.dump(sub_data, f, indent=2, ensure_ascii=False)
                
                # Success message
                QMessageBox.information(
                    self, "Purchase Successful! 🎉",
                    f"Pro package purchased successfully!\n\n"
                    f"✅ Credits deducted: {required_credits:,}\n"
                    f"✅ Pro mode is now available\n\n"
                    f"You can now access Pro features!"
                )
                
                # Refresh UI
                self.refresh_credits()
                
                # Credit purchase successful - DO NOT auto-activate Pro mode
                # User should manually activate Pro mode when needed
                # Removed auto-activation: self.parent.pilih_paket("pro")
                print(f"[DEBUG] Pro credits purchased successfully - manual activation required")
                    
            except Exception as e:
                logger.error(f"Error purchasing pro package: {e}")
                QMessageBox.critical(self, "Purchase Error", f"Failed to purchase Pro package: {str(e)}")
                
        except Exception as e:
            logger.error(f"Error in buy_pro_package_with_credits: {e}")
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")

    def buy_basic_package_with_credits(self):
        """Handle Basic package purchase with credits via Supabase"""
        try:
            email = self.cfg.get("user_data", {}).get("email", "")
            if not email:
                QMessageBox.warning(self, "Login Required", "Please login first to purchase Basic package")
                return
            
            # Check current credit balance from Supabase
            try:
                credit_data = self.supabase.get_credit_balance(email)
                if not credit_data or credit_data.get("status") != "success":
                    QMessageBox.warning(self, "Error", "Failed to get credit balance from Supabase")
                    return
                
                data = credit_data.get("data", {})
                current_balance = float(data.get("wallet_balance", 0))
                required_credits = 100000  # 100,000 credits for Basic
                
                if current_balance < required_credits:
                    QMessageBox.warning(
                        self, "Insufficient Credits",
                        f"Basic package requires {required_credits:,} credits.\n"
                        f"Your current balance: {current_balance:,} credits\n\n"
                        "Please top-up more credits in the Credit Wallet tab first."
                    )
                    return
                
                # Allow multiple Basic credit purchases for top-up
                # Removed active status check to enable continuous credit purchases
                # Users should be able to buy Basic credits multiple times to top-up
                
                # Define subscription file for later use
                subscription_file = Path("config/subscription_status.json")
                
                # Confirm purchase
                reply = QMessageBox.question(
                    self, "Confirm Purchase",
                    f"🚀 Basic Package\n\n"
                    f"Price: {required_credits:,} credits\n"
                    f"Includes:\n"
                    f"• Auto-Reply AI (Trigger Mode)\n"
                    f"• YouTube & TikTok Support\n"
                    f"• Basic TTS Voices\n"
                    f"• Chat Overlay\n"
                    f"• 24/7 Support\n\n"
                    f"Your balance after purchase: {current_balance - required_credits:,} credits\n\n"
                    f"Proceed with purchase?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if reply != QMessageBox.StandardButton.Yes:
                    return
                
                # Purchase via Supabase
                purchase_result = self.supabase.purchase_mode_credits(
                    email=email,
                    mode="basic",
                    credits_needed=required_credits
                )
                
                if not purchase_result or purchase_result.get("status") != "success":
                    QMessageBox.critical(self, "Purchase Failed", "Failed to purchase Basic package via Supabase")
                    return
                
                # Update local subscription data
                if subscription_file.exists():
                    with open(subscription_file, 'r', encoding='utf-8') as f:
                        sub_data = json.load(f)
                else:
                    sub_data = {}
                
                # Add Basic package data
                sub_data["basic"] = {
                    "active": True,
                    "purchased_at": datetime.now().isoformat(),
                    "email": email,
                    "package": "basic"
                }
                
                with open(subscription_file, 'w', encoding='utf-8') as f:
                    json.dump(sub_data, f, indent=2, ensure_ascii=False)
                
                # Show success message
                QMessageBox.information(
                    self, "Purchase Successful! 🎉",
                    f"Basic package activated successfully!\n\n"
                    f"✅ Credits deducted: {required_credits:,}\n"
                    f"✅ Remaining balance: {current_balance - required_credits:,}\n\n"
                    f"You can now access Basic features in the main application!"
                )
                
                # Refresh UI
                self.refresh_credits()
                
                # Credit purchase successful - DO NOT auto-activate Basic mode  
                # User should manually activate Basic mode when needed
                # Removed auto-activation: self.package_activated.emit("basic")
                print(f"[DEBUG] Basic credits purchased successfully - manual activation required")
                
            except Exception as e:
                QMessageBox.critical(self, "Purchase Error", f"Failed to process purchase: {str(e)}")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")
    
    def create_ipaymu_payment(self, email, package, order_id):
        """Create iPaymu payment URL (PRODUCTION, Redirect Payment - Auto semua metode pembayaran)"""
        try:
            import hmac
            import hashlib
            import time
            import requests
            import json
            
            # SANDBOX/PRODUCTION CONFIG
            ipaymu_config = self.cfg.get("ipaymu_config", {})
            ipaymu_api_key = ipaymu_config.get("API_KEY", "SANDBOXE1498BCD-9D73-4607-A2EB-FA78939BBC45")
            ipaymu_va = ipaymu_config.get("VA_NUMBER", "0000009516425913")
            sandbox_mode = ipaymu_config.get("SANDBOX_MODE", "true").lower() == "true"
            
            # Force sandbox mode untuk testing
            sandbox_mode = True
            ipaymu_api_key = "SANDBOXE1498BCD-9D73-4607-A2EB-FA78939BBC45"
            ipaymu_va = "0000009516425913"
            
            # Set URL berdasarkan mode
            if sandbox_mode:
                api_url = "https://sandbox.ipaymu.com/api/v2/payment"
                print(f"🔧 Using SANDBOX mode for testing")
            else:
                api_url = "https://my.ipaymu.com/api/v2/payment"
                print(f"🔧 Using PRODUCTION mode")
            
            # DEBUG: Cek konfigurasi
            print(f"🔍 DEBUG: API Key: {ipaymu_api_key[:8]}...")
            print(f"🔍 DEBUG: VA Number: {ipaymu_va}")
            print(f"🔍 DEBUG: Sandbox Mode: {sandbox_mode}")
            print(f"🔍 DEBUG: API URL: {api_url}")

            amount = package['price_idr']
            raw_name = f"StreamMate AI - {package['name']}"
            product_name = raw_name.encode('ascii', 'ignore').decode()
            product_price = amount
            product_qty = 1
                
            print(f"🔧 iPaymu Config: VA={ipaymu_va}, Sandbox={sandbox_mode}")
            print(f"🔧 Redirect Payment - Semua metode pembayaran otomatis tersedia")
            print(f"🔧 API URL: {api_url}")
            print(f"🔧 Mode: {'SANDBOX' if sandbox_mode else 'PRODUCTION'}")
                
            body = {
                "product": [product_name],
                "qty": [product_qty],
                "price": [product_price],
                "returnUrl": "https://streammate-callback.onrender.com/payment-completed",
                "cancelUrl": "https://streammate-callback.onrender.com/payment-completed?status=canceled",
                "notifyUrl": "https://streammate-callback.onrender.com/ipaymu-callback",
                "referenceId": order_id,
                "name": email.split('@')[0],
                "email": email,
                "phone": "08123456789"
                # TIDAK perlu paymentMethod - iPaymu akan tampilkan semua opsi otomatis
            }
            
            print(f"🔧 iPaymu Body: {json.dumps(body, indent=2)}")

            body_json = json.dumps(body, separators=(',', ':'), sort_keys=True)
            body_hash = hashlib.sha256(body_json.encode()).hexdigest()
            stringToSign = f"POST:{ipaymu_va}:{body_hash}:{ipaymu_api_key}"
            signature = hmac.new(
                ipaymu_api_key.encode('utf-8'),
                stringToSign.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()

            mode_text = "SANDBOX" if sandbox_mode else "PRODUCTION"
            print(f"🔧 [IPAYMU-{mode_text}] VA: {ipaymu_va}")
            print(f"🔧 [IPAYMU-{mode_text}] API_KEY: {ipaymu_api_key[:6]}... (hidden)")
            print(f"🔧 [IPAYMU-{mode_text}] BODY_JSON: {body_json}")
            print(f"🔧 [IPAYMU-{mode_text}] BODY_HASH: {body_hash}")
            print(f"🔧 [IPAYMU-{mode_text}] STRING_TO_SIGN: {stringToSign}")
            print(f"🔧 [IPAYMU-{mode_text}] SIGNATURE: {signature}")

            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "va": ipaymu_va,
                "signature": signature
            }

            response = requests.post(api_url, data=body_json, headers=headers)
            response_data = response.json()
            print(f"🔧 [IPAYMU-{mode_text}] RESPONSE: {response_data}")

            if response_data.get("Status") == 200:
                return response_data.get("Data", {}).get("Url")
            else:
                error_msg = response_data.get("Message", "Unknown error")
                logger.error(f"iPaymu {'SANDBOX' if sandbox_mode else 'PRODUCTION'} API error: {response_data}")
                
                # Handle specific error cases
                if "test transaksi" in error_msg.lower():
                    logger.error("❌ Akun iPaymu production belum terverifikasi atau ada masalah konfigurasi")
                    logger.error("💡 Solusi: Verifikasi akun di https://my.ipaymu.com atau gunakan sandbox mode")
                elif "unauthorized" in error_msg.lower():
                    logger.error("❌ API Key atau VA Number salah")
                elif "invalid" in error_msg.lower():
                    logger.error("❌ Data transaksi tidak valid")
                
                return None

        except Exception as e:
            logger.error(f"Failed to create iPaymu {'SANDBOX' if sandbox_mode else 'PRODUCTION'} payment: {e}")
            return None
    
    def show_payment_info_dialog(self):
        """Dialog untuk menampilkan info pembayaran"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Informasi Pembayaran")
        dialog.setFixedSize(500, 400)
        dialog.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                            stop:0 #0F1419, stop:0.3 #1a1f2e,
                                            stop:0.7 #2c3e50, stop:1 #34495e);
                color: white;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                            stop:0 #27ae60, stop:1 #229954);
                border: none;
                padding: 15px;
                border-radius: 8px;
                color: white;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                            stop:0 #58d68d, stop:1 #27ae60);
            }
            QLabel {
                color: white;
                font-size: 14px;
                line-height: 1.5;
            }
            QTextEdit {
                background: rgba(255,255,255,0.1);
                border: 1px solid #3498db;
                border-radius: 8px;
                color: white;
                font-size: 12px;
                padding: 10px;
            }
        """)
        
        layout = QVBoxLayout()
        
        # Header
        header_label = QLabel("🎯 Metode Pembayaran Tersedia")
        header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #3498db;")
        layout.addWidget(header_label)
        
        layout.addSpacing(20)
        
        # Info Text
        info_text = QTextEdit()
        info_text.setReadOnly(True)
        info_text.setMaximumHeight(200)
        info_text.setHtml("""
        <div style='color: white; font-size: 14px;'>
        <p><strong>🏦 Virtual Account (VA)</strong></p>
        <ul>
            <li>Bank BCA, BNI, BRI, Mandiri</li>
            <li>Bank Permata, CIMB, BSI, Danamon</li>
            <li>Transfer bank online</li>
        </ul>
        
        <p><strong>📱 QRIS (QR Code)</strong></p>
        <ul>
            <li>GoPay, OVO, DANA, LinkAja</li>
            <li>ShopeePay, GrabPay, dll</li>
            <li>Scan QR code untuk bayar</li>
        </ul>
        
        <p><strong>🏪 Convenience Store</strong></p>
        <ul>
            <li>Indomaret, Alfamart</li>
            <li>Bayar di toko terdekat</li>
        </ul>
        
        <p><strong>💳 Credit Card</strong></p>
        <ul>
            <li>Visa, Mastercard</li>
            <li>Pembayaran kartu kredit</li>
        </ul>
        </div>
        """)
        layout.addWidget(info_text)
        
        layout.addSpacing(20)
        
        # Continue Button
        continue_button = QPushButton("🚀 Lanjutkan ke Pembayaran")
        continue_button.clicked.connect(dialog.accept)
        layout.addWidget(continue_button)
        
        dialog.setLayout(layout)
        
        # Show dialog
        result = dialog.exec()
        return result == QDialog.DialogCode.Accepted
    
    def cancel_payment_transaction(self, order_id):
        """Cancel payment transaction"""
        try:
            if order_id:
                # Update payment transaction status to cancelled
                self.supabase._make_request(
                    'PATCH',
                    f"/rest/v1/payment_transactions?order_id=eq.{order_id}",
                    {"status": "cancelled"},
                    use_service_role=True
                )
                logger.info(f"Payment transaction {order_id} cancelled")
        except Exception as e:
            logger.error(f"Failed to cancel payment transaction: {e}")



    def process_payment(self, email, package_id):
        """Process payment untuk paket yang dipilih."""
        try:
            self.show_loading("Creating payment transaction...")
            
            # Simulasi request ke server payment
            import time
            time.sleep(1)  # Simulate network request
            
            # Buat URL payment simulasi (ganti dengan real payment gateway)
            payment_url = f"https://payment.streammateai.com?email={email}&package={package_id}"
            
            # Buka browser untuk payment
            from PyQt6.QtGui import QDesktopServices
            from PyQt6.QtCore import QUrl
            
            QDesktopServices.openUrl(QUrl(payment_url))
            
            self.hide_loading()
            
            # Show info message
            QMessageBox.information(
                self,
                "Payment Created",
                f"Payment page has been opened in browser.\n\n"
                f"After successful payment, credits will be automatically added to your account.\n\n"
                f"Close this message and refresh status to see updates."
            )
            
        except Exception as e:
            self.hide_loading()
            QMessageBox.critical(
                self,
                "Payment Error",
                f"Failed to create payment transaction:\n{str(e)}"
            )

    def show_loading(self, message="Processing..."):
        """Show loading state."""
        # Disable buttons during loading
        for btn in self.findChildren(QPushButton):
            btn.setEnabled(False)
            
    def hide_loading(self):
        """Hide loading state."""
        # Re-enable buttons
        for btn in self.findChildren(QPushButton):
            btn.setEnabled(True)
            
    def logout(self):
        """Logout dari aplikasi"""
        if self.parent and hasattr(self.parent, 'logout'):
            self.parent.logout()
        else:
            QMessageBox.information(self, "Logout", "Logout feature not available")

    def start_demo(self):
        """Start demo mode with 30 minutes limit."""
        try:
            self.show_loading("Activating Demo Mode...")
            
            # DEBUG: Tambahkan debugging yang komprehensif
            print("\n=== DEMO ACTIVATION DEBUG START ===")
            print("1. Checking for user login status...")
            
            # Import QMessageBox to fix the "cannot access local variable" error
            from PyQt6.QtWidgets import QMessageBox
            
            self.show_loading("Checking Demo & Credit Status...")
            
            try:
                # Periksa file subscription secara langsung untuk debugging
                subscription_file = Path("config/subscription_status.json")
                if subscription_file.exists():
                    print(f"2. Subscription file exists: {subscription_file}")
                    try:
                        with open(subscription_file, 'r', encoding='utf-8') as f:
                            raw_content = f.read()
                            print(f"3. Raw file content (first 100 chars): {raw_content[:100]}...")
                            if raw_content.strip():
                                subscription_data = json.loads(raw_content)
                                print(f"4. Parsed JSON email: {subscription_data.get('email', 'NOT FOUND')}")
                            else:
                                print("3. File exists but is EMPTY!")
                    except Exception as e:
                        print(f"3. ERROR reading file: {str(e)}")
                else:
                    print("2. Subscription file DOES NOT EXIST")
                
                # Juga cek settings.json
                settings_file = Path("config/settings.json")
                if settings_file.exists():
                    print(f"5. Settings file exists: {settings_file}")
                    try:
                        with open(settings_file, 'r', encoding='utf-8') as f:
                            settings_data = json.load(f)
                            user_data = settings_data.get("user_data", {})
                            print(f"6. Settings user_data: {user_data}")
                            settings_email = user_data.get("email")
                            print(f"7. Settings email: {settings_email}")
                    except Exception as e:
                        print(f"6. ERROR reading settings: {str(e)}")
                        
                # Periksa juga email yang mungkin disimpan di instance
                instance_email = getattr(self, 'email', None)
                print(f"8. Instance email attribute: {instance_email}")

                # Panggil get_current_credit_info yang sudah diperbaiki
                credit_info = self.get_current_credit_info()
                print(f"9. Credit info from function: {credit_info}")
                
                # Logika utama untuk mendapatkan email yang digunakan
                logged_in_email = credit_info.get("email")
                if not logged_in_email and hasattr(self, 'email'):
                    logged_in_email = self.email
                    print(f"10. No email in credit_info, using instance email: {logged_in_email}")
                
                # PERBAIKAN: Jika masih tidak ada email, coba ambil dari settings.json
                if not logged_in_email and settings_file.exists():
                    try:
                        with open(settings_file, 'r', encoding='utf-8') as f:
                            settings_data = json.load(f)
                        settings_email = settings_data.get("user_data", {}).get("email")
                        if settings_email:
                            logged_in_email = settings_email
                            print(f"11. Using email from settings.json: {logged_in_email}")
                    except Exception as e:
                        print(f"11. ERROR reading settings for email fallback: {str(e)}")

                print(f"12. Final logged_in_email: {logged_in_email}")
                current_credits = float(credit_info.get("hours_credit", 0.0))
                print(f"13. Current credits: {current_credits}")
                
                # PERBAIKAN: Jika email masih NULL, tanya pengguna apakah ingin login
                if not logged_in_email:
                    self.hide_loading()
                    print("14. NO EMAIL FOUND ANYWHERE. Showing login option...")
                    
                    response = QMessageBox.question(
                        self,
                        "Login Recommended",
                        "It seems you're not logged in. Would you like to login first for a better demo experience?\n\n"
                        "• YES: Go to login page\n"
                        "• NO: Continue with manual email input",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                    )
                    
                    if response == QMessageBox.StandardButton.Yes:
                        print("15. User chose to login first.")
                        # Redirect to login page/tab if available
                        if self.parent and safe_attr_check(self.parent, 'show_login_tab'):
                            self.parent.show_login_tab()
                        return
                    else:
                        print("15. User chose to continue with manual email.")
                        self.prompt_for_demo_email()
                        return

                # 1. Jika pengguna login, periksa kredit mereka terlebih dahulu
                if logged_in_email:
                    print(f"14. Logged in as {logged_in_email}, credits: {current_credits}")
                    
                    # ATURAN BARU: Jika kredit > 50, jangan izinkan demo
                    if current_credits > 50:
                        self.hide_loading()
                        print("15. Credits > 50, demo not allowed.")
                        QMessageBox.information(self, "Demo Not Available",
                            f"Hi {logged_in_email},<br><br>"
                            f"Your current credit balance (<b>{current_credits:.1f}</b>) is sufficient. The free demo is intended for new users or those with low credit.<br><br>"
                            "Please use your existing credits to enjoy all features. Thank you! 🙏")
                        return

                    # 2. Jika kredit <= 50, lanjutkan untuk memeriksa status demo harian
                    print(f"15. Credit is low ({current_credits}). Checking daily demo status...")
                    status_response = requests.get(f"{self.server_url}/api/demo/status/{logged_in_email}", timeout=10)
                    
                    self.hide_loading()
                    print(f"16. Demo status response: HTTP {status_response.status_code}")
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json().get("data", {})
                        can_demo = status_data.get("can_demo", False)
                        print(f"17. Can demo: {can_demo}")
                        
                        if can_demo:
                            # Demo tersedia, tanyakan konfirmasi sebelum aktivasi
                            reply = QMessageBox.question(self, "Activate Demo?",
                                f"Demo is available for <b>{logged_in_email}</b>. ✨<br><br>"
                                "Would you like to activate your 30-minute free demo now?",
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel)
                            if reply == QMessageBox.StandardButton.Yes:
                                print("18. User confirmed demo activation.")
                                self.activate_demo_for_email(logged_in_email)
                            else:
                                print("18. User cancelled demo activation.")
                        else:
                            # Demo sudah digunakan hari ini
                            next_reset = status_data.get('next_reset_wib', 'tomorrow at 00:00 WIB')
                            print(f"18. Demo already used. Next reset: {next_reset}")
                            QMessageBox.information(
                                self,
                                "Demo Unavailable",
                                "You can try the demo again after 00:00 WIB (midnight) tomorrow.",
                                QMessageBox.StandardButton.Ok
                            )
                            return
                    else:
                        print(f"17. Failed to check demo status: HTTP {status_response.status_code}")
                        QMessageBox.warning(self, "Error", 
                                           f"Failed to check demo status (HTTP {status_response.status_code}). Please try again.")

                # 3. Jika tidak ada pengguna yang login, langsung minta email
                else:
                    self.hide_loading()
                    print("14. No logged-in user. Prompting for email.")
                    self.prompt_for_demo_email()

            except requests.exceptions.RequestException as e:
                print(f"ERROR: Connection error - {str(e)}")
                self.hide_loading()
                QMessageBox.critical(self, "Connection Error", f"Could not connect to the server: {e}")
            except Exception as e:
                print(f"ERROR: Unexpected error - {str(e)}")
                import traceback
                print(f"TRACEBACK: {traceback.format_exc()}")
                self.hide_loading()
                QMessageBox.critical(self, "An Error Occurred", f"An unexpected error occurred: {e}")
                
            print("=== DEMO ACTIVATION DEBUG END ===\n")

        except Exception as e:
            print(f"ERROR: Unexpected error - {str(e)}")
            import traceback
            print(f"TRACEBACK: {traceback.format_exc()}")
            self.hide_loading()
            QMessageBox.critical(self, "An Error Occurred", f"An unexpected error occurred: {e}")

    def prompt_for_demo_email(self):
        """Shows a dialog to input an email for the demo."""
        from PyQt6.QtWidgets import QInputDialog, QLineEdit, QMessageBox
        
        email, ok = QInputDialog.getText(
            self, 
            "Activate 30-Minute Demo 🚀", 
            "Enter your email to start the free demo:", 
            QLineEdit.EchoMode.Normal
        )

        if ok and email:
            # Simple but effective email validation
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if re.match(email_pattern, email):
                # Save temporary email for session
                self.email = email
                print(f"[DEMO] Email validated and saved: {email}")
                
                # Directly activate basic mode without credit check
                self.enter_basic_mode(bypass_credit_check=True)
            else:
                QMessageBox.warning(self, "Invalid Email", "Please enter a valid email address.")
        else:
            print("[DEMO] Demo activation cancelled by user.")
            
    def activate_demo_for_email(self, email):
        """Registers and activates the demo for a given email."""
        print(f"[DEMO] Activating demo for email: {email}")
        self.show_loading(f"Activating for {email}...")

        try:
            register_response = requests.post(
                f"{self.server_url}/api/demo/register",
                json={"email": email},
                timeout=15
            )
            
            self.hide_loading()

            if register_response.status_code == 200:
                register_result = register_response.json()
                if register_result.get("status") == "success":
                    # Successfully registered, now save status and activate
                    self.save_and_activate_demo_data(register_result["data"], email)
                else:
                    error_message = register_result.get('message', 'Unknown error from server')
                    QMessageBox.warning(self, "Demo Activation Failed", f"Could not activate demo: {error_message}")
            else:
                try:
                    error_data = register_response.json()
                    message = error_data.get("message", "Unknown server error")
                except json.JSONDecodeError:
                    message = register_response.text
                QMessageBox.warning(
                    self, "Server Error",
                    f"Failed to activate demo. Server responded with status {register_response.status_code}.<br><br>"
                    f"Details: {message}"
                )
        except requests.exceptions.RequestException as e:
            self.hide_loading()
            QMessageBox.critical(self, "Connection Error", f"Could not connect to the server: {e}")
        except Exception as e:
            self.hide_loading()
            QMessageBox.critical(self, "An Error Occurred", f"A system error occurred: {e}")
            
    def save_and_activate_demo_data(self, demo_info, email):
        """Saves the demo data to subscription_status.json and activates the UI."""
        from datetime import datetime, timedelta
        import pytz
        
        now_utc = datetime.now(pytz.UTC)
        now_wib = now_utc.astimezone(pytz.timezone('Asia/Jakarta'))
        expire_wib = now_wib + timedelta(minutes=30)
        
        # ✅ PERBAIKAN: Demo mode sekarang mendukung Basic dan Pro
        # Tanya user mode mana yang ingin diaktifkan
        from PyQt6.QtWidgets import QMessageBox, QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
        
        demo_mode_dialog = QDialog(self)
        demo_mode_dialog.setWindowTitle("Choose Demo Mode 🚀")
        demo_mode_dialog.setModal(True)
        demo_mode_dialog.setStyleSheet("""
            QDialog {
                background-color: #f8f9fa;
                border-radius: 10px;
            }
            QLabel {
                font-size: 14px;
                color: #2c3e50;
            }
            QPushButton {
                padding: 15px 30px;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
                min-width: 200px;
            }
        """)
        
        layout = QVBoxLayout(demo_mode_dialog)
        
        # Title
        title = QLabel("Choose your demo mode:")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Basic mode button
        basic_btn = QPushButton("🤖 Basic Mode Demo")
        basic_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
            }
            QPushButton:hover {
                background-color: #45A049;
            }
        """)
        basic_btn.clicked.connect(lambda: self._activate_demo_mode("basic", demo_mode_dialog, email, expire_wib, demo_info))
        layout.addWidget(basic_btn)
        
        # Pro mode button
        pro_btn = QPushButton("🚀 Pro Mode Demo")
        pro_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        pro_btn.clicked.connect(lambda: self._activate_demo_mode("pro", demo_mode_dialog, email, expire_wib, demo_info))
        layout.addWidget(pro_btn)
        
        # Info
        info = QLabel("Both modes include 30-minute demo with full features!")
        info.setStyleSheet("font-size: 12px; color: #666; margin-top: 10px;")
        layout.addWidget(info)
        
        demo_mode_dialog.exec()
    
    def _activate_demo_mode(self, mode, dialog, email, expire_wib, demo_info):
        """Activate specific demo mode"""
        from datetime import datetime
        
        # Create subscription data based on mode
        subscription_data = {
            "email": email,
            "status": "demo",
            "package": mode,
            "expire_date": expire_wib.isoformat(),
            "expire_date_wib": expire_wib.strftime("%Y-%m-%d %H:%M:%S WIB"),
            "demo_duration_minutes": demo_info.get("remaining_minutes", 30),
            "activated_at": expire_wib.isoformat(),
            "updated_at": datetime.now().isoformat(),
            "hours_credit": 0,
            "hours_used": 0,
            "demo_used": True,
            "timezone": "Asia/Jakarta"
        }
        
        # Add mode-specific data
        if mode == "pro":
            subscription_data.update({
                "pro": {"active": True, "purchased_at": datetime.now().isoformat(), "email": email, "package": "pro"},
                "basic": {"active": True, "purchased_at": datetime.now().isoformat(), "email": email, "package": "basic"}
            })
        else:  # basic
            subscription_data.update({
                "basic": {"active": True, "purchased_at": datetime.now().isoformat(), "email": email, "package": "basic"}
            })
        
        # ✅ SIMPAN KE SUPABASE
        try:
            from modules_client.supabase_client import SupabaseClient
            supabase = SupabaseClient()
            
            # Simpan demo data ke Supabase
            demo_data = {
                "email": email,
                "demo_mode": mode,
                "demo_started_at": datetime.now().isoformat(),
                "demo_expires_at": expire_wib.isoformat(),
                "demo_duration_minutes": demo_info.get("remaining_minutes", 30),
                "demo_used": True,
                "demo_reset_at": (expire_wib + timedelta(days=1)).isoformat()  # Reset setelah 24 jam
            }
            
            # Insert atau update demo data
            demo_result = supabase._make_request(
                'POST',
                '/rest/v1/demo_usage',
                demo_data,
                use_service_role=True
            )
            
            if demo_result:
                print(f"[DEBUG] Demo data saved to Supabase: {demo_result}")
            else:
                print(f"[DEBUG] Failed to save demo data to Supabase")
                
        except Exception as e:
            print(f"[DEBUG] Error saving demo data to Supabase: {e}")
        
        # Save to file (local backup)
        subscription_file = Path("config/subscription_status.json")
        with open(subscription_file, "w", encoding="utf-8") as f:
            json.dump(subscription_data, f, indent=2, ensure_ascii=False)

        # Activate the chosen mode
        if self.parent and hasattr(self.parent, 'pilih_paket'):
            self.parent.pilih_paket(mode)
        self.package_activated.emit(mode)
        
        self.demo_active = True
        self.demo_start_time = datetime.now()
        
        # Close dialog
        dialog.close()
        
        # Show success message
        expire_display = expire_wib.strftime("%H:%M WIB")
        mode_name = "Pro" if mode == "pro" else "Basic"
        QMessageBox.information(
            self, f"{mode_name} Demo Activated! 🚀",
            f"30-minute {mode_name} demo for <b>{email}</b> is now active! ✨<br><br>"
            f"⏰ Duration: 30 minutes<br>"
            f"🕐 Ends at: <b>{expire_display}</b><br>"
            f"🎯 Mode: <b>{mode_name}</b><br><br>"
            f"The {mode_name} mode is now active. Go to the CoHost tab to start!"
        )
        
        self.refresh_credits()

    def darken_color(self, color):
        """Membuat warna lebih gelap untuk hover effect"""
        color_map = {
            "#4CAF50": "#388E3C",
            "#FF9800": "#F57C00",
            "#1877F2": "#0C63D4",
            "#42B883": "#33A06F"
        }
        return color_map.get(color, color)
        
    def closeEvent(self, event):
        """Handle close event - OPTIMASI: Stop semua timer"""
        # Stop timer
        if safe_attr_check(self, 'credit_timer'):
            self.credit_timer.stop()
        if safe_attr_check(self, 'demo_monitor_timer'):
            self.demo_monitor_timer.stop()
        event.accept()
        
    def setVisible(self, visible):
        """OPTIMASI: Start/stop timer berdasarkan visibility dan refresh saat visible"""
        super().setVisible(visible)
        if safe_attr_check(self, 'credit_timer'):
            if visible:
                self.credit_timer.start()
                # ✅ PERBAIKAN: Refresh credits saat tab visible untuk cek demo reset
                QTimer.singleShot(100, self.refresh_credits)
                
                # Also immediately check demo status if needed
                QTimer.singleShot(200, self.check_demo_status)
            else:
                self.credit_timer.stop()

    def get_current_credit_info(self):
        """
        Safely reads the current subscription status from the JSON file.
        Returns a dictionary with credit info or defaults if not found.
        """
        try:
            subscription_file = Path("config/subscription_status.json")
            if subscription_file.exists() and subscription_file.stat().st_size > 0:
                with open(subscription_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Pastikan data yang dikembalikan adalah dictionary
                    return data if isinstance(data, dict) else {}
            # Jika file tidak ada atau kosong, kembalikan dictionary kosong
            return {}
        except (json.JSONDecodeError, IOError) as e:
            print(f"[ERROR] Failed to read or parse subscription status file: {e}")
            # Jika ada error, kembalikan dictionary kosong untuk mencegah crash
            return {}

    def _get_basic_credits(self):
        """Get Basic mode credits (separate from Pro credits)"""
        try:
            email = self.cfg.get("user_data", {}).get("email", "")
            if not email:
                return 0.0
            
            # Cek dari Supabase untuk kredit Basic
            credit_data = self.supabase.get_credit_balance(email)
            if credit_data and credit_data.get("status") == "success":
                data = credit_data.get("data", {})
                return float(data.get("basic_credits", 0))
            
            # Fallback ke subscription file
            subscription_file = Path("config/subscription_status.json")
            if subscription_file.exists():
                with open(subscription_file, 'r', encoding='utf-8') as f:
                    sub_data = json.load(f)
                    return float(sub_data.get("basic_credits", 0))
            
            return 0.0
            
        except Exception as e:
            print(f"[ERROR] Error getting basic credits: {e}")
            return 0.0

    def _get_pro_credits(self):
        """Get Pro mode credits (separate from Basic credits)"""
        try:
            email = self.cfg.get("user_data", {}).get("email", "")
            if not email:
                return 0.0
            
            # Cek dari Supabase untuk kredit Pro
            credit_data = self.supabase.get_credit_balance(email)
            if credit_data and credit_data.get("status") == "success":
                data = credit_data.get("data", {})
                return float(data.get("pro_credits", 0))
            
            # Fallback ke subscription file
            subscription_file = Path("config/subscription_status.json")
            if subscription_file.exists():
                with open(subscription_file, 'r', encoding='utf-8') as f:
                    sub_data = json.load(f)
                    return float(sub_data.get("pro_credits", 0))
            
            return 0.0
            
        except Exception as e:
            print(f"[ERROR] Error getting pro credits: {e}")
            return 0.0

    def enter_basic_mode(self, bypass_credit_check=False):
        """Masuk ke mode basic dengan validasi dan UI update."""
        from PyQt6.QtWidgets import QMessageBox
        import logging
        logger = logging.getLogger(__name__)
        try:
            # Check credit availability (skip if bypass flag is set)
            if not bypass_credit_check:
                # ✅ PERBAIKAN: Gunakan Supabase untuk cek kredit Basic
                basic_credits = self._get_basic_credits()
                MIN_CREDIT_REQUIRED = 50.0
                if basic_credits < MIN_CREDIT_REQUIRED:
                    QMessageBox.warning(
                        self, "Credits Insufficient",
                        f"Credits are insufficient for Basic Mode.\n\n"
                        f"Current Basic credits: {basic_credits:.1f}\n"
                        f"Minimum required: {MIN_CREDIT_REQUIRED} Basic credits\n\n"
                        f"Please purchase Basic package first."
                    )
                    return
                # Konfirmasi masuk mode Basic
                reply = QMessageBox.question(
                    self, "Enter Basic Mode",
                    f"Enter Basic Mode?\n\n"
                    f"Basic credits available: {basic_credits:.1f}\n"
                    f"Estimated: ~{int(basic_credits / 0.45)} auto-reply\n\n"
                    f"Basic Mode will be active and start using Basic credits.",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply != QMessageBox.StandardButton.Yes:
                    return
            # ✅ PERBAIKAN UTAMA: Langsung panggil parent method
            if self.parent and safe_attr_check(self.parent, 'pilih_paket'):
                print(f"[DEBUG] Calling parent.pilih_paket('basic') directly")
                self.parent.pilih_paket("basic")
                if not bypass_credit_check:
                    QMessageBox.information(
                        self, "Basic Mode Active",
                        f"Basic Mode successfully activated!\n\n"
                        f"Basic credits available: {basic_credits:.1f}\n"
                        f"The app will switch to Basic mode."
                    )
            else:
                print(f"[DEBUG] Parent not available, using signal emit")
                self.package_activated.emit("basic")
                if not bypass_credit_check:
                    QMessageBox.information(
                        self, "Basic Mode Active",
                        f"Basic Mode successfully activated!\n\n"
                        f"Basic credits available: {basic_credits:.1f}\n"
                        f"Basic Mode activated."
                    )
        except Exception as e:
            logger.error(f"Error entering basic mode: {e}")
            QMessageBox.critical(
                self, "Error",
                f"Failed to enter Basic Mode: {str(e)}"
            )

    def enter_pro_mode(self, bypass_credit_check=False):
        """Masuk ke mode pro dengan validasi dan UI update."""
        from PyQt6.QtWidgets import QMessageBox
        import logging
        logger = logging.getLogger(__name__)
        try:
            # Check Pro credit availability (separate from Basic credits)
            if not bypass_credit_check:
                pro_credits = self._get_pro_credits()
                MIN_CREDIT_REQUIRED = 100000.0  # 100,000 credits for Pro (consistent with purchase price)
                if pro_credits < MIN_CREDIT_REQUIRED:
                    QMessageBox.warning(
                        self, "Pro Credits Insufficient",
                        f"Pro credits are insufficient for Pro Mode.\n\n"
                        f"Current Pro credits: {pro_credits:.1f}\n"
                        f"Minimum required: {MIN_CREDIT_REQUIRED:,.0f} Pro credits\n\n"
                        f"Please purchase Pro package first."
                    )
                    return
                # Konfirmasi masuk mode Pro
                reply = QMessageBox.question(
                    self, "Enter Pro Mode",
                    f"Enter Pro Mode?\n\n"
                    f"Pro credits available: {pro_credits:.1f}\n"
                    f"Estimated: ~{int(pro_credits / 0.45)} auto-reply\n\n"
                    f"Pro Mode will be active and start using Pro credits.",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply != QMessageBox.StandardButton.Yes:
                    return
            # ✅ PERBAIKAN UTAMA: Langsung panggil parent method
            if self.parent and safe_attr_check(self.parent, 'pilih_paket'):
                print(f"[DEBUG] Calling parent.pilih_paket('pro') directly")
                self.parent.pilih_paket("pro")
                if not bypass_credit_check:
                    QMessageBox.information(
                        self, "Pro Mode Active",
                        f"Pro Mode successfully activated!\n\n"
                        f"Pro credits available: {pro_credits:.1f}\n"
                        f"The app will switch to Pro mode."
                    )
            else:
                print(f"[DEBUG] Parent not available, using signal emit")
                self.package_activated.emit("pro")
                if not bypass_credit_check:
                    QMessageBox.information(
                        self, "Pro Mode Active",
                        f"Pro Mode successfully activated!\n\n"
                        f"Pro credits available: {pro_credits:.1f}\n"
                        f"Pro Mode activated."
                    )
        except Exception as e:
            logger.error(f"Error entering pro mode: {e}")
            QMessageBox.critical(
                self, "Error",
                f"Failed to enter Pro Mode: {str(e)}"
            )

    def activate_demo(self):
        """Aktifkan demo dengan validasi daily limit dan notifikasi yang tepat"""
        try:
            # ✅ PERBAIKAN: Cek status demo lokal terlebih dahulu
            subscription_file = Path("config/subscription_status.json")
            if subscription_file.exists():
                try:
                    with open(subscription_file, "r", encoding="utf-8") as f:
                        local_data = json.load(f)
                    
                    local_status = local_data.get("status", "")
                    
                    # Jika demo masih aktif
                    if local_status == "demo":
                        QMessageBox.information(
                            self,
                            "Demo Currently Active 🎮",
                            "Demo mode is currently running! ⏰\n\n"
                            "Use the available Basic features.\n"
                            "Check the Cohost tab to start streaming!"
                        )
                        return
                    
                    # Jika demo expired atau sudah digunakan
                    elif local_status == "expired" or local_data.get("demo_used", False) or local_data.get("demo_active", False) == False:
                        # Hitung waktu reset (jam 00:00 besok)
                        from datetime import datetime, timedelta
                        import pytz
                        
                        wib = pytz.timezone('Asia/Jakarta')
                        now_wib = datetime.now(wib)
                        tomorrow_midnight = (now_wib + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
                        time_until_reset = tomorrow_midnight - now_wib
                        
                        hours_left = int(time_until_reset.total_seconds() / 3600)
                        mins_left = int((time_until_reset.total_seconds() % 3600) / 60)
                        
                        QMessageBox.information(
                            self,
                            "Demo Already Used Today 📅",
                            f"30-minute demo has already been used today! ✨\n\n"
                            f"🕐 Demo will reset at: {tomorrow_midnight.strftime('%d/%m/%Y at 00:00 WIB')}\n"
                            f"⏳ Time remaining: {hours_left} hours {mins_left} minutes\n\n"
                            f"💡 Temporary solutions:\n"
                            f"• Purchase credit packages to continue\n"
                            f"• Or wait for demo reset tomorrow morning\n\n"
                            f"Thank you for using StreamMate AI! 🚀"
                        )
                        return
                        
                except Exception as e:
                    print(f"[DEBUG] Error checking local demo status: {e}")
            
            # Lanjutkan ke server check jika lokal OK
            self.start_demo()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "An Error Occurred",
                f"Sorry, an error occurred while activating demo:\n\n{str(e)}\n\n"
                f"Please try again or contact support if the problem persists."
            )

    def setup_demo_monitoring(self):
        """Setup demo monitoring system."""
        # Demo monitoring timer - optimized interval for less resource usage
        self.demo_monitor_timer = QTimer()
        self.demo_monitor_timer.timeout.connect(self.check_demo_status)
        self.demo_monitor_timer.start(120000)  # ✅ OPTIMASI: Check every 1 minute instead of 10 seconds
        
        print("[DEMO-MONITOR] Demo monitoring system initialized")
        # Check demo status on startup
        self.check_demo_status()

    def check_demo_status(self):
        """Check demo status dan handle auto-stop."""
        try:
            subscription_file = Path("config/subscription_status.json")
            if not subscription_file.exists():
                return
                
            with open(subscription_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            status = data.get("status", "")
            
            # Debug output for monitoring
            if status == "demo":
                print("[DEMO-MONITOR] Found active demo status")
            
            if status != "demo":
                if self.demo_active:
                    print("[DEMO-MONITOR] Demo status changed from active to inactive")
                self.demo_active = False
                return
                
            # Demo sedang aktif, cek apakah sudah expired
            expire_date_str = data.get("expire_date", "")
            if not expire_date_str:
                print("[DEMO-MONITOR] WARNING: Demo status is active but no expiration date found")
                return
                
            from datetime import datetime
            import pytz
            
            # Parse expire time
            try:
                if '+' in expire_date_str:
                    expire_date = datetime.fromisoformat(expire_date_str)
                else:
                    expire_date = datetime.fromisoformat(expire_date_str)
                    if expire_date.tzinfo is None:
                        wib = pytz.timezone('Asia/Jakarta')
                        expire_date = wib.localize(expire_date)
                
                now = datetime.now(pytz.timezone('Asia/Jakarta'))
                
                # Jika demo sudah expired
                if now >= expire_date:
                    print(f"[DEMO-MONITOR] Demo expired! Current time: {now.isoformat()}, Expire time: {expire_date.isoformat()}")
                    self.stop_demo_auto()
                else:
                    # Demo masih aktif, update countdown
                    remaining = expire_date - now
                    remaining_minutes = int(remaining.total_seconds() / 60)
                    remaining_seconds = int(remaining.total_seconds() % 60)
                    print(f"[DEMO-MONITOR] Demo active - {remaining_minutes} minutes {remaining_seconds} seconds remaining")
                    self.demo_active = True
                    
            except Exception as e:
                print(f"[DEMO-MONITOR] Error parsing expire date: {e}")
                import traceback
                print(traceback.format_exc())
                
        except Exception as e:
            print(f"[DEMO-MONITOR] Error checking demo status: {e}")
            import traceback
            print(traceback.format_exc())

    def stop_demo_auto(self):
        """Stop demo otomatis setelah 30 menit."""
        try:
            print("[DEMO] Auto-stopping demo after timeout...")
            
            # 1. Update status ke expired di file JSON
            subscription_file = Path("config/subscription_status.json")
            if subscription_file.exists():
                with open(subscription_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                # Hanya lanjutkan jika status masih 'demo' untuk menghindari konflik
                if data.get("status") == "demo":
                    data["status"] = "expired"
                    data["demo_active"] = False
                    data["demo_used"] = True
                    
                    with open(subscription_file, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
                    print("[DEMO-TIMEOUT] Subscription file updated: status=expired, demo_used=True")
                else:
                    print("[DEMO-TIMEOUT] Demo already stopped by another process. Aborting auto-stop.")
                    return

            # 2. Hentikan auto-reply cohost secara paksa
            self.package_activated.emit("inactive") # Ini akan mematikan cohost
            
            # 3. Emit sinyal bahwa demo sudah berakhir untuk pindah tab
            print("[DEMO-TIMEOUT] Emitting demo_expired_signal to switch tab")
            self.demo_expired_signal.emit()

            # 4. Refresh UI di tab ini
            self.refresh_credits()
            
            # 5. Tampilkan notifikasi
            QMessageBox.information(
                self,
                "Demo Selesai ⏰",
                "Demo 30 menit telah selesai!\n\n"
                "Anda akan diarahkan kembali ke halaman subscription."
            )
            
            print("[DEMO-TIMEOUT] Demo auto-stop completed successfully.")
            
        except Exception as e:
            print(f"[DEMO-TIMEOUT] Error during auto-stop: {e}")

    def refresh_supabase_data(self):
        """Refresh data dari Supabase"""
        try:
            email = self.cfg.get("user_data", {}).get("email", "")
            if not email:
                return
                
            # Call Supabase API
            credit_data = self.supabase.get_credit_balance(email)
            
            if credit_data and credit_data.get("status") == "success":
                data = credit_data.get("data", {})
                
                # Update local file
                self.update_local_subscription_file(
                    float(data.get("wallet_balance", 0)),
                    float(data.get("total_spent", 0))
                )
                
                print(f"[SYNC] ✅ Successfully synced Supabase data to local file")
                
            else:
                print(f"Supabase API error: {credit_data}")
                
        except Exception as e:
            print(f"Error refreshing Supabase data: {e}")

    def update_local_subscription_file(self, wallet_balance, total_spent):
        """Update local subscription file dengan data dari Supabase"""
        try:
            subscription_file = Path("config/subscription_status.json")
            
            if subscription_file.exists():
                with open(subscription_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                data = {}
            
            # Update dengan data Supabase
            data["credit_balance"] = wallet_balance
            data["credit_used"] = total_spent
            data["updated_at"] = datetime.now().isoformat()
            
            with open(subscription_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            print(f"Error updating subscription file: {e}")

    def show_topup_options(self):
        """Show top-up options dialog"""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame, QMessageBox, QScrollArea, QWidget
        
        dialog = QDialog(self)
        dialog.setWindowTitle("💳 Top-up Credits")
        dialog.setModal(True)
        dialog.resize(600, 500)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #F8F9FA;
            }
            QLabel {
                color: #333;
            }
        """)
        
        # Main layout
        main_layout = QVBoxLayout(dialog)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header = QLabel("💰 Choose Top-up Package")
        header.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #4CAF50;
                text-align: center;
            }
        """)
        main_layout.addWidget(header)
        
        # Info
        info = QLabel("💡 Top-up credits with real money via iPaymu payment gateway\n💰 1:1 ratio - Rp 50.000 = 50.000 credits, Rp 100.000 = 100.000 credits")
        info.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #666;
                text-align: center;
                font-style: italic;
                margin-bottom: 20px;
            }
        """)
        info.setWordWrap(True)
        main_layout.addWidget(info)
        
        # Scrollable content area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: #E0E0E0;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #BDBDBD;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #9E9E9E;
            }
        """)
        
        # Content widget for scroll area
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(15)
        
        # Get packages - RASIO 1:1 (1 Rupiah = 1 Credit)
        try:
            from modules_client.credit_wallet_client import get_credit_packages
            packages = get_credit_packages()
        except:
            packages = [
                {"id": "starter", "name": "🎯 Starter Pack", "price_idr": 50000, "total_credits": 50000, "popular": False},
                {"id": "regular", "name": "🚀 Regular Pack", "price_idr": 100000, "total_credits": 100000, "popular": True},
                {"id": "premium", "name": "💎 Premium Pack", "price_idr": 300000, "total_credits": 300000, "popular": False}
            ]
        
        # Package cards
        for pkg in packages:
            card = QFrame()
            card.setStyleSheet(f"""
                QFrame {{
                    background-color: white;
                    border: 2px solid {'#4CAF50' if pkg.get('popular', False) else '#E0E0E0'};
                    border-radius: 10px;
                    padding: 15px;
                    margin: 5px;
                }}
            """)
            
            card_layout = QVBoxLayout(card)
            
            # Package header
            header_layout = QHBoxLayout()
            
            name_label = QLabel(pkg['name'])
            name_label.setStyleSheet("font-size: 16px; font-weight: bold;")
            header_layout.addWidget(name_label)
            
            if pkg.get('popular', False):
                popular_label = QLabel("🔥 POPULAR")
                popular_label.setStyleSheet("""
                    background-color: #4CAF50;
                    color: white;
                    padding: 2px 8px;
                    border-radius: 10px;
                    font-size: 10px;
                    font-weight: bold;
                """)
                header_layout.addWidget(popular_label)
            
            header_layout.addStretch()
            card_layout.addLayout(header_layout)
            
            # Package details
            price_label = QLabel(f"💵 Rp {pkg['price_idr']:,}")
            price_label.setStyleSheet("font-size: 14px; color: #2E7D32; font-weight: bold;")
            card_layout.addWidget(price_label)
            
            credits_label = QLabel(f"💰 {pkg['total_credits']:,} Credits")
            credits_label.setStyleSheet("font-size: 14px; color: #1976D2; font-weight: bold;")
            card_layout.addWidget(credits_label)
            
            # Top-up button
            topup_btn = QPushButton(f"💳 Top-up {pkg['name']}")
            topup_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {'#4CAF50' if pkg.get('popular', False) else '#2196F3'};
                    color: white;
                    padding: 10px;
                    border-radius: 8px;
                    font-weight: bold;
                    margin-top: 10px;
                }}
                QPushButton:hover {{
                    background-color: {'#45A049' if pkg.get('popular', False) else '#1976D2'};
                }}
            """)
            topup_btn.clicked.connect(lambda checked, p=pkg: self.process_topup(p, dialog))
            card_layout.addWidget(topup_btn)
            
            content_layout.addWidget(card)
        
        # Set content widget to scroll area
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)
        
        # Close button
        close_btn = QPushButton("❌ Close")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #666;
                color: white;
                padding: 10px 20px;
                border-radius: 8px;
                font-weight: bold;
                margin-top: 10px;
            }
            QPushButton:hover {
                background-color: #555;
            }
        """)
        close_btn.clicked.connect(dialog.close)
        main_layout.addWidget(close_btn)
        
        dialog.exec()

    def process_topup(self, package, dialog):
        """Process top-up purchase via iPaymu with 1:1 ratio"""
        from PyQt6.QtWidgets import QMessageBox
        import webbrowser
        
        try:
            # Get user email
            email = self.cfg.get("user_data", {}).get("email", "")
            if not email:
                QMessageBox.warning(self, "Login Required", "Please login first to top-up credits")
                return
            
            # Verify 1:1 ratio
            if package['price_idr'] != package['total_credits']:
                QMessageBox.warning(self, "Invalid Package", f"Package ratio error: Price Rp {package['price_idr']:,} should equal {package['total_credits']:,} credits")
                return
            
            # Create order ID
            import time
            order_id = f"{email}_{int(time.time())}"
            
            # Save transaction record to VPS server first - SKIP IN SUPABASE-ONLY MODE
            if not _is_supabase_only_mode():
                try:
                    import requests
                    vps_url = "http://69.62.79.238:8000"
                    transaction_data = {
                        "email": email,
                        "order_id": order_id,
                        "package": package['name'],
                        "amount": package['price_idr'],
                        "credits": package['total_credits'],
                        "status": "pending"
                    }
                    
                    response = requests.post(
                        f"{vps_url}/api/payment/save_transaction",
                        json=transaction_data,
                        timeout=10
                    )
                    
                    if response.status_code != 200:
                        print(f"[TOPUP] Failed to save transaction to VPS: {response.status_code}")
                        # Continue anyway, callback will handle it
                        
                except Exception as e:
                    print(f"[TOPUP] Error saving transaction to VPS: {e}")
                    # Continue anyway, callback will handle it
            else:
                print(f"✅ Supabase-only mode: Skipping VPS transaction save for {package['name']}")
            
            # Create payment transaction via Supabase first
            try:
                payment_result = self.supabase.create_payment_transaction(
                    email=email,
                    package=package['name'],
                    amount=package['price_idr']
                )
                
                if payment_result and payment_result.get("status") == "success":
                    # Get iPaymu payment URL
                    ipaymu_url = self.create_ipaymu_payment(
                        email=email,
                        package=package,
                        order_id=order_id
                    )
                    
                    if ipaymu_url:
                        # Show payment info dialog first
                        if self.show_payment_info_dialog():
                            # Show confirmation dialog
                            confirm = QMessageBox.question(
                                self, "Redirect to iPaymu", 
                                f"You will be redirected to iPaymu to complete payment for:\n\n"
                                f"📦 Package: {package['name']}\n"
                                f"💰 Amount: Rp {package['price_idr']:,}\n"
                                f"✅ Credits: {package['total_credits']:,} (1:1 ratio)\n\n"
                                f"Click 'Yes' to proceed to payment page.",
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                            )
                            
                            if confirm == QMessageBox.StandardButton.Yes:
                                # Open iPaymu payment page
                                webbrowser.open(ipaymu_url)
                                
                                QMessageBox.information(
                                    self, "Payment Page Opened", 
                                    f"iPaymu payment page has been opened in your browser.\n\n"
                                    f"Please complete the payment and return to this application.\n"
                                    f"Your credits will be added automatically after payment confirmation."
                                )
                                
                                dialog.close()
                            else:
                                # Cancel payment transaction
                                self.cancel_payment_transaction(order_id)
                        else:
                            # User cancelled from info dialog
                            self.cancel_payment_transaction(order_id)
                    else:
                        error_msg = "Failed to create iPaymu payment URL"
                        
                        # Check if it's a verification issue
                        if "test transaksi" in str(e).lower():
                            error_msg = """❌ Akun iPaymu production belum terverifikasi!

💡 Solusi:
1. Login ke https://my.ipaymu.com
2. Verifikasi akun Anda
3. Pastikan Virtual Account sudah aktif
4. Coba lagi setelah verifikasi selesai

Atau gunakan sandbox mode untuk testing."""
                        
                        QMessageBox.warning(self, "Payment Error", error_msg)
                else:
                    QMessageBox.warning(self, "Payment Failed", f"Failed to create payment transaction: {payment_result.get('message', 'Unknown error')}")
                    
            except Exception as e:
                QMessageBox.critical(self, "Payment Error", f"Failed to process payment: {str(e)}")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")