# ui/main_window.py - BASIC MODE ONLY VERSION
import sys
import os
import json 
import logging
import traceback
import time
from pathlib import Path
from datetime import datetime
from collections import deque

# Setup logger
logger = logging.getLogger('VocaLive')

# Global exception handler untuk mencegah crash
def global_exception_handler(exc_type, exc_value, exc_traceback):
    """Handle uncaught exceptions to prevent application crash"""
    if issubclass(exc_type, KeyboardInterrupt):
        # Allow keyboard interrupt to work normally
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    # Log the exception
    error_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    logger.critical(f"Uncaught exception: {error_msg}")
    
    # Try to save application state before potential crash
    try:
        # Save any critical data here if needed
        logger.info("Attempting to save application state...")
    except Exception as save_error:
        logger.error(f"Failed to save application state: {save_error}")
    
    # Show user-friendly error message
    try:
        from PyQt6.QtWidgets import QMessageBox
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle("VocaLive - Error Recovery")
        msg.setText("An unexpected error occurred, but the application will continue running.")
        msg.setDetailedText(f"Error: {exc_value}\n\nThe error has been logged for debugging.")
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()
    except Exception:
        # If GUI fails, just log
        logger.error("Failed to show error dialog")

# Set global exception handler
sys.excepthook = global_exception_handler

# Import PyQt6 components
from PyQt6.QtGui import QGuiApplication, QIcon
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QMessageBox,
    QLabel, QStatusBar, QWidget, QVBoxLayout, QSizePolicy
)

# Setup project root
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv is optional

# Skema warna Facebook Theme - DARK MODE
FB_COLORS = {
    "primary": "#1877F2",
    "secondary": "#4267B2", 
    "light_bg": "#18191A",
    "dark_bg": "#0F1419",
    "text_primary": "#FFFFFF",
    "text_secondary": "#B0B3B8",
    "button_primary": "#1877F2",
    "button_secondary": "#3A3B3C",
    "success": "#42B72A",
    "warning": "#F5B800",
    "error": "#FA383E",
}

# Global dark theme styles
DARK_THEME = """
    QMainWindow, QWidget {
        background-color: #18191A;
        color: #FFFFFF;
    }
    
    QTabWidget::pane {
        border: 1px solid #3A3B3C;
        background-color: #18191A;
    }
    
    QTabBar::tab {
        background-color: #242526;
        color: #B0B3B8;
        padding: 8px 12px;
        border: none;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
    }
    
    QTabBar::tab:selected {
        background-color: #3A3B3C;
        color: #FFFFFF;
    }
    
    QTabBar::tab:hover:!selected {
        background-color: #2C2D2E;
    }
    
    QStatusBar {
        background-color: #242526;
        color: #B0B3B8;
    }
    
    QLineEdit, QTextEdit {
        background-color: #3A3B3C;
        color: #FFFFFF;
        border: 1px solid #4E4F50;
        border-radius: 4px;
        padding: 4px;
    }
    
    QLineEdit:focus, QTextEdit:focus {
        border: 1px solid #1877F2;
    }
    
    QComboBox {
        background-color: #3A3B3C;
        color: #FFFFFF;
        border: 1px solid #4E4F50;
        border-radius: 4px;
        padding: 4px;
    }
    
    QCheckBox {
        color: #FFFFFF;
    }
    
    QMessageBox {
        background-color: #18191A;
    }
    
    QMessageBox QLabel {
        color: #FFFFFF;
    }
    
    QProgressBar {
        background-color: #3A3B3C;
        border: none;
        border-radius: 4px;
        text-align: center;
        color: #FFFFFF;
    }
    
    QProgressBar::chunk {
        background-color: #1877F2;
        border-radius: 4px;
    }
"""

# Fallback ConfigManager
class ConfigManager:
    def __init__(self, config_file):
        self.config_file = config_file
        self.config = {}
        self.load_config()
    
    def load_config(self):
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load config: {e}")
            self.config = {}
    
    def get(self, key, default=None):
        return self.config.get(key, default)
    
    def set(self, key, value):
        self.config[key] = value
        self.save_config()
    
    def save_config(self):
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save config: {e}")

