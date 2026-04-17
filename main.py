#!/usr/bin/env python3
"""
VocaLive - Live Streaming Automation
Main Entry Point - Fixed Version for Windows Encoding
"""

import multiprocessing
import os
import sys

# CRITICAL FIX: Set Windows Console Encoding to UTF-8 to prevent UnicodeEncodeError
if sys.platform == "win32":
    import codecs
    # Force UTF-8 encoding for stdout and stderr to handle emoji/Unicode
    if hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            # Fallback: Wrap stdout/stderr with UTF-8 encoder - FIX for EXE
            try:
                stdout_buffer = sys.stdout.detach()
                stderr_buffer = sys.stderr.detach()

                # Check if detach() returned valid buffers (not None)
                if stdout_buffer is not None:
                    sys.stdout = codecs.getwriter('utf-8')(stdout_buffer, errors='replace')
                if stderr_buffer is not None:
                    sys.stderr = codecs.getwriter('utf-8')(stderr_buffer, errors='replace')
            except (AttributeError, OSError):
                # In frozen executable, detach might not work - skip encoding fix
                print("[WARNING] Cannot reconfigure stdout/stderr encoding in executable mode")
                pass
    else:
        # For older Python versions - with EXE compatibility check
        try:
            stdout_buffer = sys.stdout.detach()
            stderr_buffer = sys.stderr.detach()

            # Check if detach() returned valid buffers (not None)
            if stdout_buffer is not None:
                sys.stdout = codecs.getwriter('utf-8')(stdout_buffer, errors='replace')
            if stderr_buffer is not None:
                sys.stderr = codecs.getwriter('utf-8')(stderr_buffer, errors='replace')
        except (AttributeError, OSError):
            # In frozen executable, detach might not work - skip encoding fix
            print("[WARNING] Cannot reconfigure stdout/stderr encoding in executable mode")
            pass

import traceback
import warnings

# Telemetry keys
POSTHOG_PROJECT_KEY = os.environ.get("POSTHOG_PROJECT_KEY", "phc_uYwH9ByGUHwcPfnX4ThEUxePHMmycTRWictJoyTBnzSA")
SENTRY_DSN = os.environ.get("SENTRY_DSN", "https://61478c4ae40ad572269d7e6245405aae@o4511211608211456.ingest.us.sentry.io/4511213925367808")

# Filter out annoying Qt CSS warnings
warnings.filterwarnings('ignore', message='.*Unknown property.*')

# ========== SETUP VALIDATOR IMPORT ==========
# Validate setup BEFORE anything else
try:
    from modules_client.setup_validator import validate_setup
    SETUP_VALIDATOR_AVAILABLE = True
except ImportError as e:
    print(f"[WARNING] Setup validator not available: {e}")
    SETUP_VALIDATOR_AVAILABLE = False

# ========== LICENSE SYSTEM IMPORT ==========
# Import license system SEBELUM GUI setup
try:
    from modules_client.license_manager import LicenseManager
    LICENSE_SYSTEM_AVAILABLE = True
    logger_license = None  # Will be set after logger setup
except ImportError as e:
    print(f"[WARNING] License system not available: {e}")
    LICENSE_SYSTEM_AVAILABLE = False

# Suppress Qt stylesheet warnings that spam the console
def qt_message_handler(mode, context, message):
    """Custom Qt message handler to filter out CSS warnings"""
    # Ignore "Unknown property" warnings from Qt stylesheets
    if "Unknown property" in message:
        return
    # Allow other important Qt messages through
    print(f"Qt: {message}")

# Set up Qt message filtering if available
try:
    from PyQt6.QtCore import qInstallMessageHandler
    qInstallMessageHandler(qt_message_handler)
except ImportError:
    pass  # PyQt6 not loaded yet
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path

# ========== CRITICAL: HIGH DPI SETUP SEBELUM IMPORT PYQT6 ==========
# Ini HARUS dipanggil sebelum QGuiApplication atau QApplication dibuat
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
os.environ["QT_SCALE_FACTOR_ROUNDING_POLICY"] = "PassThrough"
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

