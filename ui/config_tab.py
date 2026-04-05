# ui/config_tab.py - Tab Konfigurasi API Keys

import json
import os
import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from pathlib import Path

# Setup logger
logger = logging.getLogger(__name__)

# Create a global session for efficient connection reuse
_session = requests.Session()
retry_strategy = Retry(
    total=3,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["HEAD", "GET", "POST"]
)
adapter = HTTPAdapter(pool_connections=5, pool_maxsize=10, max_retries=retry_strategy)
_session.mount("http://", adapter)
_session.mount("https://", adapter)
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QGroupBox, QTextEdit, QMessageBox, QFrame,
    QProgressBar, QCheckBox, QComboBox, QFileDialog, QScrollArea,
    QSpinBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QIcon

from modules_client.config_manager import ConfigManager
from sales_templates import get_template_list, get_template

try:
    from ui.theme import (PRIMARY, SECONDARY, ACCENT, BG_BASE, BG_SURFACE, BG_ELEVATED,
        TEXT_PRIMARY, TEXT_MUTED, TEXT_DIM, BORDER_GOLD, BORDER,
        SUCCESS, ERROR, WARNING, INFO, RADIUS, RADIUS_SM,
        btn_success, btn_danger, btn_ghost, btn_primary, status_badge, label_subtitle)
except ImportError:
    PRIMARY = "#2563EB"; BG_BASE = "#0F1623"; BG_SURFACE = "#162032"; BG_ELEVATED = "#1E2A3B"
    TEXT_PRIMARY = "#F0F6FF"; TEXT_MUTED = "#93C5FD"; TEXT_DIM = "#4B7BBA"
    ERROR = "#EF4444"; SUCCESS = "#22C55E"; WARNING = "#F59E0B"; INFO = "#38BDF8"
    BORDER_GOLD = "#1E4585"; BORDER = "#1A2E4A"; ACCENT = "#60A5FA"
    SECONDARY = "#1E3A5F"; RADIUS = "10px"; RADIUS_SM = "6px"
    def btn_success(extra=""): return f"QPushButton {{ background-color: {SUCCESS}; color: white; border: none; border-radius: 6px; padding: 8px 18px; font-weight: 700; {extra} }} QPushButton:hover {{ background-color: #16A34A; }}"
    def btn_danger(extra=""): return f"QPushButton {{ background-color: {ERROR}; color: white; border: none; border-radius: 6px; padding: 8px 18px; font-weight: 700; {extra} }} QPushButton:hover {{ background-color: #DC2626; }}"
    def btn_ghost(extra=""): return f"QPushButton {{ background-color: {BG_ELEVATED}; color: {TEXT_MUTED}; border: 1px solid {BORDER}; border-radius: 6px; padding: 7px 18px; font-weight: 600; {extra} }}"
    def btn_primary(extra=""): return f"QPushButton {{ background-color: {PRIMARY}; color: {BG_BASE}; border: none; border-radius: 6px; padding: 8px 18px; font-weight: 700; {extra} }} QPushButton:hover {{ background-color: #F59E0B; }}"
    def status_badge(color=None, size=11): c = color or PRIMARY; return f"color: {c}; font-weight: 600; font-size: {size}px; padding: 4px 10px; background-color: {BG_ELEVATED}; border: 1px solid {c}; border-radius: 6px;"
    def label_subtitle(size=11): return f"font-size: {size}px; color: {TEXT_MUTED}; background: transparent;"

class APITestThread(QThread):
    """Thread untuk test API connection"""
    result_ready = pyqtSignal(str, bool, str)  # api_type, success, message
    
    def __init__(self, api_type, api_key):
        super().__init__()
        self.api_type = api_type
        self.api_key = api_key
    
    def run(self):
        """Test API connection"""
        try:
            if self.api_type == "deepseek":
                success, message = self.test_deepseek_api()
            elif self.api_type == "chatgpt":
                success, message = self.test_chatgpt_api()
            else:
                success, message = False, "Unknown API type"
            
            self.result_ready.emit(self.api_type, success, message)
        except Exception as e:
            self.result_ready.emit(self.api_type, False, f"Error: {str(e)}")
    
    def test_deepseek_api(self):
        """Test DeepSeek API"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "user", "content": "Hello, test connection"}
                ],
                "max_tokens": 10
            }
            
            response = _session.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=10
            )
            
            if response.status_code == 200:
                return True, "✅ DeepSeek API berhasil terhubung!"
            else:
                return False, f"❌ DeepSeek API error: {response.status_code}"
                
        except Exception as e:
            return False, f"❌ DeepSeek API gagal: {str(e)}"
    
    def test_chatgpt_api(self):
        """Test ChatGPT API"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "gpt-3.5-turbo",
                "messages": [
                    {"role": "user", "content": "Hello, test connection"}
                ],
                "max_tokens": 10
            }
            
            response = _session.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=10
            )
            
            if response.status_code == 200:
                return True, "✅ ChatGPT API berhasil terhubung!"
            else:
                return False, f"❌ ChatGPT API error: {response.status_code}"
                
        except Exception as e:
            return False, f"❌ ChatGPT API gagal: {str(e)}"