# Try to import ConfigManager and database scheduler, use fallback if not available
try:
    from modules_client.config_manager import ConfigManager as RealConfigManager
    from modules_client.database_scheduler import start_database_maintenance, stop_database_maintenance
    ConfigManager = RealConfigManager
    DATABASE_SCHEDULER_AVAILABLE = True
except ImportError:
    logger.warning("Using fallback ConfigManager")
    DATABASE_SCHEDULER_AVAILABLE = False
    
    # Fallback functions for database scheduler
    def start_database_maintenance():
        logger.warning("Database scheduler not available")
        return False
    
    def stop_database_maintenance():
        logger.warning("Database scheduler not available")
        return False

# Import required tabs for Basic mode only
try:
    from ui.cohost_tab_basic import CohostTabBasic
    COHOST_AVAILABLE = True
    logger.info("CohostTabBasic imported successfully")
except ImportError:
    try:
        from cohost_tab_basic import CohostTabBasic
        COHOST_AVAILABLE = True
        logger.info("CohostTabBasic imported successfully (fallback)")
    except ImportError:
        COHOST_AVAILABLE = False
        logger.warning("CohostTabBasic not available")
        
        # Create placeholder tab
        class CohostTabBasic(QWidget):
            def __init__(self):
                super().__init__()
                layout = QVBoxLayout()
                layout.addWidget(QLabel("Cohost Tab Basic tidak tersedia"))
                self.setLayout(layout)

try:
    from ui.config_tab import ConfigTab
    CONFIG_AVAILABLE = True
    logger.info("ConfigTab imported successfully")
except ImportError:
    try:
        from config_tab import ConfigTab
        CONFIG_AVAILABLE = True
        logger.info("ConfigTab imported successfully (fallback)")
    except ImportError:
        CONFIG_AVAILABLE = False
        logger.warning("ConfigTab not available")
        
        # Create placeholder tab
        class ConfigTab(QWidget):
            def __init__(self):
                super().__init__()
                layout = QVBoxLayout()
                layout.addWidget(QLabel("Config Tab tidak tersedia"))
                self.setLayout(layout)

# Virtual Audio Tab removed - user requested removal

# Utility functions
def safe_attr_check(obj, attr_name):
    """Safely check if an object has an attribute"""
    try:
        return hasattr(obj, attr_name)
    except Exception:
        return False

# Exception handler global
def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logger.error(f"Uncaught Exception: {exc_type.__name__}: {exc_value}")
    
    # Log error to file
    try:
        error_log = Path("logs/error_log.txt")
        error_log.parent.mkdir(exist_ok=True)
        with open(error_log, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().isoformat()}] {exc_type.__name__}: {exc_value}\n")
    except Exception:
        pass  # Ignore logging errors

sys.excepthook = handle_exception

# High-DPI policy
QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
    Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
)