# Root project directory PERTAMA - handle EXE mode
if getattr(sys, 'frozen', False):
    # Running as frozen EXE
    ROOT = os.path.dirname(sys.executable)
else:
    # Running as regular Python script
    ROOT = os.path.dirname(os.path.abspath(__file__))

# ========== CAPTURE FRESH INSTALL STATUS ==========
# HARUS di-capture SEBELUM setup_validator / i18n / license sempat menyentuh settings.json.
# Path resolution konsisten dengan pattern di modules_client/config_manager.py:12-16.
_settings_path = Path(ROOT) / "config" / "settings.json"
IS_FRESH_INSTALL = not _settings_path.exists()

# Setup logging system SEBELUM import lainnya
LOG_DIR = Path(ROOT) / "logs"
LOG_DIR.mkdir(exist_ok=True)
SYSTEM_LOG = LOG_DIR / "system.log"

# Configure logging dengan format yang lebih informatif
logger = logging.getLogger('VocaLive')
logger.setLevel(logging.INFO)

# File handler dengan rotation
file_handler = RotatingFileHandler(
    SYSTEM_LOG,
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5,
    encoding='utf-8'
)
file_handler.setLevel(logging.INFO)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.WARNING)

# Format log yang lebih detail
formatter = logging.Formatter(
    '[%(asctime)s] [%(name)s] [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add handlers
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Set license logger
if LICENSE_SYSTEM_AVAILABLE:
    logger_license = logger

# ========== LOG STARTUP INFO ==========
try:
    from version import VERSION as _APP_VERSION
except Exception:
    _APP_VERSION = "1.0.3"

logger.info("=" * 60)
logger.info(f"VocaLive Starting - Version {_APP_VERSION}")
logger.info(f"Python {sys.version}")
logger.info(f"Root directory: {ROOT}")
logger.info(f"Platform: {sys.platform}")
if LICENSE_SYSTEM_AVAILABLE:
    logger.info("License system: ENABLED")
else:
    logger.warning("License system: DISABLED")
logger.info("=" * 60)
logger.info("[STARTUP] VocaLive v%s starting", _APP_VERSION)

# ========== FORCE PRODUCTION MODE ==========
def detect_application_mode():
    """Force production mode - no development mode allowed"""
    print("[PROD] MODE: Production (FORCED)")
    return "production"

# Panggil detection
APP_MODE = detect_application_mode()
logger.info(f"Application mode: {APP_MODE}")

# Export ke environment untuk module lain
os.environ["VOCALIVE_APP_MODE"] = APP_MODE

# ========== SETUP PYTHON PATH ==========
# Add project paths to Python path SEBELUM import modules
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "modules_client"))
sys.path.insert(0, os.path.join(ROOT, "modules_server"))
sys.path.insert(0, os.path.join(ROOT, "ui"))
sys.path.insert(0, os.path.join(ROOT, "listeners"))

logger.info(f"Python path updated with {len(sys.path)} entries")

# ========== SEKARANG BARU IMPORT PYQT6 ==========
try:
    from PyQt6.QtCore import Qt, QTimer
    from PyQt6.QtGui import QGuiApplication, QIcon, QPixmap
    from PyQt6.QtWidgets import QApplication, QMessageBox, QSplashScreen
    logger.info("PyQt6 imported successfully")
except ImportError as e:
    print(f"CRITICAL: PyQt6 not found: {e}")
    print("Please install PyQt6: pip install PyQt6")
    sys.exit(1)