class ConfigTab(QWidget):
    """Tab Konfigurasi untuk API Keys"""
    
    def __init__(self):
        super().__init__()
        self.cfg = ConfigManager("config/settings.json")
        self.test_thread = None
        self.init_ui()
        self.load_saved_keys()
    
    def closeEvent(self, event):
        """Cleanup when tab is closed"""
        if self.test_thread and self.test_thread.isRunning():
            self.test_thread.quit()
            if not self.test_thread.wait(1000):  # Wait 1 second
                self.test_thread.terminate()
                self.test_thread.wait(100)
        event.accept()
    
    def init_ui(self):
        """Initialize UI with scroll area"""
        # Main layout for the entire widget
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Create content widget for scroll area
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Title
        title = QLabel("🔧 Konfigurasi API Keys")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"color: {PRIMARY}; margin-bottom: 20px;")
        layout.addWidget(title)

        # Description
        desc = QLabel("Konfigurasi API untuk AI Chat Response dan Google TTS")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 14px; margin-bottom: 10px;")
        layout.addWidget(desc)

        # Language setting note
        lang_note = QLabel("💡 Setting bahasa output AI ada di tab Cohost → Pilihan Bahasa")
        lang_note.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lang_note.setStyleSheet(f"color: {PRIMARY}; font-size: 12px; margin-bottom: 20px; font-style: italic; background-color: {BG_ELEVATED}; padding: 8px; border-radius: 5px;")
        layout.addWidget(lang_note)
        
        # AI Provider Section
        self.create_ai_provider_section(layout)
        
        # Viewer Greeting Section
        self.create_viewer_greeting_section(layout)
        
        # Sales Template Section
        self.create_sales_template_section(layout)
        
        # Google TTS Section
        self.create_google_tts_section(layout)
        
        # Status Section
        self.create_status_section(layout)
        
        # Buttons
        self.create_buttons(layout)
        
        # Add stretch to push content to top
        layout.addStretch()
        
        # Set content widget to scroll area
        scroll_area.setWidget(content_widget)
        
        # Add scroll area to main layout
        main_layout.addWidget(scroll_area)
        
        # Apply Gold Seller theme
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {BG_BASE};
                color: {TEXT_PRIMARY};
                font-family: 'Segoe UI', Arial, sans-serif;
            }}
            QScrollArea {{
                border: none;
                background-color: {BG_BASE};
            }}
            QScrollArea > QWidget > QWidget {{
                background-color: {BG_BASE};
            }}
            QScrollBar:vertical {{
                background-color: {BG_SURFACE};
                width: 12px;
                border-radius: 6px;
                margin: 0;
            }}
            QScrollBar::handle:vertical {{
                background-color: {BORDER_GOLD};
                border-radius: 6px;
                min-height: 20px;
                margin: 2px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {PRIMARY};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                border: none;
                background: none;
                height: 0px;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
            QGroupBox {{
                font-weight: bold;
                font-size: 14px;
                border: 2px solid {BORDER_GOLD};
                border-radius: {RADIUS};
                margin-top: 15px;
                padding-top: 15px;
                background-color: {BG_ELEVATED};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px 0 8px;
                color: {ACCENT};
                background-color: {BG_ELEVATED};
            }}
            QLineEdit {{
                background-color: {BG_SURFACE};
                border: 2px solid {BORDER};
                border-radius: 8px;
                padding: 12px 15px;
                font-size: 13px;
                color: {TEXT_PRIMARY};
                selection-background-color: {PRIMARY};
            }}
            QLineEdit:focus {{
                border: 2px solid {PRIMARY};
                background-color: {BG_ELEVATED};
            }}
            QLineEdit:hover {{
                border: 2px solid {BORDER_GOLD};
            }}
            QLineEdit[readOnly="true"] {{
                background-color: {BG_BASE};
                color: {TEXT_MUTED};
            }}
            QPushButton {{
                background-color: {PRIMARY};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-weight: bold;
                font-size: 13px;
                min-height: 20px;
            }}
            QPushButton:hover {{
                background-color: {ACCENT};
                color: {BG_BASE};
            }}
            QPushButton:pressed {{
                background-color: {SECONDARY};
            }}
            QPushButton:disabled {{
                background-color: {BORDER};
                color: {TEXT_DIM};
            }}
            QPushButton[class="secondary"] {{
                background-color: {BG_SURFACE};
                color: {TEXT_PRIMARY};
                border: 1px solid {BORDER_GOLD};
            }}
            QPushButton[class="secondary"]:hover {{
                background-color: {BG_ELEVATED};
            }}
            QPushButton[class="success"] {{
                background-color: {SUCCESS};
            }}
            QPushButton[class="success"]:hover {{
                background-color: {SUCCESS};
                opacity: 0.85;
            }}
            QPushButton[class="danger"] {{
                background-color: {ERROR};
            }}
            QPushButton[class="danger"]:hover {{
                background-color: {ERROR};
                opacity: 0.85;
            }}
            QTextEdit {{
                background-color: {BG_ELEVATED};
                border: 2px solid {BORDER_GOLD};
                border-radius: 8px;
                padding: 12px;
                font-size: 12px;
                color: {TEXT_PRIMARY};
            }}
            QComboBox {{
                background-color: {BG_SURFACE};
                border: 2px solid {BORDER};
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 13px;
                color: {TEXT_PRIMARY};
                min-width: 150px;
            }}
            QComboBox:hover {{
                border: 2px solid {BORDER_GOLD};
            }}
            QComboBox:focus {{
                border: 2px solid {PRIMARY};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 30px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid {TEXT_PRIMARY};
                margin-right: 10px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {BG_SURFACE};
                border: 1px solid {BORDER_GOLD};
                selection-background-color: {PRIMARY};
                color: {TEXT_PRIMARY};
            }}
            QLabel {{
                color: {TEXT_PRIMARY};
            }}
            QLabel[class="status-success"] {{
                color: {SUCCESS};
                font-weight: bold;
            }}
            QLabel[class="status-error"] {{
                color: {ERROR};
                font-weight: bold;
            }}
            QLabel[class="status-warning"] {{
                color: {WARNING};
                font-weight: bold;
            }}
            QLabel[class="status-info"] {{
                color: {INFO};
                font-weight: bold;
            }}
        """)
    
    def create_ai_provider_section(self, layout):
        """Create AI Provider section with flexible API key input"""
        group = QGroupBox("🤖 AI Chat Provider")
        group_layout = QVBoxLayout(group)
        group_layout.setSpacing(15)
        
        # Provider selection with better layout
        provider_layout = QHBoxLayout()
        provider_label = QLabel("Provider:")
        provider_label.setMinimumWidth(100)
        provider_layout.addWidget(provider_label)
        
        self.provider_combo = QComboBox()
        self.provider_combo.addItems(["DeepSeek", "OpenAI (ChatGPT)"])
        self.provider_combo.currentTextChanged.connect(self.on_provider_changed)
        provider_layout.addWidget(self.provider_combo)
        provider_layout.addStretch()
        group_layout.addLayout(provider_layout)
        
        # API Key input with better styling
        api_key_label = QLabel("API Key:")
        api_key_label.setMinimumWidth(100)
        group_layout.addWidget(api_key_label)
        
        # API Key input container
        api_key_container = QHBoxLayout()
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("Masukkan API Key (sk-...)")
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.textChanged.connect(self.on_api_key_changed)
        api_key_container.addWidget(self.api_key_input)
        
        # Show/Hide button with better styling
        show_btn = QPushButton("👁️")
        show_btn.setProperty("class", "secondary")
        show_btn.setMaximumWidth(50)
        show_btn.setToolTip("Show/Hide API Key")
        show_btn.clicked.connect(lambda: self.toggle_password_visibility(self.api_key_input))
        api_key_container.addWidget(show_btn)
        
        group_layout.addLayout(api_key_container)
        
        # Button container
        button_layout = QHBoxLayout()
        
        # Test button
        self.ai_test_btn = QPushButton("🔍 Test Connection")
        self.ai_test_btn.setProperty("class", "success")
        self.ai_test_btn.clicked.connect(self.test_ai_api)
        self.ai_test_btn.setEnabled(False)  # Disabled until API key is entered
        button_layout.addWidget(self.ai_test_btn)
        
        button_layout.addStretch()
        group_layout.addLayout(button_layout)
        
        # Status with better styling
        self.ai_status = QLabel("Status: Belum ada API key")
        self.ai_status.setProperty("class", "status-info")
        self.ai_status.setStyleSheet(status_badge(TEXT_DIM))
        group_layout.addWidget(self.ai_status)
        
        layout.addWidget(group)
    
    
    def create_viewer_greeting_section(self, layout):
        """Create Custom Greeting System with 10 slots (simplified without individual timers)"""
        group = QGroupBox("🎙️ Sistem Sapaan Otomatis (Custom TTS)")
        group_layout = QVBoxLayout(group)
        group_layout.setSpacing(15)

        # Description
        desc = QLabel("Sistem sapaan otomatis dengan 10 slot custom. Timer diatur di Cohost Tab. TTS disimpan untuk hemat API.")
        desc.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px; font-style: italic; padding: 5px;")
        group_layout.addWidget(desc)

        # Timer info
        timer_info = QLabel("⏱️ Timer Interval: Diatur di Cohost Tab → Greeting Timer (berlaku untuk semua slot)")
        timer_info.setStyleSheet(f"color: {WARNING}; font-size: 12px; font-weight: bold; padding: 8px; background-color: {BG_ELEVATED}; border-radius: 4px; margin-bottom: 10px;")
        group_layout.addWidget(timer_info)

        # Enable/Disable greeting system
        self.greeting_enabled_cb = QCheckBox("🔊 Aktifkan Sistem Sapaan Otomatis")
        self.greeting_enabled_cb.setStyleSheet(f"""
            QCheckBox {{
                color: {TEXT_PRIMARY};
                font-size: 13px;
                font-weight: bold;
                padding: 5px;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
            }}
            QCheckBox::indicator:checked {{
                background-color: {PRIMARY};
                border: 2px solid {PRIMARY};
                border-radius: 3px;
            }}
            QCheckBox::indicator:unchecked {{
                background-color: {BG_SURFACE};
                border: 2px solid {BORDER};
                border-radius: 3px;
            }}
        """)
        # Check from sequential_greeting_enabled first (primary key), fallback to custom_greeting_enabled
        greeting_enabled = self.cfg.get("sequential_greeting_enabled", self.cfg.get("custom_greeting_enabled", False))
        self.greeting_enabled_cb.setChecked(greeting_enabled)
        self.greeting_enabled_cb.stateChanged.connect(self.on_custom_greeting_enabled_changed)
        group_layout.addWidget(self.greeting_enabled_cb)

        # 10 Greeting Slots Section
        slots_frame = QFrame()
        slots_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_SURFACE};
                border: 1px solid {BORDER_GOLD};
                border-radius: 8px;
                padding: 15px;
                margin: 5px;
            }}
        """)
        slots_layout = QVBoxLayout(slots_frame)
        slots_layout.setSpacing(10)

        # Slots title
        slots_title = QLabel("📝 10 Slot Sapaan Custom (Timer mengikuti Cohost Tab):")
        slots_title.setStyleSheet(f"color: {ACCENT}; font-weight: bold; font-size: 14px; margin-bottom: 10px;")
        slots_layout.addWidget(slots_title)

        # Create 10 greeting slots (without individual timers)
        self.greeting_slots = []

        for i in range(10):
            slot_container = QFrame()
            slot_container.setStyleSheet(f"""
                QFrame {{
                    background-color: {BG_ELEVATED};
                    border: 1px solid {BORDER};
                    border-radius: 6px;
                    padding: 8px;
                    margin: 2px;
                }}
            """)
            slot_layout = QHBoxLayout(slot_container)
            slot_layout.setSpacing(10)

            # Slot number label
            slot_label = QLabel(f"#{i+1}:")
            slot_label.setStyleSheet(f"color: {PRIMARY}; font-weight: bold; font-size: 12px; min-width: 25px;")
            slot_layout.addWidget(slot_label)

            # Text input for greeting
            text_input = QLineEdit()
            text_input.setPlaceholderText(f"Masukkan teks sapaan slot {i+1}... (kosong = skip)")
            text_input.setStyleSheet(f"""
                QLineEdit {{
                    background-color: {BG_SURFACE};
                    border: 1px solid {BORDER};
                    border-radius: 4px;
                    padding: 6px;
                    font-size: 12px;
                    color: {TEXT_PRIMARY};
                }}
                QLineEdit:focus {{
                    border: 2px solid {PRIMARY};
                }}
            """)
            # Load existing text from config
            existing_text = self.cfg.get(f"custom_greeting_slot_{i+1}", "")
            if existing_text:
                text_input.setText(existing_text)
            text_input.textChanged.connect(lambda text, slot=i+1: self.on_greeting_slot_changed(slot, text))
            slot_layout.addWidget(text_input, stretch=4)

            # Preview/Test button
            test_btn = QPushButton("🔊")
            test_btn.setMaximumWidth(30)
            test_btn.setMaximumHeight(25)
            test_btn.setToolTip(f"Test sapaan slot {i+1}")
            test_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {SUCCESS};
                    border: none;
                    border-radius: 4px;
                    color: white;
                    font-size: 12px;
                    padding: 2px;
                }}
                QPushButton:hover {{
                    background-color: {ACCENT};
                    color: {BG_BASE};
                }}
            """)
            test_btn.clicked.connect(lambda checked, slot=i+1: self.test_greeting_slot(slot))
            slot_layout.addWidget(test_btn)

            slots_layout.addWidget(slot_container)

            # Store references
            self.greeting_slots.append(text_input)

        group_layout.addWidget(slots_frame)

        # Control buttons
        control_layout = QHBoxLayout()

        # Save all slots button
        save_btn = QPushButton("💾 Simpan Semua Slot")
        save_btn.setStyleSheet(btn_success())
        save_btn.clicked.connect(self.save_all_greeting_slots)
        control_layout.addWidget(save_btn)

        # Clear all slots button
        clear_btn = QPushButton("🗑️ Kosongkan Semua")
        clear_btn.setStyleSheet(btn_danger())
        clear_btn.clicked.connect(self.clear_all_greeting_slots)
        control_layout.addWidget(clear_btn)

        control_layout.addStretch()
        group_layout.addLayout(control_layout)

        # Status info
        status_label = QLabel("💡 Slot kosong akan dilewat. Timer interval diatur di Cohost Tab. File TTS disimpan otomatis untuk hemat API.")
        status_label.setStyleSheet(f"color: {WARNING}; font-size: 11px; font-style: italic; padding: 8px; background-color: {BG_ELEVATED}; border-radius: 4px; margin-top: 10px;")
        group_layout.addWidget(status_label)

        layout.addWidget(group)
    
    def create_sales_template_section(self, layout):
        """Create Sales Template section for live selling context"""
        group = QGroupBox("🛍️ Template Prompt Live Selling")
        group_layout = QVBoxLayout(group)
        group_layout.setSpacing(15)
        
        # Description
        desc = QLabel("Pilih template prompt untuk berbagai jenis live selling dengan produk keranjang 1-5")
        desc.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px; font-style: italic; padding: 5px;")
        group_layout.addWidget(desc)
        
        # Template selection
        template_layout = QHBoxLayout()
        template_label = QLabel("Template:")
        template_label.setMinimumWidth(100)
        template_layout.addWidget(template_label)
        
        self.template_combo = QComboBox()
        self.template_combo.addItem("Pilih Template Selling", "")
        
        # Add templates from sales_templates.py
        for key, name, description in get_template_list():
            self.template_combo.addItem(f"{name} - {description}", key)
        
        self.template_combo.currentIndexChanged.connect(lambda index: self.on_template_changed(self.template_combo.itemData(index)))
        template_layout.addWidget(self.template_combo)
        template_layout.addStretch()
        group_layout.addLayout(template_layout)
        
        # Context Setting Area (Manual + Template)
        context_label = QLabel("Context Setting (Manual atau dari Template):")
        context_label.setStyleSheet(f"font-weight: bold; color: {TEXT_PRIMARY}; margin-top: 10px;")
        group_layout.addWidget(context_label)
        
        # Manual context input (editable)
        self.context_input = QTextEdit()
        self.context_input.setMaximumHeight(200)
        self.context_input.setMinimumHeight(200)
        self.context_input.setPlaceholderText("Tulis context setting manual di sini, atau pilih template di bawah untuk mengisi otomatis...")
        
        # Load existing context from config
        existing_context = self.cfg.get("user_context", "")
        if existing_context:
            self.context_input.setPlainText(existing_context)
        
        self.context_input.setStyleSheet(f"""
            QTextEdit {{
                background-color: {BG_ELEVATED};
                border: 2px solid {BORDER_GOLD};
                border-radius: 8px;
                padding: 12px;
                font-size: 12px;
                color: {TEXT_PRIMARY};
                line-height: 1.4;
            }}
            QTextEdit:focus {{
                border: 2px solid {PRIMARY};
                background-color: {BG_SURFACE};
            }}
        """)
        group_layout.addWidget(self.context_input)
        
        # Template preview area (now editable as example/guide)
        template_label = QLabel("Template Contoh (Bisa Diedit sebagai Panduan):")
        template_label.setStyleSheet(f"font-weight: bold; color: {ACCENT}; margin-top: 15px;")
        group_layout.addWidget(template_label)
        
        self.template_preview = QTextEdit()
        self.template_preview.setMaximumHeight(150)
        self.template_preview.setMinimumHeight(150)
        self.template_preview.setPlaceholderText("Pilih template untuk melihat contoh prompt yang baik, lalu edit sesuai kebutuhan...")
        self.template_preview.setReadOnly(False)  # Now editable!
        self.template_preview.setStyleSheet(f"""
            QTextEdit {{
                background-color: {BG_ELEVATED};
                border: 2px solid {ACCENT};
                border-radius: 8px;
                padding: 12px;
                font-size: 12px;
                color: {TEXT_PRIMARY};
                line-height: 1.3;
            }}
            QTextEdit:focus {{
                border: 2px solid {PRIMARY};
                background-color: {BG_SURFACE};
            }}
        """)
        group_layout.addWidget(self.template_preview)
        
        # Button controls
        button_layout = QHBoxLayout()
        
        # Copy template to context button
        copy_template_btn = QPushButton("⬆️ Copy Template ke Context")
        copy_template_btn.setProperty("class", "secondary")
        copy_template_btn.clicked.connect(self.copy_template_to_context)
        copy_template_btn.setEnabled(False)
        button_layout.addWidget(copy_template_btn)
        self.copy_template_btn = copy_template_btn
        
        # Save context button
        save_context_btn = QPushButton("💾 Save Context Setting")
        save_context_btn.setProperty("class", "success")
        save_context_btn.clicked.connect(self.save_context_setting)
        button_layout.addWidget(save_context_btn)
        
        # Clear context button  
        clear_context_btn = QPushButton("🗑️ Clear")
        clear_context_btn.setProperty("class", "danger")
        clear_context_btn.clicked.connect(self.clear_context_setting)
        button_layout.addWidget(clear_context_btn)
        
        button_layout.addStretch()
        group_layout.addLayout(button_layout)
        
        # Status
        self.template_status = QLabel("Status: Belum ada template dipilih")
        self.template_status.setStyleSheet(f"color: {TEXT_DIM}; font-size: 12px; padding: 8px; background-color: {BG_ELEVATED}; border-radius: 4px;")
        group_layout.addWidget(self.template_status)
        
        layout.addWidget(group)
    
    def create_google_tts_section(self, layout):
        """Create Google TTS section with API Key only (simplified)"""
        group = QGroupBox("🎤 Google Text-to-Speech & Gemini Flash TTS")
        group_layout = QVBoxLayout(group)
        group_layout.setSpacing(15)

        # Description with better styling
        desc = QLabel("Masukkan Google Cloud / Gemini API Key untuk TTS (bisa pakai 1 API Key untuk kedua layanan)")
        desc.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px; font-style: italic; padding: 5px;")
        group_layout.addWidget(desc)

        # Info about Gemini Flash TTS
        gemini_info = QLabel("💡 Gemini Flash TTS: 19 suara ekspresif baru tersedia di pilihan suara (Gemini-Puck, Gemini-Kore, dll)")
        gemini_info.setStyleSheet(f"color: {INFO}; font-size: 11px; font-style: italic; padding: 5px; background-color: {BG_ELEVATED}; border-radius: 4px;")
        group_layout.addWidget(gemini_info)

        # API Key input container
        api_key_container = QHBoxLayout()
        api_key_label = QLabel("API Key:")
        api_key_label.setMinimumWidth(80)
        api_key_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        api_key_container.addWidget(api_key_label)

        self.tts_api_key_input = QLineEdit()
        self.tts_api_key_input.setPlaceholderText("Masukkan Google Cloud API Key...")
        self.tts_api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.tts_api_key_input.textChanged.connect(self.on_tts_api_key_changed)
        api_key_container.addWidget(self.tts_api_key_input)

        # Show/Hide API Key button
        show_api_btn = QPushButton("👁️")
        show_api_btn.setProperty("class", "secondary")
        show_api_btn.setMaximumWidth(50)
        show_api_btn.setToolTip("Show/Hide API Key")
        show_api_btn.clicked.connect(lambda: self.toggle_password_visibility(self.tts_api_key_input))
        api_key_container.addWidget(show_api_btn)

        group_layout.addLayout(api_key_container)

        # API Key info with better formatting
        api_key_info_frame = QFrame()
        api_key_info_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_ELEVATED};
                border: 1px solid {ACCENT};
                border-radius: 6px;
                padding: 10px;
                margin: 5px;
            }}
        """)
        api_key_info_layout = QVBoxLayout(api_key_info_frame)
        api_key_info_layout.setSpacing(5)

        info_title = QLabel("📋 Cara Mendapatkan API Key:")
        info_title.setStyleSheet(f"color: {ACCENT}; font-weight: bold; font-size: 12px;")
        api_key_info_layout.addWidget(info_title)

        steps = [
            "1. Buka Google Cloud Console (console.cloud.google.com)",
            "2. Pilih/Buat Project baru",
            "3. Enable 'Cloud Text-to-Speech API'",
            "4. APIs & Services → Credentials → Create Credentials → API Key",
            "5. Restrict key: Pilih 'Cloud Text-to-Speech API' saja",
            "6. Copy API Key dan paste di sini"
        ]

        for step in steps:
            step_label = QLabel(step)
            step_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px; padding-left: 10px;")
            api_key_info_layout.addWidget(step_label)

        group_layout.addWidget(api_key_info_frame)

        # Button container
        tts_button_layout = QHBoxLayout()

        # Test button
        self.tts_test_btn = QPushButton("🔍 Test Google TTS")
        self.tts_test_btn.setProperty("class", "success")
        self.tts_test_btn.clicked.connect(self.test_google_tts)
        self.tts_test_btn.setEnabled(False)  # Disabled until API key is provided
        tts_button_layout.addWidget(self.tts_test_btn)

        tts_button_layout.addStretch()
        group_layout.addLayout(tts_button_layout)

        # Status with better styling
        self.tts_status = QLabel("Status: Belum ada API Key")
        self.tts_status.setProperty("class", "status-info")
        self.tts_status.setStyleSheet(status_badge(TEXT_DIM))
        group_layout.addWidget(self.tts_status)

        layout.addWidget(group)
    
    def create_status_section(self, layout):
        """Create status section with better styling"""
        group = QGroupBox("📊 Status Konfigurasi")
        group_layout = QVBoxLayout(group)
        group_layout.setSpacing(15)
        
        # Status overview with better styling
        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(120)
        self.status_text.setMinimumHeight(120)
        self.status_text.setPlainText("Belum ada konfigurasi yang diatur")
        self.status_text.setReadOnly(True)
        self.status_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: {BG_ELEVATED};
                border: 2px solid {BORDER_GOLD};
                border-radius: 8px;
                padding: 15px;
                font-size: 13px;
                color: {TEXT_PRIMARY};
                font-family: 'Consolas', 'Monaco', monospace;
                line-height: 1.4;
            }}
        """)
        group_layout.addWidget(self.status_text)
        
        # Connection status indicators
        indicators_layout = QHBoxLayout()
        
        # AI Status Indicator
        self.ai_indicator = QLabel("🔴 AI: Tidak terhubung")
        self.ai_indicator.setStyleSheet(f"""
            QLabel {{
                background-color: {BG_SURFACE};
                border: 1px solid {BORDER_GOLD};
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 12px;
                font-weight: bold;
                color: {ERROR};
            }}
        """)
        indicators_layout.addWidget(self.ai_indicator)
        
        # TTS Status Indicator
        self.tts_indicator = QLabel("🔴 TTS: Tidak terhubung")
        self.tts_indicator.setStyleSheet(f"""
            QLabel {{
                background-color: {BG_SURFACE};
                border: 1px solid {BORDER_GOLD};
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 12px;
                font-weight: bold;
                color: {ERROR};
            }}
        """)
        indicators_layout.addWidget(self.tts_indicator)
        
        indicators_layout.addStretch()
        group_layout.addLayout(indicators_layout)
        
        layout.addWidget(group)
    
    def create_buttons(self, layout):
        """Create action buttons with better styling"""
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        # Save button with success styling
        save_btn = QPushButton("💾 Simpan Konfigurasi")
        save_btn.setProperty("class", "success")
        save_btn.clicked.connect(self.save_config)
        save_btn.setMinimumHeight(45)
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {SUCCESS};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-weight: bold;
                font-size: 14px;
                min-height: 20px;
            }}
            QPushButton:hover {{
                background-color: {ACCENT};
                color: {BG_BASE};
            }}
        """)
        button_layout.addWidget(save_btn)
        
        # Reset button with danger styling
        reset_btn = QPushButton("🔄 Reset Konfigurasi")
        reset_btn.setProperty("class", "danger")
        reset_btn.clicked.connect(self.reset_config)
        reset_btn.setMinimumHeight(45)
        reset_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ERROR};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-weight: bold;
                font-size: 14px;
                min-height: 20px;
            }}
            QPushButton:hover {{
                background-color: {WARNING};
                color: {BG_BASE};
            }}
        """)
        button_layout.addWidget(reset_btn)
        
        # Test All button
        test_all_btn = QPushButton("🔍 Test Semua Koneksi")
        test_all_btn.clicked.connect(self.test_all_connections)
        test_all_btn.setMinimumHeight(45)
        test_all_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {SECONDARY};
                color: {TEXT_PRIMARY};
                border: 1px solid {BORDER_GOLD};
                border-radius: 8px;
                padding: 12px 24px;
                font-weight: bold;
                font-size: 14px;
                min-height: 20px;
            }}
            QPushButton:hover {{
                background-color: {PRIMARY};
                color: white;
            }}
        """)
        button_layout.addWidget(test_all_btn)
        
        layout.addLayout(button_layout)
    
    def on_provider_changed(self, provider):
        """Handle provider selection change"""
        if provider == "DeepSeek":
            self.api_key_input.setPlaceholderText("Masukkan DeepSeek API Key (sk-...)")
        elif provider == "OpenAI (ChatGPT)":
            self.api_key_input.setPlaceholderText("Masukkan OpenAI API Key (sk-...)")
        self.update_status_overview()
    
    def on_api_key_changed(self):
        """Handle API key input change"""
        api_key = self.api_key_input.text().strip()
        self.ai_test_btn.setEnabled(len(api_key) > 0)
        
        if len(api_key) > 0:
            self.ai_status.setText("Status: API key siap untuk ditest")
            self.ai_status.setProperty("class", "status-warning")
            self.ai_status.setStyleSheet(status_badge(WARNING))
        else:
            self.ai_status.setText("Status: Belum ada API key")
            self.ai_status.setProperty("class", "status-info")
            self.ai_status.setStyleSheet(status_badge(TEXT_DIM))
        
        self.update_status_overview()
    
    def test_all_connections(self):
        """Test all configured connections"""
        api_key = self.api_key_input.text().strip()
        tts_api_key = self.tts_api_key_input.text().strip()

        if not api_key and not tts_api_key:
            QMessageBox.warning(
                self,
                "Peringatan",
                "Tidak ada konfigurasi yang dapat ditest.\nSilakan atur AI API Key dan Google TTS API Key terlebih dahulu."
            )
            return

        # Test AI API if configured
        if api_key:
            self.test_ai_api()

        # Test Google TTS if configured
        if tts_api_key:
            self.test_google_tts()

        # Show completion message
        QTimer.singleShot(2000, lambda: QMessageBox.information(
            self,
            "Test Selesai",
            "Test koneksi telah selesai. Periksa status masing-masing layanan di atas."
        ))
    
    def on_tts_api_key_changed(self):
        """Handle TTS API Key input change"""
        api_key = self.tts_api_key_input.text().strip()

        # Enable test button if API key is provided
        if len(api_key) > 0:
            self.tts_test_btn.setEnabled(True)
            self.tts_status.setText("Status: API Key siap untuk ditest")
            self.tts_status.setProperty("class", "status-warning")
            self.tts_status.setStyleSheet(status_badge(WARNING))
        else:
            self.tts_test_btn.setEnabled(False)
            self.tts_status.setText("Status: Belum ada API Key")
            self.tts_status.setProperty("class", "status-info")
            self.tts_status.setStyleSheet(status_badge(TEXT_DIM))

        self.update_status_overview()
    
    def on_template_changed(self, template_key):
        """Handle template selection change"""
        if template_key:
            template_content = get_template(template_key)
            self.template_preview.setPlainText(template_content)
            self.copy_template_btn.setEnabled(True)
            self.template_status.setText("Status: Template siap di-copy ke Context Setting")
            self.template_status.setStyleSheet(f"color: {WARNING}; font-size: 12px; padding: 8px; background-color: {BG_ELEVATED}; border-radius: 4px; font-weight: bold;")
        else:
            self.template_preview.setPlaceholderText("Pilih template untuk melihat contoh prompt yang baik...")
            self.template_preview.clear()
            self.copy_template_btn.setEnabled(False)
            self.template_status.setText("Status: Belum ada template dipilih")
            self.template_status.setStyleSheet(f"color: {TEXT_DIM}; font-size: 12px; padding: 8px; background-color: {BG_ELEVATED}; border-radius: 4px;")
    
    def copy_template_to_context(self):
        """Copy template content to context input for editing"""
        template_content = self.template_preview.toPlainText().strip()
        if not template_content:
            QMessageBox.warning(self, "Peringatan", "Template kosong atau belum dipilih.")
            return
        
        # Copy template content to context input
        self.context_input.setPlainText(template_content)
        self.template_status.setText("Status: ✅ Template berhasil di-copy ke Context Setting")
        self.template_status.setStyleSheet(f"color: {SUCCESS}; font-size: 12px; padding: 8px; background-color: {BG_ELEVATED}; border-radius: 4px; font-weight: bold;")
    
    def save_context_setting(self):
        """Save context setting from manual input"""
        context_content = self.context_input.toPlainText().strip()
        
        if not context_content:
            QMessageBox.warning(self, "Peringatan", "Context setting kosong. Silakan isi terlebih dahulu.")
            return
        
        try:
            # Save context to user_context setting
            config = self.cfg.get_all_settings()
            config["user_context"] = context_content
            
            # Save to file
            config_path = Path("config/settings.json")
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            self.template_status.setText("Status: ✅ Context Setting berhasil disimpan")
            self.template_status.setStyleSheet(f"color: {SUCCESS}; font-size: 12px; padding: 8px; background-color: {BG_ELEVATED}; border-radius: 4px; font-weight: bold;")
            
            QMessageBox.information(
                self, 
                "Sukses", 
                "✅ Context Setting berhasil disimpan!\n\n"
                "AI sekarang akan menggunakan context yang baru.\n"
                "Perubahan berlaku untuk semua reply AI selanjutnya."
            )
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"❌ Gagal menyimpan context setting:\n{str(e)}")
    
    def clear_context_setting(self):
        """Clear context setting"""
        reply = QMessageBox.question(
            self, 
            "Konfirmasi", 
            "Yakin ingin menghapus Context Setting?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.context_input.clear()
            self.template_status.setText("Status: Context Setting dikosongkan")
            self.template_status.setStyleSheet(f"color: {INFO}; font-size: 12px; padding: 8px; background-color: {BG_ELEVATED}; border-radius: 4px;")
    
    def toggle_password_visibility(self, line_edit):
        """Toggle password visibility for line edit"""
        if line_edit.echoMode() == QLineEdit.EchoMode.Password:
            line_edit.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            line_edit.setEchoMode(QLineEdit.EchoMode.Password)
    
    def test_ai_api(self):
        """Test AI API connection"""
        api_key = self.api_key_input.text().strip()
        provider = self.provider_combo.currentText()
        
        if not api_key:
            self.ai_status.setText("Status: ❌ API key kosong")
            self.ai_status.setStyleSheet(status_badge(ERROR))
            return
        
        self.ai_test_btn.setText("⏳ Testing...")
        self.ai_test_btn.setEnabled(False)
        
        # Determine API type for testing
        api_type = "deepseek" if provider == "DeepSeek" else "chatgpt"
        
        # Stop existing thread if running
        if self.test_thread and self.test_thread.isRunning():
            self.test_thread.quit()
            self.test_thread.wait(500)
        
        # Start test thread
        self.test_thread = APITestThread(api_type, api_key)
        self.test_thread.result_ready.connect(self.on_test_result)
        self.test_thread.start()
    
    def test_google_tts(self):
        """Test Google TTS API Key"""
        api_key = self.tts_api_key_input.text().strip()

        if not api_key:
            self.tts_status.setText("Status: ❌ Belum ada API Key")
            self.tts_status.setStyleSheet(status_badge(ERROR))
            return

        self.tts_test_btn.setText("⏳ Testing...")
        self.tts_test_btn.setEnabled(False)

        # Backup current settings
        config_path = Path("config/settings.json")
        backup_settings = None

        try:
            # Backup current settings
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    backup_settings = json.load(f)

            # Temporarily save API key to settings for testing
            config = self.cfg.get_all_settings()
            config["google_tts_api_key"] = api_key

            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            logger.info("[CONFIG_TEST] Temporarily saved API key for testing")

            # Reinitialize TTS engine with new API key
            from modules_server.tts_engine import reinitialize_tts_engine, speak

            logger.info("[CONFIG_TEST] Reinitializing TTS engine for test...")
            if not reinitialize_tts_engine():
                raise Exception("Gagal menginisialisasi TTS engine")

            logger.info("[CONFIG_TEST] TTS engine reinitialized, testing...")

            test_text = "Test Google TTS berhasil!"

            # Try to speak with the configured API key
            success = speak(
                text=test_text,
                language_code="id-ID",
                force_google_tts=True
            )

            if success:
                self.tts_status.setText("Status: ✅ API Key valid dan TTS berfungsi!")
                self.tts_status.setProperty("class", "status-success")
                self.tts_status.setStyleSheet(status_badge(SUCCESS))
                logger.info("[CONFIG_TEST] ✅ Google TTS test successful")
            else:
                raise Exception("TTS gagal dijalankan. Periksa API Key dan quota Anda.")

        except Exception as e:
            self.tts_status.setText(f"Status: ❌ Error: {str(e)}")
            self.tts_status.setProperty("class", "status-error")
            self.tts_status.setStyleSheet(status_badge(ERROR))
            logger.error(f"[CONFIG_TEST] ❌ Google TTS test failed: {e}")

            # Restore backup settings on failure
            if backup_settings and config_path.exists():
                try:
                    with open(config_path, 'w', encoding='utf-8') as f:
                        json.dump(backup_settings, f, indent=2, ensure_ascii=False)
                    logger.info("[CONFIG_TEST] Restored backup settings after test failure")

                    # Reinitialize again to restore old config
                    from modules_server.tts_engine import reinitialize_tts_engine
                    reinitialize_tts_engine()
                except Exception as restore_error:
                    logger.error(f"[CONFIG_TEST] Failed to restore backup: {restore_error}")

        finally:
            self.tts_test_btn.setText("🔍 Test Google TTS")
            self.tts_test_btn.setEnabled(True)
            self.update_status_overview()
    
    def on_test_result(self, api_type, success, message):
        """Handle API test result"""
        self.ai_test_btn.setText("🔍 Test Connection")
        self.ai_test_btn.setEnabled(True)
        
        if success:
            self.ai_status.setText(f"Status: {message}")
            self.ai_status.setProperty("class", "status-success")
            self.ai_status.setStyleSheet(status_badge(SUCCESS))
        else:
            self.ai_status.setText(f"Status: {message}")
            self.ai_status.setProperty("class", "status-error")
            self.ai_status.setStyleSheet(status_badge(ERROR))
        
        self.update_status_overview()
    
    def update_status_overview(self):
        """Update status overview with better formatting"""
        api_key = self.api_key_input.text().strip()
        provider = self.provider_combo.currentText()
        tts_api_key = self.tts_api_key_input.text().strip() if hasattr(self, 'tts_api_key_input') else ""

        status_lines = []
        status_lines.append("=== STATUS KONFIGURASI ===")
        status_lines.append("")

        # AI Provider Status
        if api_key:
            status_lines.append(f"✅ {provider} API: Terkonfigurasi ({len(api_key)} karakter)")
            self.ai_indicator.setText(f"🟢 AI: {provider} Terhubung")
            self.ai_indicator.setStyleSheet(f"""
                QLabel {{
                    background-color: {SUCCESS};
                    border: 1px solid {SUCCESS};
                    border-radius: 6px;
                    padding: 8px 12px;
                    font-size: 12px;
                    font-weight: bold;
                    color: white;
                }}
            """)
        else:
            status_lines.append(f"❌ {provider} API: Belum dikonfigurasi")
            self.ai_indicator.setText("🔴 AI: Tidak terhubung")
            self.ai_indicator.setStyleSheet(f"""
                QLabel {{
                    background-color: {ERROR};
                    border: 1px solid {ERROR};
                    border-radius: 6px;
                    padding: 8px 12px;
                    font-size: 12px;
                    font-weight: bold;
                    color: white;
                }}
            """)

        # Google TTS Status (API Key only)
        if tts_api_key:
            status_lines.append(f"✅ Google TTS: Terkonfigurasi")
            status_lines.append(f"   🔑 API Key: {'*' * (len(tts_api_key) - 4)}{tts_api_key[-4:] if len(tts_api_key) > 4 else '****'}")
            self.tts_indicator.setText("🟢 TTS: Google Cloud")
            self.tts_indicator.setStyleSheet(f"""
                QLabel {{
                    background-color: {SUCCESS};
                    border: 1px solid {SUCCESS};
                    border-radius: 6px;
                    padding: 8px 12px;
                    font-size: 12px;
                    font-weight: bold;
                    color: white;
                }}
            """)
        else:
            status_lines.append("❌ Google TTS: Belum dikonfigurasi")
            self.tts_indicator.setText("🔴 TTS: Tidak terhubung")
            self.tts_indicator.setStyleSheet(f"""
                QLabel {{
                    background-color: {ERROR};
                    border: 1px solid {ERROR};
                    border-radius: 6px;
                    padding: 8px 12px;
                    font-size: 12px;
                    font-weight: bold;
                    color: white;
                }}
            """)

        status_lines.append("")

        # Overall Status
        if api_key and tts_api_key:
            status_lines.append("🎉 SIAP DIGUNAKAN!")
            status_lines.append("   Semua fitur VocaLive dapat berfungsi optimal.")
        elif api_key:
            status_lines.append("⚠️  SEBAGIAN SIAP")
            status_lines.append("   AI Chat berfungsi, TTS perlu dikonfigurasi.")
        else:
            status_lines.append("❌ BELUM SIAP")
            status_lines.append("   Perlu konfigurasi AI API untuk menggunakan aplikasi.")

        self.status_text.setPlainText("\n".join(status_lines))
    
    def save_config(self):
        """Save configuration"""
        try:
            # Get current config
            config = self.cfg.get_all_settings()

            # Update API keys
            if "api_keys" not in config:
                config["api_keys"] = {}

            api_key = self.api_key_input.text().strip()
            provider = self.provider_combo.currentText()
            tts_api_key = self.tts_api_key_input.text().strip()

            # Save AI provider selection (CRITICAL FIX!)
            if provider == "DeepSeek":
                config["ai_provider"] = "deepseek"
            elif provider == "OpenAI (ChatGPT)":
                config["ai_provider"] = "chatgpt"

            # Save AI API keys
            if api_key:
                if provider == "DeepSeek":
                    config["api_keys"]["DEEPSEEK_API_KEY"] = api_key
                elif provider == "OpenAI (ChatGPT)":
                    config["api_keys"]["OPENAI_API_KEY"] = api_key

            # Save Google TTS API Key only
            if tts_api_key:
                config["google_tts_api_key"] = tts_api_key
            else:
                # Remove API key if empty
                if "google_tts_api_key" in config:
                    del config["google_tts_api_key"]

            # Save to file
            config_path = Path("config/settings.json")
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            # IMPORTANT: Reinitialize TTS engine to load new API key
            if tts_api_key:
                try:
                    from modules_server.tts_engine import reinitialize_tts_engine
                    logger.info("[CONFIG] Reinitializing TTS engine with new API key...")
                    if reinitialize_tts_engine():
                        logger.info("[CONFIG] ✅ TTS engine reinitialized successfully")
                    else:
                        logger.warning("[CONFIG] ⚠️ TTS engine reinitialization failed")
                except Exception as reinit_error:
                    logger.error(f"[CONFIG] Failed to reinitialize TTS engine: {reinit_error}")

            # IMPORTANT: Reinitialize AI modules to load new API keys
            if api_key:
                try:
                    if provider == "DeepSeek":
                        from modules_client.deepseek_ai import reinitialize_deepseek
                        logger.info("[CONFIG] Reinitializing DeepSeek AI with new API key...")
                        reinitialize_deepseek()
                        logger.info("[CONFIG] ✅ DeepSeek AI reinitialized successfully")
                    elif provider == "OpenAI (ChatGPT)":
                        from modules_client.chatgpt_ai import reinitialize_chatgpt
                        logger.info("[CONFIG] Reinitializing ChatGPT AI with new API key...")
                        reinitialize_chatgpt()
                        logger.info("[CONFIG] ✅ ChatGPT AI reinitialized successfully")
                except Exception as ai_reinit_error:
                    logger.error(f"[CONFIG] Failed to reinitialize AI: {ai_reinit_error}")

            # Show success message
            QMessageBox.information(
                self,
                "Success",
                f"✅ Konfigurasi berhasil disimpan!\n\n"
                f"Google TTS: {'API Key' if tts_api_key else 'Belum dikonfigurasi'}"
            )
            self.update_status_overview()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"❌ Gagal menyimpan konfigurasi:\n{str(e)}")
    
    def load_saved_keys(self):
        """Load saved API keys and context"""
        try:
            api_keys = self.cfg.get("api_keys", {})
            tts_api_key = self.cfg.get("google_tts_api_key", "")
            user_context = self.cfg.get("user_context", "")

            # Load AI API key based on available keys
            if "DEEPSEEK_API_KEY" in api_keys:
                self.provider_combo.setCurrentText("DeepSeek")
                self.api_key_input.setText(api_keys["DEEPSEEK_API_KEY"])
            elif "OPENAI_API_KEY" in api_keys:
                self.provider_combo.setCurrentText("OpenAI (ChatGPT)")
                self.api_key_input.setText(api_keys["OPENAI_API_KEY"])

            # Load Google TTS API Key
            if tts_api_key and hasattr(self, 'tts_api_key_input'):
                self.tts_api_key_input.setText(tts_api_key)
                self.tts_test_btn.setEnabled(True)

            # Load existing context
            if user_context and hasattr(self, 'context_input'):
                self.context_input.setPlainText(user_context)

            self.update_status_overview()

        except Exception as e:
            print(f"Error loading saved keys: {e}")
    
    def reset_config(self):
        """Reset configuration"""
        reply = QMessageBox.question(
            self, 
            "Konfirmasi", 
            "Yakin ingin reset semua konfigurasi?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.api_key_input.clear()

            # Reset TTS API Key
            if hasattr(self, 'tts_api_key_input'):
                self.tts_api_key_input.clear()

            # Reset context setting
            if hasattr(self, 'context_input'):
                self.context_input.clear()
            if hasattr(self, 'template_preview'):
                self.template_preview.clear()

            # Reset greeting slots
            if hasattr(self, 'greeting_slots'):
                for text_input in self.greeting_slots:
                    text_input.clear()
            
            self.ai_status.setText("Status: Belum ada API key")
            self.ai_status.setProperty("class", "status-info")
            self.ai_status.setStyleSheet(status_badge(TEXT_DIM))
            
            self.tts_status.setText("Status: Belum ada file kredensial")
            self.tts_status.setProperty("class", "status-info")
            self.tts_status.setStyleSheet(status_badge(TEXT_DIM))
            
            if hasattr(self, 'template_status'):
                self.template_status.setText("Status: Semua konfigurasi direset")
                self.template_status.setStyleSheet(f"color: {INFO}; font-size: 12px; padding: 8px; background-color: {BG_ELEVATED}; border-radius: 4px;")
            
            # Reset button states
            self.ai_test_btn.setEnabled(False)
            self.tts_test_btn.setEnabled(False)
            if hasattr(self, 'copy_template_btn'):
                self.copy_template_btn.setEnabled(False)
            
            self.update_status_overview()
    
    
    def on_greeting_enabled_changed(self):
        """Handle viewer greeting enabled/disabled change"""
        try:
            enabled = self.greeting_enabled_cb.isChecked()
            self.cfg.set("viewer_greeting_enabled", enabled)
            print(f"[CONFIG] Viewer greeting system: {'Enabled' if enabled else 'Disabled'}")
            self.update_greeting_example()
        except Exception as e:
            print(f"Error changing greeting enabled setting: {e}")
    
    def on_detection_window_changed(self):
        """Handle detection window duration change"""
        try:
            duration = self.detection_window_spin.value()
            self.cfg.set("viewer_detection_window", duration)
            print(f"[CONFIG] Detection window changed to: {duration} seconds")
            self.update_greeting_example()
        except Exception as e:
            print(f"Error changing detection window: {e}")
    
    def on_wait_interval_changed(self):
        """Handle wait interval duration change"""
        try:
            interval = self.wait_interval_spin.value()
            self.cfg.set("viewer_wait_interval", interval)
            print(f"[CONFIG] Wait interval changed to: {interval} seconds")
            self.update_greeting_example()
        except Exception as e:
            print(f"Error changing wait interval: {e}")
    
    def update_greeting_example(self):
        """Update the greeting system example text"""
        try:
            if hasattr(self, 'greeting_example_label'):
                detection_window = self.detection_window_spin.value()
                wait_interval = self.wait_interval_spin.value()
                
                # Convert to user-friendly format
                detection_text = f"{detection_window} detik"
                if detection_window >= 3600:  # Hours
                    hours = detection_window // 3600
                    minutes = (detection_window % 3600) // 60
                    detection_text = f"{hours} jam {minutes} menit" if minutes else f"{hours} jam"
                elif detection_window >= 60:  # Minutes
                    detection_text = f"{detection_window//60} menit {detection_window%60} detik" if detection_window % 60 else f"{detection_window//60} menit"
                
                wait_text = f"{wait_interval} detik"
                if wait_interval >= 3600:  # Hours
                    hours = wait_interval // 3600
                    minutes = (wait_interval % 3600) // 60
                    wait_text = f"{hours} jam {minutes} menit" if minutes else f"{hours} jam"
                elif wait_interval >= 60:  # Minutes
                    wait_text = f"{wait_interval//60} menit {wait_interval%60} detik" if wait_interval % 60 else f"{wait_interval//60} menit"
                
                example_text = f"Contoh: Sistem akan aktif selama {detection_text} untuk mendeteksi penonton baru, lalu menunggu {wait_text} sebelum siklus berikutnya"
                self.greeting_example_label.setText(example_text)
        except Exception as e:
            print(f"Error updating greeting example: {e}")
    
    # === CUSTOM GREETING SYSTEM METHODS ===
    
    def on_custom_greeting_enabled_changed(self):
        """Handle custom greeting system enabled/disabled change with 5-slot validation"""
        try:
            enabled = self.greeting_enabled_cb.isChecked()
            
            if enabled:
                # Count filled greeting slots
                filled_slots = 0
                for text_input in self.greeting_slots:
                    if text_input.text().strip():
                        filled_slots += 1
                
                # Require minimum 5 filled slots
                if filled_slots < 5:
                    # Show warning and uncheck
                    QMessageBox.warning(
                        self,
                        "Peringatan",
                        f"⚠️ Minimal 5 slot sapaan harus diisi untuk mengaktifkan fitur sapaan.\n\n"
                        f"Saat ini hanya {filled_slots} slot yang terisi.\n"
                        f"Silakan isi minimal {5 - filled_slots} slot lagi."
                    )
                    # Uncheck the checkbox
                    self.greeting_enabled_cb.setChecked(False)
                    return
            
            # Save to both keys for compatibility with different greeting systems
            self.cfg.set("custom_greeting_enabled", enabled)
            self.cfg.set("sequential_greeting_enabled", enabled)
            print(f"[CONFIG] Custom greeting system: {'Enabled' if enabled else 'Disabled'}")
        except Exception as e:
            print(f"Error changing custom greeting enabled setting: {e}")
    
    def on_greeting_slot_changed(self, slot_number, text):
        """Handle greeting slot text change"""
        try:
            # Auto-save slot text when changed
            self.cfg.set(f"custom_greeting_slot_{slot_number}", text)
            print(f"[CONFIG] Greeting slot {slot_number} updated: {text[:30]}...")
        except Exception as e:
            print(f"Error saving greeting slot {slot_number}: {e}")
    
    
    def test_greeting_slot(self, slot_number):
        """Test play greeting for specific slot"""
        try:
            # Get text from slot
            if slot_number <= len(self.greeting_slots):
                text_input = self.greeting_slots[slot_number - 1]
                text = text_input.text().strip()

                if not text:
                    QMessageBox.warning(self, "Peringatan", f"Slot {slot_number} kosong. Masukkan teks terlebih dahulu.")
                    return

                print(f"[CONFIG] Testing greeting slot {slot_number}: {text}")

                # Import TTS function
                try:
                    from modules_server.tts_engine import speak

                    # Get current voice setting
                    voice_setting = self.cfg.get("tts_voice", "id-ID-Standard-B (MALE)")
                    language_code = "id-ID"  # Default Indonesian

                    # Play TTS
                    success = speak(
                        text=text,
                        voice_name=voice_setting,
                        language_code=language_code,
                        force_google_tts=True
                    )

                    if success:
                        print(f"[CONFIG] Successfully played test for slot {slot_number}")
                    else:
                        QMessageBox.warning(self, "Error", f"Gagal memutar TTS untuk slot {slot_number}")

                except ImportError as e:
                    QMessageBox.warning(self, "Error", f"TTS engine tidak tersedia: {e}")

        except Exception as e:
            print(f"Error testing greeting slot {slot_number}: {e}")
            QMessageBox.critical(self, "Error", f"Error testing slot {slot_number}: {str(e)}")
    
    def save_all_greeting_slots(self):
        """Save all greeting slots to config (without individual timers)"""
        try:
            saved_count = 0
            for i, text_input in enumerate(self.greeting_slots):
                slot_number = i + 1
                text = text_input.text().strip()

                # Save text only (timer handled by Cohost Tab)
                self.cfg.set(f"custom_greeting_slot_{slot_number}", text)

                if text:  # Count only non-empty slots
                    saved_count += 1

            QMessageBox.information(
                self,
                "Tersimpan",
                f"✅ Berhasil menyimpan {saved_count} slot sapaan yang terisi.\n"
                f"Slot kosong akan dilewat saat sistem berjalan.\n"
                f"Timer interval diatur di Cohost Tab."
            )
            print(f"[CONFIG] Saved {saved_count} greeting slots")

        except Exception as e:
            print(f"Error saving greeting slots: {e}")
            QMessageBox.critical(self, "Error", f"Gagal menyimpan slot: {str(e)}")
    
    def clear_all_greeting_slots(self):
        """Clear all greeting slots"""
        try:
            reply = QMessageBox.question(
                self,
                "Konfirmasi",
                "Yakin ingin mengosongkan semua slot sapaan?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                # Clear UI
                for text_input in self.greeting_slots:
                    text_input.clear()

                # Clear config (text only, no timers)
                for i in range(10):
                    slot_number = i + 1
                    self.cfg.set(f"custom_greeting_slot_{slot_number}", "")

                print("[CONFIG] All greeting slots cleared")
                QMessageBox.information(self, "Berhasil", "✅ Semua slot sapaan telah dikosongkan.")

        except Exception as e:
            print(f"Error clearing greeting slots: {e}")
            QMessageBox.critical(self, "Error", f"Gagal mengosongkan slot: {str(e)}")