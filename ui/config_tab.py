# ui/config_tab.py - Tab Konfigurasi API Keys

import json
import logging
import os
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

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
from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from modules_client import i18n
from modules_client.config_manager import ConfigManager
from modules_client.i18n import t
from sales_templates import get_template

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
        label_subtitle,
        status_badge,
    )
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
            elif self.api_type == "gemini":
                success, message = self.test_gemini_api()
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
                return True, t("config.test.deepseek_ok")
            else:
                return False, t("config.test.deepseek_err", code=response.status_code)

        except Exception as e:
            return False, t("config.test.deepseek_fail", reason=str(e))

    def test_gemini_api(self):
        """Test Gemini API — coba primary model dulu, fallback jika 403"""
        models = ["gemini-3.1-flash-lite-preview", "gemini-flash-lite-latest"]
        data = {
            "contents": [{"role": "user", "parts": [{"text": "Hello, test connection"}]}],
            "generationConfig": {"maxOutputTokens": 10},
        }
        headers = {
            "x-goog-api-key": self.api_key,
            "Content-Type": "application/json",
        }
        for model in models:
            try:
                url = (
                    f"https://generativelanguage.googleapis.com/v1beta/models/"
                    f"{model}:generateContent"
                )
                response = _session.post(url, headers=headers, json=data, timeout=10)
                if response.status_code == 200:
                    return True, t("config.test.gemini_ok", model=model)
                elif response.status_code == 403:
                    continue  # coba model berikutnya
                else:
                    return False, t("config.test.gemini_err", code=response.status_code, detail=response.text[:100])
            except Exception as e:
                return False, t("config.test.gemini_fail", reason=str(e))
        return False, t("config.test.gemini_all_403")

    # ChatGPT disabled — uncomment to re-enable
    # def test_chatgpt_api(self): ...


class PolishKnowledgeThread(QThread):
    """Thread untuk menyempurnakan teks pengetahuan produk via AI + riset web"""
    finished = pyqtSignal(str)      # hasil AI, atau "" jika gagal
    status_update = pyqtSignal(str) # progress text untuk label

    def __init__(self, text: str):
        super().__init__()
        self.text = text

    def run(self):
        try:
            self.status_update.emit(t("config.polish.status_research"))
            research = self._research_products()

            self.status_update.emit(t("config.polish.status_writing"))
            from modules_client.api import generate_reply

            # Polish output = AI output untuk user_context → WAJIB follow output_language
            # (master control dari Cohost tab). Architecture final:
            #   - ui_language (di Konfigurasi tab) → HANYA UI chrome: label, tombol, dialog
            #   - output_language (di Cohost tab) → SEMUA AI output + TTS voice + greeting
            cfg = ConfigManager("config/settings.json")
            output_lang = cfg.get("output_language", "Indonesia")

            if output_lang == "English":
                research_section = (
                    f"\n\nProduct research from the internet:\n{research}" if research else ""
                )
                prompt = (
                    "You are a highly experienced and enthusiastic professional live selling AI host. "
                    "Your task: transform the following product knowledge text into a complete knowledge base "
                    "ready for the AI to use when answering viewer questions on TikTok Live.\n\n"
                    "OUTPUT INSTRUCTIONS — follow this order EXACTLY:\n\n"
                    "SECTION 1 — ROLE (must appear at the very top):\n"
                    "Write the AI host role definition block, example format:\n"
                    "```\n"
                    "## AI HOST ROLE\n"
                    "You are a professional live selling host selling [mention the product] on TikTok Live.\n"
                    "Always reply to viewer comments as an enthusiastic, knowledgeable, and persuasive seller.\n"
                    "Help buyers make quick purchase decisions. Use warm and energetic language.\n"
                    "Never mention that you are an AI.\n"
                    "```\n\n"
                    "SECTION 2 — PRODUCT KNOWLEDGE:\n"
                    "1. Preserve ALL of the seller's original info (cart numbers, prices, promos)\n"
                    "2. Add technical specs & strengths from your own knowledge\n"
                    "3. Add real benefits for the buyer\n"
                    "4. Include example reply scripts for common viewer questions\n"
                    "5. Neatly formatted per product, easy for the AI to read\n\n"
                    f"Seller's original text:\n{self.text}"
                    f"{research_section}\n\n"
                    "Write ONLY the output directly (starting from ## AI HOST ROLE). No intro or outro."
                )
            elif output_lang == "Malaysia":
                research_section = (
                    f"\n\nHasil kajian produk dari internet:\n{research}" if research else ""
                )
                prompt = (
                    "Anda ialah AI host live selling profesional yang sangat berpengalaman dan bersemangat. "
                    "Tugas anda: ubah teks pengetahuan produk berikut menjadi knowledge base lengkap "
                    "yang sedia dipakai AI untuk menjawab soalan penonton di TikTok Live.\n\n"
                    "ARAHAN OUTPUT — ikut urutan ini DENGAN TEPAT:\n\n"
                    "BAHAGIAN 1 — PERANAN (wajib berada di paling atas):\n"
                    "Tulis blok definisi peranan AI host, contoh format:\n"
                    "```\n"
                    "## PERANAN AI HOST\n"
                    "Anda ialah host live selling profesional yang menjual [sebutkan produk] di TikTok Live.\n"
                    "Sentiasa balas komen penonton sebagai penjual yang bersemangat, berpengetahuan, dan meyakinkan.\n"
                    "Bantu pembeli buat keputusan beli dengan pantas. Gunakan bahasa yang mesra dan bertenaga.\n"
                    "Jangan sesekali sebut bahawa anda ialah AI.\n"
                    "```\n\n"
                    "BAHAGIAN 2 — KNOWLEDGE PRODUK:\n"
                    "1. Kekalkan SEMUA info asal penjual (nombor keranjang, harga, promosi)\n"
                    "2. Tambah spesifikasi teknikal & kelebihan daripada pengetahuan anda\n"
                    "3. Tambah manfaat sebenar untuk pembeli\n"
                    "4. Sertakan contoh skrip balasan untuk soalan lazim penonton\n"
                    "5. Format kemas setiap produk, mudah dibaca AI\n\n"
                    f"Teks asal penjual:\n{self.text}"
                    f"{research_section}\n\n"
                    "Tulis HANYA outputnya terus (bermula dari ## PERANAN AI HOST). Tanpa intro atau penutup."
                )
            else:
                # Indonesia (default)
                research_section = (
                    f"\n\nHasil riset produk dari internet:\n{research}" if research else ""
                )
                prompt = (
                    "Kamu adalah AI host live selling profesional yang sangat berpengalaman dan antusias. "
                    "Tugasmu: ubah teks pengetahuan produk berikut menjadi knowledge base lengkap "
                    "yang siap dipakai AI untuk menjawab pertanyaan penonton di TikTok Live.\n\n"
                    "INSTRUKSI OUTPUT — ikuti urutan ini PERSIS:\n\n"
                    "BAGIAN 1 — PERAN (wajib ada di paling atas):\n"
                    "Tulis blok definisi peran AI host, contoh format:\n"
                    "```\n"
                    "## PERAN AI HOST\n"
                    "Kamu adalah host live selling profesional yang menjual [sebutkan produk] di TikTok Live.\n"
                    "Selalu jawab komentar penonton sebagai penjual yang antusias, berpengetahuan, dan persuasif.\n"
                    "Bantu pembeli mengambil keputusan beli dengan cepat. Gunakan bahasa yang hangat dan energik.\n"
                    "Jangan pernah menyebutkan bahwa kamu adalah AI.\n"
                    "```\n\n"
                    "BAGIAN 2 — KNOWLEDGE PRODUK:\n"
                    "1. Pertahankan SEMUA info asli penjual (nomor keranjang, harga, promo)\n"
                    "2. Tambahkan spesifikasi teknis & keunggulan dari pengetahuanmu\n"
                    "3. Tambahkan benefit nyata buat pembeli\n"
                    "4. Sertakan contoh script balasan untuk pertanyaan umum penonton\n"
                    "5. Format rapi per produk, mudah dibaca AI\n\n"
                    f"Teks asli penjual:\n{self.text}"
                    f"{research_section}\n\n"
                    "Tulis HANYA output-nya langsung (mulai dari ## PERAN AI HOST). Tanpa intro atau penutup."
                )

            result = generate_reply(prompt, max_tokens=800, fast_mode=False)
            self.finished.emit(result.strip() if result else "")
        except Exception:
            self.finished.emit("")

    def _research_products(self) -> str:
        """Cari info produk via DuckDuckGo Instant Answer API (gratis, no key)"""
        try:
            import requests
            # Buat query dari teks user — ambil 80 char pertama sebagai konteks produk
            query = f"{self.text[:120]} spesifikasi keunggulan harga"
            resp = requests.get(
                "https://api.duckduckgo.com/",
                params={"q": query, "format": "json", "no_html": "1", "skip_disambig": "1"},
                timeout=8,
                headers={"User-Agent": "VocaLive/1.0"}
            )
            data = resp.json()
            parts = []
            if data.get("Abstract"):
                parts.append(data["Abstract"])
            for topic in data.get("RelatedTopics", [])[:3]:
                if isinstance(topic, dict) and topic.get("Text"):
                    parts.append(topic["Text"])
            return "\n".join(parts) if parts else ""
        except Exception:
            return ""  # riset gagal → AI tetap jalan dengan pengetahuan sendiri