# ========== GLOBAL EXCEPTION HANDLER ==========
def handle_exception(exc_type, exc_value, exc_traceback):
    """Enhanced global exception handler dengan debug logging"""
    # Skip keyboard interrupt
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    # Format error message dengan full traceback
    error_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))

    # Enhanced logging dengan lebih banyak detail
    logger.critical(f"[FORCE-CLOSE-DEBUG] Uncaught Exception: {exc_type.__name__}: {exc_value}")
    logger.critical(f"[FORCE-CLOSE-DEBUG] Traceback:\n{error_msg}")

    # Print ke console untuk debugging real-time
    print("\n[FORCE-CLOSE-DEBUG] ========== CRITICAL ERROR ==========")
    print(f"[FORCE-CLOSE-DEBUG] Exception Type: {exc_type.__name__}")
    print(f"[FORCE-CLOSE-DEBUG] Exception Value: {exc_value}")
    print("[FORCE-CLOSE-DEBUG] Traceback:")
    print(error_msg)
    print("[FORCE-CLOSE-DEBUG] =====================================\n")

    # Save error to temp file untuk debugging
    error_log_path = Path(ROOT) / "temp" / "error_log.txt"
    error_log_path.parent.mkdir(exist_ok=True)

    try:
        with open(error_log_path, "a", encoding="utf-8") as f:
            f.write(f"\n[{datetime.now().isoformat()}] FORCE-CLOSE-DEBUG:\n")
            f.write(f"Exception Type: {exc_type.__name__}\n")
            f.write(f"Exception Value: {exc_value}\n")
            f.write(f"Traceback:\n{error_msg}")
            f.write("\n" + "="*80 + "\n")
        logger.info(f"[FORCE-CLOSE-DEBUG] Error details saved to: {error_log_path}")
        print(f"[FORCE-CLOSE-DEBUG] Error details saved to: {error_log_path}")
    except Exception as log_error:
        logger.error(f"[FORCE-CLOSE-DEBUG] Failed to write error log: {log_error}")
        print(f"[FORCE-CLOSE-DEBUG] Failed to write error log: {log_error}")

    # Enhanced error handling - try to keep app alive for non-critical errors
    critical_errors = [
        'SystemError', 'MemoryError', 'KeyboardInterrupt',
        'SystemExit', 'GeneratorExit', 'RuntimeError'
    ]

    error_name = exc_type.__name__
    is_critical = error_name in critical_errors

    print(f"[FORCE-CLOSE-DEBUG] Error classification: {'CRITICAL' if is_critical else 'NON-CRITICAL'}")

    # Show error dialog jika QApplication sudah ada
    try:
        if QApplication.instance():
            if is_critical:
                print("[FORCE-CLOSE-DEBUG] Showing critical error dialog and forcing exit")
                QMessageBox.critical(
                    None,
                    "VocaLive - Critical Error",
                    f"Application encountered a critical error and must close:\n\n"
                    f"{exc_type.__name__}: {exc_value}\n\n"
                    f"Error details saved to: {error_log_path}\n\n"
                    f"Click OK to exit application.",
                    QMessageBox.StandardButton.Ok
                )
                # Force exit for critical errors
                QApplication.instance().quit()
            else:
                print("[FORCE-CLOSE-DEBUG] Showing recoverable error dialog")
                QMessageBox.warning(
                    None,
                    "VocaLive - Error Recovered",
                    f"Application encountered an error but will continue:\n\n"
                    f"{exc_type.__name__}: {exc_value}\n\n"
                    f"Error details saved to: {error_log_path}\n\n"
                    f"If problems persist, please restart the application.",
                    QMessageBox.StandardButton.Ok
                )
                # Try to continue for non-critical errors
                print("[FORCE-CLOSE-DEBUG] Attempting to continue after non-critical error")
                return
    except Exception as dialog_error:
        # If even the error dialog fails, log it and exit gracefully
        logger.error(f"[FORCE-CLOSE-DEBUG] Failed to show error dialog: {dialog_error}")
        print(f"[FORCE-CLOSE-DEBUG] Failed to show error dialog: {dialog_error}")
        if is_critical:
            print("[FORCE-CLOSE-DEBUG] Forcing exit due to critical error")
            sys.exit(1)

# Install global exception handler
sys.excepthook = handle_exception

