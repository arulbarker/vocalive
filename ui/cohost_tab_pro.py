# ui/cohost_tab_pro.py
# Di bagian import pada cohost_tab_pro.py
import sys
import json
import subprocess
import threading
import time
import re
import json  # TAMBAHAN
import sounddevice as sd
import soundfile as sf
# Di awal file, setelah import
import logging
logging.basicConfig(
    filename="logs/cohost_pro.log",
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
from pathlib import Path

import keyboard
from PyQt6.QtCore    import QThread, pyqtSignal, QTimer, Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QComboBox,
    QPushButton, QTextEdit, QHBoxLayout, QCheckBox, QSpinBox, QScrollArea, QGroupBox, QSizePolicy
)
from datetime import datetime
from modules_server.tts_google import speak_with_google_cloud
from modules_client.subscription_checker import get_today_usage, add_usage, time_until_next_day
from PyQt6.QtWidgets import QMessageBox

# ─── fallback modules_client & modules_server ───────────────────────
# Lebih konsisten import TTS
try:
    from modules_client.config_manager import ConfigManager
    from modules_client.api import generate_reply
    from modules_client.translate_stt import transcribe
    from modules_server.tts_engine import speak
    from modules_server.tts_google import speak_with_google_cloud
    USE_GOOGLE_TTS = True
except ImportError:
    from modules_server.config_manager import ConfigManager
    from modules_server.deepseek_ai import generate_reply
    from modules_server.tts_engine import speak
    # STT hanya ada di client; jika tidak ada, stub error:
    def transcribe(*args, **kwargs):
        raise NotImplementedError("Fitur STT hanya tersedia di environment client")
    USE_GOOGLE_TTS = False

print(f"[DEBUG] TTS Engine loaded: {'Google TTS' if USE_GOOGLE_TTS else 'Default TTS'}")

    

# Paths
ROOT         = Path(__file__).resolve().parent.parent
SCRIPT_PATH  = ROOT / "listeners" / "chat_listener.py"
CHAT_BUFFER  = ROOT / "temp" / "chat_buffer.jsonl"
COHOST_LOG   = ROOT / "temp" / "cohost_log.txt"
TRIGGER_FILE = ROOT / "temp" / "trigger.txt"
VOICES_PATH  = ROOT / "config" / "voices.json"

# Utility functions for simplifying hasattr checks
def safe_attr_check(obj, attr_name):
    """Check if object has attribute and it's truthy"""
    try:
        return hasattr(obj, attr_name) and getattr(obj, attr_name)
    except Exception:
        return False

def safe_timer_check(obj, timer_name):
    """Check if object has timer attribute and it's active"""
    return safe_attr_check(obj, timer_name) and getattr(obj, timer_name) and getattr(obj, timer_name).isActive()

class FileMonitorThread(QThread):
    newComment = pyqtSignal(str, str)

    def __init__(self, buffer_file: Path):
        super().__init__()
        self.buffer_file = buffer_file
        self._seen = set()
        self._running = True
        buffer_file.parent.mkdir(exist_ok=True)
        buffer_file.touch(exist_ok=True)

    def run(self):
        while self._running:
            try:
                lines = self.buffer_file.read_text(encoding="utf-8").splitlines()
            except:
                lines = []
            for line in lines:
                try:
                    e = json.loads(line)
                    key = (e["author"], e["message"])
                    if key not in self._seen:
                        self._seen.add(key)
                        self.newComment.emit(e["author"], e["message"])
                except:
                    continue
            time.sleep(0.5)

    def stop(self):
        self._running = False
        self.wait()


class ReplyThread(QThread):
    finished = pyqtSignal(str, str, str)

    def __init__(
        self,
        author: str,
        message: str,
        cohost_name: str,
        streamer_name: str,
        personality: str,
        lang_out: str,
        extra_prompt: str,
        voice_model: str | None
    ):
        super().__init__()
        self.author        = author
        self.message       = message
        self.cohost_name   = cohost_name
        self.streamer_name = streamer_name
        self.personality   = personality
        self.lang_out      = lang_out
        self.extra         = extra_prompt
        self.voice_model   = voice_model

    def run(self):
        prompt = (
            f"Kamu adalah AI Co-Host {self.cohost_name} dengan kepribadian {self.personality}, "
            f"siaran bersama streamer {self.streamer_name}. "
            f"Komentar penonton ({self.author}): \"{self.message}\". "
            f"Balas {self.author} dalam bahasa {self.lang_out.lower()} "
            "tanpa tanda baca, tanpa emoji, tanpa huruf tebal, sebut nama penanya."
        )
        if self.extra:
            prompt += f" {self.extra}"

        reply = generate_reply(prompt) or ""
        # hapus semua punctuation kecuali tanda tanya
        reply = re.sub(r"[^\w\s\?]", "", reply)

        # Track AI usage untuk mode Pro
        try:
            from modules_server.real_credit_tracker import credit_tracker
            estimated_tokens = len(reply.split()) * 1.3
            credits_used = credit_tracker.track_ai_usage(int(estimated_tokens), mode="pro")
            print(f"AI Reply tracked [PRO]: {len(reply)} chars, ~{estimated_tokens:.0f} tokens = {credits_used:.4f} credits")
        except Exception as tracking_error:
            print(f"Error tracking AI usage: {tracking_error}")

        try:
            code = "id-ID" if self.lang_out == "Indonesia" else "en-US"
            speak(reply, code, self.voice_model)
        except Exception as e:
            print(f"Error in TTS: {e}")

        self.finished.emit(self.author, self.message, reply)


class STTThread(QThread):
    result = pyqtSignal(str)

    def __init__(self, mic_index: int, src_lang: str, use_google: bool):
        super().__init__()
        self.mic_index = mic_index
        self.src_lang = src_lang
        self.use_google = use_google

    def run(self):
        wav_path = Path("temp/cohost_record.wav")
        record_buffer = []
        try:
            with sd.InputStream(
                samplerate=16000, channels=1, device=self.mic_index,
                callback=lambda indata, *_: record_buffer.extend(indata.copy())
            ):
                while Path("temp/trigger.txt").read_text() == "ON":
                    time.sleep(0.05)
            sf.write(str(wav_path), record_buffer, 16000)
        except Exception as e:
            print(f"Error in recording: {e}")
            self.result.emit("")
            return

        txt = transcribe(str(wav_path), self.src_lang, self.use_google) or ""
        self.result.emit(txt.strip())


class TikTokListenerThread(QThread):
    newComment = pyqtSignal(str, str)

    def __init__(self, nickname: str):
        super().__init__()
        # pastikan diawali '@'
        self.nickname = nickname if nickname.startswith("@") else "@" + nickname
        self._ready = False

    def run(self):
        from TikTokLive import TikTokLiveClient
        from TikTokLive.events import ConnectEvent, CommentEvent

        client = TikTokLiveClient(unique_id=self.nickname)

        @client.on(ConnectEvent)
        async def on_connect(evt):
            # tunggu 3 detik sebelum mulai emit komentar
            threading.Timer(3.0, lambda: setattr(self, "_ready", True)).start()

        @client.on(CommentEvent)
        async def on_comment(evt: CommentEvent):
            if not self._ready:
                return
            # kirim ke slot utama
            self.newComment.emit(evt.user.nickname, evt.comment)

        client.run()

    def stop(self):
        # tidak ada API stop, cukup tandai flag jika perlu
        self._ready = False


