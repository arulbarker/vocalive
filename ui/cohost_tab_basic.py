# SIMPLIFIED VERSION - Mengurangi kompleksitas threading untuk mencegah force close
# Fokus pada stabilitas dan fitur inti dengan dukungan YouTube dan TikTok

import json
import logging
import os
import re
import sys
import threading
import time
import traceback
from collections import defaultdict, deque
from datetime import datetime, timedelta

logger = logging.getLogger('VocaLive.Cohost')

from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QColor, QFont, QPalette, QTextCursor
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

# SIMPLIFIED: Minimal imports untuk mengurangi dependency issues
try:
    from modules_client.api import generate_reply_with_scene
    from modules_client.config_manager import ConfigManager
    from modules_client.logger import Logger
    from modules_server.tts_engine import speak
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

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
        LOG_TEXTEDIT_STYLE,
        PRIMARY,
        RADIUS,
        RADIUS_SM,
        SECONDARY,
        SUCCESS,
        TEXT_DIM,
        TEXT_MUTED,
        TEXT_PRIMARY,
        WARNING,
        btn_accent,
        btn_danger,
        btn_ghost,
        btn_secondary,
        btn_success,
        label_subtitle,
        label_title,
        status_badge,
    )
except ImportError:
    PRIMARY = "#2563EB"; BG_BASE = "#0F1623"; BG_SURFACE = "#162032"; BG_ELEVATED = "#1E2A3B"
    TEXT_PRIMARY = "#F0F6FF"; TEXT_MUTED = "#93C5FD"; TEXT_DIM = "#4B7BBA"
    ERROR = "#EF4444"; SUCCESS = "#22C55E"; WARNING = "#F59E0B"; INFO = "#38BDF8"
    BORDER_GOLD = "#1E4585"; BORDER = "#1A2E4A"; ACCENT = "#60A5FA"
    SECONDARY = "#1E3A5F"; RADIUS = "10px"; RADIUS_SM = "6px"
    def btn_success(extra=""): return f"QPushButton {{ background-color: {SUCCESS}; color: white; border: none; border-radius: 6px; padding: 8px 18px; font-weight: 700; font-size: 12px; {extra} }} QPushButton:hover {{ background-color: #16A34A; }}"
    def btn_danger(extra=""): return f"QPushButton {{ background-color: {ERROR}; color: white; border: none; border-radius: 6px; padding: 8px 18px; font-weight: 700; font-size: 12px; {extra} }} QPushButton:hover {{ background-color: #DC2626; }}"
    def btn_ghost(extra=""): return f"QPushButton {{ background-color: {BG_ELEVATED}; color: {TEXT_MUTED}; border: 1px solid {BORDER}; border-radius: 6px; padding: 7px 18px; font-weight: 600; {extra} }}"
    def btn_accent(extra=""): return f"QPushButton {{ background-color: {ACCENT}; color: {BG_BASE}; border: none; border-radius: 6px; padding: 8px 18px; font-weight: 700; {extra} }}"
    def btn_secondary(extra=""): return f"QPushButton {{ background-color: transparent; color: {PRIMARY}; border: 1px solid {PRIMARY}; border-radius: 6px; padding: 7px 18px; font-weight: 600; {extra} }}"
    def status_badge(color=None, size=11): c = color or PRIMARY; return f"color: {c}; font-weight: 600; font-size: {size}px; padding: 4px 10px; background-color: {BG_ELEVATED}; border: 1px solid {c}; border-radius: 6px;"
    def label_title(size=16): return f"font-size: {size}pt; font-weight: 700; color: {PRIMARY}; background: transparent;"
    def label_subtitle(size=11): return f"font-size: {size}px; color: {TEXT_MUTED}; background: transparent;"
    LOG_TEXTEDIT_STYLE = f"QTextEdit {{ background-color: {BG_ELEVATED}; color: {TEXT_MUTED}; border: 1px solid {BORDER_GOLD}; border-radius: 6px; padding: 8px; font-family: Consolas, monospace; font-size: 11px; }}"

# Helper function untuk safe attribute check
def safe_attr_check(obj, attr_name):
    """Safely check if object has attribute"""
    try:
        return hasattr(obj, attr_name) and getattr(obj, attr_name) is not None
    except Exception:
        return False

# SIMPLIFIED REPLY THREAD - Mengurangi kompleksitas
class SimpleReplyThread(QThread):
    """Simplified reply thread dengan error handling minimal tapi efektif"""
    finished = pyqtSignal(str, str, str, int)  # author, message, reply, scene_id

    def __init__(self, author, message, is_greeting=False, language="Indonesia", parent=None):
        super().__init__(parent)
        self.author = author or "Unknown"
        self.message = message or "[No message]"
        self.is_greeting = is_greeting
        self.language = language
        self.daemon = True  # Ensure thread doesn't block app exit

    def _clean_ai_response(self, raw_text):
        """Clean AI response from emojis, formatting, and special chars for TTS"""
        if not raw_text:
            return ""

        import re

        text = raw_text.strip()

        # Remove ALL markdown formatting
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # **bold**
        text = re.sub(r'\*(.*?)\*', r'\1', text)      # *italic*
        text = re.sub(r'__(.*?)__', r'\1', text)      # __underline__
        text = re.sub(r'_(.*?)_', r'\1', text)        # _underline_
        text = re.sub(r'`(.*?)`', r'\1', text)        # `code`
        text = re.sub(r'~~(.*?)~~', r'\1', text)      # ~~strikethrough~~

        # Remove ALL emojis and emoticons completely for clean TTS
        text = re.sub(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002600-\U000027BF\U0001F900-\U0001F9FF\U00002700-\U000027BF\U00002B00-\U00002BFF\U00002934-\U00002935\U000025A0-\U000025FF\U0001F170-\U0001F251\U00002000-\U0000206F\U0001F004\U0001F0CF\U0001F18E\U0001F191-\U0001F251\U00002764\U00002763\U0001F494\U0001F495\U0001F496\U0001F497\U0001F498\U0001F499\U0001F49A\U0001F49B\U0001F49C\U0001F49D\U0001F49E\U0001F49F\U00002728\U000026A8\U000026F9\U0000267F\U0001F3C3\U0001F3C4]', '', text)
        text = re.sub(r'[:;=8xX]-?[)\]}>dDpP(\[{<|\\/@#$%^&*oO0]', '', text)  # ASCII emoticons
        text = re.sub(r'[)\]}>dDpP(\[{<|\\/@#$%^&*oO0]-?[:;=8xX]', '', text)  # Reverse emoticons
        text = re.sub(r'✨|⭐|🌟|💫|🔥|👍|👏|❤️|💖|💕|🎉|🥳|😊|😍|🤩', '', text)  # Specific common emojis

        # Remove excessive punctuation but keep natural sentence flow
        text = re.sub(r'[!]{2,}', '.', text)         # !!! -> .
        text = re.sub(r'[?]{2,}', '?', text)         # ??? -> ?
        text = re.sub(r'[.]{2,}', '.', text)         # ... -> .
        text = re.sub(r'[,]{2,}', ',', text)         # ,, -> ,

        # Remove special symbols that TTS reads weirdly
        text = re.sub(r'[~#$%^&*+={}[\]|\\<>]', '', text)  # Remove special chars
        text = re.sub(r'[@]', ' at ', text)          # @ -> "at"
        text = re.sub(r'[/]', ' atau ', text)        # / -> "atau"

        # Remove quotes and parentheses (TTS reads them literally)
        text = re.sub(r'["\'""`]', '', text)         # Remove all quotes
        text = re.sub(r'[()[\]{}]', '', text)        # Remove brackets

        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()

        return text

    def run(self):
        """Simplified run method dengan minimal error handling"""
        scene_id = 0  # default: tidak ada produk relevan
        try:
            # Get user context from config for better AI responses
            from modules_client.config_manager import ConfigManager
            cfg = ConfigManager()
            user_context = cfg.get("user_context", "")

            # Special handling for greeting messages - much shorter and focused
            if self.is_greeting:
                # For greetings, use the message as direct prompt (already formatted in handle_viewer_greeting)
                prompt = self.message  # This is the greeting prompt like "Sapa penonton baru bernama X dengan singkat..."
            else:
                # Regular comment handling with full context
                if user_context and user_context.strip():
                    prompt = f"""Context: {user_context.strip()}

Penonton bernama {self.author} berkomentar: "{self.message}"

Sebagai karakter sesuai context di atas, jawab komentar dari {self.author} dengan natural dan interaktif.

PENTING: Berikan respons yang SINGKAT, PADAT, dan LANGSUNG TO THE POINT (maksimal 2-3 kalimat pendek, sekitar 200-250 karakter). Jangan bertele-tele! Sebut nama {self.author} secara natural. Fokus pada 1 poin utama saja."""
                else:
                    # Fallback jika tidak ada context - tetap sertakan nama untuk interaksi yang lebih personal
                    prompt = f"""Penonton bernama {self.author} berkomentar: "{self.message}"

Jawab komentar dari {self.author} dengan natural dan ramah.

PENTING: Berikan respons yang SINGKAT dan LANGSUNG (maksimal 2 kalimat pendek, sekitar 150-200 karakter). Jangan panjang lebar! Sebut nama {self.author} dalam respons."""

            # API call dengan context-aware prompt
            # PERFORMANCE: Use fast_mode for chat replies (5s timeout, 80 tokens)
            reply, scene_id = generate_reply_with_scene(prompt, fast_mode=True)
            try:
                from modules_client.telemetry import capture as _tel_capture
                _tel_capture("cohost_reply_generated", {
                    "provider": cfg.get("ai_provider", "unknown"),
                    "has_scene": scene_id > 0,
                })
            except Exception:
                pass

            # Clean AI response from emojis, formatting, and special chars
            if reply:
                reply = self._clean_ai_response(reply)

            # Basic validation with natural fallback
            if not reply or len(reply.strip()) == 0:
                if self.is_greeting:
                    # Sales-oriented fallback greeting based on language setting
                    if self.language == "Malaysia":
                        reply = f"Hai {self.author}, selamat datang! Jom tengok-tengok produk kita!"
                    elif self.language == "English":
                        reply = f"Hello {self.author}, welcome! Check out our products!"
                    else:  # Indonesia (default)
                        reply = f"Halo {self.author}, selamat datang! Yuk lihat-lihat produk kita!"
                else:
                    reply = f"Hai {self.author}, terima kasih komentarnya!"

            # Different truncation limits for greetings vs regular comments
            # IMPORTANT: Keep responses SHORT for fast TTS playback!
            if self.is_greeting:
                # Greeting should be shorter - max 150 characters (~10-15 second audio)
                if len(reply) > 150:
                    reply = reply[:147] + "..."
            else:
                # Regular comments - max 300 characters (~20-25 second audio)
                # 300 chars = ~20s audio (fast, responsive, not boring!)
                if len(reply) > 300:
                    reply = reply[:297] + "..."

            # Emit signal - simple, no retry logic
            self.finished.emit(self.author, self.message, reply, scene_id)

        except Exception as e:
            # Simple fallback reply with username - different for greetings and languages
            if self.is_greeting:
                if self.language == "Malaysia":
                    fallback_reply = f"Hai {self.author}, selamat datang! Jom tengok-tengok produk kita!"
                elif self.language == "English":
                    fallback_reply = f"Hello {self.author}, welcome! Check out our products!"
                else:  # Indonesia (default)
                    fallback_reply = f"Halo {self.author}, selamat datang! Yuk lihat-lihat produk kita!"
            else:
                fallback_reply = f"Hai {self.author}, terima kasih!"
            self.finished.emit(self.author, self.message, fallback_reply, 0)
            print(f"[SimpleReplyThread] Error: {e}")