def check_dependencies():
    """Check critical dependencies sebelum aplikasi dimulai"""
    logger.info("Checking critical dependencies...")

    required_modules = {
        'PyQt6': 'pip install PyQt6',
        'requests': 'pip install requests',
        'keyboard': 'pip install keyboard',
        'pygame': 'pip install pygame',
        'cryptography': 'pip install cryptography',
    }

    missing_modules = []

    for module, install_cmd in required_modules.items():
        try:
            if module == 'PyQt6':
                # PyQt6 sudah diimport di atas
                continue
            else:
                __import__(module)
            logger.debug(f"[OK] {module} - OK")
        except ImportError:
            missing_modules.append((module, install_cmd))
            logger.error(f"[MISSING] {module} - MISSING")

    if missing_modules:
        error_msg = "Missing required dependencies:\n\n"
        for module, cmd in missing_modules:
            error_msg += f"- {module}: {cmd}\n"

        logger.error("Critical dependencies missing!")
        print(error_msg)
        return False

    logger.info("All critical dependencies OK")
    return True

def initialize_directories():
    """Initialize required directories dengan error handling"""
    logger.info("Initializing directory structure...")

    required_dirs = [
        "temp", "logs", "config", "knowledge",
        "knowledge_bases", "assets",
        "temp/cache", "resources"
    ]

    for directory in required_dirs:
        dir_path = Path(ROOT) / directory
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"[OK] Directory created/verified: {directory}")
        except Exception as e:
            logger.error(f"[ERROR] Failed to create directory {directory}: {e}")
            return False

    logger.info("Directory structure initialized successfully")
    return True

def validate_application_license():
    """Validate application license before starting GUI"""
    if not LICENSE_SYSTEM_AVAILABLE:
        logger.warning("License system disabled - continuing without validation")
        return True

    logger.info("Checking application license...")

    try:
        license_manager = LicenseManager(ROOT)

        # Check if license exists and is valid
        is_valid, message = license_manager.is_license_valid()

        if is_valid:
            # License is valid
            license_info = license_manager.get_license_info()
            logger.info(f"License validation successful: {message}")

            if 'days_remaining' in license_info:
                days = license_info['days_remaining']
                if license_info.get('is_unlimited', False):
                    logger.info("License: UNLIMITED duration")
                    print("[LICENSE] ✅ Unlimited license")
                else:
                    logger.info(f"License expires in {days} days")
                    print(f"[LICENSE] ✅ {days} days remaining")

            print(f"[LICENSE] ✅ {message}")
            return True
        else:
            # License invalid or not found - show license dialog
            logger.warning(f"License validation failed: {message}")
            print(f"[LICENSE] ❌ {message}")

            # Import and show license dialog
            try:
                # Create minimal QApplication for license dialog
                from PyQt6.QtWidgets import QApplication

                # Create QApplication jika belum ada
                app = QApplication.instance()
                if not app:
                    app = QApplication(sys.argv)
                    app.setStyle('Fusion')

                # Import license dialog
                sys.path.insert(0, os.path.join(ROOT, "ui"))
                from ui.license_dialog import show_license_dialog

                print("[LICENSE] Opening license activation dialog...")
                logger.info("Showing license activation dialog")

                # Show license dialog
                success, license_key = show_license_dialog()

                if success:
                    logger.info("License activated successfully via dialog")
                    print("[LICENSE] ✅ License activated successfully!")
                    return True
                else:
                    logger.warning("License activation cancelled by user")
                    print("[LICENSE] ❌ License activation cancelled")
                    return False

            except Exception as dialog_error:
                logger.error(f"License dialog error: {dialog_error}")
                print(f"[LICENSE] Dialog error: {dialog_error}")
                return False

    except Exception as e:
        logger.error(f"License validation error: {e}")
        print(f"[LICENSE] Validation error: {e}")
        return False