class ConfigTab(QWidget):
    """Tab Konfigurasi untuk API Keys"""

    tts_key_type_changed = pyqtSignal(str)  # "gemini" | "cloud" | "all"
    greeting_status_changed = pyqtSignal(str, str)  # state, message
    output_language_changed = pyqtSignal(str)  # "Indonesia" | "Malaysia" | "English"

    def __init__(self):
        super().__init__()
        self.cfg = ConfigManager("config/settings.json")
        self.test_thread = None
        self.init_ui()
        self.load_saved_keys()
        self.greeting_status_changed.connect(self._apply_greeting_status)

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
        title = QLabel(t("config.title"))
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"color: {PRIMARY}; margin-bottom: 20px;")
        layout.addWidget(title)

        # Description
        desc = QLabel(t("config.desc"))
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 14px; margin-bottom: 10px;")
        layout.addWidget(desc)

        # Language setting note
        lang_note = QLabel(t("config.note.output_language"))
        lang_note.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lang_note.setStyleSheet(f"color: {PRIMARY}; font-size: 12px; margin-bottom: 20px; font-style: italic; background-color: {BG_ELEVATED}; padding: 8px; border-radius: 5px;")
        layout.addWidget(lang_note)

        # ===== UI Language (bilingual UI support) =====
        ui_lang_layout = QHBoxLayout()
        ui_lang_label = QLabel(t("config.label.ui_language"))
        ui_lang_label.setMinimumWidth(220)
        ui_lang_layout.addWidget(ui_lang_label)

        self.ui_lang_combo = QComboBox()
        self.ui_lang_combo.addItem("Bahasa Indonesia", "id")
        self.ui_lang_combo.addItem("English", "en")
        self.ui_lang_combo.setCurrentIndex(0 if i18n.current_language() == "id" else 1)
        self.ui_lang_combo.currentIndexChanged.connect(self.on_ui_language_changed)
        ui_lang_layout.addWidget(self.ui_lang_combo)
        ui_lang_layout.addStretch()
        layout.addLayout(ui_lang_layout)

        # v1.0.27: Master Output Language selector di PALING ATAS
        # Setting ini master control untuk SEMUA output audio/AI:
        # - AI reply ke komentar viewer TikTok
        # - Greeting saat app start + auto-generated greetings
        # - Preview voice, Test TTS
        # - Polish Knowledge output
        # - Sales template content
        self.create_output_language_section(layout)

        # AI Provider Section
        self.create_ai_provider_section(layout)
        # v1.0.26: TTS section langsung di bawah AI provider (per user request)
        self.create_google_tts_section(layout)

        # Viewer Greeting Section
        self.create_viewer_greeting_section(layout)

        # Sales Template Section
        self.create_sales_template_section(layout)

        # NOTE: Google TTS Section sudah dipanggil langsung setelah AI provider (line 388).
        # Tidak panggil lagi di sini untuk hindari duplicate widget.

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

    def create_output_language_section(self, layout):
        """Master output audio section (v1.0.27).

        Master control untuk SEMUA output AI + TTS:
        - Bahasa Output (Indonesia/Malaysia/English)
        - Voice (Gemini voices, auto-filter by language)
        - Preview voice button

        Dipindahkan dari Cohost tab supaya user punya satu source of truth
        di Config tab. Cohost tab sekarang pure operation (start/stop/log).
        """
        group = QGroupBox(t("config.section.output_audio"))
        group_layout = QVBoxLayout(group)
        group_layout.setSpacing(12)

        # Info
        info = QLabel(t("config.output.info"))
        info.setWordWrap(True)
        info.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px; font-style: italic; padding: 5px;")
        group_layout.addWidget(info)

        # Language row
        lang_row = QHBoxLayout()
        lang_label = QLabel(t("config.output.label.language"))
        lang_label.setMinimumWidth(130)
        lang_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        lang_row.addWidget(lang_label)

        self.output_lang_combo = QComboBox()
        self.output_lang_combo.addItems(["Indonesia", "Malaysia", "English"])
        current_lang = self.cfg.get("output_language", "Indonesia")
        self.output_lang_combo.setCurrentText(current_lang)
        self.output_lang_combo.currentTextChanged.connect(self._on_output_lang_changed)
        lang_row.addWidget(self.output_lang_combo)
        lang_row.addStretch()
        group_layout.addLayout(lang_row)

        # Voice row
        voice_row = QHBoxLayout()
        voice_label = QLabel(t("config.output.label.voice"))
        voice_label.setMinimumWidth(130)
        voice_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        voice_row.addWidget(voice_label)

        self.output_voice_combo = QComboBox()
        self.output_voice_combo.setMinimumWidth(280)
        voice_row.addWidget(self.output_voice_combo)

        self.output_preview_btn = QPushButton(t("config.output.btn.preview"))
        self.output_preview_btn.setFixedWidth(100)
        self.output_preview_btn.clicked.connect(self._on_output_preview_clicked)
        voice_row.addWidget(self.output_preview_btn)
        voice_row.addStretch()
        group_layout.addLayout(voice_row)

        # Populate voice combo berdasar current language
        self._populate_output_voice_combo(current_lang)

        # Connect voice change → save ke settings
        self.output_voice_combo.currentTextChanged.connect(self._on_output_voice_changed)

        layout.addWidget(group)

    def _populate_output_voice_combo(self, language: str):
        """Isi voice combo berdasar language — Gemini voices only."""
        self.output_voice_combo.blockSignals(True)
        self.output_voice_combo.clear()
        try:
            voices_file = os.path.join(os.path.dirname(__file__), '..', 'config', 'voices.json')
            with open(voices_file, 'r', encoding='utf-8') as f:
                voices_data = json.load(f)
            lang_key = {"Indonesia": "id-ID", "Malaysia": "ms-MY"}.get(language, "en-US")
            voices = []
            if "gemini_flash" in voices_data and lang_key in voices_data["gemini_flash"]:
                for v in voices_data["gemini_flash"][lang_key]:
                    voices.append(f"{v['model']} ({v['gender']})")
            if not voices:
                voices = ["Gemini-Puck (MALE)", "Gemini-Zephyr (FEMALE)"]
            self.output_voice_combo.addItems(voices)
            # Set saved voice if exists
            saved = self.cfg.get("tts_voice", voices[0])
            if saved in voices:
                self.output_voice_combo.setCurrentText(saved)
            else:
                self.output_voice_combo.setCurrentIndex(0)
        except Exception as e:
            logger.error(f"Failed to populate output voice: {e}")
            self.output_voice_combo.addItems(["Gemini-Puck (MALE)", "Gemini-Zephyr (FEMALE)"])
        self.output_voice_combo.blockSignals(False)

    def _on_output_lang_changed(self, language: str):
        """Handler saat user pilih bahasa output. Save + emit signal + update voice list."""
        # Save ke settings + derive ai_language
        self.cfg.set("output_language", language)
        ai_lang_map = {"Indonesia": "indonesian", "Malaysia": "malaysian", "English": "english"}
        self.cfg.set("ai_language", ai_lang_map.get(language, "indonesian"))
        # Refresh voice list untuk bahasa baru
        self._populate_output_voice_combo(language)
        # Emit signal untuk Cohost tab sync
        self.output_language_changed.emit(language)
        logger.info(f"[CONFIG] Output language → {language}")

    def _on_output_voice_changed(self, voice: str):
        """Save voice selection ke settings."""
        if voice:
            self.cfg.set("tts_voice", voice)
            logger.info(f"[CONFIG] TTS voice → {voice}")

    def _on_output_preview_clicked(self):
        """Preview voice yang dipilih dengan sample text."""
        voice = self.output_voice_combo.currentText()
        lang = self.output_lang_combo.currentText()
        if not voice:
            QMessageBox.warning(self, t("common.warning"), t("config.output.err.no_voice"))
            return
        # Check Gemini API key
        api_key = self.cfg.get("api_keys", {}).get("GEMINI_API_KEY", "").strip()
        if not api_key:
            api_key = self.cfg.get("google_tts_api_key", "").strip()
        if not api_key:
            QMessageBox.warning(self, t("common.error"), t("config.output.err.no_api_key"))
            return

        # Sample text dari i18n — default Indonesian/English/Malaysian samples
        # Kalau locale spesifik tidak ada sample terpisah, pakai generic sample
        sample_en = "Hello, this is a voice preview sample. Welcome!"
        sample_id = "Halo, ini adalah contoh suara untuk preview. Selamat datang!"
        sample_ms = "Helo, ini contoh suara untuk preview. Selamat datang!"
        samples = {"Indonesia": sample_id, "Malaysia": sample_ms, "English": sample_en}
        lang_codes = {"Indonesia": "id-ID", "Malaysia": "ms-MY", "English": "en-US"}
        voice_model = voice.split('(')[0].strip()
        sample = samples.get(lang, sample_id)

        self.output_preview_btn.setEnabled(False)
        self.output_preview_btn.setText(t("config.output.btn.playing"))

        def on_done():
            self.output_preview_btn.setEnabled(True)
            self.output_preview_btn.setText(t("config.output.btn.preview"))

        try:
            from modules_server.tts_engine import speak
            success = speak(
                text=sample, voice_name=voice_model,
                language_code=lang_codes.get(lang, "id-ID"),
                on_finished=on_done, force_google_tts=True
            )
            if not success:
                on_done()
                from modules_server.tts_engine import get_tts_engine
                err = getattr(get_tts_engine(), 'last_error', '') or "Unknown error (check logs/system.log)"
                QMessageBox.warning(self, t("common.error"),
                    t("config.output.err.preview_failed", voice=voice, err=err))
        except Exception as e:
            on_done()
            QMessageBox.critical(self, t("common.error"), f"{type(e).__name__}: {e}")

    def create_ai_provider_section(self, layout):
        """Create AI Provider section with flexible API key input"""
        group = QGroupBox(t("config.section.ai_provider"))
        group_layout = QVBoxLayout(group)
        group_layout.setSpacing(15)

        # Provider selection with better layout
        provider_layout = QHBoxLayout()
        provider_label = QLabel(t("config.label.provider"))
        provider_label.setMinimumWidth(100)
        provider_layout.addWidget(provider_label)

        self.provider_combo = QComboBox()
        # ChatGPT disabled — uncomment to re-enable: ["DeepSeek", "Gemini Flash Lite", "OpenAI (ChatGPT)"]
        self.provider_combo.addItems(["DeepSeek", "Gemini Flash Lite"])
        self.provider_combo.currentTextChanged.connect(self.on_provider_changed)
        provider_layout.addWidget(self.provider_combo)
        provider_layout.addStretch()
        group_layout.addLayout(provider_layout)

        # API Key input with better styling
        api_key_label = QLabel(t("config.label.api_key"))
        api_key_label.setMinimumWidth(100)
        group_layout.addWidget(api_key_label)

        # API Key input container
        api_key_container = QHBoxLayout()
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText(t("config.placeholder.api_key"))
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.textChanged.connect(self.on_api_key_changed)
        api_key_container.addWidget(self.api_key_input)

        # Show/Hide button with better styling
        show_btn = QPushButton(t("config.btn.show"))
        show_btn.setProperty("class", "secondary")
        show_btn.setMinimumWidth(70)
        show_btn.setMaximumWidth(90)
        show_btn.setToolTip(t("config.tooltip.show_api_key"))
        show_btn.clicked.connect(lambda: self.toggle_password_visibility(self.api_key_input))
        api_key_container.addWidget(show_btn)

        group_layout.addLayout(api_key_container)

        # Button container
        button_layout = QHBoxLayout()

        # Test button
        self.ai_test_btn = QPushButton(t("config.btn.test_connection"))
        self.ai_test_btn.setProperty("class", "success")
        self.ai_test_btn.clicked.connect(self.test_ai_api)
        self.ai_test_btn.setEnabled(False)  # Disabled until API key is entered
        button_layout.addWidget(self.ai_test_btn)

        button_layout.addStretch()
        group_layout.addLayout(button_layout)

        # Status with better styling
        self.ai_status = QLabel(t("config.status.no_api_key"))
        self.ai_status.setProperty("class", "status-info")
        self.ai_status.setStyleSheet(status_badge(TEXT_DIM))
        group_layout.addWidget(self.ai_status)

        layout.addWidget(group)


    def create_viewer_greeting_section(self, layout):
        """Greeting AI System — ON/OFF toggle + status indicator"""
        try:
            from ui.theme import (
                BG_BASE,
                BG_ELEVATED,
                BG_SURFACE,
                BORDER,
                CARD_STYLE,
                ERROR,
                PRIMARY,
                SECONDARY,
                SUCCESS,
                TEXT_MUTED,
                TEXT_PRIMARY,
                WARNING,
                btn_danger,
                btn_ghost,
                btn_primary,
                btn_success,
            )
            BORDER_COLOR = BORDER
        except ImportError:
            PRIMARY = "#2563EB"; BG_SURFACE = "#162032"
            BG_ELEVATED = "#1E2A3B"; TEXT_PRIMARY = "#F0F6FF"; TEXT_MUTED = "#94A3B8"
            SUCCESS = "#10B981"; WARNING = "#F59E0B"; ERROR = "#EF4444"
            BORDER_COLOR = "#1E3A5F"
            def btn_success(extra=""): return f"background-color:{SUCCESS};color:white;border:none;border-radius:6px;padding:6px 14px;{extra}"
            def btn_danger(extra=""): return f"background-color:{ERROR};color:white;border:none;border-radius:6px;padding:6px 14px;{extra}"

        from PyQt6.QtWidgets import QCheckBox, QFrame, QGroupBox, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

        group = QGroupBox(t("config.section.greeting_ai"))
        group_layout = QVBoxLayout(group)
        group_layout.setSpacing(12)

        # Deskripsi
        desc = QLabel(t("config.greeting.desc"))
        desc.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px; padding: 4px; line-height: 1.5;")
        desc.setWordWrap(True)
        group_layout.addWidget(desc)

        # Toggle ON/OFF
        self.greeting_ai_cb = QCheckBox(t("config.greeting.toggle"))
        self.greeting_ai_cb.setStyleSheet(f"""
            QCheckBox {{
                color: {TEXT_PRIMARY};
                font-size: 13px;
                font-weight: bold;
                padding: 5px;
            }}
            QCheckBox::indicator {{
                width: 18px; height: 18px;
            }}
            QCheckBox::indicator:checked {{
                background-color: {PRIMARY};
                border: 2px solid {PRIMARY};
                border-radius: 3px;
            }}
            QCheckBox::indicator:unchecked {{
                background-color: {BG_SURFACE};
                border: 2px solid {BORDER_COLOR};
                border-radius: 3px;
            }}
        """)
        greeting_ai_enabled = self.cfg.get("greeting_ai_enabled", False)
        self.greeting_ai_cb.setChecked(greeting_ai_enabled)
        self.greeting_ai_cb.stateChanged.connect(self.on_greeting_ai_enabled_changed)
        group_layout.addWidget(self.greeting_ai_cb)

        # Status frame
        status_frame = QFrame()
        status_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_ELEVATED};
                border: 1px solid {BORDER_COLOR};
                border-radius: 8px;
                padding: 12px;
            }}
        """)
        status_layout = QVBoxLayout(status_frame)
        status_layout.setSpacing(6)

        self.greeting_ai_status_label = QLabel(t("config.greeting.status_inactive"))
        self.greeting_ai_status_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 13px; font-weight: bold;")
        status_layout.addWidget(self.greeting_ai_status_label)

        last_updated = self.cfg.get("greeting_ai_last_updated", None)
        last_text = t("config.greeting.last_updated", time=last_updated) if last_updated else t("config.greeting.never_updated")
        self.greeting_ai_updated_label = QLabel(last_text)
        self.greeting_ai_updated_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px; font-style: italic;")
        status_layout.addWidget(self.greeting_ai_updated_label)

        group_layout.addWidget(status_frame)

        # Tombol regenerasi manual
        regen_btn_layout = QHBoxLayout()
        self.greeting_ai_regen_btn = QPushButton(t("config.greeting.regen_btn"))
        self.greeting_ai_regen_btn.setStyleSheet(btn_success())
        self.greeting_ai_regen_btn.setEnabled(greeting_ai_enabled)
        self.greeting_ai_regen_btn.clicked.connect(self.on_greeting_ai_regen_clicked)
        regen_btn_layout.addWidget(self.greeting_ai_regen_btn)
        regen_btn_layout.addStretch()
        group_layout.addLayout(regen_btn_layout)

        # Info
        info = QLabel(t("config.greeting.info"))
        info.setStyleSheet(f"color: {WARNING}; font-size: 11px; font-style: italic; padding: 6px; background-color: {BG_ELEVATED}; border-radius: 4px;")
        info.setWordWrap(True)
        group_layout.addWidget(info)

        layout.addWidget(group)

    def create_sales_template_section(self, layout):
        """Create product knowledge section — AI uses this to understand what's being sold"""
        group = QGroupBox(t("config.section.product_knowledge"))
        group_layout = QVBoxLayout(group)
        group_layout.setSpacing(10)

        desc = QLabel(t("config.knowledge.desc"))
        desc.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px; padding: 6px; line-height: 1.5;")
        desc.setWordWrap(True)
        group_layout.addWidget(desc)

        # Editable knowledge text area
        self.context_input = QTextEdit()
        self.context_input.setMinimumHeight(200)
        self.context_input.setMaximumHeight(240)
        self.context_input.setPlaceholderText(t("config.knowledge.placeholder"))
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
                line-height: 1.5;
            }}
            QTextEdit:focus {{
                border: 2px solid {PRIMARY};
                background-color: {BG_SURFACE};
            }}
        """)
        self.context_input.textChanged.connect(self._update_char_count)
        group_layout.addWidget(self.context_input)

        # Char count label
        self.char_count_label = QLabel("")
        self.char_count_label.setStyleSheet(f"color: {TEXT_DIM}; font-size: 11px; padding: 2px 4px;")
        group_layout.addWidget(self.char_count_label)
        self._update_char_count()

        # Buttons
        button_layout = QHBoxLayout()

        save_context_btn = QPushButton(t("config.btn.save_knowledge"))
        save_context_btn.setStyleSheet(btn_success())
        save_context_btn.clicked.connect(self.save_context_setting)
        button_layout.addWidget(save_context_btn)

        self.polish_btn = QPushButton(t("config.btn.polish_ai"))
        self.polish_btn.setStyleSheet(btn_primary())
        self.polish_btn.clicked.connect(self._polish_knowledge_with_ai)
        button_layout.addWidget(self.polish_btn)

        self.revert_btn = QPushButton(t("config.btn.revert"))
        self.revert_btn.setStyleSheet(btn_ghost())
        self.revert_btn.clicked.connect(self._revert_context)
        self.revert_btn.setVisible(False)
        button_layout.addWidget(self.revert_btn)

        clear_context_btn = QPushButton(t("config.btn.clear"))
        clear_context_btn.setStyleSheet(btn_danger())
        clear_context_btn.clicked.connect(self.clear_context_setting)
        button_layout.addWidget(clear_context_btn)

        button_layout.addStretch()
        group_layout.addLayout(button_layout)

        layout.addWidget(group)

    def create_google_tts_section(self, layout):
        """TTS section — conditional Gemini API key input berdasar AI provider.

        Rules (per v1.0.26):
        - AI Provider = Gemini → TTS pakai same key dari AI section (tidak ada input di TTS)
        - AI Provider = DeepSeek → TTS butuh Gemini key terpisah (input muncul di TTS section)

        Input `tts_api_key_input` dinamis visible/hidden via _update_tts_key_visibility()
        yang dipanggil dari on_provider_changed.
        """
        group = QGroupBox(t("config.section.tts"))
        group_layout = QVBoxLayout(group)
        group_layout.setSpacing(12)

        # Info label — konten berubah dinamis via _update_tts_key_visibility()
        self.tts_info_label = QLabel()
        self.tts_info_label.setWordWrap(True)
        self.tts_info_label.setStyleSheet(
            f"color: {ACCENT}; font-size: 12px; padding: 8px; "
            f"background-color: {BG_ELEVATED}; border-radius: 6px;"
        )
        group_layout.addWidget(self.tts_info_label)

        # Conditional API key input — visible hanya kalau AI=DeepSeek
        self.tts_key_container = QWidget()
        key_row = QHBoxLayout(self.tts_key_container)
        key_row.setContentsMargins(0, 0, 0, 0)

        key_label = QLabel(t("config.tts.label.gemini_key"))
        key_label.setMinimumWidth(120)
        key_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        key_row.addWidget(key_label)

        self.tts_api_key_input = QLineEdit()
        self.tts_api_key_input.setPlaceholderText(t("config.tts.placeholder.gemini_key"))
        self.tts_api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.tts_api_key_input.textChanged.connect(self._on_tts_gemini_key_changed)
        key_row.addWidget(self.tts_api_key_input)

        show_btn = QPushButton(t("config.btn.show_key"))
        show_btn.setProperty("class", "secondary")
        show_btn.setFixedWidth(70)
        show_btn.clicked.connect(lambda: self.toggle_password_visibility(self.tts_api_key_input))
        key_row.addWidget(show_btn)

        group_layout.addWidget(self.tts_key_container)

        # Hidden legacy widgets — tidak visible tapi di-reference method lain
        self.tts_detect_btn = QPushButton()
        self.tts_detect_btn.setVisible(False)
        self.tts_key_type_label = QLabel()
        self.tts_key_type_label.setVisible(False)

        # Voice selector for test
        voice_row = QHBoxLayout()
        voice_row_label = QLabel(t("config.label.test_voice"))
        voice_row_label.setMinimumWidth(80)
        voice_row_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        voice_row.addWidget(voice_row_label)

        self.tts_voice_combo = QComboBox()
        self.tts_voice_combo.setMinimumWidth(280)
        self._populate_tts_voice_combo("all")  # default: semua voice
        voice_row.addWidget(self.tts_voice_combo)
        voice_row.addStretch()
        group_layout.addLayout(voice_row)

        # Button container
        tts_button_layout = QHBoxLayout()

        # Test button
        self.tts_test_btn = QPushButton(t("config.btn.test_tts"))
        self.tts_test_btn.setProperty("class", "success")
        self.tts_test_btn.clicked.connect(self.test_google_tts)
        self.tts_test_btn.setEnabled(False)  # Disabled until API key is provided
        tts_button_layout.addWidget(self.tts_test_btn)

        tts_button_layout.addStretch()
        group_layout.addLayout(tts_button_layout)

        # Status with better styling
        self.tts_status = QLabel(t("config.tts.status_no_key"))
        self.tts_status.setProperty("class", "status-info")
        self.tts_status.setStyleSheet(status_badge(TEXT_DIM))
        group_layout.addWidget(self.tts_status)

        layout.addWidget(group)

    def create_status_section(self, layout):
        """Create status section with better styling"""
        group = QGroupBox(t("config.section.status"))
        group_layout = QVBoxLayout(group)
        group_layout.setSpacing(15)

        # Status overview with better styling
        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(120)
        self.status_text.setMinimumHeight(120)
        self.status_text.setPlainText(t("config.status.empty_overview"))
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
        self.ai_indicator = QLabel(t("config.status.ai_not_connected"))
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
        self.tts_indicator = QLabel(t("config.status.tts_not_connected"))
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
        save_btn = QPushButton(t("config.btn.save_config"))
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
        reset_btn = QPushButton(t("config.btn.reset_config"))
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
        test_all_btn = QPushButton(t("config.btn.test_all"))
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

    def on_ui_language_changed(self, idx):
        """Handle perubahan UI language — save ke config + tampilkan restart prompt."""
        new_lang = self.ui_lang_combo.itemData(idx)
        if new_lang == i18n.current_language():
            return
        i18n.set_language(new_lang)
        QMessageBox.information(
            self,
            t("common.info"),
            t("config.info.restart_required"),
        )

    def on_provider_changed(self, provider):
        """Handle provider selection change"""
        if provider == "DeepSeek":
            self.api_key_input.setPlaceholderText(t("config.placeholder.deepseek_key"))
        elif provider == "Gemini Flash Lite":
            self.api_key_input.setPlaceholderText(t("config.placeholder.gemini_key"))
        # v1.0.26: toggle TTS API key input visibility
        self._update_tts_key_visibility(provider)
        self.update_status_overview()

    def _update_tts_key_visibility(self, provider: str):
        """Show/hide Gemini API Key input di TTS section berdasar AI provider.

        - AI=Gemini → key sudah di AI section, TTS pakai same → hide input, info-only
        - AI=DeepSeek → butuh Gemini key terpisah untuk TTS → show input
        """
        if not hasattr(self, 'tts_key_container'):
            return  # TTS section belum di-create

        is_gemini_ai = provider == "Gemini Flash Lite"
        self.tts_key_container.setVisible(not is_gemini_ai)

        if is_gemini_ai:
            self.tts_info_label.setText(t("config.tts.info_provider_gemini"))
            # Sync TTS status dari AI key — kalau user sudah isi Gemini key di AI section,
            # TTS otomatis available karena sharing key
            self._sync_tts_status_to_ai_key()
        else:
            self.tts_info_label.setText(t("config.tts.info_provider_deepseek"))

    def _sync_tts_status_to_ai_key(self):
        """Set tts_status berdasar AI key input (karena shared key untuk Gemini provider)."""
        if not hasattr(self, 'tts_status') or not hasattr(self, 'api_key_input'):
            return
        ai_key = self.api_key_input.text().strip()
        if ai_key:
            self.tts_status.setText(t("config.tts.status_ready"))
            self.tts_status.setProperty("class", "status-warning")
            self.tts_status.setStyleSheet(status_badge(WARNING))
            if hasattr(self, 'tts_test_btn'):
                self.tts_test_btn.setEnabled(True)
        else:
            self.tts_status.setText(t("config.tts.status_no_key"))
            self.tts_status.setProperty("class", "status-info")
            self.tts_status.setStyleSheet(status_badge(TEXT_DIM))
            if hasattr(self, 'tts_test_btn'):
                self.tts_test_btn.setEnabled(False)

    def _on_tts_gemini_key_changed(self):
        """Auto-save Gemini TTS key ke api_keys.GEMINI_API_KEY saat user ketik."""
        new_key = self.tts_api_key_input.text().strip()
        if not new_key:
            return
        try:
            cfg = self.cfg.get_all_settings()
            if "api_keys" not in cfg:
                cfg["api_keys"] = {}
            cfg["api_keys"]["GEMINI_API_KEY"] = new_key
            config_path = Path("config/settings.json")
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(cfg, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save Gemini TTS key: {e}")

    def on_api_key_changed(self):
        """Handle API key input change"""
        api_key = self.api_key_input.text().strip()
        self.ai_test_btn.setEnabled(len(api_key) > 0)

        if len(api_key) > 0:
            self.ai_status.setText(t("config.status.api_key_ready"))
            self.ai_status.setProperty("class", "status-warning")
            self.ai_status.setStyleSheet(status_badge(WARNING))
        else:
            self.ai_status.setText(t("config.status.no_api_key"))
            self.ai_status.setProperty("class", "status-info")
            self.ai_status.setStyleSheet(status_badge(TEXT_DIM))

        # v1.0.26: Kalau provider=Gemini, key ini juga dipakai TTS → sync TTS status
        provider = self.provider_combo.currentText() if hasattr(self, 'provider_combo') else ""
        if provider == "Gemini Flash Lite":
            self._sync_tts_status_to_ai_key()

        self.update_status_overview()

    def test_all_connections(self):
        """Test all configured connections"""
        api_key = self.api_key_input.text().strip()
        tts_api_key = self.tts_api_key_input.text().strip()

        if not api_key and not tts_api_key:
            QMessageBox.warning(
                self,
                t("common.warning"),
                t("config.msg.test_all_empty")
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
            t("config.msg.test_all_done_title"),
            t("config.msg.test_all_done")
        ))

    def on_tts_api_key_changed(self):
        """Handle TTS API Key input change"""
        api_key = self.tts_api_key_input.text().strip()

        if len(api_key) > 0:
            self.tts_test_btn.setEnabled(True)
            self.tts_detect_btn.setEnabled(True)
            self.tts_status.setText(t("config.tts.status_ready"))
            self.tts_status.setProperty("class", "status-warning")
            self.tts_status.setStyleSheet(status_badge(WARNING))
            # Reset label deteksi saat key berubah
            self.tts_key_type_label.setText(t("config.tts.key_type_undetected_hint"))
            self.tts_key_type_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px; padding: 3px 5px;")
        else:
            self.tts_test_btn.setEnabled(False)
            self.tts_detect_btn.setEnabled(False)
            self.tts_status.setText(t("config.tts.status_no_key"))
            self.tts_status.setProperty("class", "status-info")
            self.tts_status.setStyleSheet(status_badge(TEXT_DIM))

        self.update_status_overview()

    def _update_char_count(self):
        """Update character count label"""
        count = len(self.context_input.toPlainText())
        self.char_count_label.setText(t("config.knowledge.char_count", count=count))

    def on_template_changed(self, template_key):
        """Load selected template directly into the editable context input"""
        if template_key:
            self.context_input.setPlainText(get_template(template_key))

    def _polish_knowledge_with_ai(self):
        """Use AI to improve the product knowledge text"""
        text = self.context_input.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, t("config.err.text_empty_title"), t("config.err.text_empty"))
            return

        self._original_context = text
        self.polish_btn.setEnabled(False)
        self.polish_btn.setText(t("config.btn.polish_processing"))
        self.char_count_label.setText(t("config.knowledge.processing"))
        self.revert_btn.setVisible(False)

        self._polish_thread = PolishKnowledgeThread(text)
        self._polish_thread.finished.connect(self._on_polish_done)
        self._polish_thread.status_update.connect(self.char_count_label.setText)
        self._polish_thread.start()

    def _on_polish_done(self, result: str):
        """Handle AI polish result"""
        self.polish_btn.setEnabled(True)
        self.polish_btn.setText(t("config.btn.polish_ai"))
        if result:
            self.context_input.setPlainText(result)
            self.revert_btn.setVisible(True)
            self.char_count_label.setText(t("config.knowledge.char_count_polished", count=len(result)))
        else:
            self._update_char_count()
            QMessageBox.warning(self, t("config.err.polish_failed_title"), t("config.err.polish_failed"))

    def _revert_context(self):
        """Revert to original text before AI polishing"""
        if hasattr(self, '_original_context') and self._original_context:
            self.context_input.setPlainText(self._original_context)
            self._original_context = ""
        self.revert_btn.setVisible(False)

    def save_context_setting(self):
        """Save context setting from manual input"""
        context_content = self.context_input.toPlainText().strip()

        if not context_content:
            QMessageBox.warning(self, t("common.warning"), t("config.err.context_empty"))
            return

        try:
            # Save context to user_context setting
            config = self.cfg.get_all_settings()
            config["user_context"] = context_content

            # Save to file
            config_path = Path("config/settings.json")
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            self.char_count_label.setText(t("config.knowledge.char_count_saved", count=len(context_content)))

            QMessageBox.information(
                self,
                t("config.msg.context_saved_title"),
                t("config.msg.context_saved")
            )

        except Exception as e:
            QMessageBox.critical(self, t("common.error"), t("config.err.context_save_failed", reason=str(e)))

    def clear_context_setting(self):
        """Clear context setting"""
        reply = QMessageBox.question(
            self,
            t("common.confirm"),
            t("config.confirm.clear_context"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.context_input.clear()
            self.template_combo.setCurrentIndex(0)

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
            self.ai_status.setText(t("config.status.api_key_empty"))
            self.ai_status.setStyleSheet(status_badge(ERROR))
            return

        # v1.0.26: Auto-save key ke settings SEBELUM test supaya TTS reinit
        # (di on_test_result on success) bisa baca key yang benar.
        try:
            cfg = self.cfg.get_all_settings()
            if "api_keys" not in cfg:
                cfg["api_keys"] = {}
            key_field = "GEMINI_API_KEY" if provider == "Gemini Flash Lite" else "DEEPSEEK_API_KEY"
            cfg["api_keys"][key_field] = api_key
            cfg["ai_provider"] = "gemini" if provider == "Gemini Flash Lite" else "deepseek"
            config_path = Path("config/settings.json")
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(cfg, f, indent=2, ensure_ascii=False)
            logger.info(f"[CONFIG] Auto-saved {key_field} before test")
        except Exception as e:
            logger.warning(f"Auto-save before test failed: {e}")

        self.ai_test_btn.setText(t("config.btn.testing"))
        self.ai_test_btn.setEnabled(False)

        # Determine API type for testing
        api_type_map = {"DeepSeek": "deepseek", "Gemini Flash Lite": "gemini"}
        api_type = api_type_map.get(provider, "deepseek")

        # Stop existing thread if running
        if self.test_thread and self.test_thread.isRunning():
            self.test_thread.quit()
            self.test_thread.wait(500)

        # Start test thread
        self.test_thread = APITestThread(api_type, api_key)
        self.test_thread.result_ready.connect(self.on_test_result)
        self.test_thread.start()

    def _populate_tts_voice_combo(self, key_type: str = "all"):
        """Isi dropdown suara test — Gemini voices only.

        Per v1.0.25: Cloud TTS voices (Standard/Chirp3/Wavenet) di-remove untuk
        simplify. Gemini key lebih umum dipakai user (dari AI Studio) dan support
        multilingual voices yang natural. Cloud voices butuh Cloud TTS API
        key terpisah yang jarang dipakai.

        Parameter key_type dipertahankan untuk backward-compat tapi ignored.
        """
        self.tts_voice_combo.clear()
        voices = []
        try:
            voices_file = os.path.join(os.path.dirname(__file__), '..', 'config', 'voices.json')
            with open(voices_file, 'r', encoding='utf-8') as f:
                voices_data = json.load(f)

            if "gemini_flash" in voices_data:
                for lang_code, voice_list in voices_data["gemini_flash"].items():
                    for v in voice_list:
                        label = f"{v['model']} ({v['gender']}) - {lang_code}"
                        if label not in voices:
                            voices.append(label)
        except Exception:
            pass

        if not voices:
            voices = ["Gemini-Puck (MALE) - id-ID", "Gemini-Zephyr (FEMALE) - id-ID"]

        self.tts_voice_combo.addItems(voices)

        for i, v in enumerate(voices):
            if v.startswith("Gemini-Puck"):
                self.tts_voice_combo.setCurrentIndex(i)
                break

    def _detect_key_type(self):
        """Probe API key ke Gemini dan Cloud TTS untuk deteksi tipe — jalankan di thread."""
        api_key = self.tts_api_key_input.text().strip()
        if not api_key:
            return

        self.tts_detect_btn.setText(t("config.btn.detecting"))
        self.tts_detect_btn.setEnabled(False)
        self.tts_key_type_label.setText(t("config.tts.detecting"))
        self.tts_key_type_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px; padding: 3px 5px;")

        def probe():
            import requests as req
            supports_gemini = False
            supports_cloud = False
            try:
                r = req.get(
                    "https://generativelanguage.googleapis.com/v1beta/models",
                    params={"key": api_key, "pageSize": 1},
                    timeout=8
                )
                supports_gemini = r.status_code == 200
            except Exception:
                pass
            try:
                r = req.get(
                    "https://texttospeech.googleapis.com/v1/voices",
                    params={"key": api_key, "languageCode": "id-ID"},
                    timeout=8
                )
                supports_cloud = r.status_code == 200
            except Exception:
                pass
            return supports_gemini, supports_cloud

        class _DetectThread(QThread):
            done = pyqtSignal(bool, bool)
            def __init__(self, fn):
                super().__init__()
                self._fn = fn
            def run(self):
                result = self._fn()
                self.done.emit(*result)

        self._detect_thread = _DetectThread(probe)
        self._detect_thread.done.connect(self._on_detection_done)
        self._detect_thread.start()

    def _on_detection_done(self, supports_gemini: bool, supports_cloud: bool):
        """Update UI berdasarkan hasil deteksi key type."""
        self.tts_detect_btn.setText(t("config.btn.detect_key_type"))
        self.tts_detect_btn.setEnabled(True)

        if supports_gemini and supports_cloud:
            key_type = "all"
            label = t("config.tts.detect_all")
            color = SUCCESS
        elif supports_gemini:
            key_type = "gemini"
            label = t("config.tts.detect_gemini")
            color = SUCCESS
        elif supports_cloud:
            key_type = "cloud"
            label = t("config.tts.detect_cloud")
            color = SUCCESS
        else:
            key_type = "all"
            label = t("config.tts.detect_none")
            color = ERROR

        self.tts_key_type_label.setText(label)
        self.tts_key_type_label.setStyleSheet(f"color: {color}; font-size: 11px; padding: 3px 5px; font-weight: bold;")
        self._populate_tts_voice_combo(key_type)
        # Simpan ke config agar Cohost tab bisa baca
        self.cfg.set("tts_key_type", key_type)
        # Broadcast ke tab lain (main_window akan forward ke Cohost tab)
        self.tts_key_type_changed.emit(key_type)
        logger.info(f"[TTS_DETECT] gemini={supports_gemini}, cloud={supports_cloud} → key_type={key_type}")

    def test_google_tts(self):
        """Test TTS pakai unified GEMINI_API_KEY (per v1.0.26).

        Tidak ada input field terpisah — key dibaca dari api_keys.GEMINI_API_KEY.
        User isi key di section AI Provider di atas.
        """
        api_key = self.cfg.get("api_keys", {}).get("GEMINI_API_KEY", "").strip()
        # Fallback: legacy google_tts_api_key untuk backward-compat
        if not api_key:
            api_key = self.cfg.get("google_tts_api_key", "").strip()

        if not api_key:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, t("common.error"),
                "Gemini API Key belum diisi.\nIsi di section 'AI Provider' di atas.")
            self.tts_status.setText(t("config.tts.status_no_key_err"))
            self.tts_status.setStyleSheet(status_badge(ERROR))
            return

        self.tts_test_btn.setText(t("config.btn.testing"))
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
                raise Exception(t("config.tts.engine_init_failed"))

            logger.info("[CONFIG_TEST] TTS engine reinitialized, testing...")

            test_text = t("config.tts.test_text")

            # Pakai voice yang dipilih user di combo, bukan voice dari Cohost tab
            selected_voice = self.tts_voice_combo.currentText().split(' (')[0].strip()
            # Ekstrak lang code dari nama voice (misal "en-AU-Chirp3-..." → "en-AU")
            # Gemini voices multilingual → derive lang_code dari output_language
            if selected_voice.startswith("Gemini-"):
                output_lang = self.cfg.get("output_language", "Indonesia")
                lang_map = {"Indonesia": "id-ID", "Malaysia": "ms-MY", "English": "en-US"}
                lang_code = lang_map.get(output_lang, "id-ID")
            else:
                parts = selected_voice.split('-')
                lang_code = f"{parts[0]}-{parts[1]}" if len(parts) >= 2 else "id-ID"

            logger.info(f"[CONFIG_TEST] Testing voice: {selected_voice}")
            success = speak(
                text=test_text,
                voice_name=selected_voice,
                language_code=lang_code,
                force_google_tts=True
            )

            if success:
                self.tts_status.setText(t("config.tts.status_ok"))
                self.tts_status.setProperty("class", "status-success")
                self.tts_status.setStyleSheet(status_badge(SUCCESS))
                logger.info("[CONFIG_TEST] ✅ Google TTS test successful")
            else:
                raise Exception(t("config.tts.test_failed"))

        except Exception as e:
            self.tts_status.setText(t("config.tts.status_err", reason=str(e)))
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
            self.tts_test_btn.setText(t("config.btn.test_google_tts"))
            self.tts_test_btn.setEnabled(True)
            self.update_status_overview()

    def on_test_result(self, api_type, success, message):
        """Handle API test result"""
        self.ai_test_btn.setText(t("config.btn.test_connection"))
        self.ai_test_btn.setEnabled(True)

        if success:
            self.ai_status.setText(t("config.status.prefix", message=message))
            self.ai_status.setProperty("class", "status-success")
            self.ai_status.setStyleSheet(status_badge(SUCCESS))
            # v1.0.26: Kalau provider=Gemini, AI test sukses = TTS juga valid (same key)
            provider = self.provider_combo.currentText() if hasattr(self, 'provider_combo') else ""
            if provider == "Gemini Flash Lite" and hasattr(self, 'tts_status'):
                self.tts_status.setText(t("config.tts.status_ok"))
                self.tts_status.setProperty("class", "status-success")
                self.tts_status.setStyleSheet(status_badge(SUCCESS))
                # Reinit TTS engine supaya load key baru
                try:
                    from modules_server.tts_engine import reinitialize_tts_engine
                    reinitialize_tts_engine()
                    logger.info("[CONFIG] TTS engine reinitialized after AI Gemini test success")
                except Exception as e:
                    logger.warning(f"TTS reinit skipped: {e}")
        else:
            self.ai_status.setText(t("config.status.prefix", message=message))
            self.ai_status.setProperty("class", "status-error")
            self.ai_status.setStyleSheet(status_badge(ERROR))

        self.update_status_overview()

    def update_status_overview(self):
        """Update status overview with better formatting"""
        api_key = self.api_key_input.text().strip()
        provider = self.provider_combo.currentText()
        tts_api_key = self.tts_api_key_input.text().strip() if hasattr(self, 'tts_api_key_input') else ""

        status_lines = []
        status_lines.append(t("config.status.header"))
        status_lines.append("")

        # AI Provider Status
        if api_key:
            status_lines.append(t("config.status.ai_configured", provider=provider, count=len(api_key)))
            self.ai_indicator.setText(t("config.status.ai_connected", provider=provider))
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
            status_lines.append(t("config.status.ai_unconfigured", provider=provider))
            self.ai_indicator.setText(t("config.status.ai_not_connected"))
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
            status_lines.append(t("config.status.tts_configured"))
            masked = f"{'*' * (len(tts_api_key) - 4)}{tts_api_key[-4:] if len(tts_api_key) > 4 else '****'}"
            status_lines.append(t("config.status.tts_key_masked", masked=masked))
            self.tts_indicator.setText(t("config.status.tts_connected"))
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
            status_lines.append(t("config.status.tts_unconfigured"))
            self.tts_indicator.setText(t("config.status.tts_not_connected"))
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
            status_lines.append(t("config.status.ready"))
            status_lines.append(t("config.status.ready_detail"))
        elif api_key:
            status_lines.append(t("config.status.partial"))
            status_lines.append(t("config.status.partial_detail"))
        else:
            status_lines.append(t("config.status.not_ready"))
            status_lines.append(t("config.status.not_ready_detail"))

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

            # Save AI provider selection
            provider_map = {"DeepSeek": "deepseek", "Gemini Flash Lite": "gemini"}
            config["ai_provider"] = provider_map.get(provider, "deepseek")

            # Save AI API keys
            if api_key:
                if provider == "DeepSeek":
                    config["api_keys"]["DEEPSEEK_API_KEY"] = api_key
                elif provider == "Gemini Flash Lite":
                    config["api_keys"]["GEMINI_API_KEY"] = api_key

            # v1.0.26: Simpan Gemini TTS key (kalau provider=DeepSeek, ada input terpisah)
            # Kalau provider=Gemini, tts_api_key sengaja kosong (input hidden) — TTS pakai
            # api_key (AI key) yang sudah disimpan di GEMINI_API_KEY di atas.
            if tts_api_key and provider == "DeepSeek":
                config["api_keys"]["GEMINI_API_KEY"] = tts_api_key

            # Save to file
            config_path = Path("config/settings.json")
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            # IMPORTANT: Reinitialize TTS engine setelah GEMINI_API_KEY berubah.
            # Dulu hanya reinit kalau tts_api_key diisi — tapi sekarang GEMINI_API_KEY bisa
            # datang dari AI section (provider=Gemini) atau TTS input (provider=DeepSeek).
            # Reinit kalau salah satu sumber menghasilkan key baru.
            should_reinit_tts = (
                (provider == "Gemini Flash Lite" and api_key) or  # AI Gemini → key shared
                (provider == "DeepSeek" and tts_api_key)           # DeepSeek → separate Gemini key
            )
            if should_reinit_tts:
                try:
                    from modules_server.tts_engine import reinitialize_tts_engine
                    logger.info("[CONFIG] Reinitializing TTS engine with new GEMINI_API_KEY...")
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
                    elif provider == "Gemini Flash Lite":
                        from modules_client.gemini_ai import reinitialize_gemini
                        logger.info("[CONFIG] Reinitializing Gemini AI with new API key...")
                        reinitialize_gemini()
                        logger.info("[CONFIG] ✅ Gemini AI reinitialized successfully")
                except Exception as ai_reinit_error:
                    logger.error(f"[CONFIG] Failed to reinitialize AI: {ai_reinit_error}")

            # Telemetry: config saved
            try:
                from modules_client.telemetry import capture as _tel_capture
                current_voice = self.tts_voice_combo.currentText() if hasattr(self, 'tts_voice_combo') else ""
                _tel_capture("config_saved", {"provider": provider, "tts_voice": current_voice})
            except Exception:
                pass

            # Show success message
            tts_status = t("config.msg.tts_configured_short") if tts_api_key else t("config.msg.tts_unconfigured_short")
            QMessageBox.information(
                self,
                t("config.msg.save_success_title"),
                t("config.msg.save_success", tts_status=tts_status)
            )
            self.update_status_overview()

        except Exception as e:
            QMessageBox.critical(self, t("common.error"), t("config.err.save_failed", reason=str(e)))

    def load_saved_keys(self):
        """Load saved API keys and context"""
        try:
            api_keys = self.cfg.get("api_keys", {})
            user_context = self.cfg.get("user_context", "")

            # Load AI API key berdasarkan ai_provider yang tersimpan
            ai_provider = self.cfg.get("ai_provider", "deepseek")
            if ai_provider == "gemini" and "GEMINI_API_KEY" in api_keys:
                self.provider_combo.setCurrentText("Gemini Flash Lite")
                self.api_key_input.setText(api_keys["GEMINI_API_KEY"])
            elif "DEEPSEEK_API_KEY" in api_keys:
                self.provider_combo.setCurrentText("DeepSeek")
                self.api_key_input.setText(api_keys["DEEPSEEK_API_KEY"])

            # v1.0.26: Gemini TTS key (dipakai kalau provider=DeepSeek)
            # Populate input dengan GEMINI_API_KEY dari api_keys, bukan google_tts_api_key
            if hasattr(self, 'tts_api_key_input'):
                gemini_tts_key = api_keys.get("GEMINI_API_KEY", "")
                # Fallback: legacy google_tts_api_key untuk backward-compat
                if not gemini_tts_key:
                    gemini_tts_key = self.cfg.get("google_tts_api_key", "")
                self.tts_api_key_input.setText(gemini_tts_key)

            # Set visibility TTS key berdasar current provider
            if hasattr(self, '_update_tts_key_visibility'):
                current_provider = self.provider_combo.currentText()
                self._update_tts_key_visibility(current_provider)
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
            t("common.confirm"),
            t("config.confirm.reset"),
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

            self.ai_status.setText(t("config.status.no_api_key"))
            self.ai_status.setProperty("class", "status-info")
            self.ai_status.setStyleSheet(status_badge(TEXT_DIM))

            self.tts_status.setText(t("config.status.tts_no_credential"))
            self.tts_status.setProperty("class", "status-info")
            self.tts_status.setStyleSheet(status_badge(TEXT_DIM))

            if hasattr(self, 'template_status'):
                self.template_status.setText(t("config.status.all_reset"))
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
                        t("common.warning"),
                        t("config.greeting.slots_min_5", filled=filled_slots, need=5 - filled_slots)
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
                    QMessageBox.warning(self, t("common.warning"), t("config.greeting.slot_empty", slot=slot_number))
                    return

                print(f"[CONFIG] Testing greeting slot {slot_number}: {text}")

                # Import TTS function
                try:
                    from modules_server.tts_engine import speak

                    # Get current voice setting
                    voice_setting = self.cfg.get("tts_voice", "id-ID-Standard-B (MALE)")
                    # Derive language_code dari output_language (bilingual-aware)
                    output_lang = self.cfg.get("output_language", "Indonesia")
                    lang_map = {"Indonesia": "id-ID", "Malaysia": "ms-MY", "English": "en-US"}
                    language_code = lang_map.get(output_lang, "id-ID")

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
                        QMessageBox.warning(self, t("common.error"), t("config.greeting.tts_failed", slot=slot_number))

                except ImportError as e:
                    QMessageBox.warning(self, t("common.error"), t("config.greeting.tts_unavailable", reason=str(e)))

        except Exception as e:
            print(f"Error testing greeting slot {slot_number}: {e}")
            QMessageBox.critical(self, t("common.error"), t("config.greeting.slot_test_err", slot=slot_number, reason=str(e)))

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
                t("config.greeting.slots_saved_title"),
                t("config.greeting.slots_saved", count=saved_count)
            )
            print(f"[CONFIG] Saved {saved_count} greeting slots")

        except Exception as e:
            print(f"Error saving greeting slots: {e}")
            QMessageBox.critical(self, t("common.error"), t("config.greeting.slots_save_failed", reason=str(e)))

    def clear_all_greeting_slots(self):
        """Clear all greeting slots"""
        try:
            reply = QMessageBox.question(
                self,
                t("common.confirm"),
                t("config.greeting.confirm_clear_slots"),
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
                QMessageBox.information(self, t("config.greeting.slots_cleared_title"), t("config.greeting.slots_cleared"))

        except Exception as e:
            print(f"Error clearing greeting slots: {e}")
            QMessageBox.critical(self, t("common.error"), t("config.greeting.slots_clear_failed", reason=str(e)))

    def on_greeting_ai_enabled_changed(self):
        """Handle Greeting AI toggle ON/OFF."""
        try:
            enabled = self.greeting_ai_cb.isChecked()
            self.cfg.set("greeting_ai_enabled", enabled)
            self.cfg.set("sequential_greeting_enabled", enabled)
            self.cfg.set("custom_greeting_enabled", enabled)

            if hasattr(self, 'greeting_ai_regen_btn'):
                self.greeting_ai_regen_btn.setEnabled(enabled)

            if enabled:
                # Generate sapaan segera saat toggle ON — siap sebelum live dimulai
                from modules_client.sequential_greeting_manager import get_sequential_greeting_manager
                mgr = get_sequential_greeting_manager()
                mgr.prepare_texts()
            else:
                self.update_greeting_ai_status("idle", t("config.greeting.status_inactive"))

            print(f"[CONFIG] Greeting AI: {'ON' if enabled else 'OFF'}")
        except Exception as e:
            print(f"[CONFIG] Error on_greeting_ai_enabled_changed: {e}")

    def on_greeting_ai_regen_clicked(self):
        """Trigger manual regenerasi greeting AI (bisa sebelum atau saat live)."""
        try:
            from modules_client.sequential_greeting_manager import GreetingState, get_sequential_greeting_manager
            mgr = get_sequential_greeting_manager()
            if mgr.state == GreetingState.IDLE:
                # Belum live — pakai prepare_texts (tidak mulai timer)
                mgr.prepare_texts()
            else:
                # Sedang live — pakai force_regenerate (swap teks tanpa stop playback)
                mgr.force_regenerate()
            self.update_greeting_ai_status("regenerating", t("config.greeting.status_regenerating"))
        except Exception as e:
            print(f"[CONFIG] Error on_greeting_ai_regen_clicked: {e}")

    def update_greeting_ai_status(self, state: str, message: str):
        """Entry point callable from any thread — emits signal for GUI-thread update."""
        try:
            self.greeting_status_changed.emit(state, message)
        except Exception as e:
            print(f"[CONFIG] Error emitting greeting status: {e}")

    def _apply_greeting_status(self, state: str, message: str):
        """Apply greeting status update on GUI thread (called via signal)."""
        try:
            if not hasattr(self, 'greeting_ai_status_label'):
                return
            self.greeting_ai_status_label.setText(message)
            if state == "active":
                last_updated = self.cfg.get("greeting_ai_last_updated", "—")
                if hasattr(self, 'greeting_ai_updated_label'):
                    self.greeting_ai_updated_label.setText(t("config.greeting.last_updated", time=last_updated))
        except Exception as e:
            print(f"[CONFIG] Error _apply_greeting_status: {e}")