class CohostTabPro(QWidget):
    ttsAboutToStart = pyqtSignal()
    ttsFinished = pyqtSignal()
    personaChanged = pyqtSignal(str)
    speakingStarted = pyqtSignal(str, float)  # Signal baru: text, intensity
    speakingStopped = pyqtSignal()  # Signal baru
    replyGenerated = pyqtSignal(str, str, str)  # author, message, reply
    
    def __init__(self):
        super().__init__()
        self.cfg = ConfigManager("config/settings.json")
        self.proc = None
        self.monitor = None
        self.tiktok_thread = None
        self.reply_queue = []
        self.reply_busy = False
        self.delay_timer = None
        self.hotkey_enabled = True
        self.stt_thread = None
        self.threads = []
        self.conversation_active = False
        self.usage_timer = QTimer()
        self.usage_timer.setInterval(60_000)  # 1 menit
        self.usage_timer.timeout.connect(self._track_usage)
        self.avatar_controller = None  # Placeholder for avatar controller
        self.tts_active = False
        self.reply_queue = []
        self.reply_busy = False
        self.current_tts_text = ""  # Track text untuk estimasi

        # Pastikan folder/temp dan file trigger ada
        TRIGGER_FILE.parent.mkdir(exist_ok=True)
        if not TRIGGER_FILE.exists():
            TRIGGER_FILE.write_text("OFF")

        # ─── UI Setup dengan Scroll Area ──────────────────────────────────────────────────
        # Main layout untuk widget ini
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Buat scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Widget konten yang akan di-scroll
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setSpacing(8)  # Kurangi spacing untuk efisiensi
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Set content widget ke scroll area
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)
        
        layout.addWidget(QLabel("🤖 Auto-Reply Chat (YouTube & TikTok)"))

        # Platform selection
        layout.addWidget(QLabel("Pilih Platform Komentar:"))
        self.platform_cb = QComboBox()
        self.platform_cb.addItems(["YouTube", "TikTok", "YouTube + TikTok"])
        layout.addWidget(self.platform_cb)

        # Input TikTok Nickname
        layout.addWidget(QLabel("Nickname TikTok:"))
        self.nickname_input = QLineEdit(self.cfg.get("tiktok_nickname", ""))
        layout.addWidget(self.nickname_input)

        # Input Video ID YouTube
        layout.addWidget(QLabel("Video ID YouTube:"))
        self.videoid_input = QLineEdit(self.cfg.get("video_id", ""))
        layout.addWidget(self.videoid_input)

        # Tombol simpan input platform
        self.save_platform_btn = QPushButton("💾 Simpan Platform & ID")
        self.save_platform_btn.clicked.connect(self.save_platform_inputs)
        layout.addWidget(self.save_platform_btn)

        # Nama Streamer
        layout.addWidget(QLabel("Nama Streamer:"))
        self.streamer_input = QLineEdit(self.cfg.get("streamer_name", "Streamer"))
        layout.addWidget(self.streamer_input)
        btn = QPushButton("💾 Simpan Nama Streamer")
        btn.clicked.connect(self.save_streamer)
        layout.addWidget(btn)

        # lalu baru pasang koneksi dan panggil update awal:
        self.platform_cb.currentTextChanged.connect(self._update_platform_ui)
        self._update_platform_ui(self.platform_cb.currentText())

        # Bahasa Output
        layout.addWidget(QLabel("Bahasa Output:"))
        self.out_lang = QComboBox()
        self.out_lang.addItems(["Indonesia", "English"])
        self.out_lang.setCurrentText(self.cfg.get("reply_language", "Indonesia"))
        self.out_lang.currentTextChanged.connect(self.on_language_change)
        layout.addWidget(self.out_lang)

        # Kepribadian
        layout.addWidget(QLabel("Kepribadian AI:"))
        self.person_cb = QComboBox()
        self.person_cb.addItems([
            "Ceria", "Pemarah", "Sombong", "Suka Bercanda", "Bijaksana",
            "Santai", "Tenang", "Bahasa Gaul Indonesia", "Bahasa Sunda", "Positive Vibe"
        ])
        self.person_cb.setCurrentText(self.cfg.get("personality", "Ceria"))
        self.person_cb.currentTextChanged.connect(self.save_personality)
        layout.addWidget(self.person_cb)

        # 🔥 ENHANCED: Prompt Templates System
        layout.addWidget(QLabel("🎭 AI Character & Prompt:"))
        
        # Template selector
        template_row = QHBoxLayout()
        template_row.addWidget(QLabel("📋 Quick Templates:"))
        self.template_combo = QComboBox()
        self.template_combo.addItems([
            "📝 Custom Prompt",
            "🎮 Gaming - MOBA Expert", 
            "🎮 Gaming - FPS Pro",
            "💰 Sales - E-Commerce", 
            "💰 Sales - Digital Products"
        ])
        self.template_combo.currentTextChanged.connect(self.load_template)
        template_row.addWidget(self.template_combo, 2)
        
        btn_preview_template = QPushButton("👁️ Preview")
        btn_preview_template.clicked.connect(self.preview_template)
        template_row.addWidget(btn_preview_template, 1)
        
        layout.addLayout(template_row)

        # Custom prompt text area
        layout.addWidget(QLabel("✏️ Edit Prompt (customize as needed):"))
        self.custom = QTextEdit(self.cfg.get("custom_context", ""))
        self.custom.setPlaceholderText("Choose a template above or write your custom prompt...")
        self.custom.setMinimumHeight(100)
        self.custom.setMaximumHeight(150)
        layout.addWidget(self.custom)

        # Action buttons
        button_row = QHBoxLayout()
        self.custom_btn = QPushButton("💾 Save Prompt")
        self.custom_btn.clicked.connect(self.save_custom)
        button_row.addWidget(self.custom_btn)
        
        btn_clear = QPushButton("🗑️ Clear")
        btn_clear.clicked.connect(lambda: self.custom.clear())
        button_row.addWidget(btn_clear)
        
        btn_reset_template = QPushButton("🔄 Reset Template")
        btn_reset_template.clicked.connect(lambda: self.load_template(self.template_combo.currentText()))
        button_row.addWidget(btn_reset_template)
        
        layout.addLayout(button_row)

        # Mode Balasan
        row = QHBoxLayout()
        row.addWidget(QLabel("Mode Balasan:"))
        self.mode_cb = QComboBox()
        self.mode_cb.addItems(["Sequential", "Delay Latest", "Trigger"])
        self.mode_cb.setCurrentText(self.cfg.get("reply_mode", "Sequential"))
        self.mode_cb.currentTextChanged.connect(self.save_mode)
        row.addWidget(self.mode_cb)
        row.addWidget(QLabel("Delay (detik):"))
        self.delay_spin = QSpinBox()
        self.delay_spin.setRange(1, 60)
        self.delay_spin.setValue(self.cfg.get("reply_delay", 5))
        row.addWidget(self.delay_spin)
        btn = QPushButton("💾 Simpan Mode")
        btn.clicked.connect(self.save_mode)
        row.addWidget(btn)
        layout.addLayout(row)

        # 🔥 ENHANCED: Memory Statistics
        memory_group = QGroupBox("🧠 Memory & Statistics")
        memory_layout = QVBoxLayout(memory_group)
        
        # Memory stats display
        self.memory_stats_label = QLabel("📊 Viewer Memory: 0 viewers tracked")
        memory_layout.addWidget(self.memory_stats_label)
        
        layout.addWidget(memory_group)

        # 🔥 ENHANCED: Streamer Communication
        comm_group = QGroupBox("🎤 Streamer Communication")
        comm_layout = QVBoxLayout(comm_group)
        
        # Microphone selection
        mic_row = QHBoxLayout()
        mic_row.addWidget(QLabel("🎙️ Microphone:"))
        self.mic_combo = QComboBox()
        self.load_microphones()
        mic_row.addWidget(self.mic_combo, 2)
        
        btn_refresh_mic = QPushButton("🔄")
        btn_refresh_mic.clicked.connect(self.load_microphones)
        btn_refresh_mic.setToolTip("Refresh microphone list")
        mic_row.addWidget(btn_refresh_mic)
        comm_layout.addLayout(mic_row)
        
        # Hotkey settings (enhanced)
        hotkey_row = QHBoxLayout()
        hotkey_row.addWidget(QLabel("⌨️ Talk Hotkey:"))
        self.chk_ctrl = QCheckBox("Ctrl")
        hotkey_row.addWidget(self.chk_ctrl)
        self.chk_alt = QCheckBox("Alt")
        hotkey_row.addWidget(self.chk_alt)
        self.chk_shift = QCheckBox("Shift")
        hotkey_row.addWidget(self.chk_shift)
        self.key_combo = QComboBox()
        for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789":
            self.key_combo.addItem(c)
        hotkey_row.addWidget(self.key_combo)
        comm_layout.addLayout(hotkey_row)
        
        # Hotkey display and controls
        hotkey_control_row = QHBoxLayout()
        self.hk_edit = QLineEdit(self.cfg.get("cohost_hotkey", "Ctrl+Alt+X"))
        self.hk_edit.setReadOnly(True)
        hotkey_control_row.addWidget(self.hk_edit)
        
        btn_save_hotkey = QPushButton("💾 Save Hotkey")
        btn_save_hotkey.clicked.connect(self.save_hotkey)
        hotkey_control_row.addWidget(btn_save_hotkey)
        
        self.toggle_btn = QPushButton("🔔 Chat: ON")
        self.toggle_btn.setCheckable(True)
        self.toggle_btn.setChecked(True)
        self.toggle_btn.clicked.connect(self.toggle_hotkey)
        hotkey_control_row.addWidget(self.toggle_btn)
        comm_layout.addLayout(hotkey_control_row)
        
        layout.addWidget(comm_group)

        # 🔥 ENHANCED: Activity Log
        log_group = QGroupBox("📋 Activity Log")
        log_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        log_layout = QVBoxLayout(log_group)
        
        # Main log layout with text area and button panel
        log_row = QHBoxLayout()
        
        # Log view (main text area)
        self.log_view = QTextEdit()
        self.log_view.setMinimumHeight(200)
        self.log_view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.log_view.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #555;
                border-radius: 4px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 10px;
                padding: 5px;
            }
        """)
        log_row.addWidget(self.log_view, 3)
        
        # Button panel (matching Basic version)
        button_panel = QVBoxLayout()
        button_panel.addStretch()

        button_style = """
            QPushButton {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 8px;
                margin: 5px;
                text-align: left;
                min-height: 40px;
                color: black;
            }
            QPushButton:hover { background-color: #e0e0e0; }
        """

        btn_filter_stats = QPushButton("📊 Filter Stats")
        btn_filter_stats.setStyleSheet(button_style)
        btn_filter_stats.clicked.connect(self.show_filter_stats)
        button_panel.addWidget(btn_filter_stats)

        btn_reset_stats = QPushButton("🔄 Reset Stats")
        btn_reset_stats.setStyleSheet(button_style)
        btn_reset_stats.clicked.connect(self.reset_statistics)
        button_panel.addWidget(btn_reset_stats)

        btn_statistics = QPushButton("📊 Cache & Spam\nStatistics")
        btn_statistics.setStyleSheet(button_style)
        btn_statistics.clicked.connect(self.show_cache_spam_stats)
        button_panel.addWidget(btn_statistics)

        btn_reset_spam = QPushButton("🚫 Reset Spam\nBlocks")
        btn_reset_spam.setStyleSheet(button_style)
        btn_reset_spam.clicked.connect(self.reset_spam_blocks)
        button_panel.addWidget(btn_reset_spam)

        btn_reset_daily = QPushButton("📅 Reset Daily\nInteractions")
        btn_reset_daily.setStyleSheet(button_style)
        btn_reset_daily.clicked.connect(self.reset_daily_interactions)
        button_panel.addWidget(btn_reset_daily)

        # Set equal widths for all buttons
        max_width = 180
        for btn in [btn_filter_stats, btn_reset_stats, btn_statistics, btn_reset_spam, btn_reset_daily]:
            btn.setMaximumWidth(max_width)
            btn.setMinimumWidth(max_width)

        button_panel.addStretch()
        log_row.addLayout(button_panel, 1)
        log_layout.addLayout(log_row)
        
        # Log controls (simplified)
        log_controls = QHBoxLayout()
        btn_clear_log = QPushButton("🗑️ Clear Log")
        btn_clear_log.clicked.connect(lambda: self.log_view.clear())
        log_controls.addWidget(btn_clear_log)
        
        btn_export_log = QPushButton("💾 Export Log")
        btn_export_log.clicked.connect(self.export_log)
        log_controls.addWidget(btn_export_log)
        
        self.auto_scroll_check = QCheckBox("Auto Scroll")
        self.auto_scroll_check.setChecked(True)
        log_controls.addWidget(self.auto_scroll_check)
        log_layout.addLayout(log_controls)

        # 🔥 ENHANCED: Trigger & Cooldown Settings
        trigger_group = QGroupBox("⚙️ Trigger & Cooldown Settings")
        trigger_layout = QVBoxLayout(trigger_group)
        
        # Enhanced trigger words (multiple)
        trigger_layout.addWidget(QLabel("🎯 Viewer Triggers (separate with comma):"))
        self.trigger_words_input = QLineEdit()
        existing_triggers = self.cfg.get("trigger_words", [])
        if isinstance(existing_triggers, list):
            self.trigger_words_input.setText(", ".join(existing_triggers))
        else:
            self.trigger_words_input.setText(self.cfg.get("trigger_word", ""))
        self.trigger_words_input.setPlaceholderText("example: bro, hey, ?, greet me, help")
        trigger_layout.addWidget(self.trigger_words_input)
        
        trigger_btn_row = QHBoxLayout()
        btn_save_triggers = QPushButton("💾 Save Triggers")
        btn_save_triggers.clicked.connect(self.save_trigger_words)
        trigger_btn_row.addWidget(btn_save_triggers)
        
        btn_test_trigger = QPushButton("🧪 Test Trigger")
        btn_test_trigger.clicked.connect(self.test_trigger)
        trigger_btn_row.addWidget(btn_test_trigger)
        trigger_layout.addLayout(trigger_btn_row)

        # Cooldown controls
        cooldown_row = QHBoxLayout()
        cooldown_row.addWidget(QLabel("⏱️ Batch Cooldown:"))
        self.cooldown_spin = QSpinBox()
        self.cooldown_spin.setRange(0, 30)
        self.cooldown_spin.setValue(self.cfg.get("cooldown_duration", 10))
        self.cooldown_spin.valueChanged.connect(self.update_cooldown)
        self.cooldown_spin.setToolTip("Delay between batch reply processing (seconds)")
        cooldown_row.addWidget(self.cooldown_spin)
        cooldown_row.addWidget(QLabel("sec"))
        
        cooldown_row.addWidget(QLabel("👤 Viewer Cooldown:"))
        self.viewer_cooldown_spin = QSpinBox()
        self.viewer_cooldown_spin.setRange(1, 30)
        self.viewer_cooldown_spin.setValue(self.cfg.get("viewer_cooldown_minutes", 3))
        self.viewer_cooldown_spin.valueChanged.connect(self.update_viewer_cooldown)
        self.viewer_cooldown_spin.setToolTip("Minimum delay between questions from same viewer (minutes)")
        cooldown_row.addWidget(self.viewer_cooldown_spin)
        cooldown_row.addWidget(QLabel("min"))
        trigger_layout.addLayout(cooldown_row)

        # Queue and daily limits
        limits_row = QHBoxLayout()
        limits_row.addWidget(QLabel("📋 Max Queue:"))
        self.max_queue_spin = QSpinBox()
        self.max_queue_spin.setRange(1, 10)
        self.max_queue_spin.setValue(self.cfg.get("max_queue_size", 5))
        self.max_queue_spin.valueChanged.connect(self.update_max_queue)
        self.max_queue_spin.setToolTip("Maximum comments in batch queue")
        limits_row.addWidget(self.max_queue_spin)
        
        limits_row.addWidget(QLabel("📅 Daily Limit:"))
        self.daily_limit_spin = QSpinBox()
        self.daily_limit_spin.setRange(1, 50)
        self.daily_limit_spin.setValue(self.cfg.get("viewer_daily_limit", 5))
        self.daily_limit_spin.valueChanged.connect(self.update_daily_limit)
        self.daily_limit_spin.setToolTip("Maximum interactions per viewer per day")
        limits_row.addWidget(self.daily_limit_spin)
        trigger_layout.addLayout(limits_row)

        # Topic cooldown and blocking
        topic_row = QHBoxLayout()
        topic_row.addWidget(QLabel("🚫 Topic Cooldown:"))
        self.topic_cooldown_spin = QSpinBox()
        self.topic_cooldown_spin.setRange(1, 60)
        self.topic_cooldown_spin.setValue(self.cfg.get("topic_cooldown_minutes", 5))
        self.topic_cooldown_spin.valueChanged.connect(self.update_topic_cooldown)
        self.topic_cooldown_spin.setToolTip("Prevent same topic repetition (minutes)")
        topic_row.addWidget(self.topic_cooldown_spin)
        topic_row.addWidget(QLabel("min"))
        
        self.topic_blocking_input = QLineEdit()
        self.topic_blocking_input.setText(self.cfg.get("blocked_topics", ""))
        self.topic_blocking_input.setPlaceholderText("blocked topics (comma separated)")
        topic_row.addWidget(self.topic_blocking_input)
        
        btn_save_topics = QPushButton("💾 Save")
        btn_save_topics.clicked.connect(self.save_topic_settings)
        topic_row.addWidget(btn_save_topics)
        trigger_layout.addLayout(topic_row)
        
        layout.addWidget(trigger_group)

        # 🔥 ENHANCED: Voice & Control Settings
        voice_group = QGroupBox("🔊 Voice & Control Settings")
        voice_layout = QVBoxLayout(voice_group)
        
        # Suara CoHost
        voice_layout.addWidget(QLabel("🎤 CoHost Voice:"))
        voice_row = QHBoxLayout()
        self.voice_cb = QComboBox()
        voice_row.addWidget(self.voice_cb, 2)
        btn_preview = QPushButton("🔈 Preview")
        btn_preview.clicked.connect(self.preview_cohost_voice)
        voice_row.addWidget(btn_preview)
        btn_save_voice = QPushButton("💾 Save")
        btn_save_voice.clicked.connect(self.save_cohost_voice)
        voice_row.addWidget(btn_save_voice)
        voice_layout.addLayout(voice_row)

        # Start / Stop controls
        voice_layout.addWidget(QLabel("🎮 Auto-Reply Control:"))
        self.status = QLabel("Status: Ready")
        voice_layout.addWidget(self.status)
        
        control_row = QHBoxLayout()
        self.btn_start = QPushButton("▶️ Start Auto-Reply")
        self.btn_start.clicked.connect(self.start)
        control_row.addWidget(self.btn_start)
        self.btn_stop = QPushButton("⏹️ Stop Auto-Reply")
        self.btn_stop.clicked.connect(self.stop)
        control_row.addWidget(self.btn_stop)
        voice_layout.addLayout(control_row)
        
        layout.addWidget(voice_group)
        layout.addWidget(log_group)

        # finalize UI callbacks
        self.mode_cb.currentTextChanged.connect(self.update_mode_ui)
        self.update_mode_ui(self.mode_cb.currentText())
        self._load_hotkey()
        self.load_cohost_voices(self.out_lang.currentText())

        # start hotkey listener thread
        threading.Thread(target=self._hotkey_listener, daemon=True).start()

    # Method baru untuk menghubungkan dengan avatar controller
    def set_avatar_controller(self, controller):
        """Connect to avatar controller."""
        self.avatar_controller = controller
        if hasattr(controller, 'update_animaze_persona'):
            # Connect signals
            self.personaChanged.connect(controller.update_animaze_persona)
            self.speakingStarted.connect(
                lambda text, intensity: controller.set_speaking_state(True, text, intensity))
            self.speakingStopped.connect(
                lambda: controller.set_speaking_state(False))
            
            # Initial update
            controller.update_animaze_persona(self.person_cb.currentText())
            self.log_view.append("[INFO] Avatar controller terhubung")

    # — UI helpers —
    def update_mode_ui(self, mode):
        """Update UI based on reply mode selection."""
        self.delay_spin.setEnabled(mode == "Delay Latest")
        is_trigger = (mode == "Trigger")
        
        # Update enhanced trigger controls
        if safe_attr_check(self, 'trigger_words_input'):
            self.trigger_words_input.setEnabled(is_trigger)
        
        # Update old trigger controls for backward compatibility
        if safe_attr_check(self, 'trigger_input'):
            self.trigger_input.setEnabled(is_trigger)
        if safe_attr_check(self, 'trigger_btn'):
            self.trigger_btn.setEnabled(is_trigger)

    def on_language_change(self, lang):
        self.save_language(lang)
        self.load_cohost_voices(lang)

    def load_cohost_voices(self, lang):
        self.voice_cb.clear()
        try:
            voices = json.loads(Path(VOICES_PATH).read_text(encoding="utf-8")).get("chirp3", {})
            key = "id-ID" if lang == "Indonesia" else "en-US"
            for v in voices.get(key, []):
                self.voice_cb.addItem(v["model"], v["model"])
            stored = self.cfg.get("cohost_voice_model", "")
            idx = self.voice_cb.findData(stored)
            if idx >= 0:
                self.voice_cb.setCurrentIndex(idx)
        except Exception as e:
            print(f"Error loading voices: {e}")

    def preview_cohost_voice(self):
        voice = self.voice_cb.currentData()
        code = "id-ID" if self.out_lang.currentText() == "Indonesia" else "en-US"
        self.log_view.append(f"[Preview] {voice}")
        speak("Ini preview suara CoHost!", language_code=code, voice_name=voice)

    def save_cohost_voice(self):
        voice = self.voice_cb.currentData()
        self.cfg.set("cohost_voice_model", voice)
        self.log_view.append(f"[INFO] Suara CoHost disimpan: {voice}")

    def _parse(self, h): 
        return [p.lower() for p in h.split("+") if p]
    
    def _is_pressed(self, h): 
        return all(keyboard.is_pressed(p) for p in self._parse(h))

    def _load_hotkey(self):
        hot = self.cfg.get("cohost_hotkey", "Ctrl+Alt+X")
        for p in hot.split("+"):
            if p == "Ctrl":
                self.chk_ctrl.setChecked(True)
            elif p == "Alt":
                self.chk_alt.setChecked(True)
            elif p == "Shift":
                self.chk_shift.setChecked(True)
            else:
                idx = self.key_combo.findText(p)
                if idx >= 0:
                    self.key_combo.setCurrentIndex(idx)
        self.hk_edit.setText(hot)

    # — Simpan setting —
    def save_trigger(self):
        w = self.trigger_input.text().strip()
        self.cfg.set("trigger_word", w)
        self.log_view.append(f"[INFO] Trigger disimpan: {w}")

    def save_streamer(self):
        n = self.streamer_input.text().strip()
        self.cfg.set("streamer_name", n)
        self.log_view.append(f"[INFO] Streamer disimpan: {n}")

    def save_language(self, lang):
        self.cfg.set("reply_language", lang)
        self.log_view.append(f"[INFO] Bahasa output disimpan: {lang}")

    def save_personality(self, p):
        self.cfg.set("personality", p)
        self.log_view.append(f"[INFO] Personality disimpan: {p}")
        # Emit sinyal perubahan kepribadian
        self.personaChanged.emit(p)

    def save_custom(self):
        c = self.custom.text().strip()
        self.cfg.set("custom_context", c)
        self.log_view.append("[INFO] Prompt tambahan disimpan")

    def save_mode(self):
        m = self.mode_cb.currentText()
        d = self.delay_spin.value()
        self.cfg.set("reply_mode", m)
        self.cfg.set("reply_delay", d)
        self.log_view.append(f"[INFO] Mode disimpan: {m} (delay {d}s)")

    def save_hotkey(self):
        mods = [m for cb, m in [
            (self.chk_ctrl, "Ctrl"), (self.chk_alt, "Alt"), (self.chk_shift, "Shift")
        ] if cb.isChecked()]
        key = self.key_combo.currentText()
        hot = "+".join(mods + ([key] if key else []))
        self.cfg.set("cohost_hotkey", hot)
        self.hk_edit.setText(hot)
        self.log_view.append(f"[INFO] Hotkey disimpan: {hot}")

    def save_platform_inputs(self):
        # ambil input mentah
        raw_video = self.videoid_input.text().strip()
        # jika ada "youtu" di string, parsing URL → ambil param v atau path akhir
        if "youtu" in raw_video:
            from urllib.parse import urlparse, parse_qs
            p = urlparse(raw_video)
            # coba ambil query v
            vid = parse_qs(p.query).get("v", [])
            if vid:
                video_id = vid[0]
            else:
                # fallback: ambil bagian path terakhir
                video_id = p.path.rsplit("/", 1)[-1]
        else:
            video_id = raw_video

        # set ke config & update field agar terlihat ke user
        self.cfg.set("video_id", video_id)
        self.videoid_input.setText(video_id)

        # simpan TikTok nickname seperti biasa
        self.cfg.set("tiktok_nickname", self.nickname_input.text().strip())

        self.log_view.append("[INFO] Platform input disimpan.")

    def toggle_hotkey(self):
        on = self.toggle_btn.isChecked()
        # Ubah teks tombol sesuai state
        self.toggle_btn.setText("🔔 Ngobrol: ON" if on else "🔕 Ngobrol: OFF")
        # Simpan flag internal
        self.hotkey_enabled = on

    def _update_platform_ui(self, plat: str):
        is_tiktok = plat in ("TikTok", "YouTube + TikTok")
        is_youtube = plat in ("YouTube", "YouTube + TikTok")

        # show/hide field
        self.nickname_input.setVisible(is_tiktok)
        self.videoid_input.setVisible(is_youtube)

    def toggle_hotkey_off(self):
        """Mute CoHost chat (nonaktifkan hotkey)."""
        if safe_attr_check(self, "toggle_btn"):
            self.toggle_btn.setChecked(False)
        self.hotkey_enabled = False

    def toggle_hotkey_on(self):
        """Unmute CoHost chat (aktifkan hotkey kembali)."""
        if safe_attr_check(self, "toggle_btn"):
            self.toggle_btn.setChecked(True)
        self.hotkey_enabled = True

    # — Hold-to-Talk Listener —  
    def _hotkey_listener(self):
        prev = False
        while True:
            time.sleep(0.05)
            if not self.hotkey_enabled:
                prev = False
                continue

            hot = self.cfg.get("cohost_hotkey", "Ctrl+Alt+X")
            pressed = self._is_pressed(hot)

            if pressed and not prev:
                prev = True
                self.conversation_active = True   # mute auto-reply saat mic aktif
                TRIGGER_FILE.write_text("ON")
                self.log_view.append("🔴 Mulai merekam...")

                mic_index = self.cfg.get("selected_mic_index", 0)
                src_lang = self.cfg.get("cohost_input_lang", "ind_Latn")
                use_google = True  # karena ini Pro
                self.stt_thread = STTThread(mic_index, src_lang, use_google)
                self.stt_thread.result.connect(self._handle_speech)
                self.stt_thread.start()

            elif not pressed and prev:
                prev = False
                self.conversation_active = False  # unmute auto-reply
                TRIGGER_FILE.write_text("OFF")
                self.log_view.append("⏳ Memproses...")

    # — Handle hasil STT Hold-to-Talk —  
    def _handle_speech(self, txt: str):
        # release mute chat sehingga auto-reply jalan kembali
        self.conversation_active = False

        txt = txt.strip()
        if not txt:
            self.log_view.append("[WARN] STT kosong.")
            return

        self.log_view.append(f"🎙️ Kamu: {txt}")

        # Build prompt untuk DeepSeek
        prompt = (
            f"Kamu adalah AI Co-Host {self.cfg.get('cohost_name','CoHost')} "
            f"dengan kepribadian {self.person_cb.currentText()}. "
            f"User berkata: \"{txt}\". "
            f"Balas dalam bahasa {self.out_lang.currentText().lower()} tanpa emoji dan tanpa sebut nama cohost."
        )
        reply = generate_reply(prompt) or ""

        # Track AI usage untuk mode Pro
        try:
            from modules_server.real_credit_tracker import credit_tracker
            estimated_tokens = len(reply.split()) * 1.3
            credits_used = credit_tracker.track_ai_usage(int(estimated_tokens), mode="pro")
            self.log_view.append(f"💳 AI Usage [PRO]: {credits_used:.4f} credits")
        except Exception as tracking_error:
            self.log_view.append(f"❌ AI tracking error: {tracking_error}")

        # Emit signal untuk avatar
        self.speakingStarted.emit(reply, 0.8)  # Asumsi intensitas 0.8

        # TTS sesuai setting bahasa output
        code = "id-ID" if self.out_lang.currentText() == "Indonesia" else "en-US"
        speak(reply, language_code=code, voice_name=self.cfg.get("cohost_voice_model"))

        # Signal bahwa sudah selesai bicara
        self.speakingStopped.emit()

        self.log_view.append(f"🤖 {reply}")

    def start(self):
        """Start auto-reply untuk mode Basic dengan validasi lengkap."""
        # TAMBAHAN: Skip usage tracking untuk test mode
        main_window = self.window()
        if safe_attr_check(main_window, 'license_validator') and main_window.license_validator.testing_mode:
            print("[DEBUG] Test mode active - skipping usage tracking")
            # Jangan start usage timer
        else:
            # Normal flow - track usage
            self.hour_tracker.start_tracking()
            self.credit_timer.start()
        self.conversation_active = False  # pastikan reset
        self.save_platform_inputs()       # simpan nickname & video ID terbaru

        # TAMBAHKAN DI SINI - CEK KREDIT LEBIH AWAL
        # Ambil data kredit dari license_validator
        main_window = self.window()
        if safe_attr_check(main_window, 'license_validator'):
            license_data = main_window.license_validator.validate()
            daily_usage = license_data.get("daily_usage", {})
            today = datetime.now().date().isoformat()
            used_hours = daily_usage.get(today, 0)
            
            # Tentukan limit berdasarkan tier
            tier = license_data.get("tier", "demo")
            if tier == "basic":
                limit_hours = 5
            elif tier == "pro": 
                limit_hours = 12
            else:  # demo
                limit_hours = 0.5
            
            remaining_hours = max(0, limit_hours - used_hours)
            
            # Cek kredit
            if remaining_hours <= 0:
                if safe_attr_check(main_window, 'show_no_credit_dialog'):
                    main_window.show_no_credit_dialog()
                else:
                    QMessageBox.critical(self, "Kredit Habis", 
                                         "Kredit jam Anda telah habis.\nSilakan beli paket untuk melanjutkan.")
                return
            elif remaining_hours < 1:
                if safe_attr_check(main_window, 'show_credit_warning'):
                    main_window.show_credit_warning(remaining_hours)
                else:
                    QMessageBox.warning(self, "Kredit Rendah",
                                        f"Sisa kredit: {remaining_hours:.1f} jam")

        platform = self.platform_cb.currentText()
        video_id = self.videoid_input.text().strip()
        nickname = self.nickname_input.text().strip()

        if platform not in ["YouTube", "TikTok", "YouTube + TikTok"]:
            self.log_view.append("[ERROR] Pilih platform komentar terlebih dahulu.")
            return
        if "YouTube" in platform and len(video_id) != 11:
            self.log_view.append("[ERROR] Video ID harus 11 karakter.")
            return
        if "TikTok" in platform and not nickname:
            self.log_view.append("[ERROR] TikTok nickname tidak boleh kosong.")
            return
        if not SCRIPT_PATH.exists():
            self.log_view.append(f"[ERROR] chat_listener tidak ditemukan: {SCRIPT_PATH}")
            return

        # Bersihkan buffer
        CHAT_BUFFER.write_text("")
        COHOST_LOG.parent.mkdir(exist_ok=True)
        COHOST_LOG.write_text("")

        # Hentikan listener lama
        if self.monitor:
            self.monitor.stop()
            self.monitor = None
        if self.tiktok_thread:
            self.tiktok_thread.terminate()
            self.tiktok_thread = None
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            self.proc = None

        # Start YouTube listener
        if "YouTube" in platform:
            try:
                self.proc = subprocess.Popen(["python", "-u", str(SCRIPT_PATH)])
                self.log_view.append("[YouTube] Listener dimulai")
                self.monitor = FileMonitorThread(CHAT_BUFFER)
                self.monitor.newComment.connect(self._enqueue)
                self.monitor.start()
            except Exception as e:
                self.log_view.append(f"[ERROR] Gagal menjalankan listener: {e}")
                return

        # Start TikTok listener
        if "TikTok" in platform:
            try:
                self.tiktok_thread = TikTokListenerThread(nickname)
                self.tiktok_thread.newComment.connect(self._enqueue)
                self.tiktok_thread.start()
                self.log_view.append("[TikTok] Listener dimulai")
            except Exception as e:
                self.log_view.append(f"[ERROR] Gagal menjalankan TikTok listener: {e}")

        self.log_view.append(f"[INFO] Auto-Reply dimulai untuk: {platform}")

        # — jika developer/debug_mode, skip kuota
        if self.cfg.get("debug_mode", False):
            self.log_view.append("[DEBUG] Developer mode: kuota tidak diberlakukan")
        else:
            # Cek batas segera, lalu jalankan timer per menit
            self._track_usage()
            self.usage_timer.start()

    def stop(self):
        # hentikan semua listener
        if self.monitor:
            self.monitor.stop()
        if self.tiktok_thread:
            self.tiktok_thread.stop()
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            self.proc = None
        if safe_attr_check(self, "delay_timer") and self.delay_timer:
            self.delay_timer.cancel()
        self.log_view.append("[INFO] Semua listener dihentikan.")

        # matikan timer pemakaian
        self.usage_timer.stop()

    def _track_usage(self):
        """Track usage untuk mode Pro dengan multiplier 5x dan menggunakan pro_credits"""
        # jika ada demo expired_at, dan paket basic
        exp = self.cfg.get("expired_at", None)
        if self.cfg.get("paket") == "basic" and exp:
            if datetime.fromisoformat(exp) <= datetime.now():
                self.usage_timer.stop()
                self.stop()
                QMessageBox.information(
                    self,
                    "Demo Habis",
                    "Mode demo sudah berakhir."
                )
                return
            else:
                # masih demo, lewati hitung kuota harian
                remaining = datetime.fromisoformat(exp) - datetime.now()
                menit = remaining.seconds // 60
                self.log_view.append(f"[Demo] Sisa {menit} menit")
                return

        # jika bukan demo, lanjutkan cek kuota harian
        tier, used, limit = get_today_usage()
        if used >= limit:
            self.usage_timer.stop()
            self.stop()
            detik = time_until_next_day()
            jam = detik // 3600
            menit = (detik % 3600) // 60
            QMessageBox.information(
                self,
                "Waktu Habis",
                f"Waktu penggunaan harian habis.\nCoba lagi dalam {jam} jam {menit} menit."
            )
            return

        # Mode Pro = 5x lipat usage dan menggunakan pro_credits
        try:
            # Cek apakah debug mode (skip tracking)
            if self.cfg.get("debug_mode", False):
                self.log_view.append("[PRO] Developer Mode: credits not enforced")
                return
            
            # 🔥 FORCE immediate credit deduction untuk AI dan TTS usage (MODE PRO)
            tts_chars = getattr(self, 'current_reply_char_count', 100)
            tts_credits = tts_chars * 5.0 / 100    # PRO: 5x lipat dari basic (1.0 → 5.0)
            ai_credits = 100 * 7.5 / 100          # PRO: 5x lipat dari basic (1.5 → 7.5)
            total_credits = tts_credits + ai_credits
            
            self.log_view.append(f"[PRO] 💳 Credit deduction: TTS={tts_credits:.4f}, AI={ai_credits:.4f}, Total={total_credits:.4f}")
            
            # Get user email
            email = self.cfg.get("user_data", {}).get("email", "")
            if not email:
                self.log_view.append("[PRO] ❌ No email found for credit deduction")
                return
            
            # Force TTS deduction via Supabase - PRO MODE
            if tts_credits > 0:
                try:
                    from modules_client.supabase_client import SupabaseClient
                    supabase = SupabaseClient()
                    tts_success = supabase.deduct_mode_credits(
                        email=email,
                        amount=tts_credits,
                        mode="pro",
                        component="TTS",
                        description=f"PRO TTS processing {tts_chars} characters"
                    )
                    if not tts_success or tts_success.get("status") != "success":
                        self.log_view.append("[PRO] ❌ PRO TTS credit deduction FAILED!")
                        self.log_view.append(f"[PRO] Error: {tts_success.get('message', 'Unknown error')}")
                    else:
                        self.log_view.append(f"[PRO] ✅ PRO TTS: {tts_credits:.4f} credits deducted")
                except Exception as e:
                    self.log_view.append(f"[PRO] ❌ PRO TTS credit deduction error: {e}")
            
            # Force AI deduction via Supabase - PRO MODE
            if ai_credits > 0:
                try:
                    from modules_client.supabase_client import SupabaseClient
                    supabase = SupabaseClient()
                    ai_success = supabase.deduct_mode_credits(
                        email=email,
                        amount=ai_credits,
                        mode="pro",
                        component="AI",
                        description="PRO AI reply generation (100 tokens)"
                    )
                    if not ai_success or ai_success.get("status") != "success":
                        self.log_view.append("[PRO] ❌ PRO AI credit deduction FAILED!")
                        self.log_view.append(f"[PRO] Error: {ai_success.get('message', 'Unknown error')}")
                    else:
                        self.log_view.append(f"[PRO] ✅ PRO AI: {ai_credits:.4f} credits deducted")
                except Exception as e:
                    self.log_view.append(f"[PRO] ❌ PRO AI credit deduction error: {e}")
            
            # Update session stats
            if not safe_attr_check(self, 'session_usage'):
                self.session_usage = {"tts_chars": 0, "ai_requests": 0, "total_credits_used": 0}
            
            self.session_usage["tts_chars"] += tts_chars
            self.session_usage["ai_requests"] += 1
            self.session_usage["total_credits_used"] += total_credits
            
            # Log session totals
            self.log_view.append(f"[PRO] 💰 PRO Mode Session total: {self.session_usage.get('total_credits_used', 0):.4f} credits used")
            
        except Exception as e:
            self.log_view.append(f"[PRO] Error in PRO Mode usage tracking: {e}")
        
        # Original usage tracking for time-based limits
        pro_usage = 5  # 5x lipat dari basic
        add_usage(pro_usage)
        self.log_view.append(f"[Langganan PRO] +{pro_usage} menit (tier: {tier}) - 5x multiplier")

    # — Queue & Processing —  
    def _enqueue(self, author, message):
        """
        Tambahkan komentar ke antrian balasan berdasarkan mode yang dipilih.
        
        Args:
            author (str): Nama pengirim komentar
            message (str): Isi komentar yang akan diproses
            
        Proses:
            - Skip jika sedang dalam mode percakapan
            - Mode Trigger: hanya proses jika mengandung kata kunci
            - Mode Delay Latest: jadwalkan balasan setelah delay
            - Mode Sequential: proses langsung secara berurutan
        """
        if self.conversation_active:
            print(f"[DEBUG] Conversation active - skipping message from {author}")
            return

        current_mode = self.mode_cb.currentText()
        print(f"[DEBUG] Processing message | Mode: {current_mode} | Author: {author}")
        print(f"[DEBUG] Message preview: {message[:50]}{'...' if len(message) > 50 else ''}")
        
        trigger_word = self.cfg.get("trigger_word", "").lower().strip()
        delay_seconds = max(1, min(self.delay_spin.value(), 60))  # Batasi 1-60 detik

        # Mode Trigger
        if current_mode == "Trigger":
            self._process_trigger_mode(author, message, trigger_word)
            
        # Mode Delay Latest    
        elif current_mode == "Delay Latest":
            self._process_delay_mode(author, message, delay_seconds)
            
        # Mode Sequential (default)
        else:  
            print("[DEBUG] Processing in sequential mode")
            self._enqueue_actual(author, message)

    def _process_trigger_mode(self, author, message, trigger_word):
        """Proses komentar dalam mode Trigger."""
        if trigger_word and trigger_word in message.lower():
            print(f"[DEBUG] Trigger word '{trigger_word}' matched")
            self._enqueue_actual(author, message)
        else:
            print(f"[DEBUG] No trigger word match - message ignored")

    def _process_delay_mode(self, author, message, delay):
        """Proses komentar dalam mode Delay Latest."""
        print(f"[DEBUG] Setting up delay timer for {delay} seconds")
        
        # Hentikan timer sebelumnya jika ada
        self._cleanup_existing_timer()
        
        # Buat QTimer baru dengan parent yang jelas
        self.delay_timer = QTimer(self)
        self.delay_timer.setSingleShot(True)
        
        # Gunakan functools.partial untuk menghindari masalah scope lambda
        from functools import partial
        self.delay_timer.timeout.connect(
            partial(self._enqueue_actual, author, message))
            
        self.delay_timer.start(delay * 1000)
        
        # Update UI
        self.log_view.append(f"⏱️ Reply scheduled in {delay} seconds")
        print(f"[DEBUG] Delay timer started | Duration: {delay}s | Author: {author}")

    def _cleanup_existing_timer(self):
        """Bersihkan timer yang sudah ada."""
        if safe_attr_check(self, "delay_timer") and self.delay_timer:
            try:
                if isinstance(self.delay_timer, threading.Timer):
                    self.delay_timer.cancel()
                elif isinstance(self.delay_timer, QTimer):
                    self.delay_timer.stop()
                print("[DEBUG] Previous timer stopped")
            except Exception as e:
                print(f"[ERROR] Timer cleanup failed: {str(e)}")

    def _enqueue_actual(self, author, message):
        """
        Tambahkan komentar ke antrian dan mulai pemrosesan jika belum.
        
        Args:
            author: Nama pengirim komentar
            message: Isi komentar
        """
        self.log_view.append(f"👤 {author}: {message}")
        self.reply_queue.append((author, message))
        print(f"[DEBUG] Enqueued message | Queue size: {len(self.reply_queue)}")
        
        if not self.reply_busy:
            print("[DEBUG] Starting queue processing")
            self._dequeue()
        else:
            print("[DEBUG] Processing busy - item queued")

    def _dequeue(self):
        """Proses komentar berikutnya dari antrian."""
        if not self.reply_queue:
            print("[DEBUG] Queue empty - resetting busy flag")
            self.reply_busy = False
            return
        
        print(f"[DEBUG] Processing next item | Queue size: {len(self.reply_queue)}")
        self.reply_busy = True
        
        author, msg = self.reply_queue.pop(0)
        print(f"[DEBUG] Generating reply for: {author}: {msg[:50]}...")
        
        # Prepare thread parameters
        voice_model = self.cfg.get("cohost_voice_model", None)
        rt = ReplyThread(
            author=author,
            message=msg,
            cohost_name=self.cfg.get("cohost_name", "CoHost"),
            streamer_name=self.cfg.get("streamer_name", "Streamer"),
            personality=self.person_cb.currentText(),
            lang_out=self.out_lang.currentText(),
            extra_prompt=self.cfg.get("custom_context", ""),
            voice_model=voice_model
        )
        
        # Setup thread signals
        rt.finished.connect(self._on_reply)
        rt.finished.connect(
            lambda *_: self.threads.remove(rt) if rt in self.threads else None)
        
        # Start processing
        self.threads.append(rt)
        rt.start()
        print("[DEBUG] ReplyThread started")

    # Perbaikan untuk CohostTab pada cohost_tab_pro.py

    # PERBAIKAN 1: Perbaiki metode _on_reply pada CohostTab (cohost_tab_pro.py)

    def _on_reply(self, author, message, reply):
        """
        Handler untuk balasan yang sudah digenerate.
    
        Memperbarui UI, menyimpan log, dan memulai proses TTS.
        """
        if not reply:
            self.log_view.append("[WARN] Gagal mendapatkan balasan.")
            self.reply_busy = False
            QTimer.singleShot(100, self._dequeue)
            return
        self.current_tts_text = reply
    
        try:
            # Update UI (overlay dan log)
            mw = self.window()
            if safe_attr_check(mw, "overlay_tab"):
                mw.overlay_tab.update_overlay(author, reply)
    
            self.log_view.append(f"🤖 {reply}")
    
            # Track AI usage untuk mode Pro
            try:
                from modules_server.real_credit_tracker import credit_tracker
                estimated_tokens = len(reply.split()) * 1.3
                credits_used = credit_tracker.track_ai_usage(int(estimated_tokens), mode="pro")
                self.log_view.append(f"💳 AI Usage [PRO]: {credits_used:.4f} credits")
            except Exception as tracking_error:
                self.log_view.append(f"❌ AI tracking error: {tracking_error}")

            # Log ke file
            COHOST_LOG.parent.mkdir(exist_ok=True)
            with open(str(COHOST_LOG), "a", encoding="utf-8") as f:
                f.write(f"{author}\t{message}\t{reply}\n")
            self.replyGenerated.emit(author, message, reply)
    
            # Mulai TTS dengan urutan:
            # 1. Emit signal ttsAboutToStart (F1)
            # 2. Setup timer untuk deteksi selesai
            # 3. Lakukan TTS
    
            print("[DEBUG] Starting TTS process")
    
            # Emit signal dan panggil F1
            self.ttsAboutToStart.emit()
            print("[DEBUG] ttsAboutToStart signal emitted")
            self.ttsAboutToStart.emit()
    
            # Setup timer berdasarkan panjang teks
            self._setup_tts_timers(reply)
    
            # Lakukan TTS
            code = "id-ID" if self.out_lang.currentText() == "Indonesia" else "en-US"
            voice_model = self.cfg.get("cohost_voice_model", None)
    
            print(f"[DEBUG] Executing TTS with voice={voice_model}, lang={code}")
            print(f"[DEBUG] Text preview: '{reply[:50]}{'...' if len(reply) > 50 else ''}'")
    
            speak(reply, code, voice_model)
    
        except Exception as e:
            print(f"[ERROR] Error in _on_reply: {e}")
            import traceback
            traceback.print_exc()
    
            # Pastikan cleanup meskipun ada error
            if safe_attr_check(self, 'tts_active'):
                self.ttsFinished.emit()
                print("[DEBUG] ttsFinished signal emitted (error recovery)")
                self.tts_active = False
    
            self.reply_busy = False
            QTimer.singleShot(100, self._dequeue)

    def _manual_tts_finished(self):
        """Timer-based fallback untuk TTS selesai."""
        print("[DEBUG] Manual TTS finished timer triggered")
    
        # Hentikan timeout timer jika masih aktif
        if safe_timer_check(self, 'safety_timer'):
            self.safety_timer.stop()
    
        # Emit signal TTS selesai
        self.ttsFinished.emit()
        print("[DEBUG] ttsFinished signal emitted via timer")
    
        # Reset state
        self.reply_busy = False
    
        # Process antrian berikutnya
        QTimer.singleShot(100, self._dequeue)

    def _on_tts_finished(self):
        """
        Handler terpadu untuk penyelesaian TTS normal.
        Dipanggil ketika timer utama berakhir.
        """
        if not self.tts_active:
            print("[DEBUG] Ignoring TTS finished event - not active")
            return
    
        print("[DEBUG] TTS finished normally")
    
        # Tandai TTS selesai
        self.tts_active = False
    
        # Hentikan timer yang masih berjalan
        self._cleanup_timers()
    
        # Emit signal untuk F2
        self.ttsFinished.emit()
        print("[DEBUG] ttsFinished signal emitted (normal)")
    
        # Reset state dan siapkan untuk antrian berikutnya
        self._prepare_next_message()

    def _tts_safety_timeout(self):
        """
        Handler timeout untuk TTS yang berjalan terlalu lama.
        Dipanggil ketika safety timer berakhir.
        """
        if not self.tts_active:
            print("[DEBUG] Ignoring safety timeout - TTS not active")
            return
    
        print("[WARN] TTS safety timeout triggered - force completing TTS")
    
        # Tandai TTS selesai
        self.tts_active = False
    
        # Hentikan timer yang masih berjalan
        self._cleanup_timers()
    
        # Emit signal untuk F2
        self.ttsFinished.emit()
        print("[DEBUG] ttsFinished signal emitted (safety)")
    
        # Reset state dan siapkan untuk antrian berikutnya
        self._prepare_next_message()

    def _prepare_next_message(self):
        """Persiapkan untuk pemrosesan pesan berikutnya."""
        self.reply_busy = False
        QTimer.singleShot(100, self._dequeue)

    def _handle_tts_failure(self):
        """Central handler untuk kegagalan TTS."""
        # Pastikan signal ttsFinished dipancarkan
        try:
            self.ttsFinished.emit()
            print("[DEBUG] ttsFinished signal emitted via failure handler")
        except:
            pass
    
        # Reset state
        self.reply_busy = False
    
        # Lanjutkan ke antrian berikutnya
        QTimer.singleShot(100, self._dequeue)

    def _cleanup_timers(self):
        """
        Bersihkan semua timer aktif.
        Mencegah timer berjalan ganda atau konflik.
        """
        for timer_name in ['tts_timer', 'safety_timer']:
            if safe_attr_check(self, timer_name):
                timer = getattr(self, timer_name)
                if isinstance(timer, QTimer) and timer.isActive():
                    timer.stop()
                    print(f"[DEBUG] Stopped {timer_name}")

    def _finish_tts(self):
        """Tandai TTS selesai dan siapkan untuk antrian berikutnya."""
        # Cek jika TTS aktif, panggil F2
        if self.tts_active:
            print("[DEBUG] TTS finishing - calling F2")
            # Emit signal animasi berhenti
            self.ttsFinished.emit()
            print("[DEBUG] ttsFinished signal emitted")
        
        # Reset flag
        self.tts_active = False
        self.reply_busy = False
        
        # Proses pesan berikutnya jika ada
        QTimer.singleShot(100, self._dequeue)
    
    # Tambahkan metode ini untuk dipanggil dari MonitorThread
    def resume_processing(self):
        """Dipanggil ketika PyTChat mulai dibaca lagi."""
        # Jika sedang dalam TTS, tandai selesai
        if self.tts_active:
            print("[DEBUG] PyTChat resumed - finishing TTS")
            self._finish_tts()

    def _explicit_end_tts(self):
        """Metode eksplisit untuk mengakhiri TTS setelah durasi tertentu."""
        print("[DEBUG] Executing explicit TTS end procedure")
        
        try:
            # Pastikan timer dihentikan
            if safe_timer_check(self, 'tts_timer'):
                self.tts_timer.stop()
                print("[DEBUG] Stopped active TTS timer")
            
            # Emit sinyal penyelesaian
            self.ttsFinished.emit()
            print("[DEBUG] Emitted ttsFinished signal")
            
            # Reset state
            self.reply_busy = False
            
            # Lanjutkan ke item berikutnya dengan delay kecil
            QTimer.singleShot(100, self._dequeue)
            
        except Exception as e:
            print(f"[ERROR] Error in _explicit_end_tts: {str(e)}")
            self._cleanup_tts_state()

    def _cleanup_tts_state(self):
        """Bersihkan state TTS dan pastikan tidak ada deadlock."""
        self.ttsFinished.emit()
        self.reply_busy = False
        if safe_timer_check(self, 'tts_timer'):
            self.tts_timer.stop()

    def _calculate_tts_duration(self, text):
        """
        Estimasi durasi TTS berdasarkan panjang teks.
    
        Menggunakan rumus sederhana:
        - Bahasa Indonesia: sekitar 12 karakter/detik
        - Bahasa Inggris: sekitar 14 karakter/detik
        - Tambah buffer 1.5 detik untuk proses awal dan akhir
        """
        # Tentukan kecepatan berdasarkan bahasa output
        chars_per_second = 14 if self.out_lang.currentText() == "English" else 12
    
        # Bersihkan teks dari karakter non-printable
        cleaned_text = re.sub(r'[^\w\s\?\,\.\!]', '', text)
    
        # Hitung durasi berdasarkan jumlah kata
        words = cleaned_text.split()
        word_count = len(words)
        char_count = len(cleaned_text)
    
        # Durasi berbasis karakter dengan minimal 2 detik
        duration = max(2.0, (char_count / chars_per_second) + 1.5)
    
        print(f"[DEBUG] TTS Duration estimate: {duration:.2f}s for {word_count} words ({char_count} chars)")
        return duration
    
    def _setup_tts_timers(self, text):
        """
        Setup timer untuk mendeteksi selesainya TTS.
    
        Menggunakan 2 timer:
        1. Timer normal: perkiraan durasi TTS berdasarkan panjang teks
        2. Safety timer: 2x durasi normal untuk menghindari deadlock
        """
        # Bersihkan timer yang mungkin masih aktif
        self._cleanup_timers()
    
        # Set flag TTS aktif
        self.tts_active = True
    
        # Hitung durasi berdasarkan panjang teks
        duration = self._calculate_tts_duration(text)
    
        # Timer utama - perkiraan selesainya TTS
        self.tts_timer = QTimer(self)
        self.tts_timer.setSingleShot(True)
        self.tts_timer.timeout.connect(self._on_tts_finished)
        self.tts_timer.start(int(duration * 1000))
    
        # Safety timer - jika TTS tidak selesai dalam 2x waktu
        self.safety_timer = QTimer(self)
        self.safety_timer.setSingleShot(True)
        self.safety_timer.timeout.connect(self._tts_safety_timeout)
        self.safety_timer.start(int(duration * 2000))
    
        print(f"[DEBUG] TTS timers set: normal={duration:.1f}s, safety={duration*2:.1f}s")

    # 🔥 ENHANCED: Template System Methods
    def load_template(self, template_name):
        """Load predefined template based on selection."""
        templates = {
            "🎮 Gaming - MOBA Expert": """You are a MOBA gaming expert and co-host. You help viewers with:
- Champion/hero strategies and builds
- Game mechanics and meta analysis  
- Team composition advice
- Skill combos and timing
- Map awareness tips
Keep responses concise, helpful, and engaging for stream viewers.""",
            
            "🎮 Gaming - FPS Pro": """You are an FPS gaming expert and co-host. You assist viewers with:
- Weapon recommendations and loadouts
- Map callouts and positioning
- Aim training techniques
- Movement mechanics
- Competitive strategies
Provide quick, actionable advice that enhances their gameplay.""",
            
            "💰 Sales - E-Commerce": """You are a sales expert co-host specializing in e-commerce. You help with:
- Product recommendations
- Deal analysis and value assessment
- Shopping tips and best practices
- Brand comparisons
- Purchase decision guidance
Be persuasive yet honest, focusing on viewer value and satisfaction.""",
            
            "💰 Sales - Digital Products": """You are a digital products sales expert and co-host. You assist with:
- Software and app recommendations
- Digital service evaluations
- Subscription value analysis
- Tech product comparisons
- Digital marketing insights
Provide informed advice that helps viewers make smart digital purchases."""
        }
        
        if template_name in templates:
            self.custom.setPlainText(templates[template_name])
            self.log_view.append(f"[INFO] Template loaded: {template_name}")

    def preview_template(self):
        """Preview current template content."""
        current_text = self.custom.toPlainText()
        if current_text:
            from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton
            dialog = QDialog(self)
            dialog.setWindowTitle("Template Preview")
            dialog.setModal(True)
            dialog.resize(500, 300)
            
            layout = QVBoxLayout(dialog)
            preview_text = QTextEdit()
            preview_text.setPlainText(current_text)
            preview_text.setReadOnly(True)
            layout.addWidget(preview_text)
            
            close_btn = QPushButton("Close")
            close_btn.clicked.connect(dialog.close)
            layout.addWidget(close_btn)
            
            dialog.exec()
        else:
            self.log_view.append("[WARN] No template content to preview")

    # 🔥 ENHANCED: Trigger and Cooldown Methods
    def save_trigger_words(self):
        """Save multiple trigger words."""
        words_text = self.trigger_words_input.text().strip()
        if words_text:
            words_list = [w.strip() for w in words_text.split(",") if w.strip()]
            self.cfg.set("trigger_words", words_list)
            self.cfg.set("trigger_word", words_text)  # Backward compatibility
            self.log_view.append(f"[INFO] Trigger words saved: {words_list}")
        else:
            self.cfg.set("trigger_words", [])
            self.cfg.set("trigger_word", "")
            self.log_view.append("[INFO] Trigger words cleared")

    def test_trigger(self):
        """Test trigger word matching."""
        test_message = "hey bro, can you help me with this game?"
        words_text = self.trigger_words_input.text().strip()
        if words_text:
            words_list = [w.strip().lower() for w in words_text.split(",") if w.strip()]
            matches = [word for word in words_list if word in test_message.lower()]
            if matches:
                self.log_view.append(f"[TEST] ✅ Triggers matched: {matches}")
            else:
                self.log_view.append(f"[TEST] ❌ No triggers matched in test message")
        else:
            self.log_view.append("[TEST] ❌ No trigger words configured")

    def update_cooldown(self, value):
        """Update batch cooldown setting."""
        self.cfg.set("cooldown_duration", value)
        self.log_view.append(f"[INFO] Batch cooldown updated: {value}s")

    def update_viewer_cooldown(self, value):
        """Update viewer cooldown setting."""
        self.cfg.set("viewer_cooldown_minutes", value)
        self.log_view.append(f"[INFO] Viewer cooldown updated: {value} minutes")

    def update_max_queue(self, value):
        """Update maximum queue size."""
        self.cfg.set("max_queue_size", value)
        self.log_view.append(f"[INFO] Max queue size updated: {value}")

    def update_daily_limit(self, value):
        """Update daily interaction limit per viewer."""
        self.cfg.set("viewer_daily_limit", value)
        self.log_view.append(f"[INFO] Daily limit updated: {value} interactions per viewer")

    def update_topic_cooldown(self, value):
        """Update topic cooldown setting."""
        self.cfg.set("topic_cooldown_minutes", value)
        self.log_view.append(f"[INFO] Topic cooldown updated: {value} minutes")

    def save_topic_settings(self):
        """Save topic blocking settings."""
        blocked_topics = self.topic_blocking_input.text().strip()
        self.cfg.set("blocked_topics", blocked_topics)
        self.log_view.append(f"[INFO] Blocked topics saved: {blocked_topics}")

    # 🔥 ENHANCED: Statistics and Memory Methods
    def show_filter_stats(self):
        """Show detailed filter statistics (matching Basic version)."""
        try:
            from datetime import datetime
            today = datetime.now().strftime("%Y-%m-%d")
            
            # Initialize filter stats if not exists
            if not safe_attr_check(self, 'filter_stats'):
                self.filter_stats = {
                    "toxic": 0, "short": 0, "emoji": 0, "spam": 0, "numeric": 0
                }
            
            # Calculate total filtered
            total_filtered = sum(self.filter_stats.values())
            
            # Daily interactions stats
            today_viewers = 0
            total_interactions_today = 0
            status_counts = {"new": 0, "regular": 0, "vip": 0}
            
            if safe_attr_check(self, 'viewer_daily_interactions'):
                for author, data in self.viewer_daily_interactions.items():
                    if data.get("date") == today:
                        today_viewers += 1
                        total_interactions_today += data.get("interaction_count", 0)
                        status = data.get("status", "new")
                        status_counts[status] += 1

            stats_msg = "\n[FILTER STATISTICS]\n"
            stats_msg += "=" * 40 + "\n"
            stats_msg += f"Toxic words: {self.filter_stats.get('toxic', 0)}\n"
            stats_msg += f"Short messages: {self.filter_stats.get('short', 0)}\n"
            stats_msg += f"Emoji only: {self.filter_stats.get('emoji', 0)}\n"
            stats_msg += f"Spam/daily limit: {self.filter_stats.get('spam', 0)}\n"
            stats_msg += f"Numeric spam: {self.filter_stats.get('numeric', 0)}\n"
            stats_msg += "=" * 40 + "\n"
            stats_msg += f"Total filtered: {total_filtered}\n\n"
            
            stats_msg += "[DAILY INTERACTIONS]\n"
            stats_msg += "=" * 40 + "\n"
            stats_msg += f"Active viewers today: {today_viewers}\n"
            stats_msg += f"Total interactions today: {total_interactions_today}\n"
            stats_msg += f"New viewers: {status_counts['new']}\n"
            stats_msg += f"Regular viewers: {status_counts['regular']}\n"
            stats_msg += f"VIP viewers: {status_counts['vip']}\n"
            stats_msg += f"Limit per same question: {getattr(self, 'daily_message_limit', 3)}x/day"

            self.log_view.append(stats_msg)
            
        except Exception as e:
            self.log_view.append(f"[ERROR] Failed to show filter stats: {e}")

    def show_cache_spam_stats(self):
        """Show cache and spam statistics (matching Basic version)."""
        try:
            import textwrap
            
            # Initialize components if not exists
            if not safe_attr_check(self, 'cache_manager'):
                cache_stats = {
                    'total_entries': 0,
                    'total_hits': 0,
                    'hit_rate': 0.0,
                    'cache_size_kb': 0.0
                }
            else:
                cache_stats = self.cache_manager.get_stats()
            
            if not safe_attr_check(self, 'spam_detector'):
                spam_stats = {
                    'total_users': 0,
                    'blocked_users': 0,
                    'total_messages': 0,
                    'active_blocks': []
                }
            else:
                spam_stats = self.spam_detector.get_overall_stats()

            stats_msg = textwrap.dedent(f"""
                [CACHE STATISTICS]
                Total Entries: {cache_stats['total_entries']}
                Total Hits: {cache_stats['total_hits']}
                Hit Rate: {cache_stats['hit_rate']:.1f}%
                Cache Size: {cache_stats['cache_size_kb']:.1f} KB

                [SPAM DETECTION]
                Total Users: {spam_stats['total_users']}
                Blocked Users: {spam_stats['blocked_users']}
                Total Messages: {spam_stats['total_messages']}
                Active Blocks: {', '.join(spam_stats['active_blocks'])}
            """).strip()

            self.log_view.append(stats_msg)
            
        except Exception as e:
            self.log_view.append(f"[ERROR] Failed to show cache/spam stats: {e}")

    def reset_statistics(self):
        """Reset filter statistics (matching Basic version)."""
        try:
            # Reset filter stats
            if not safe_attr_check(self, 'filter_stats'):
                self.filter_stats = {
                    "toxic": 0, "short": 0, "emoji": 0, "spam": 0, "numeric": 0
                }
            else:
                self.filter_stats = {
                    "toxic": 0, "short": 0, "emoji": 0, "spam": 0, "numeric": 0
                }
            
            # Reset viewer memory if exists
            if safe_attr_check(self, 'viewer_memory'):
                self.viewer_memory.reset_statistics()
                self.update_memory_stats()
                
            self.log_view.append("[INFO] ✅ Filter statistics have been reset")
            
        except Exception as e:
            self.log_view.append(f"[ERROR] Failed to reset statistics: {e}")

    def reset_spam_blocks(self):
        """Reset spam block records (matching Basic version)."""
        try:
            import time
            
            # Count currently blocked viewers
            blocked_count = 0
            if safe_attr_check(self, 'viewer_daily_interactions'):
                current_time = time.time()
                for author, data in self.viewer_daily_interactions.items():
                    if data.get("blocked_until", 0) > current_time:
                        blocked_count += 1
                # Reset all spam data
                self.viewer_daily_interactions.clear()

            # Reset old system if exists
            if safe_attr_check(self, 'viewer_cooldowns'):
                blocked_count += sum(1 for data in self.viewer_cooldowns.values() if data.get("blocked_until", 0) > time.time())
                self.viewer_cooldowns.clear()
                
            # Reset spam detector if exists
            if safe_attr_check(self, 'spam_detector'):
                self.spam_detector.reset_blocks()
                
            self.log_view.append(f"[RESET] {blocked_count} spam blocks removed, all viewers can ask questions again")
            self.log_view.append("[RESET] Daily interaction history has been reset")
            
        except Exception as e:
            self.log_view.append(f"[ERROR] Failed to reset spam blocks: {e}")

    def reset_daily_interactions(self):
        """Reset daily interaction counters (matching Basic version)."""
        try:
            interaction_count = 0
            
            # Reset daily interactions
            if safe_attr_check(self, 'viewer_daily_interactions'):
                interaction_count = len(self.viewer_daily_interactions)
                self.viewer_daily_interactions.clear()
                
            # Reset viewer memory daily interactions if exists
            if safe_attr_check(self, 'viewer_memory'):
                self.viewer_memory.reset_daily_interactions()
                self.update_memory_stats()
                
            self.log_view.append(f"[RESET] {interaction_count} daily interactions reset")
            self.log_view.append("[RESET] All viewers can ask questions about any topic again")
            
        except Exception as e:
            self.log_view.append(f"[ERROR] Failed to reset daily interactions: {e}")

    def update_memory_stats(self):
        """Update memory statistics display."""
        try:
            if safe_attr_check(self, 'viewer_memory'):
                stats = self.viewer_memory.get_statistics()
                viewer_count = len(stats.get('viewers', {}))
                self.memory_stats_label.setText(f"📊 Viewer Memory: {viewer_count} viewers tracked")
        except Exception as e:
            self.memory_stats_label.setText("📊 Viewer Memory: Error loading stats")

    # 🔥 ENHANCED: Microphone and Communication Methods
    def load_microphones(self):
        """Load available microphones."""
        self.mic_combo.clear()
        try:
            import sounddevice as sd
            devices = sd.query_devices()
            for i, device in enumerate(devices):
                if device['max_input_channels'] > 0:
                    self.mic_combo.addItem(f"{device['name']}", i)
            
            # Set saved microphone
            saved_mic = self.cfg.get("selected_microphone", "")
            if saved_mic:
                idx = self.mic_combo.findText(saved_mic)
                if idx >= 0:
                    self.mic_combo.setCurrentIndex(idx)
        except Exception as e:
            self.log_view.append(f"[ERROR] Failed to load microphones: {e}")
            self.mic_combo.addItem("Default Microphone", -1)

    def export_log(self):
        """Export activity log to file."""
        try:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"cohost_pro_log_{timestamp}.txt"
            
            log_content = self.log_view.toPlainText()
            if log_content:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(f"StreamMate AI - CoHost Pro Log\n")
                    f.write(f"Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("="*50 + "\n\n")
                    f.write(log_content)
                
                self.log_view.append(f"[INFO] ✅ Log exported to: {filename}")
            else:
                self.log_view.append("[WARN] No log content to export")
        except Exception as e:
            self.log_view.append(f"[ERROR] Failed to export log: {e}")

    def save_custom(self):
        """Save custom prompt with enhanced validation."""
        c = self.custom.toPlainText().strip()
        if c:
            self.cfg.set("custom_context", c)
            self.log_view.append("[INFO] ✅ Custom prompt saved successfully")
            
            # Update template combo to show custom
            if self.template_combo.currentText() != "📝 Custom Prompt":
                self.template_combo.setCurrentText("📝 Custom Prompt")
        else:
            self.cfg.set("custom_context", "")
            self.log_view.append("[INFO] Custom prompt cleared")


    def closeEvent(self, event):
        # stop the usage timer and all listeners when the window closes
        self.usage_timer.stop()
        self.stop()
        super().closeEvent(event)