def main():
    """Main application entry point"""
    logger.info("Starting main application...")

    # ========== STEP 1: VALIDATE SETUP ==========
    # This MUST run FIRST before any other checks
    if SETUP_VALIDATOR_AVAILABLE:
        print("[SETUP] Validating application configuration...")
        try:
            is_valid = validate_setup(root_dir=ROOT, show_gui=True)
            if not is_valid:
                logger.critical("Setup validation failed - missing required configuration files")
                print("[SETUP] ❌ Application cannot start due to configuration errors")
                print("[SETUP] 📖 Please read PANDUAN_INSTALL_USER.md for setup instructions")
                return 1
            print("[SETUP] ✅ Configuration validation passed")
        except Exception as e:
            logger.error(f"Setup validation error: {e}")
            print(f"[SETUP] ⚠️ Warning: Could not complete setup validation: {e}")
            # Continue anyway - don't block if validator has issues
    else:
        logger.warning("Setup validator not available - skipping validation")

    # Check dependencies
    if not check_dependencies():
        logger.critical("Critical dependencies missing, exiting...")
        return 1

    # Initialize directories
    if not initialize_directories():
        logger.critical("Failed to initialize directories, exiting...")
        return 1

    print("[SUCCESS] VocaLive main application initialized successfully")
    print(f"[INFO] Mode: {APP_MODE}")
    print(f"[INFO] Root directory: {ROOT}")

    # ========== I18N INITIALIZATION ==========
    # Initialize i18n SEBELUM license dialog supaya dialog bilingual dari first launch.
    # IS_FRESH_INSTALL di-capture di module-level sebelum setup_validator run.
    try:
        from modules_client import i18n
        i18n.init(fresh_install=IS_FRESH_INSTALL)
        logger.info("[STARTUP] i18n initialized, lang=%s (fresh_install=%s)",
                    i18n.current_language(), IS_FRESH_INSTALL)
    except Exception as e:
        logger.error(f"[STARTUP] i18n init failed (non-fatal): {e}")

    # ========== LICENSE VALIDATION ==========
    print("[LICENSE] Validating application license...")
    _license_is_valid = validate_application_license()
    logger.info("[STARTUP] License valid: %s", _license_is_valid)
    if not _license_is_valid:
        logger.critical("License validation failed - application cannot start")
        print("[LICENSE] ❌ Application cannot start without valid license")

        # Show final message and exit
        try:
            from PyQt6.QtWidgets import QApplication, QMessageBox
            app = QApplication.instance() or QApplication(sys.argv)
            QMessageBox.critical(
                None,
                "VocaLive - License Required",
                "VocaLive requires a valid license to run.\n\n"
                "Please contact support to obtain a license key.\n\n"
                "Application will now exit.",
                QMessageBox.StandardButton.Ok
            )
        except Exception:
            pass

        return 1

    logger.info("License validation completed successfully")

    # Init monitoring (PostHog + Sentry) — non-blocking, never crashes app
    from modules_client.telemetry import capture as telemetry_capture
    from modules_client.telemetry import init as telemetry_init
    from modules_client.telemetry import set_user_context
    telemetry_init(POSTHOG_PROJECT_KEY, SENTRY_DSN, _APP_VERSION)
    logger.info("[STARTUP] Telemetry initialized")
    set_user_context({"platform": "windows", "app_mode": APP_MODE})
    telemetry_capture("app_launched")

    # LAUNCH GUI APPLICATION
    try:
        print("[GUI] Launching VocaLive GUI...")

        from PyQt6.QtWidgets import QApplication, QMessageBox

        # Create or get existing QApplication
        app = QApplication.instance()
        if not app:
            app = QApplication(sys.argv)
        # Set application properties
        app.setApplicationName("VocaLive")
        app.setApplicationVersion(_APP_VERSION)
        app.setOrganizationName("VocaLive")
        app.setOrganizationDomain("vocalive.com")

        # Apply dark theme
        app.setStyle('Fusion')

        # ⚡ LOADING INDICATOR: Simple console-based loading for now
        print("[LOADING] VocaLive is starting up...")
        # Splash screen disabled to prevent QPaintDevice segfault (see CLAUDE.md)

        # Import and create main window
        sys.path.insert(0, os.path.join(ROOT, "ui"))

        # Console loading progress
        print("[LOADING] Setting up UI components...")

        # Fix relative imports for frozen executable
        import importlib.util

        # Load main_window module with proper path handling
        main_window_path = os.path.join(ROOT, "ui", "main_window.py")

        print("[LOADING] Loading main window...")

        # Check if running from frozen executable
        if getattr(sys, 'frozen', False):
            # In frozen mode, try direct import
            try:
                from ui.main_window import MainWindow
                print("[GUI] Imported MainWindow from ui.main_window")
            except ImportError:
                # Fallback: manual module loading
                spec = importlib.util.spec_from_file_location("main_window", main_window_path)
                main_window_module = importlib.util.module_from_spec(spec)
                sys.modules["main_window"] = main_window_module
                spec.loader.exec_module(main_window_module)
                MainWindow = main_window_module.MainWindow
                print("[GUI] Loaded MainWindow via importlib")
        else:
            # Development mode
            try:
                # Try standard import first
                from ui.main_window import MainWindow
                print("[GUI] Imported MainWindow from ui.main_window (development mode)")
            except ImportError:
                # Fallback: manual module loading untuk development mode
                spec = importlib.util.spec_from_file_location("main_window", main_window_path)
                main_window_module = importlib.util.module_from_spec(spec)
                sys.modules["main_window"] = main_window_module
                spec.loader.exec_module(main_window_module)
                MainWindow = main_window_module.MainWindow
                print("[GUI] Loaded MainWindow via importlib (development mode fallback)")

        # Console loading progress
        print("[LOADING] Initializing features...")

        # Create main window
        main_window = MainWindow()
        logger.info("[STARTUP] MainWindow created, entering event loop")

        # CRITICAL: Start real-time license monitoring
        if LICENSE_SYSTEM_AVAILABLE:
            try:
                from modules_client.license_monitor import create_license_monitor
                license_monitor = create_license_monitor(main_window)
                license_monitor.start_monitoring()
                print("[LICENSE] Real-time license monitoring started")
            except Exception as e:
                print(f"[LICENSE] Warning: License monitoring failed to start: {e}")

        print("[LOADING] Finalizing startup...")

        main_window.show()

        print("[LOADING] Ready!")

        print("[GUI] VocaLive GUI launched successfully")
        logger.info("GUI application started")

        # Enhanced application exit handling
        try:
            # Set up proper signal handling for graceful shutdown
            import signal

            def signal_handler(signum, frame):
                logger.info(f"Received signal {signum}, initiating graceful shutdown...")
                try:
                    main_window.close()
                    app.quit()
                except Exception as e:
                    logger.error(f"Error during signal shutdown: {e}")
                    app.exit(1)

            # Register signal handlers (Windows compatible)
            if hasattr(signal, 'SIGTERM'):
                signal.signal(signal.SIGTERM, signal_handler)
            if hasattr(signal, 'SIGINT'):
                signal.signal(signal.SIGINT, signal_handler)

            # Set quit on last window closed
            app.setQuitOnLastWindowClosed(True)

            # Start event loop with proper error handling
            logger.info("Starting Qt event loop...")
            exit_code = app.exec()

            print("[GUI] VocaLive GUI closed")
            logger.info(f"GUI application closed with exit code: {exit_code}")
            logger.info("[SHUTDOWN] App closing")

            # Flush Sentry — tutup sesi Release Health dengan bersih
            try:
                from modules_client.telemetry import close as telemetry_close
                telemetry_close()
            except Exception:
                pass

            # Force cleanup before exit
            try:
                app.closeAllWindows()
                app.quit()

                # Force garbage collection
                import gc
                gc.collect()

            except Exception as cleanup_error:
                logger.error(f"Error during final cleanup: {cleanup_error}")

            return exit_code

        except Exception as event_loop_error:
            logger.error(f"Event loop error: {event_loop_error}")
            try:
                app.exit(1)
            except Exception:
                pass
            return 1

    except Exception as e:
        error_msg = f"Failed to launch GUI: {e}"
        print(f"[ERROR] {error_msg}")
        logger.error(error_msg)

        # Show error in message box if possible
        try:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(None, "VocaLive Error", error_msg)
        except Exception:
            pass

        return 1

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