# TTS THREAD - Jalankan TTS di background agar GUI tidak freeze
class TTSThread(QThread):
    """Run TTS (HTTP request + pygame playback) in a background thread.
    GUI stays fully responsive while audio plays.
    """
    finished = pyqtSignal()

    def __init__(self, text, voice_model, language_code, parent=None):
        super().__init__(parent)
        self.text = text
        self.voice_model = voice_model
        self.language_code = language_code
        self.daemon = True

    def run(self):
        try:
            from modules_server.tts_engine import speak
            speak(self.text, voice_name=self.voice_model,
                  language_code=self.language_code,
                  force_google_tts=True)
        except Exception as e:
            print(f"[TTSThread] Error: {e}")
        finally:
            self.finished.emit()


# SIMPLIFIED LISTENER - Mengurangi kompleksitas pytchat
class SimpleListener(QThread):
    """Simplified listener dengan minimal overhead"""
    newComment = pyqtSignal(str, str)
    logMessage = pyqtSignal(str, str)

    def __init__(self, video_id, parent=None):
        super().__init__(parent)
        self.video_id = video_id
        self.running = False
        self.daemon = True

    def run(self):
        """Simplified pytchat listener with signal fix"""
        try:
            # CRITICAL FIX: Bypass signal issue by monkey-patching
            import signal
            original_signal = signal.signal

            def safe_signal(sig, handler):
                """Safe signal handler that doesn't fail in threads"""
                try:
                    return original_signal(sig, handler)
                except ValueError as e:
                    # "signal only works in main thread" - ignore this error
                    if "main thread" in str(e):
                        print(f"[SimpleListener] Signal registration ignored in thread: {e}")
                        return None
                    raise

            # Apply monkey patch
            signal.signal = safe_signal

            import pytchat
            chat = pytchat.create(video_id=self.video_id)
            self.running = True

            # Restore original signal after pytchat creation
            signal.signal = original_signal

            while self.running and chat.is_alive():
                try:
                    for c in chat.get().sync_items():
                        if not self.running:
                            break

                        author = c.author.name
                        message = c.message

                        # Simple emit
                        self.newComment.emit(author, message)

                except Exception as e:
                    print(f"[SimpleListener] Chat error: {e}")
                    time.sleep(1)  # Brief pause on error

        except Exception as e:
            self.logMessage.emit("ERROR", f"Listener failed: {e}")

    def stop(self):
        """Simple stop method"""
        self.running = False
        self.quit()

# VIEWER GREETING MANAGER - Sistem otomatis untuk menyapa penonton baru
class ViewerGreetingManager(QThread):
    """Manage viewer greeting with customizable timing and auto greeting queue"""
    greetingRequested = pyqtSignal(str, str)  # username, display_name
    logMessage = pyqtSignal(str, str)
    statusChanged = pyqtSignal(str)  # status message

    def __init__(self, parent=None):
        super().__init__(parent)
        self.cfg = ConfigManager()
        self.is_active = False
        self.detection_active = False
        self.pending_greetings = []  # Queue for viewers to greet
        self.seen_viewers = set()  # Track seen viewers to avoid duplicates
        self.daemon = True

    def start_greeting_system(self):
        """Start the viewer greeting system"""
        enabled = self.cfg.get("viewer_greeting_enabled", False)
        if not enabled:
            self.logMessage.emit("INFO", "Viewer greeting system disabled in settings")
            return

        self.is_active = True
        self.start()
        self.logMessage.emit("INFO", "Viewer greeting system started")

    def stop_greeting_system(self):
        """Stop the viewer greeting system"""
        self.is_active = False
        self.detection_active = False
        self.pending_greetings.clear()
        self.seen_viewers.clear()
        self.quit()
        self.logMessage.emit("INFO", "Viewer greeting system stopped")

    def add_viewer(self, username, display_name):
        """Add viewer to greeting queue if detection is active"""
        if not self.is_active or not self.detection_active:
            return

        # Avoid duplicate greetings
        viewer_key = f"{username}:{display_name}"
        if viewer_key in self.seen_viewers:
            return

        self.seen_viewers.add(viewer_key)
        self.pending_greetings.append((username, display_name))
        self.logMessage.emit("INFO", f"Added viewer to greeting queue: @{username} ({display_name})")

        # Keep memory manageable
        if len(self.seen_viewers) > 200:
            # Keep only recent half
            recent_viewers = list(self.seen_viewers)[-100:]
            self.seen_viewers = set(recent_viewers)

    def run(self):
        """Main greeting system loop with timing controls"""
        try:
            while self.is_active:
                # Get current settings
                detection_window = self.cfg.get("viewer_detection_window", 60)  # seconds
                wait_interval = self.cfg.get("viewer_wait_interval", 300)  # seconds

                # Start detection phase
                self.detection_active = True
                self.statusChanged.emit(f"🟢 Detecting viewers for {detection_window} seconds...")
                self.logMessage.emit("INFO", f"Detection phase started: {detection_window} seconds")

                # Detection phase - actively collect viewers
                start_time = time.time()
                while self.is_active and (time.time() - start_time) < detection_window:
                    time.sleep(1)  # Check every second

                # End detection phase
                self.detection_active = False

                # Process pending greetings
                if self.pending_greetings and self.is_active:
                    greeting_count = len(self.pending_greetings)
                    self.statusChanged.emit(f"🎤 Processing {greeting_count} greetings...")
                    self.logMessage.emit("INFO", f"Processing {greeting_count} pending greetings")

                    # Send greetings to queue (spaced out to avoid spam)
                    for i, (username, display_name) in enumerate(self.pending_greetings):
                        if not self.is_active:
                            break

                        self.greetingRequested.emit(username, display_name)

                        # Space out greetings (2 seconds between each)
                        if i < len(self.pending_greetings) - 1:
                            time.sleep(2)

                    self.pending_greetings.clear()

                # Wait phase
                if self.is_active:
                    self.statusChanged.emit(f"⏳ Waiting {wait_interval//60} minutes until next cycle...")
                    self.logMessage.emit("INFO", f"Wait phase started: {wait_interval} seconds")

                    # Wait phase - no detection
                    start_time = time.time()
                    while self.is_active and (time.time() - start_time) < wait_interval:
                        time.sleep(5)  # Check every 5 seconds during wait

        except Exception as e:
            self.logMessage.emit("ERROR", f"Error in greeting system: {e}")
        finally:
            self.statusChanged.emit("⏹️ Viewer greeting system stopped")