class UnifiedCommentProcessor:
    """Unified comment processing system with spam/toxic filtering and cohost routing

    Logic Flow:
    1. Check blacklist/whitelist FIRST
    2. Filter toxic words and spam
    3. Check Cohost triggers -> Cohost responds
    """

    # Toxic keywords to filter (expanded list)
    TOXIC_KEYWORDS = [
        "bodoh", "goblok", "anjing", "bangsat", "tolol", "babi", "idiot",
        "ngentot", "kontol", "memek", "pepek", "asu", "jancok", "cuk",
        "tai", "taik", "bego", "brengsek", "setan", "iblis", "kampret"
    ]

    def __init__(self, cohost_tab=None):
        self.cohost_tab = cohost_tab

        # User list manager for blacklist/whitelist
        try:
            from modules_client.user_list_manager import get_user_list_manager
            self.user_list_manager = get_user_list_manager()
            logger.info("[UnifiedCommentProcessor] User list manager loaded")
        except ImportError:
            self.user_list_manager = None
            logger.warning("[UnifiedCommentProcessor] User list manager not available")

        # Unified queue for all comments
        self.unified_queue = deque(maxlen=20)

        # Anti-spam tracking for cohost
        self.cohost_user_tracker = {}

        # Spam detection - track repeated messages per user
        self.user_message_history = {}  # {username: [(timestamp, message_hash), ...]}
        self.SPAM_WINDOW = 60  # Check spam in last 60 seconds
        self.MAX_SIMILAR_MESSAGES = 3  # 3+ similar messages = spam

        # Processing status
        self.is_processing = False

        # Cooldown settings
        self.GENERAL_COOLDOWN = 30    # 30 seconds for general Q&A

        logger.info("UnifiedCommentProcessor initialized with SPAM+TOXIC FILTER")
    
    def _is_toxic(self, message):
        """Check if message contains toxic words"""
        message_lower = message.lower()
        for word in self.TOXIC_KEYWORDS:
            if word in message_lower:
                return True, word
        return False, None
    
    def _get_message_hash(self, message):
        """Create simple hash for message comparison"""
        import hashlib
        # Normalize message: lowercase, remove punctuation, remove common words
        normalized = message.lower().strip()
        for word in ["bang", "bro", "gan", "min", "kak", "sis"]:
            normalized = normalized.replace(word, "")
        normalized = ''.join(c for c in normalized if c.isalnum() or c.isspace())
        return hashlib.md5(normalized.encode()).hexdigest()[:8]
    
    def _is_spam(self, author, message):
        """Check if user is spamming similar messages"""
        current_time = time.time()
        msg_hash = self._get_message_hash(message)
        
        # Get user history
        if author not in self.user_message_history:
            self.user_message_history[author] = []
        
        user_history = self.user_message_history[author]
        
        # Clean old messages (older than SPAM_WINDOW)
        user_history = [(ts, h) for ts, h in user_history if current_time - ts < self.SPAM_WINDOW]
        
        # Count similar messages
        similar_count = sum(1 for ts, h in user_history if h == msg_hash)
        
        # Add current message to history
        user_history.append((current_time, msg_hash))
        
        # Keep only last 20 messages per user
        if len(user_history) > 20:
            user_history = user_history[-20:]
        
        self.user_message_history[author] = user_history
        
        # Check if spam
        if similar_count >= self.MAX_SIMILAR_MESSAGES:
            return True, f"Pesan serupa {similar_count}x dalam {self.SPAM_WINDOW}s"
        
        return False, None
    
    def process_comment(self, author, message):
        """Process incoming comment with BLACKLIST/WHITELIST + SPAM/TOXIC FILTER

        Priority Order:
        1. Check BLACKLIST first (block immediately)
        2. Check WHITELIST (bypass cooldowns)
        3. Filter toxic words (block immediately)
        4. Filter spam messages (block repeated messages)
        5. Check cohost triggers -> route to cohost
        """
        try:
            logger.info(f"[UnifiedProcessor] 📨 Processing comment from {author}: {message[:50]}...")
            current_time = time.time()
            
            # ===== STEP -1: BLACKLIST CHECK =====
            if self.user_list_manager:
                if self.user_list_manager.is_blacklisted(author):
                    logger.warning(f"[UnifiedProcessor] 🚫 BLACKLISTED USER: {author} - IGNORING")
                    print(f"[FILTER] 🚫 BLACKLISTED USER: {author} - pesan diabaikan")
                    return  # Stop processing - ignore blacklisted users completely
            
            # ===== STEP 0: WHITELIST CHECK (for bypass cooldown) =====
            is_vip = False
            if self.user_list_manager:
                is_vip = self.user_list_manager.is_whitelisted(author)
                if is_vip:
                    logger.info(f"[UnifiedProcessor] ⭐ VIP USER: {author} - bypass cooldown")
                    print(f"[VIP] ⭐ {author} adalah VIP - bypass cooldown")
            
            # ===== STEP 1: TOXIC WORD FILTER =====
            is_toxic, toxic_word = self._is_toxic(message)
            if is_toxic:
                logger.warning(f"[UnifiedProcessor] 🚫 TOXIC BLOCKED: '{toxic_word}' from {author}")
                print(f"[FILTER] 🚫 TOXIC MESSAGE BLOCKED: kata '{toxic_word}' dari {author}")
                return  # Stop processing - don't respond to toxic messages
            
            # ===== STEP 1.5: SPAM DETECTION (VIP bypass) =====
            if not is_vip:  # VIP users bypass spam filter
                is_spam, spam_reason = self._is_spam(author, message)
                if is_spam:
                    logger.warning(f"[UnifiedProcessor] 🚫 SPAM BLOCKED: {spam_reason} from {author}")
                    print(f"[FILTER] 🚫 SPAM MESSAGE BLOCKED: {spam_reason} dari {author}")
                    return  # Stop processing - don't respond to spam
            
            # ===== STEP 2: CHECK COHOST TRIGGERS =====
            logger.info(f"[UnifiedProcessor] 💬 Checking Cohost triggers...")
            print(f"[TRIGGER ROUTER] 💬 Checking Cohost triggers...")
            
            if not self.cohost_tab:
                logger.warning("[UnifiedProcessor] No cohost tab available")
                return
            
            # Check for cohost trigger words
            if hasattr(self.cohost_tab, 'check_trigger'):
                is_trigger = self.cohost_tab.check_trigger(message)
                
                if is_trigger:
                    logger.info(f"[UnifiedProcessor] 🗣️ COHOST TRIGGER MATCHED for {author}")
                    print(f"[TRIGGER ROUTER] 🗣️ Cohost trigger matched -> Routing to Cohost tab")
                    
                    # Check cohost cooldown
                    cohost_user_key = f"cohost_{author}"
                    if cohost_user_key in self.cohost_user_tracker:
                        last_reply_time = self.cohost_user_tracker[cohost_user_key]
                        if current_time - last_reply_time < self.GENERAL_COOLDOWN:
                            logger.info(f"[UnifiedProcessor] Cohost user {author} in cooldown ({self.GENERAL_COOLDOWN}s)")
                            return
                    
                    # Update cohost tracker
                    self.cohost_user_tracker[cohost_user_key] = current_time
                    
                    # Generate AI reply using cohost tab
                    if hasattr(self.cohost_tab, 'generate_cohost_reply'):
                        self.cohost_tab.generate_cohost_reply(author, message)
                        logger.info(f"[UnifiedProcessor] ✅ Routed to Cohost tab for AI reply")
                    else:
                        logger.warning("[UnifiedProcessor] Cohost tab missing generate_cohost_reply method")
                else:
                    logger.debug(f"[UnifiedProcessor] No cohost trigger matched for: {message[:30]}...")
            else:
                logger.warning("[UnifiedProcessor] Cohost tab missing check_trigger method")
                
        except Exception as e:
            logger.error(f"[UnifiedProcessor] Error processing comment: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    def process_queue(self):
        """Process queued comments"""
        try:
            if not self.unified_queue or self.is_processing:
                return
            
            self.is_processing = True
            item = self.unified_queue.popleft()
            
            # Process the queued item
            self.process_comment(item['author'], item['message'])
            
            self.is_processing = False
        except Exception as e:
            logger.error(f"[UnifiedProcessor] Queue processing error: {e}")
            self.is_processing = False
    
class MainWindow(QMainWindow):
    """Main window aplikasi VocaLive - Basic Mode Only."""
    
    def __init__(self):
        super().__init__()
        
        # Log mode yang digunakan
        logger.info("VocaLive - Basic Mode Only")
        
        # Setup window properties
        self.setWindowTitle("VocaLive - Basic Mode")
        self.resize(1000, 700)
        self.setMinimumSize(800, 600)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Setup status bar
        self._setup_status_bar()
        
        # Setup icon jika tersedia
        self._setup_icon()
        
        # Load configuration
        self.cfg = ConfigManager("config/settings.json")
        version = "v7.2"
        self.cfg.set("app_version", version)
        
        # Create main tabs directly
        self._create_main_tabs()
        
        # Initialize unified comment processor after tabs are created
        self.unified_processor = None
        self._setup_unified_processor()
        
        # Show main tabs
        self.setCentralWidget(self.main_tabs)
        
        # Start database maintenance scheduler
        try:
            if DATABASE_SCHEDULER_AVAILABLE:
                start_database_maintenance()
                logger.info("Database maintenance scheduler started")
            else:
                logger.warning("Database scheduler not available")
        except Exception as scheduler_error:
            logger.error(f"Failed to start database scheduler: {scheduler_error}")
    
    def closeEvent(self, event):
        """Handle application close event with comprehensive cleanup"""
        try:
            logger.info("Application closing...")
            
            # Force cleanup all tabs before closing
            for i in range(self.main_tabs.count()):
                tab = self.main_tabs.widget(i)
                if hasattr(tab, 'closeEvent'):
                    try:
                        # Create a dummy close event for tab cleanup
                        from PyQt6.QtGui import QCloseEvent
                        dummy_event = QCloseEvent()
                        tab.closeEvent(dummy_event)
                        logger.info(f"Tab {i} cleanup completed")
                    except Exception as tab_error:
                        logger.error(f"Error cleaning up tab {i}: {tab_error}")
            
            # Stop database maintenance scheduler
            try:
                if DATABASE_SCHEDULER_AVAILABLE:
                    stop_database_maintenance()
                    logger.info("Database maintenance scheduler stopped")
            except Exception as scheduler_error:
                logger.error(f"Error stopping database scheduler: {scheduler_error}")
            
            # Run comprehensive cleanup system
            try:
                from comprehensive_cleanup import cleanup_all_resources
                cleanup_result = cleanup_all_resources()
                if cleanup_result["success"]:
                    logger.info(f"✅ Comprehensive cleanup completed: {cleanup_result['stats']['components_cleaned']} components cleaned")
                else:
                    logger.warning(f"⚠️ Cleanup completed with errors: {len(cleanup_result['errors'])} errors")
            except ImportError:
                logger.warning("⚠️ Comprehensive cleanup system not available, using fallback")
                # Fallback to basic garbage collection
                import gc
                gc.collect()
            except Exception as cleanup_error:
                logger.error(f"❌ Error in comprehensive cleanup: {cleanup_error}")
                # Fallback to basic garbage collection
                import gc
                gc.collect()
            
            event.accept()
            
        except Exception as e:
            logger.error(f"Error during close: {e}")
            # Emergency cleanup if normal cleanup fails
            try:
                from comprehensive_cleanup import emergency_cleanup
                emergency_result = emergency_cleanup()
                logger.info(f"Emergency cleanup result: {emergency_result}")
            except Exception as emergency_error:
                logger.error(f"Emergency cleanup failed: {emergency_error}")
            
            # Force accept even if cleanup fails
            event.accept()
    
    def _setup_status_bar(self):
        """Setup status bar dengan label yang diperlukan."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # API status label
        self.api_status_label = QLabel("API Status: Ready")
        self.status_bar.addPermanentWidget(self.api_status_label)
    
    def _setup_icon(self):
        """Setup aplikasi icon jika tersedia."""
        try:
            icon_path = os.path.join(ROOT, "icon.ico")
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
        except Exception as e:
            logger.warning(f"Failed to load icon: {e}")
    
    def _create_main_tabs(self):
        """Create main tab widget dengan Cohost Basic dan Config Tab."""
        self.main_tabs = QTabWidget()
        
        # Add Cohost Basic tab
        if COHOST_AVAILABLE:
            try:
                self.cohost_tab = CohostTabBasic()
                self.main_tabs.addTab(self.cohost_tab, "Cohost Basic")
                logger.info("Cohost Basic tab added successfully")
            except Exception as e:
                logger.error(f"Failed to create Cohost Basic tab: {e}")
                placeholder = QWidget()
                layout = QVBoxLayout()
                layout.addWidget(QLabel(f"Error loading Cohost Basic: {e}"))
                placeholder.setLayout(layout)
                self.main_tabs.addTab(placeholder, "Cohost Basic (Error)")
        
        # Add Config tab
        if CONFIG_AVAILABLE:
            try:
                self.config_tab = ConfigTab()
                self.main_tabs.addTab(self.config_tab, "Konfigurasi")
                logger.info("Config tab added successfully")
            except Exception as e:
                logger.error(f"Failed to create Config tab: {e}")
                placeholder = QWidget()
                layout = QVBoxLayout()
                layout.addWidget(QLabel(f"Error loading Config: {e}"))
                placeholder.setLayout(layout)
                self.main_tabs.addTab(placeholder, "Konfigurasi (Error)")
        
        # Add Analytics tab
        try:
            from ui.analytics_tab import AnalyticsTab
            self.analytics_tab = AnalyticsTab()
            self.main_tabs.addTab(self.analytics_tab, "📊 Analytics")
            logger.info("Analytics tab added successfully")
        except Exception as e:
            logger.error(f"Failed to create Analytics tab: {e}")
            placeholder = QWidget()
            layout = QVBoxLayout()
            layout.addWidget(QLabel(f"Error loading Analytics Tab: {e}"))
            placeholder.setLayout(layout)
            self.main_tabs.addTab(placeholder, "📊 Analytics (Error)")

        # Add User Management tab
        try:
            from ui.user_management_tab import UserManagementTab
            self.user_management_tab = UserManagementTab()
            self.main_tabs.addTab(self.user_management_tab, "👥 User Management")
            logger.info("User Management tab added successfully")
        except Exception as e:
            logger.error(f"Failed to create User Management tab: {e}")
            placeholder = QWidget()
            layout = QVBoxLayout()
            layout.addWidget(QLabel(f"Error loading User Management Tab: {e}"))
            placeholder.setLayout(layout)
            self.main_tabs.addTab(placeholder, "👥 User Management (Error)")

        # Add Developer tab
        try:
            from ui.developer_tab import DeveloperTab
            self.developer_tab = DeveloperTab()
            self.main_tabs.addTab(self.developer_tab, "👨‍💻 Developer")
            logger.info("Developer tab added successfully")
        except Exception as e:
            logger.error(f"Failed to create Developer tab: {e}")
            placeholder = QWidget()
            layout = QVBoxLayout()
            layout.addWidget(QLabel(f"Error loading Developer Tab: {e}"))
            placeholder.setLayout(layout)
            self.main_tabs.addTab(placeholder, "👨‍💻 Developer (Error)")

        # Virtual Audio tab removed - user requested removal
        
        # DISABLED: Old direct connection system - causes double processing
        # Using unified processor system instead to prevent duplicate replies
        logger.info("Direct Cohost-OBS connection disabled - using unified processor system")
        
        # Set default tab to Cohost Basic
        self.main_tabs.setCurrentIndex(0)
        
        logger.info("Main tabs created successfully")
    
    def _setup_unified_processor(self):
        """Setup unified comment processor"""
        try:
            if not hasattr(self, 'cohost_tab'):
                logger.warning("Cohost tab not available for unified processor")
                return

            # Initialize unified processor
            self.unified_processor = UnifiedCommentProcessor(
                cohost_tab=getattr(self, 'cohost_tab', None)
            )

            # Replace cohost tab's comment processing with unified system
            if hasattr(self.cohost_tab, 'process_comment_signal'):
                try:
                    self.cohost_tab.process_comment_signal.disconnect()
                except Exception:
                    pass
                self.cohost_tab.process_comment_signal.connect(self.unified_processor.process_comment)
                logger.info("Connected cohost comments to unified processor")

            logger.info("Unified comment processor setup completed")

        except Exception as e:
            logger.error(f"Failed to setup unified processor: {e}")
            import traceback
            traceback.print_exc()

def main():
    """Main function untuk menjalankan aplikasi."""
    try:
        app = QApplication(sys.argv)
        app.setApplicationName("VocaLive Basic")
        app.setApplicationVersion("1.0.0-basic")
        
        # Setup logging dengan error handling
        try:
            os.makedirs('logs', exist_ok=True)
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler('logs/streammate.log', encoding='utf-8'),
                    logging.StreamHandler()
                ]
            )
        except Exception as log_error:
            print(f"Failed to setup logging: {log_error}")
            # Fallback to basic logging
            logging.basicConfig(level=logging.INFO)
        
        # Create main window dengan error handling
        try:
            window = MainWindow()
            window.show()
            logger.info("VocaLive started successfully")
        except Exception as window_error:
            logger.critical(f"Failed to create main window: {window_error}")
            return 1
        
        # Setup application recovery timer
        recovery_timer = QTimer()
        recovery_timer.timeout.connect(lambda: logger.debug("Application heartbeat - running normally"))
        recovery_timer.start(300000)  # Log heartbeat every 5 minutes
        
        # Run application dengan error handling
        try:
            exit_code = app.exec()
            logger.info(f"Application exited with code: {exit_code}")
            return exit_code
        except Exception as app_error:
            logger.critical(f"Application runtime error: {app_error}")
            return 1
            
    except Exception as main_error:
        print(f"Critical error in main(): {main_error}")
        return 1

if __name__ == "__main__":
    main()