# SIMPLIFIED TIKTOK LISTENER
class SimpleTikTokListener(QThread):
    """Simplified TikTok listener dengan minimal overhead dan viewer join detection"""
    newComment = pyqtSignal(str, str)
    viewerJoined = pyqtSignal(str, str)  # username, display_name
    logMessage = pyqtSignal(str, str)

    # Grace period in seconds — ignore all comments during this window after connect.
    # TikTokLive dumps recent chat history on connect; this filters them out.
    CONNECT_GRACE_PERIOD = 3.0

    def __init__(self, username, parent=None):
        super().__init__(parent)
        self.username = username.replace("@", "").strip()
        self.running = False
        self.client = None
        self.seen_messages = set()
        self.daemon = True
        self.start_timestamp = None  # Track when listener started
        self._grace_period_over = False  # True after grace period ends

    def should_skip_comment(self, event_timestamp_ms, current_time):
        """Determine if a comment should be skipped based on timing.

        After connecting, TikTokLive sends a batch of old comments (history dump).
        We use a grace period to drop ALL comments that arrive in the first few
        seconds after connect. After the grace period, only truly live comments
        come through.

        Args:
            event_timestamp_ms: Event timestamp in milliseconds (None if unavailable)
            current_time: Current time.time() value

        Returns:
            True if comment should be skipped (old chat), False if realtime
        """
        if self.start_timestamp is None:
            return False

        elapsed = current_time - self.start_timestamp

        # During grace period — skip ALL comments (history dump)
        if not self._grace_period_over:
            if elapsed < self.CONNECT_GRACE_PERIOD:
                return True
            # Grace period just ended — mark it and accept from now on
            self._grace_period_over = True

        # After grace period — also filter by event timestamp if available
        if event_timestamp_ms:
            event_time = event_timestamp_ms / 1000.0
            # Skip comments whose event timestamp is before we connected
            if event_time < self.start_timestamp:
                return True

        return False

    def run(self):
        """Simplified TikTok listener"""
        try:
            self.logMessage.emit("INFO", f"[TikTok] Initializing listener for @{self.username}")

            # CRITICAL FIX: Reset state untuk fresh start setiap kali run
            # Ini penting untuk restart aplikasi agar tidak block komentar lama
            self.seen_messages.clear()  # Clear duplicate tracking
            self.start_timestamp = None  # Reset connection timestamp
            self._grace_period_over = False  # Reset grace period
            self.running = False  # Will be set to True after client creation

            self.logMessage.emit("INFO", "[TikTok] State reset - ready for fresh connection")

            from TikTokLive import TikTokLiveClient
            from TikTokLive.events import CommentEvent, ConnectEvent, DisconnectEvent, JoinEvent

            self.logMessage.emit("INFO", "[TikTok] TikTokLive library imported successfully")
            self.logMessage.emit("INFO", f"[TikTok] Creating client for @{self.username}")

            # Create TikTok client
            self.client = TikTokLiveClient(unique_id=self.username)
            self.running = True

            self.logMessage.emit("INFO", "[TikTok] Client created, setting up event handlers...")

            @self.client.on(ConnectEvent)
            async def on_connect(event):
                import time
                self.start_timestamp = time.time()  # Record connection time
                self._grace_period_over = False  # Reset grace period on every connect
                logger.info("[COHOST] TikTok connected: username=%s", self.username)
                self.logMessage.emit("INFO", f"✅ Connected! Menunggu {self.CONNECT_GRACE_PERIOD:.0f}s untuk skip history lama...")
                try:
                    from modules_client.config_manager import ConfigManager as _CM
                    from modules_client.telemetry import capture as _tel_capture
                    _tel_capture("tiktok_connected", {"nickname": _CM().get("tiktok_nickname", "")})
                except Exception:
                    pass

            @self.client.on(CommentEvent)
            async def on_comment(event):
                if not self.running:
                    return

                try:
                    import time
                    current_time = time.time()

                    # Filter old chat — delegasi ke method yang bisa di-unit-test
                    was_grace = not self._grace_period_over
                    event_ts = event.timestamp if hasattr(event, 'timestamp') and event.timestamp else None
                    if self.should_skip_comment(event_ts, current_time):
                        return
                    # Log when grace period just ended
                    if was_grace and self._grace_period_over:
                        self.logMessage.emit("INFO", "✅ Grace period selesai — mulai tangkap komentar LIVE")

                    # Extract author and message
                    author = event.user.nickname if safe_attr_check(event.user, 'nickname') else str(event.user.unique_id)
                    message = event.comment

                    if not message or not message.strip():
                        return  # Skip empty messages

                    # Duplicate detection untuk realtime chat
                    # Setiap session punya timeline sendiri berdasarkan connection time
                    import hashlib
                    time_since_connect = int(current_time - self.start_timestamp) if self.start_timestamp else 0
                    # Group comments in 5-second windows untuk lebih responsive
                    time_window = time_since_connect // 5

                    comment_key = f"{author}:{hashlib.md5(message.encode()).hexdigest()[:8]}:{time_window}"

                    if comment_key in self.seen_messages:
                        self.logMessage.emit("DEBUG", f"[TikTok] 🔁 Duplicate detected in window {time_window}, skipping")
                        return  # Duplicate in same 5-second window

                    self.seen_messages.add(comment_key)

                    # IMPROVED: Keep memory manageable with rolling cleanup
                    # Remove oldest 50 entries instead of clearing all
                    if len(self.seen_messages) > 150:
                        # Convert to list, remove first 50, convert back to set
                        messages_list = list(self.seen_messages)
                        self.seen_messages = set(messages_list[50:])
                        self.logMessage.emit("DEBUG", "[TikTok] Cleaned up duplicate tracking (kept newest 100)")

                    # Log and emit new comment
                    logger.debug("[COHOST] Comment received: user=%s, msg_len=%d", author, len(message))
                    self.logMessage.emit("INFO", f"[TikTok Comment] {author}: {message[:50]}")
                    self.newComment.emit(author, message)

                except Exception as comment_error:
                    self.logMessage.emit("ERROR", f"Error processing TikTok comment: {comment_error}")
                    # Don't block future comments if one fails
                    import traceback
                    self.logMessage.emit("DEBUG", f"Traceback: {traceback.format_exc()}")

            @self.client.on(JoinEvent)
            async def on_join(event):
                if not self.running:
                    return

                try:
                    # Process viewer join with safe attribute check
                    username = event.user.unique_id if safe_attr_check(event.user, 'unique_id') else "Unknown"
                    display_name = event.user.nickname if safe_attr_check(event.user, 'nickname') else username

                    # Emit signal for viewer join processing
                    self.viewerJoined.emit(username, display_name)

                except Exception as join_error:
                    self.logMessage.emit("ERROR", f"Error processing viewer join: {join_error}")

            @self.client.on(DisconnectEvent)
            async def on_disconnect(event):
                self.logMessage.emit("INFO", "Disconnected from TikTok Live")
                self.running = False

            self.logMessage.emit("INFO", "[TikTok] Event handlers registered successfully")
            self.logMessage.emit("INFO", "[TikTok] Attempting to connect to live stream...")
            self.logMessage.emit("INFO", f"[TikTok] ⚠️ Make sure @{self.username} is LIVE right now!")

            # Start the client
            self.logMessage.emit("INFO", "[TikTok] Starting client.run()...")
            self.client.run()

            self.logMessage.emit("INFO", "[TikTok] client.run() completed (connection closed)")

        except ImportError:
            self.logMessage.emit("ERROR", "❌ TikTokLive library not found. Install with: pip install TikTokLive")
        except Exception as e:
            self.logMessage.emit("ERROR", f"❌ TikTok listener error: {e}")
            import traceback
            self.logMessage.emit("DEBUG", f"Full traceback: {traceback.format_exc()}")

    def stop(self):
        """Simple stop method with proper cleanup for restart support"""
        self.running = False

        if self.client:
            try:
                # Suppress betterproto cleanup warnings
                import warnings
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    # Try to stop client gracefully
                    try:
                        self.client.stop()
                    except Exception:
                        pass
            except Exception as e:
                # Ignore cleanup errors (common with TikTokLive on Windows)
                pass
            finally:
                # CRITICAL: Always clear client reference completely
                self.client = None

        # Clear all state for fresh restart
        self.seen_messages.clear()
        self.start_timestamp = None
        self._grace_period_over = False

        # Quit thread
        try:
            self.quit()
        except Exception:
            pass

# MAIN SIMPLIFIED COHOST CLASS
class CohostTabBasicSimplified(QWidget):
    """Simplified version focusing on core functionality and stability"""

    # Simple signals
    ttsFinished = pyqtSignal()
    replyGenerated = pyqtSignal(str, str, str)
    process_comment_signal = pyqtSignal(str, str)  # For OBS trigger detection

    def __init__(self):
        super().__init__()

        # Popup window reference (set from main_window via set_popup_window)
        self._popup_window = None
        self._psm_cache = None  # cached ProductSceneManager untuk popup

        # Core configuration
        self.cfg = ConfigManager("config/settings.json")
        self.logger = Logger()

        # Simple state management
        self.reply_busy = False       # True while TTS is playing → blocks queue pop
        self.conversation_active = False
        self.comment_counter = 0

        # Simple data structures — baca saved setting, fallback ke default
        _saved_queue_size = self.cfg.get("cohost_max_queue", 10)
        self.reply_queue = deque(maxlen=max(1, _saved_queue_size))
        self.recent_messages = deque(maxlen=50)  # Limited history
        self.viewer_cooldowns = {}  # Simple cooldown tracking

        # Thread management - simplified
        self.listener_thread = None
        self.tiktok_listener_thread = None
        self.active_reply_threads = []  # Track active threads
        self._tts_thread = None          # Keep reference to active TTSThread

        # Custom greeting system (new)
        from modules_client.custom_greeting_manager import get_greeting_manager
        self.custom_greeting_manager = get_greeting_manager()

        # Sequential greeting system (time-based)
        from modules_client.sequential_greeting_manager import get_sequential_greeting_manager
        self.sequential_greeting_manager = get_sequential_greeting_manager()

        # Analytics manager for live tracking
        try:
            from modules_client.analytics_manager import get_analytics_manager
            self.analytics = get_analytics_manager()
            self.logger.info("Analytics manager initialized")
        except ImportError:
            self.analytics = None
            self.logger.warning("Analytics manager not available")

        # Add dummy viewer_greeting_manager for backward compatibility
        class DummyViewerGreetingManager:
            def start_greeting_system(self):
                pass
            def stop_greeting_system(self):
                pass
            def add_viewer(self, username, display_name):
                pass

        self.viewer_greeting_manager = DummyViewerGreetingManager()

        # Statistics counters for unified status table
        self.total_comments = 0
        self.total_ai_replies = 0
        self.total_triggers = 0
        self.max_concurrent_threads = 2  # Limit concurrent threads

        # OBS Integration removed - now handled separately by OBS Tab

        # Timers - simplified
        self.cooldown_timer = QTimer()
        self.cooldown_timer.timeout.connect(self._process_queue)

        # Cleanup timer: hapus viewer_cooldowns yang sudah expired tiap 5 menit
        self._cleanup_timer = QTimer()
        self._cleanup_timer.timeout.connect(self._cleanup_cooldowns)
        self._cleanup_timer.start(5 * 60 * 1000)  # 5 menit

        # Initialize UI
        self.init_ui()

        # Setup cleanup on app exit
        QApplication.instance().aboutToQuit.connect(self.cleanup)

    def set_popup_window(self, popup_window):
        """Wire ProductPopupWindow ke cohost tab (dipanggil dari main_window)."""
        self._popup_window = popup_window

    def closeEvent(self, event):
        """Handle close event to ensure proper cleanup"""
        try:
            # Stop auto reply first
            self.stop()

            # Additional cleanup
            if hasattr(self, 'listener_thread') and self.listener_thread:
                self.listener_thread.stop()
                self.listener_thread.wait(3000)
                self.listener_thread = None

            if hasattr(self, 'tiktok_listener_thread') and self.tiktok_listener_thread:
                self.tiktok_listener_thread.stop()
                self.tiktok_listener_thread.wait(3000)
                self.tiktok_listener_thread = None

            # Clear any remaining threads
            if hasattr(self, 'active_reply_threads'):
                for thread in self.active_reply_threads:
                    if thread and thread.isRunning():
                        thread.quit()
                        thread.wait(1000)
                self.active_reply_threads.clear()

            self.log_message("INFO", "Application closing - all processes stopped")
            event.accept()

        except Exception as e:
            self.log_message("ERROR", f"Error during close: {e}")
            event.accept()

    def init_ui(self):
        """Simplified UI initialization with scroll area"""
        # Create main layout
        main_layout = QVBoxLayout()

        # Add tutorial button at the top — compact, tidak full-width
        tutorial_row = QHBoxLayout()
        tutorial_button = QPushButton("📺 Panduan Penggunaan")
        tutorial_button.setFixedHeight(36)
        tutorial_button.setFixedWidth(200)
        tutorial_button.setStyleSheet(btn_accent("font-size: 12px; padding: 4px 16px;"))
        tutorial_button.clicked.connect(self.open_tutorial)
        tutorial_row.addStretch()
        tutorial_row.addWidget(tutorial_button)
        main_layout.addLayout(tutorial_row)

        # Create scroll area for all content
        main_scroll_area = QScrollArea()
        main_scroll_area.setWidgetResizable(True)
        main_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        main_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Create content widget
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)

        # Basic controls with status indicator
        controls_group = QGroupBox("⚡ Controls")
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(12)

        self.start_button = QPushButton("▶  Mulai Auto Reply")
        self.start_button.setStyleSheet(btn_success("font-size: 13px; padding: 10px 22px; min-width: 160px;"))
        self.start_button.clicked.connect(self.start)

        self.stop_button = QPushButton("■  Stop")
        self.stop_button.setStyleSheet(btn_danger("font-size: 13px; padding: 10px 22px; min-width: 120px;"))
        self.stop_button.clicked.connect(self.stop)

        # Status indicator — pakai status_badge
        self.status_indicator = QLabel("🔴  OFF")
        self.status_indicator.setStyleSheet(status_badge(ERROR, size=13))

        status_text = QLabel("Status:")
        status_text.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")

        controls_layout.addWidget(self.start_button)
        controls_layout.addWidget(self.stop_button)
        controls_layout.addSpacing(16)
        controls_layout.addWidget(status_text)
        controls_layout.addWidget(self.status_indicator)
        controls_layout.addStretch()
        controls_group.setLayout(controls_layout)

        # Platform selection
        platform_group = QGroupBox("Platform")
        platform_layout = QVBoxLayout()

        self.platform_combo = QComboBox()
        # YouTube disabled — uncomment to re-enable: self.platform_combo.addItems(["YouTube", "TikTok"])
        self.platform_combo.addItems(["TikTok"])
        self.platform_combo.setCurrentText("TikTok")
        self.platform_combo.currentTextChanged.connect(self._update_platform_ui)
        platform_layout.addWidget(self.platform_combo)

        # YouTube Video ID input
        self.video_id_label = QLabel("YouTube Video ID:")
        platform_layout.addWidget(self.video_id_label)
        self.video_id_input = QLineEdit()
        self.video_id_input.setPlaceholderText("Enter YouTube video ID")
        self.video_id_input.setText(self.cfg.get("video_id", ""))
        platform_layout.addWidget(self.video_id_input)

        # TikTok Nickname input
        self.tiktok_label = QLabel("TikTok Nickname:")
        platform_layout.addWidget(self.tiktok_label)
        self.tiktok_input = QLineEdit()
        self.tiktok_input.setPlaceholderText("Enter TikTok username (without @)")
        self.tiktok_input.setText(self.cfg.get("tiktok_nickname", ""))
        platform_layout.addWidget(self.tiktok_input)

        platform_group.setLayout(platform_layout)

        # Update UI based on current platform
        self._update_platform_ui(self.platform_combo.currentText())

        # Context info (managed via Config tab)
        context_info = QLabel("📋 Context Setting: Diatur melalui Config Tab → Template Live Selling")
        context_info.setStyleSheet(f"color: {PRIMARY}; font-weight: bold; padding: 8px; background-color: {BG_ELEVATED}; border-radius: 6px; margin: 5px;")

        # Language & Voice Settings Group
        language_group = QGroupBox("Language & Voice Settings")
        language_layout = QVBoxLayout()

        # Language selection
        lang_layout = QHBoxLayout()
        lang_layout.addWidget(QLabel("Output Language:"))
        self.language_combo = QComboBox()
        self.language_combo.addItems(["Indonesia", "Malaysia", "English"])
        current_lang = self.cfg.get("output_language", "Indonesia")
        self.language_combo.setCurrentText(current_lang)
        self.language_combo.currentTextChanged.connect(self.on_language_changed)
        lang_layout.addWidget(self.language_combo)
        language_layout.addLayout(lang_layout)

        # Voice selection
        voice_layout = QHBoxLayout()
        voice_layout.addWidget(QLabel("Voice:"))
        self.voice_combo = QComboBox()
        self.update_voice_options(current_lang)
        voice_layout.addWidget(self.voice_combo)

        # Preview button
        self.preview_voice_btn = QPushButton("🔊 Preview")
        self.preview_voice_btn.setFixedWidth(80)
        self.preview_voice_btn.clicked.connect(self.preview_selected_voice)
        voice_layout.addWidget(self.preview_voice_btn)

        language_layout.addLayout(voice_layout)

        language_group.setLayout(language_layout)

        # Trigger & Settings Group
        settings_group = QGroupBox("🎯 Trigger & Queue Settings")
        settings_layout = QVBoxLayout()

        # Trigger words input (max 5 triggers)
        trigger_layout = QHBoxLayout()
        trigger_layout.addWidget(QLabel("Trigger Words (max 5):"))
        self.trigger_input = QLineEdit()
        existing_triggers = self.cfg.get("trigger_words", [])
        if isinstance(existing_triggers, list):
            self.trigger_input.setText(", ".join(existing_triggers))
        self.trigger_input.setPlaceholderText("bang,halo,salam,oke,dan (max 5, kosong = balas semua)")
        trigger_layout.addWidget(self.trigger_input)

        save_trigger_btn = QPushButton("💾 Save")
        save_trigger_btn.setStyleSheet(btn_ghost())
        save_trigger_btn.clicked.connect(self.save_trigger_settings)
        trigger_layout.addWidget(save_trigger_btn)
        settings_layout.addLayout(trigger_layout)

        # Trigger info label
        trigger_info = QLabel("💡 Tips: Kosongkan untuk membalas semua komentar. Tanda tanya (?) otomatis dibalas.")
        trigger_info.setStyleSheet(label_subtitle())
        settings_layout.addWidget(trigger_info)

        # Cooldown settings
        cooldown_layout = QHBoxLayout()
        cooldown_layout.addWidget(QLabel("Cooldown/Penonton (mnt):"))
        self.viewer_cooldown_spin = QSpinBox()
        self.viewer_cooldown_spin.setRange(0, 30)  # 0 = tidak ada cooldown (reply semua komentar)
        self.viewer_cooldown_spin.setValue(self.cfg.get("viewer_cooldown_minutes", 1))
        self.viewer_cooldown_spin.setSpecialValueText("Semua")  # tampilkan "Semua" saat nilai 0
        self.viewer_cooldown_spin.setToolTip(
            "0 = Balas semua komentar (cocok untuk streamer baru)\n"
            "1-5 = Batasi tiap penonton 1-5 menit sekali (cocok untuk stream ramai)"
        )
        cooldown_layout.addWidget(self.viewer_cooldown_spin)

        cooldown_layout.addWidget(QLabel("Max Antrian:"))
        self.queue_spin = QSpinBox()
        self.queue_spin.setRange(1, 50)  # naikkan max ke 50 untuk stream sangat ramai
        self.queue_spin.setValue(self.cfg.get("cohost_max_queue", 10))
        self.queue_spin.setToolTip(
            "Jumlah komentar yang menunggu giliran dibalas.\n"
            "Stream sepi: 5-10 | Stream ramai: 15-30"
        )
        cooldown_layout.addWidget(self.queue_spin)

        # Sequential Greeting Timer
        cooldown_layout.addWidget(QLabel("Greeting Timer (sec):"))
        self.greeting_timer_spin = QDoubleSpinBox()
        self.greeting_timer_spin.setRange(0.5, 999999)  # 0.5 second minimum, unlimited maximum
        self.greeting_timer_spin.setValue(self.cfg.get("sequential_greeting_interval", 180))
        self.greeting_timer_spin.setSuffix("s")
        self.greeting_timer_spin.valueChanged.connect(self.on_greeting_timer_changed)
        cooldown_layout.addWidget(self.greeting_timer_spin)
        settings_layout.addLayout(cooldown_layout)

        # Greeting Mode: Random only (Sequential removed)
        # Force random mode in config
        self.cfg.set("greeting_play_mode", "random")
        if hasattr(self, 'sequential_greeting_manager'):
            self.sequential_greeting_manager.set_play_mode("random")

        # Mode info (Random only)
        mode_info_layout = QHBoxLayout()
        mode_info = QLabel("🎲 Mode Sapaan: Random (Acak dari slot yang terisi)")
        mode_info.setStyleSheet(f"color: {SUCCESS}; font-weight: bold; font-size: 12px; padding: 5px; background-color: {BG_ELEVATED}; border-radius: 4px;")
        mode_info_layout.addWidget(mode_info)
        mode_info_layout.addStretch()
        settings_layout.addLayout(mode_info_layout)

        settings_group.setLayout(settings_layout)

        # Status display
        self.status_display = QTextEdit()
        self.status_display.setMaximumHeight(200)
        self.status_display.setReadOnly(True)

        # Comment display
        self.comment_display = QTextEdit()
        self.comment_display.setReadOnly(True)

        # Add to main layout
        layout.addWidget(controls_group)
        layout.addWidget(platform_group)
        layout.addWidget(context_info)
        layout.addWidget(language_group)
        layout.addWidget(settings_group)

        # Unified Status & Activity Table (BIG TABLE)
        status_group = QGroupBox("📊 Live Status & Activity Monitor")
        status_layout = QVBoxLayout()

        # Create comprehensive status table
        self.status_table = QTableWidget()
        self.status_table.setColumnCount(6)
        self.status_table.setHorizontalHeaderLabels([
            "🕒 Time",
            "👤 User",
            "💬 Comment",
            "🤖 AI Response",
            "🎯 Trigger",
            "📊 Status"
        ])

        # Set table properties for big display
        header = self.status_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Time
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # User
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # Comment (25%)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)  # AI Response (35%)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Trigger
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Status

        # Make table BIG as requested
        self.status_table.setMinimumHeight(400)
        self.status_table.setMaximumHeight(500)
        self.status_table.setAlternatingRowColors(True)
        self.status_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        # Enhanced table styling
        self.status_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {BG_BASE};
                color: {TEXT_PRIMARY};
                gridline-color: {BORDER};
                font-size: 12px;
                border: 2px solid {BORDER_GOLD};
                border-radius: 8px;
            }}
            QTableWidget::item {{
                padding: 8px;
                border-bottom: 1px solid {BORDER};
            }}
            QTableWidget::item:selected {{
                background-color: {PRIMARY};
                color: white;
            }}
            QTableWidget::item:alternate {{
                background-color: {BG_ELEVATED};
            }}
            QHeaderView::section {{
                background-color: {SECONDARY};
                color: {TEXT_PRIMARY};
                padding: 12px;
                border: 1px solid {BORDER_GOLD};
                font-weight: bold;
                font-size: 13px;
            }}
        """)

        status_layout.addWidget(self.status_table)

        # System Status Summary Row (below table)
        summary_layout = QHBoxLayout()

        # Connection indicators — status_badge gives bordered pill style
        self.ai_status_label = QLabel("🔴 AI: Disconnected")
        self.ai_status_label.setStyleSheet(status_badge(ERROR))

        self.listener_status_label = QLabel("🔴 Listener: Stopped")
        self.listener_status_label.setStyleSheet(status_badge(ERROR))

        self.tts_status_label = QLabel("🔴 TTS: Not Ready")
        self.tts_status_label.setStyleSheet(status_badge(ERROR))

        # Greeting status
        self.greeting_status_label = QLabel("⏹️ Greeting: Disabled")
        self.greeting_status_label.setStyleSheet(status_badge(TEXT_DIM))

        # Statistics
        self.stats_label = QLabel("📈 0 Komentar | 0 Balasan | 0 Trigger")
        self.stats_label.setStyleSheet(status_badge(INFO))

        summary_layout.addWidget(self.ai_status_label)
        summary_layout.addWidget(self.listener_status_label)
        summary_layout.addWidget(self.tts_status_label)
        summary_layout.addWidget(self.greeting_status_label)
        summary_layout.addWidget(self.stats_label)
        summary_layout.addStretch()

        status_layout.addLayout(summary_layout)
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)

        # Set content widget to main scroll area
        main_scroll_area.setWidget(content_widget)

        # Add main scroll area to main layout
        main_layout.addWidget(main_scroll_area)

        self.setLayout(main_layout)

        # Initialize status display
        self.update_status_summary()

    def _update_platform_ui(self, platform):
        """Update UI based on selected platform"""
        if platform == "YouTube":
            self.video_id_label.setVisible(True)
            self.video_id_input.setVisible(True)
            self.tiktok_label.setVisible(False)
            self.tiktok_input.setVisible(False)
        elif platform == "TikTok":
            self.video_id_label.setVisible(False)
            self.video_id_input.setVisible(False)
            self.tiktok_label.setVisible(True)
            self.tiktok_input.setVisible(True)

        # Save platform selection
        self.cfg.set("platform", platform)

    def on_language_changed(self, language):
        """Handle language selection change"""
        self.cfg.set("output_language", language)

        # Map UI language to AI language setting
        ai_language_map = {
            "Indonesia": "indonesian",
            "Malaysia": "malaysian",
            "English": "english"
        }

        ai_language = ai_language_map.get(language, "indonesian")
        self.cfg.set("ai_language", ai_language)

        # Update voice options based on selected language (FIXED: Malaysia uses Malaysia voices)
        self.update_voice_options(language)

        self.log_message("INFO", f"Output language changed to: {language}")
        self.log_message("INFO", f"AI language set to: {ai_language}")

    def update_voice_options(self, language):
        """Update voice options based on selected language using voices.json"""
        self.voice_combo.clear()

        # Baca tipe key yang sudah dideteksi di Config tab
        key_type = self.cfg.get("tts_key_type", "all")  # "gemini" | "cloud" | "all"

        try:
            # Load voices from voices.json
            voices_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "voices.json")
            with open(voices_file, 'r', encoding='utf-8') as f:
                voices_data = json.load(f)

            # Tentukan section yang ditampilkan berdasarkan tipe key
            if key_type == "gemini":
                id_sections  = ["gemini_flash"]
                my_sections  = ["gemini_flash"]
                en_sections  = ["gemini_flash"]
            elif key_type == "cloud":
                id_sections  = ["gtts_standard", "gtts_wavenet", "chirp3"]
                my_sections  = ["gtts_standard", "chirp3"]
                en_sections  = ["gtts_standard", "chirp3"]
            else:  # "all" atau belum dideteksi
                id_sections  = ["gtts_standard", "gtts_wavenet", "chirp3", "gemini_flash"]
                my_sections  = ["gtts_standard", "chirp3", "gemini_flash"]
                en_sections  = ["gtts_standard", "chirp3"]

            voices = []
            if language == "Indonesia":
                for voice_type in id_sections:
                    if voice_type in voices_data and "id-ID" in voices_data[voice_type]:
                        for voice in voices_data[voice_type]["id-ID"]:
                            voices.append(f"{voice['model']} ({voice['gender']})")

            elif language == "Malaysia":
                for voice_type in my_sections:
                    if voice_type in voices_data and "ms-MY" in voices_data[voice_type]:
                        for voice in voices_data[voice_type]["ms-MY"]:
                            voices.append(f"{voice['model']} ({voice['gender']})")

            else:  # English
                for lang_code in ["en-US", "en-GB", "en-AU", "en-IN"]:
                    for voice_type in en_sections:
                        if voice_type in voices_data and lang_code in voices_data[voice_type]:
                            for voice in voices_data[voice_type][lang_code]:
                                voices.append(f"{voice['model']} ({voice['gender']})")
                # Gemini voices for English (hanya jika tidak mode cloud-only)
                if key_type != "cloud" and "gemini_flash" in voices_data and "en-US" in voices_data["gemini_flash"]:
                    for voice in voices_data["gemini_flash"]["en-US"]:
                        voices.append(f"{voice['model']} ({voice['gender']})")

            # Fallback to default voices if loading fails
            if not voices:
                if language == "Indonesia":
                    voices = ["id-ID-Standard-A (FEMALE)", "id-ID-Standard-B (MALE)"]
                elif language == "Malaysia":
                    voices = ["ms-MY-Standard-A (FEMALE)", "ms-MY-Standard-B (MALE)"]
                else:
                    voices = ["en-US-Standard-A (MALE)", "en-US-Standard-C (FEMALE)"]

        except Exception as e:
            self.log_message("ERROR", f"Error loading voices: {e}")
            # Fallback voices
            if language == "Indonesia":
                voices = ["id-ID-Standard-A (FEMALE)", "id-ID-Standard-B (MALE)"]
            else:
                voices = ["en-US-Standard-A (MALE)", "en-US-Standard-C (FEMALE)"]

        self.voice_combo.addItems(voices)

        # Set saved voice — jika tidak ada di list (misal voice dihapus), reset ke voice pertama
        saved_voice = self.cfg.get("tts_voice", voices[0])
        if saved_voice in voices:
            self.voice_combo.setCurrentText(saved_voice)
        else:
            self.voice_combo.setCurrentIndex(0)
            self.cfg.set("tts_voice", voices[0])
            self.log_message("INFO", f"Voice tersimpan '{saved_voice}' tidak tersedia, reset ke: {voices[0]}")

        # Disconnect dulu agar tidak double-connect saat update_voice_options dipanggil ulang
        try:
            self.voice_combo.currentTextChanged.disconnect(self.on_voice_changed)
        except TypeError:
            pass  # Belum terhubung — tidak apa-apa
        self.voice_combo.currentTextChanged.connect(self.on_voice_changed)

    def on_voice_changed(self, voice):
        """Handle voice selection change"""
        self.cfg.set("tts_voice", voice)
        self.log_message("INFO", f"TTS voice changed to: {voice}")

    def preview_selected_voice(self):
        """Preview the currently selected voice with sample text"""
        try:
            selected_voice = self.voice_combo.currentText()
            if not selected_voice:
                self.log_message("WARN", "No voice selected for preview")
                return

            # Disable preview button during playback
            self.preview_voice_btn.setEnabled(False)
            self.preview_voice_btn.setText("🔊 Playing...")

            # Extract voice model name (remove gender part)
            # Format: "en-IN-Chirp3-HD-Pulcherrima (FEMALE)" -> "en-IN-Chirp3-HD-Pulcherrima"
            voice_model = selected_voice.split('(')[0].strip()

            # Extract language code from voice model name
            # Examples: "en-IN-...", "ms-MY-...", "id-ID-...", "Gemini-..."
            language_code = "id-ID"  # Default to Indonesian
            sample_text = "Halo, ini adalah contoh suara untuk preview."  # Default Indonesian sample

            # Check if this is a Gemini voice
            if voice_model.startswith('Gemini-'):
                # Gemini voices are multilingual — use sample text sesuai bahasa yang dipilih user
                current_lang = self.cfg.get("language", "Indonesia")
                if current_lang == "Malaysia":
                    language_code = "ms-MY"
                    sample_text = "Helo, ini adalah contoh suara untuk preview. Selamat datang!"
                elif current_lang == "English":
                    language_code = "en-US"
                    sample_text = "Hello, this is a voice preview sample. Welcome!"
                else:
                    language_code = "id-ID"
                    sample_text = "Halo, ini adalah contoh suara untuk preview. Selamat datang!"
            elif '-' in voice_model:
                parts = voice_model.split('-')
                if len(parts) >= 2:
                    # Get language code (e.g., "en-IN", "ms-MY", "id-ID")
                    language_code = f"{parts[0]}-{parts[1]}"

                    # Set appropriate sample text based on language code
                    if language_code.startswith('id-'):
                        sample_text = "Halo, ini adalah contoh suara Indonesia untuk preview."
                    elif language_code.startswith('ms-'):
                        sample_text = "Halo, ini adalah contoh suara Malaysia untuk preview."
                    elif language_code.startswith('en-'):
                        sample_text = "Hello, this is a voice preview sample."
                    else:
                        sample_text = "Halo, ini adalah contoh suara untuk preview."

            self.log_message("INFO", f"Playing voice preview: {selected_voice}")

            def on_preview_finished():
                """Callback when preview finished"""
                self.preview_voice_btn.setEnabled(True)
                self.preview_voice_btn.setText("🔊 Preview")
                self.log_message("INFO", "Voice preview completed")

            # Play TTS preview with Google TTS only (avoid dual playback)
            success = speak(
                text=sample_text,
                voice_name=voice_model,
                language_code=language_code,
                on_finished=on_preview_finished,
                force_google_tts=True
            )

            if not success:
                self.log_message("ERROR", f"Failed to preview voice: {selected_voice}")
                on_preview_finished()  # Re-enable button

        except Exception as e:
            self.log_message("ERROR", f"Voice preview error: {e}")
            self.preview_voice_btn.setEnabled(True)
            self.preview_voice_btn.setText("🔊 Preview")

    def save_trigger_settings(self):
        """Save trigger words and cooldown settings with max 5 limit"""
        try:
            # Save trigger words with proper persistence
            trigger_text = self.trigger_input.text().strip()
            if trigger_text:
                trigger_words = [word.strip() for word in trigger_text.split(',') if word.strip()]
                # Limit to max 5 triggers
                if len(trigger_words) > 5:
                    trigger_words = trigger_words[:5]
                    self.trigger_input.setText(", ".join(trigger_words))
                    self.log_message("WARN", "Trigger dibatasi maksimal 5, kelebihan dihapus")
                self.cfg.set("trigger_words", trigger_words)
            else:
                self.cfg.set("trigger_words", [])

            # FORCE SAVE to disk to ensure persistence
            self.cfg.save()

            # Save cooldown settings
            self.cfg.set("viewer_cooldown_minutes", self.viewer_cooldown_spin.value())
            self.cfg.set("cohost_max_queue", self.queue_spin.value())

            # Update queue max size
            self.reply_queue = deque(maxlen=self.queue_spin.value())

            # Save greeting timer setting
            greeting_timer = self.greeting_timer_spin.value()
            self.cfg.set("sequential_greeting_interval", greeting_timer)

            # Update sequential greeting manager if exists
            if hasattr(self, 'sequential_greeting_manager'):
                self.sequential_greeting_manager.set_greeting_interval(greeting_timer)

            self.log_message("INFO", f"Settings saved: Triggers={trigger_words if trigger_text else 'None'}, Cooldown={self.cooldown_spin.value()}s, Queue={self.queue_spin.value()}, GreetingTimer={greeting_timer}s")

        except Exception as e:
            self.log_message("ERROR", f"Failed to save settings: {e}")

    def on_greeting_timer_changed(self, value):
        """Handle greeting timer spinbox change"""
        try:
            # Save to config
            self.cfg.set("sequential_greeting_interval", value)

            # Update sequential greeting manager if exists
            if hasattr(self, 'sequential_greeting_manager'):
                self.sequential_greeting_manager.set_greeting_interval(value)

            self.log_message("INFO", f"Greeting timer updated to {value} seconds ({value/60:.1f} minutes)")

        except Exception as e:
            self.log_message("ERROR", f"Failed to update greeting timer: {e}")

    def on_greeting_mode_changed(self, mode_text=None):
        """Handle greeting mode - Always use Random mode"""
        try:
            # Always use random mode (sequential removed)
            mode = "random"

            # Save to config
            self.cfg.set("greeting_play_mode", mode)

            # Update sequential greeting manager if exists
            if hasattr(self, 'sequential_greeting_manager'):
                self.sequential_greeting_manager.set_play_mode(mode)

            self.log_message("INFO", "Greeting mode: Random")

        except Exception as e:
            self.log_message("ERROR", f"Failed to update greeting mode: {e}")

    def update_status_indicator(self, is_active):
        """Update the status indicator lamp"""
        if is_active:
            self.status_indicator.setText("🟢  ON — Active")
            self.status_indicator.setStyleSheet(status_badge(SUCCESS, size=13))
        else:
            self.status_indicator.setText("🔴  OFF")
            self.status_indicator.setStyleSheet(status_badge(ERROR, size=13))

    def start(self):
        """Start simplified listener"""
        # PERFORMANCE FIX: Prevent multiple simultaneous starts
        if hasattr(self, '_is_starting') and self._is_starting:
            self.log_message("WARNING", "Start already in progress, please wait...")
            return

        # Set starting flag
        self._is_starting = True

        # Disable start button during startup
        self.start_button.setEnabled(False)
        self.start_button.setText("Starting...")

        try:
            platform = self.platform_combo.currentText()

            # Stop existing listeners first (force cleanup)
            self.stop()

            # YouTube disabled — platform is TikTok only
            # To re-enable YouTube, uncomment the block below and restore the dropdown
            # if platform == "YouTube":
            #     video_id = self.video_id_input.text().strip()
            #     if not video_id:
            #         self.log_message("ERROR", "Please enter a YouTube video ID")
            #         return
            #     self.cfg.set("video_id", video_id)
            #     if self.analytics:
            #         try:
            #             self.analytics.start_session(platform="youtube")
            #         except Exception as e:
            #             self.logger.error(f"Failed to start analytics: {e}")
            #     self.listener_thread = SimpleListener(video_id)
            #     self.listener_thread.newComment.connect(self.handle_comment)
            #     self.listener_thread.logMessage.connect(self.log_message)
            #     self.listener_thread.start()
            #     self.log_message("INFO", f"Started YouTube listener for video: {video_id}")
            # else:  # TikTok
            if True:  # TikTok only
                username = self.tiktok_input.text().strip()
                if not username:
                    self.log_message("ERROR", "Please enter a TikTok username")
                    return

                # Save TikTok username
                self.cfg.set("tiktok_nickname", username)

                # Start analytics session
                if self.analytics:
                    try:
                        self.analytics.start_session(platform="tiktok")
                        self.log_message("INFO", "Analytics session started")
                    except Exception as e:
                        self.logger.error(f"Failed to start analytics: {e}")

                # Start TikTok listener immediately (no delay needed)
                self.tiktok_listener_thread = SimpleTikTokListener(username)
                self.tiktok_listener_thread.newComment.connect(self.handle_comment)
                self.tiktok_listener_thread.viewerJoined.connect(self.handle_viewer_join)
                self.tiktok_listener_thread.logMessage.connect(self.log_message)
                self.tiktok_listener_thread.start()

                self.log_message("INFO", f"Started TikTok listener for @{username}")

                # Start old viewer greeting system if enabled (for backward compatibility)
                self.viewer_greeting_manager.start_greeting_system()

            # Start new sequential greeting system
            if hasattr(self, 'sequential_greeting_manager'):
                self.sequential_greeting_manager.start()

            # Keep old custom greeting system for fallback
            if hasattr(self, 'custom_greeting_manager'):
                # Don't start the old system, let sequential handle it
                pass

            # Update status indicator
            self.update_status_indicator(True)

            # Telemetry: listener started
            try:
                from modules_client.telemetry import capture as _tel_capture
                _tel_capture("listener_started", {"platform": "tiktok", "username": username})
            except Exception:
                pass

            # Start queue processing
            self.cooldown_timer.start(2000)  # Process every 2 seconds

        finally:
            # Re-enable start button
            self._is_starting = False
            self.start_button.setEnabled(True)
            self.start_button.setText("Start")

    def stop(self):
        """Stop all processes - with proper TikTok cleanup for restart support"""
        # Telemetry: listener stopped
        try:
            from modules_client.telemetry import capture as _tel_capture
            _tel_capture("listener_stopped", {})
        except Exception:
            pass

        # Stop timer
        self.cooldown_timer.stop()

        # Stop YouTube listener - immediate terminate
        if self.listener_thread:
            self.listener_thread.stop()
            self.listener_thread.terminate()
            self.listener_thread.wait(500)  # Wait up to 500ms for cleanup
            self.listener_thread = None

        # Stop TikTok listener - fast cleanup for quick restart
        if self.tiktok_listener_thread:
            self.tiktok_listener_thread.stop()
            self.tiktok_listener_thread.terminate()
            # Brief wait — thread sudah di-terminate, tidak perlu lama
            self.tiktok_listener_thread.wait(300)  # 300ms cukup untuk cleanup
            self.tiktok_listener_thread = None

        # Process Qt events to ensure cleanup is complete
        from PyQt6.QtWidgets import QApplication
        QApplication.processEvents()

        # End analytics session
        if self.analytics:
            try:
                self.analytics.end_session()
                self.log_message("INFO", "Analytics session ended and saved")
            except Exception as e:
                self.logger.error(f"Failed to end analytics: {e}")

        # Stop viewer greeting system
        self.viewer_greeting_manager.stop_greeting_system()

        # Stop sequential greeting system
        if hasattr(self, 'sequential_greeting_manager'):
            self.sequential_greeting_manager.stop()

        # Stop custom greeting system
        if hasattr(self, 'custom_greeting_manager'):
            self.custom_greeting_manager.stop()

        # Clean up reply threads (non-blocking)
        for thread in self.active_reply_threads[:]:
            if thread.isRunning():
                thread.quit()
                # Don't wait - let threads finish naturally
        self.active_reply_threads.clear()

        # Update status indicator
        self.update_status_indicator(False)

        self.log_message("INFO", "Stopped all processes")

    def add_comment_to_display(self, username, message, comment_type="normal", ai_response=None):
        """Add comment to display — delegates to add_status_entry (comments_table dihapus dari UI)"""
        try:
            # comments_table tidak ada lagi di init_ui; gunakan status_table via add_status_entry
            # comment_type "trigger" sudah ditandai oleh add_status_entry secara terpisah
            pass  # Tampilan sudah dihandle di handle_comment() → add_status_entry()

            # ── legacy block di bawah ini dinonaktifkan ────────────────────────────────
            # row_position = self.comments_table.rowCount()   # AttributeError: no comments_table
        except Exception as e:
            self.log_message("ERROR", f"Error adding comment to display: {e}")

    def update_ai_response_in_table(self, username, message, ai_response):
        """No-op — update AI response ditangani oleh update_status_entry_with_ai_response"""
        pass

    def scroll_to_bottom(self):
        """Scroll comments area to bottom"""
        try:
            scroll_area = self.comments_widget.parent()
            if hasattr(scroll_area, 'verticalScrollBar'):
                scroll_area.verticalScrollBar().setValue(scroll_area.verticalScrollBar().maximum())
        except Exception:
            pass

    def handle_comment(self, author, message):
        """Handle incoming comment - simplified"""
        self.comment_counter += 1
        self.total_comments += 1

        # Track recent messages for anti-spam
        self.recent_messages.append(message)

        # Display comment in unified status table
        self.add_status_entry(author, message)

        # Add to colored display (keep for backward compatibility)
        self.add_comment_to_display(author, message, "normal")

        # Track analytics (lightweight operation)
        if self.analytics:
            try:
                self.analytics.track_comment(author, message, replied=False)
            except Exception as e:
                self.logger.error(f"Analytics tracking error: {e}")

        # Emit signal to Unified Processor for centralized processing
        # This prevents double processing - unified processor handles both Cohost and OBS triggers
        self.process_comment_signal.emit(author, message)

        # DISABLED: Internal processing to prevent double replies
        # All processing is now handled by UnifiedProcessor in main_window.py
        # This ensures no duplicate TTS responses

    def generate_cohost_reply(self, author, message, is_vip=False):
        """Generate Cohost reply - called by UnifiedProcessor only"""
        try:
            self.add_comment_to_display(author, message, "trigger")
            self.add_to_queue(author, message, is_vip=is_vip)
            if hasattr(self, 'custom_greeting_manager'):
                self.custom_greeting_manager.add_trigger(author, message, "reply_pending")
        except Exception as e:
            self.logger.error(f"Error in generate_cohost_reply: {e}")

    def display_comment(self, author, message):
        """Display comment in UI"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        comment_text = f"[{timestamp}] {author}: {message}\n"

        self.comment_display.append(comment_text)

        # Keep display manageable
        if self.comment_display.document().blockCount() > 100:
            cursor = self.comment_display.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
            cursor.removeSelectedText()

    def check_trigger(self, message):
        """Check if message contains trigger words — gunakan cache config, tidak reload dari disk"""
        try:
            triggers = self.cfg.get("trigger_words", [])

            self.logger.info(f"[COHOST TRIGGER] Real-time loaded triggers: {triggers}")

            # If no triggers set, reply to all comments
            if not triggers:
                self.logger.info("[COHOST TRIGGER] No triggers set, replying to all comments")
                return True

            message_lower = message.lower()

            # ONLY check for configured trigger words (including "?" if user added it)
            # No automatic "?" trigger - only if explicitly set by user
            for trigger in triggers:
                if trigger.lower() == "?" and "?" in message:
                    # User explicitly set "?" as trigger
                    self.logger.info(f"[COHOST TRIGGER] User-defined '?' trigger matched: {message}")
                    return True
                elif trigger.lower() != "?" and trigger.lower() in message_lower:
                    # Regular word triggers
                    self.logger.info(f"[COHOST TRIGGER] Trigger '{trigger}' matched in: {message}")
                    return True

            self.logger.info(f"[COHOST TRIGGER] No trigger matched for: {message}")
            return False
        except Exception as e:
            self.logger.error(f"Error checking trigger: {e}")
            return True  # Default to responding if config fails


    def add_to_queue(self, author, message, is_vip=False):
        """Add comment to reply queue — VIP user bypass cooldown sepenuhnya"""
        # Toxic filter (berlaku untuk semua, termasuk VIP)
        if self.is_toxic(message):
            logger.debug("[COHOST] Filtered out: user=%s, reason=%s", author, "toxic")
            self.log_message("WARN", f"Toxic content from {author}, ignored")
            return

        # Spam filter — VIP bypass
        if not is_vip and self.is_spam(author, message):
            logger.debug("[COHOST] Filtered out: user=%s, reason=%s", author, "spam")
            self.log_message("WARN", f"Spam from {author}, ignored")
            return

        # Cooldown check — VIP bypass; cooldown=0 berarti reply semua
        now = time.time()
        viewer_cooldown_seconds = self.cfg.get("viewer_cooldown_minutes", 1) * 60
        if not is_vip and viewer_cooldown_seconds > 0:
            if author in self.viewer_cooldowns:
                if now - self.viewer_cooldowns[author] < viewer_cooldown_seconds:
                    logger.debug("[COHOST] Filtered out: user=%s, reason=%s", author, "cooldown")
                    return

        logger.debug("[COHOST] Filter passed: user=%s", author)
        self.viewer_cooldowns[author] = now
        self.reply_queue.append((author, message, now))
        label = "⭐ VIP" if is_vip else author
        self.log_message("INFO", f"Queued: {label}")

    def _process_queue(self):
        """Process reply queue — satu item per satu TTS (serialized pipeline)"""
        # reply_busy = True artinya TTS sedang bermain; tunggu sampai selesai
        if self.reply_busy or not self.reply_queue:
            return

        # Bersihkan thread yang sudah selesai SEBELUM hitung
        self.active_reply_threads = [t for t in self.active_reply_threads if t.isRunning()]

        # Batasi AI calls concurrent (max 1 untuk menjaga urutan TTS)
        if self.active_reply_threads:
            return

        # Ambil item berikutnya dari queue
        queue_item = self.reply_queue.popleft()
        if len(queue_item) == 4:
            author, message, timestamp, is_greeting = queue_item
        else:
            author, message, timestamp = queue_item
            is_greeting = False

        # Notify sequential greeting system about trigger start
        if hasattr(self, 'sequential_greeting_manager'):
            self.sequential_greeting_manager.on_trigger_start()

        current_language = self.language_combo.currentText()
        reply_thread = SimpleReplyThread(author, message, is_greeting=is_greeting, language=current_language)
        reply_thread.finished.connect(self.handle_reply)
        reply_thread.start()
        self.active_reply_threads.append(reply_thread)

        self.log_message("INFO", f"Processing reply for: {author}")

    def clean_ai_response(self, text):
        """Clean AI response completely for natural TTS - remove ALL formatting and symbols"""
        import re

        # Remove ALL markdown formatting
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # **bold**
        text = re.sub(r'\*(.*?)\*', r'\1', text)      # *italic*
        text = re.sub(r'__(.*?)__', r'\1', text)      # __underline__
        text = re.sub(r'_(.*?)_', r'\1', text)        # _underline_
        text = re.sub(r'`(.*?)`', r'\1', text)        # `code`
        text = re.sub(r'~~(.*?)~~', r'\1', text)      # ~~strikethrough~~

        # Remove ALL emojis and emoticons completely
        text = re.sub(r'[😀-🙏🌀-🗿🚀-🛿🇀-🇿💀-💿]+', '', text)  # Unicode emojis
        text = re.sub(r'[:;=8xX]-?[)\]}>dDpP(\[{<|\\/@#$%^&*oO0]', '', text)  # ASCII emoticons
        text = re.sub(r'[)\]}>dDpP(\[{<|\\/@#$%^&*oO0]-?[:;=8xX]', '', text)  # Reverse emoticons

        # Remove excessive punctuation but keep natural sentence flow
        text = re.sub(r'[!]{2,}', '.', text)         # !!! -> .
        text = re.sub(r'[?]{2,}', '?', text)         # ??? -> ?
        text = re.sub(r'[.]{2,}', '.', text)         # ... -> .
        text = re.sub(r'[,]{2,}', ',', text)         # ,, -> ,

        # Remove special symbols that TTS reads weirdly
        text = re.sub(r'[~#$%^&*+={}[\]|\\<>]', '', text)  # Remove special chars
        text = re.sub(r'[@]', ' at ', text)          # @ -> "at"
        text = re.sub(r'[/]', ' atau ', text)        # / -> "atau"

        # Remove quotes and parentheses (TTS reads them literally)
        text = re.sub(r'["\'""`]', '', text)         # Remove all quotes
        text = re.sub(r'[()[\]{}]', '', text)        # Remove brackets

        # Clean up numbers and symbols that sound weird in TTS
        text = re.sub(r'(\d+)%', r'\1 persen', text) # 50% -> "50 persen"
        text = re.sub(r'(\d+)\+', r'\1 lebih', text) # 18+ -> "18 lebih"

        # Clean up extra spaces and normalize
        text = re.sub(r'\s+', ' ', text).strip()

        # Ensure natural sentence ending for TTS
        if text and not text.endswith('.') and not text.endswith('!') and not text.endswith('?'):
            text = text + '.'

        # Add slight pause for natural TTS flow
        text = ' ' + text.strip() + ' '

        return text

    def handle_reply(self, author, message, reply, scene_id=0):
        """Handle generated reply — display + TTS (non-blocking)"""
        # Jangan TTS-kan error message dari AI
        if reply.startswith("ERROR:") or reply.lower().startswith("error"):
            self.log_message("ERROR", f"AI error untuk {author}, skip TTS: {reply[:80]}")
            return

        clean_reply = self.clean_ai_response(reply)
        logger.info("[COHOST] Reply generated: user=%s, reply_len=%d, scene_id=%d", author, len(clean_reply), scene_id)

        # Tampilkan balasan di log
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.comment_display.append(f"[{timestamp}] AI → {author}: {clean_reply}\n")
        self.update_status_entry_with_ai_response(author, clean_reply)

        # Emit overlay signal sebelum TTS agar teks muncul bersamaan dengan suara
        self.replyGenerated.emit(author, message, clean_reply)

        # Trigger product popup jika ada scene_id dan fitur diaktifkan user
        if scene_id > 0 and self._popup_window is not None:
            try:
                from modules_client.product_scene_manager import ProductSceneManager
                if self._psm_cache is None:
                    self._psm_cache = ProductSceneManager()
                else:
                    self._psm_cache.reload()
                if not self._psm_cache.get_enabled():
                    self.logger.info("[POPUP] Popup dilewati — fitur dimatikan user")
                else:
                    scene = self._psm_cache.get_scene_by_id(scene_id)
                    if scene and scene.get('video_path'):
                        # Set telemetry scene info before showing product
                        self._popup_window._tel_scene_id = scene_id
                        self._popup_window._tel_scene_name = scene.get('name', '')
                        self._popup_window.show_product(scene['video_path'])
                        self.logger.info(f"[POPUP] Popup: scene_id={scene_id}, name={scene.get('name')}")
            except Exception as e:
                self.logger.warning(f"[POPUP] Popup error: {e}")

        if self.analytics:
            try:
                self.analytics.mark_replied(author)
            except Exception as e:
                self.logger.error(f"Analytics error: {e}")

        # Set busy SEBELUM mulai TTS — queue tidak akan diproses sampai TTS selesai
        self.reply_busy = True
        self.do_tts(clean_reply)
        self.log_message("INFO", f"Reply → {author}")

    def do_tts(self, text):
        """Mulai TTS di background thread — GUI tidak freeze"""
        try:
            selected_voice = self.cfg.get("tts_voice", "id-ID-Standard-A")
            voice_model = selected_voice.split('(')[0].strip()
            output_language = self.cfg.get("output_language", "Indonesia")

            if voice_model.startswith("Gemini-"):
                lang_map = {"Indonesia": "id-ID", "Malaysia": "ms-MY", "English": "en-US"}
                language_code = lang_map.get(output_language, "id-ID")
            elif '-' in voice_model:
                parts = voice_model.split('-')
                language_code = f"{parts[0]}-{parts[1]}" if len(parts) >= 2 else "id-ID"
            else:
                language_code = "id-ID"

            self._tts_thread = TTSThread(text, voice_model, language_code)
            self._tts_thread.finished.connect(self._on_tts_finished)
            self._tts_thread.start()
            logger.info("[COHOST] TTS queued: reply_len=%d", len(text))
            self.log_message("TTS", f"Speaking: {voice_model}")

        except Exception as e:
            self.log_message("ERROR", f"TTS error: {e}")
            self.reply_busy = False  # Pastikan queue tidak terkunci selamanya

    def _on_tts_finished(self):
        """Dipanggil saat TTSThread selesai — buka kunci queue"""
        try:
            self.ttsFinished.emit()
            if hasattr(self, 'sequential_greeting_manager'):
                self.sequential_greeting_manager.on_trigger_complete()
        except Exception as e:
            self.log_message("ERROR", f"TTS finished callback: {e}")
        finally:
            self.reply_busy = False  # Buka kunci — queue bisa proses item berikutnya

    def log_message(self, level, message):
        """Log message to status display"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_text = f"[{timestamp}] {level}: {message}\n"

        self.status_display.append(log_text)

        # Keep log manageable
        if self.status_display.document().blockCount() > 50:
            cursor = self.status_display.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
            cursor.removeSelectedText()

    def is_spam(self, author, message):
        """Simple anti-spam check"""
        try:
            # Check for repeated messages (relaxed for trigger testing)
            recent_count = sum(1 for msg in self.recent_messages if msg == message)
            if recent_count >= 5:  # Increased from 3 to 5 to allow more trigger testing
                return True

            # Check for excessive caps
            if len(message) > 10 and message.isupper():
                return True

            # Check for excessive repeated characters
            if re.search(r'(.)\1{4,}', message):
                return True

            return False
        except Exception:
            return False

    def is_toxic(self, message):
        """Simple toxic content filter"""
        try:
            toxic_words = self.cfg.get("toxic_words", [
                "toxic", "spam", "hate", "stupid", "idiot", "fool",
                "bodoh", "tolol", "goblok", "bangsat", "anjing"
            ])

            message_lower = message.lower()
            for word in toxic_words:
                if word.lower() in message_lower:
                    return True

            return False
        except Exception:
            return False

    def _cleanup_cooldowns(self):
        """Hapus viewer_cooldowns yang sudah expired — cegah memory leak di stream panjang"""
        try:
            now = time.time()
            max_cooldown = self.cfg.get("viewer_cooldown_minutes", 1) * 60
            # Pertahankan hanya entry yang masih dalam window cooldown
            self.viewer_cooldowns = {
                author: ts for author, ts in self.viewer_cooldowns.items()
                if now - ts < max_cooldown
            }
        except Exception as e:
            self.logger.warning(f"Cooldown cleanup error: {e}")

    def add_status_entry(self, author, message, ai_response="", trigger="", status="Received"):
        """Add entry to unified status table"""
        try:
            current_time = datetime.now().strftime("%H:%M:%S")

            # Insert new row at the top
            self.status_table.insertRow(0)

            # Add data to columns
            self.status_table.setItem(0, 0, QTableWidgetItem(current_time))
            self.status_table.setItem(0, 1, QTableWidgetItem(author or "System"))
            self.status_table.setItem(0, 2, QTableWidgetItem(message[:100] + "..." if len(message) > 100 else message))
            self.status_table.setItem(0, 3, QTableWidgetItem(ai_response[:300] + "..." if len(ai_response) > 300 else ai_response))
            self.status_table.setItem(0, 4, QTableWidgetItem(trigger))

            # Color-code status
            status_item = QTableWidgetItem(status)
            if status == "AI Reply":
                status_item.setBackground(QColor(SUCCESS))
            elif status == "Triggered":
                status_item.setBackground(QColor(WARNING))
            elif status == "Error":
                status_item.setBackground(QColor(ERROR))
            elif status == "Filtered":
                status_item.setBackground(QColor(TEXT_DIM))
            else:
                status_item.setBackground(QColor(INFO))

            self.status_table.setItem(0, 5, status_item)

            # Keep only last 100 entries for performance
            if self.status_table.rowCount() > 100:
                self.status_table.removeRow(100)

            # Update statistics
            self.update_status_summary()

        except Exception as e:
            print(f"Error adding status entry: {e}")

    def update_status_entry_with_ai_response(self, author, ai_response):
        """Update the most recent entry with AI response"""
        try:
            # Find the most recent entry for this author
            for row in range(min(10, self.status_table.rowCount())):  # Check last 10 entries
                user_item = self.status_table.item(row, 1)
                if user_item and user_item.text() == author:
                    # Update AI response column
                    ai_item = QTableWidgetItem(ai_response[:300] + "..." if len(ai_response) > 300 else ai_response)
                    self.status_table.setItem(row, 3, ai_item)

                    # Update status
                    status_item = QTableWidgetItem("AI Reply")
                    status_item.setBackground(QColor(SUCCESS))
                    self.status_table.setItem(row, 5, status_item)

                    self.total_ai_replies += 1
                    self.update_status_summary()
                    break

        except Exception as e:
            print(f"Error updating status with AI response: {e}")

    def update_status_summary(self):
        """Update the status summary indicators"""
        try:
            # Update connection status indicators
            if hasattr(self, 'ai_status_label'):
                # AI status based on API key configuration
                ai_provider = self.cfg.get("ai_provider", "deepseek").lower()
                api_keys = self.cfg.get("api_keys", {})

                # Check if AI has valid API key
                ai_configured = False
                if ai_provider == "deepseek":
                    ai_configured = bool(api_keys.get("DEEPSEEK_API_KEY", "").strip())
                elif ai_provider == "gemini":
                    ai_configured = bool(api_keys.get("GEMINI_API_KEY", "").strip())
                elif ai_provider == "chatgpt":
                    ai_configured = bool(api_keys.get("OPENAI_API_KEY", "").strip())

                if ai_configured:
                    self.ai_status_label.setText("🟢 AI: Ready")
                    self.ai_status_label.setStyleSheet(status_badge(SUCCESS))
                else:
                    self.ai_status_label.setText("🔴 AI: Not Ready")
                    self.ai_status_label.setStyleSheet(status_badge(ERROR))

            if hasattr(self, 'listener_status_label'):
                # Check listener status
                is_running = (self.listener_thread and self.listener_thread.isRunning()) or (self.tiktok_listener_thread and self.tiktok_listener_thread.isRunning())
                if is_running:
                    self.listener_status_label.setText("🟢 Listener: Active")
                    self.listener_status_label.setStyleSheet(status_badge(SUCCESS))
                else:
                    self.listener_status_label.setText("🔴 Listener: Stopped")
                    self.listener_status_label.setStyleSheet(status_badge(ERROR))

            if hasattr(self, 'tts_status_label'):
                # TTS status based on API key or credentials file
                tts_api_key = self.cfg.get("google_tts_api_key", "").strip()
                tts_file = self.cfg.get("google_tts_credentials", "")

                # Check if either API key or credentials file exists
                if (tts_api_key) or (tts_file and os.path.exists(tts_file)):
                    self.tts_status_label.setText("🟢 TTS: Ready")
                    self.tts_status_label.setStyleSheet(status_badge(SUCCESS))
                else:
                    self.tts_status_label.setText("🔴 TTS: Not Ready")
                    self.tts_status_label.setStyleSheet(status_badge(ERROR))

            if hasattr(self, 'stats_label'):
                # Update statistics
                self.stats_label.setText(f"📈 Comments: {self.total_comments} | AI Replies: {self.total_ai_replies} | Triggers: {self.total_triggers}")

        except Exception as e:
            print(f"Error updating status summary: {e}")

    def open_tutorial(self):
        """Open tutorial video in browser"""
        import webbrowser
        tutorial_url = "https://streammate-ai-seller.lovable.app/"
        try:
            webbrowser.open(tutorial_url)
            self.log_message("INFO", "Tutorial video opened in browser")
        except Exception as e:
            self.log_message("ERROR", f"Failed to open tutorial: {e}")

    def _clean_ai_response(self, raw_text):
        """Clean AI response from emojis, formatting, and special chars for TTS"""
        if not raw_text:
            return ""

        import re

        text = raw_text.strip()

        # Remove ALL markdown formatting
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # **bold**
        text = re.sub(r'\*(.*?)\*', r'\1', text)      # *italic*
        text = re.sub(r'__(.*?)__', r'\1', text)      # __underline__
        text = re.sub(r'_(.*?)_', r'\1', text)        # _underline_
        text = re.sub(r'`(.*?)`', r'\1', text)        # `code`
        text = re.sub(r'~~(.*?)~~', r'\1', text)      # ~~strikethrough~~

        # Remove ALL emojis and emoticons completely for clean TTS
        text = re.sub(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002600-\U000027BF\U0001F900-\U0001F9FF\U00002700-\U000027BF\U00002B00-\U00002BFF\U00002934-\U00002935\U000025A0-\U000025FF\U0001F170-\U0001F251\U00002000-\U0000206F\U0001F004\U0001F0CF\U0001F18E\U0001F191-\U0001F251\U00002764\U00002763\U0001F494\U0001F495\U0001F496\U0001F497\U0001F498\U0001F499\U0001F49A\U0001F49B\U0001F49C\U0001F49D\U0001F49E\U0001F49F\U00002728\U000026A8\U000026F9\U0000267F\U0001F3C3\U0001F3C4]', '', text)
        text = re.sub(r'[:;=8xX]-?[)\]}>dDpP(\[{<|\\/@#$%^&*oO0]', '', text)  # ASCII emoticons
        text = re.sub(r'[)\]}>dDpP(\[{<|\\/@#$%^&*oO0]-?[:;=8xX]', '', text)  # Reverse emoticons
        text = re.sub(r'✨|⭐|🌟|💫|🔥|👍|👏|❤️|💖|💕|🎉|🥳|😊|😍|🤩', '', text)  # Specific common emojis

        # Remove excessive punctuation but keep natural sentence flow
        text = re.sub(r'[!]{2,}', '.', text)         # !!! -> .
        text = re.sub(r'[?]{2,}', '?', text)         # ??? -> ?
        text = re.sub(r'[.]{2,}', '.', text)         # ... -> .
        text = re.sub(r'[,]{2,}', ',', text)         # ,, -> ,

        # Remove special symbols that TTS reads weirdly
        text = re.sub(r'[~#$%^&*+={}[\]|\\<>]', '', text)  # Remove special chars
        text = re.sub(r'[@]', ' at ', text)          # @ -> "at"
        text = re.sub(r'[/]', ' atau ', text)        # / -> "atau"

        # Remove quotes and parentheses (TTS reads them literally)
        text = re.sub(r'["\'""`]', '', text)         # Remove all quotes
        text = re.sub(r'[()[\]{}]', '', text)        # Remove brackets

        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()

        return text

    def cleanup(self):
        """Simple cleanup on exit"""
        print("[Cleanup] Starting simplified cleanup...")
        self.stop()

        # Reset filter states on close
        self.viewer_cooldowns.clear()
        self.recent_messages.clear()
        self.reply_queue.clear()

        # Additional cleanup for TikTok listener
        if self.tiktok_listener_thread:
            self.tiktok_listener_thread.stop()
            self.tiktok_listener_thread.wait(1000)
            self.tiktok_listener_thread = None

        # Clean up greeting systems
        if hasattr(self, 'sequential_greeting_manager'):
            self.sequential_greeting_manager.stop()

        print("[Cleanup] Filter states reset and cleanup completed")

    def handle_viewer_join(self, username, display_name):
        """Handle viewer join event from TikTok listener"""
        try:
            # Add viewer to greeting manager queue
            self.viewer_greeting_manager.add_viewer(username, display_name)

        except Exception as e:
            self.log_message("ERROR", f"Error handling viewer join: {e}")

    def handle_viewer_greeting(self, username, display_name):
        """Handle greeting request from greeting manager"""
        try:
            # Get current language setting for appropriate response
            current_language = self.language_combo.currentText()

            # Create direct sales-oriented greeting with clear structure
            if current_language == "Indonesia":
                greeting_prompt = f"Jawab dengan tepat: Halo {display_name}, selamat datang! Yuk lihat-lihat produk unggulan kita yang lagi promo hari ini!"
            elif current_language == "Malaysia":
                greeting_prompt = f"Jawab dengan tepat: Hai {display_name}, selamat datang! Jom tengok-tengok produk terbaik kita yang ada discount menarik!"
            else:  # English
                greeting_prompt = f"Reply exactly: Hello {display_name}, welcome! Check out our amazing products with special offers today!"

            # Add to reply queue with special greeting flag
            self.reply_queue.append(("🤖 Auto Greeting", username, greeting_prompt, True))  # True = is_greeting
            self.log_message("INFO", f"Added sales greeting for @{username} ({display_name}) in {current_language}")

        except Exception as e:
            self.log_message("ERROR", f"Error handling viewer greeting: {e}")

    def update_greeting_status(self, status_message):
        """Update greeting status label"""
        try:
            if hasattr(self, 'greeting_status_label'):
                self.greeting_status_label.setText(status_message)

                # Update style based on status
                if "Detecting" in status_message:
                    self.greeting_status_label.setStyleSheet(status_badge(SUCCESS))
                elif "Processing" in status_message:
                    self.greeting_status_label.setStyleSheet(status_badge(WARNING))
                elif "Waiting" in status_message:
                    self.greeting_status_label.setStyleSheet(status_badge(INFO))
                else:
                    self.greeting_status_label.setStyleSheet(status_badge(TEXT_DIM))

        except Exception as e:
            self.log_message("ERROR", f"Error updating greeting status: {e}")

# Alias untuk kompatibilitas
CohostTabBasic = CohostTabBasicSimplified
