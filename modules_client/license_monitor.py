#!/usr/bin/env python3
"""
VocaLive - Real-time License Monitor
Monitors license status and force close app if manually disabled
"""

import sys
import time
import threading
from datetime import datetime
from PyQt6.QtCore import QTimer, QObject, pyqtSignal
from modules_client.license_manager import LicenseManager

class LicenseMonitor(QObject):
    """Real-time license monitor untuk aplikasi"""

    # Signals
    license_invalid = pyqtSignal(str)  # Emit when license becomes invalid
    license_warning = pyqtSignal(str, int)  # Emit when license expires soon (message, days)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.license_manager = LicenseManager()
        self.monitoring = False
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_license_status)

        # Check intervals - optimized for Google Sheets API limits
        self.check_interval = 120 * 60 * 1000  # 2 hours in milliseconds (API friendly)
        self.warning_days = 7  # Warn when less than 7 days remaining

        print("[LICENSE_MONITOR] Initialized")

    def start_monitoring(self):
        """Start real-time license monitoring"""
        if self.monitoring:
            return

        print("[LICENSE_MONITOR] Starting license monitoring...")
        self.monitoring = True

        # Initial check
        self.check_license_status()

        # Start periodic checks
        self.timer.start(self.check_interval)
        print(f"[LICENSE_MONITOR] Monitoring started (check every {self.check_interval/1000/60:.1f} minutes)")

    def stop_monitoring(self):
        """Stop license monitoring"""
        if not self.monitoring:
            return

        print("[LICENSE_MONITOR] Stopping license monitoring...")
        self.monitoring = False
        self.timer.stop()

    def check_license_status(self):
        """Check license status with real-time validation"""
        try:
            print(f"[LICENSE_MONITOR] Checking license status at {datetime.now().strftime('%H:%M:%S')}")

            # Cek session via AppScript (action=cek)
            is_valid, message = self.license_manager.is_license_valid(force_online_check=True)

            if not is_valid:
                print(f"[LICENSE_MONITOR] ❌ License invalid: {message}")
                self.license_invalid.emit(message)
                self.stop_monitoring()
                return

            # Check expiry warning
            license_info = self.license_manager.get_license_info()
            if license_info and 'days_remaining' in license_info:
                days_remaining = license_info['days_remaining']

                if days_remaining > 0 and days_remaining <= self.warning_days:
                    print(f"[LICENSE_MONITOR] ⚠️ License expires in {days_remaining} days")
                    self.license_warning.emit(f"License expires in {days_remaining} days", days_remaining)
                elif days_remaining == 0:
                    print(f"[LICENSE_MONITOR] ⚠️ License expires today!")
                    self.license_warning.emit("License expires today!", 0)
                elif license_info.get('is_unlimited', False):
                    print(f"[LICENSE_MONITOR] ✅ Unlimited license")
                else:
                    print(f"[LICENSE_MONITOR] ✅ License valid ({days_remaining} days remaining)")
            else:
                print(f"[LICENSE_MONITOR] ✅ License valid")

        except Exception as e:
            print(f"[LICENSE_MONITOR] Error checking license: {e}")
            # Don't emit invalid signal on network errors

class LicenseEnforcer:
    """Force application termination when license becomes invalid"""

    @staticmethod
    def force_close_application(reason="License invalid"):
        """Force close application immediately"""
        print(f"[LICENSE_ENFORCER] FORCE CLOSING APPLICATION: {reason}")

        try:
            # Show message to user
            from PyQt6.QtWidgets import QMessageBox, QApplication

            app = QApplication.instance()
            if app:
                # Create message box
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Icon.Critical)
                msg.setWindowTitle("License Invalid")
                msg.setText(f"Application will close.\n\nReason: {reason}")
                msg.setStandardButtons(QMessageBox.StandardButton.Ok)
                msg.exec()
        except Exception as e:
            print(f"[LICENSE_ENFORCER] Error showing message: {e}")

        # Force terminate
        try:
            # Close all windows
            from PyQt6.QtWidgets import QApplication
            app = QApplication.instance()
            if app:
                app.quit()
        except:
            pass

        # Nuclear option - force exit
        import os
        print("[LICENSE_ENFORCER] Terminating process...")
        os._exit(1)

def create_license_monitor(main_window=None):
    """Create and setup license monitor for main application"""
    monitor = LicenseMonitor()

    # Connect signals
    monitor.license_invalid.connect(
        lambda reason: LicenseEnforcer.force_close_application(reason)
    )

    monitor.license_warning.connect(
        lambda message, days: print(f"[LICENSE_WARNING] {message}")
    )

    return monitor

# Background license checker (thread-based for non-GUI usage)
class BackgroundLicenseChecker:
    """Background license checker untuk server/background tasks"""

    def __init__(self, check_interval=7200):  # 2 hours (API friendly)
        self.license_manager = LicenseManager()
        self.check_interval = check_interval
        self.running = False
        self.thread = None

    def start(self):
        """Start background checking"""
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        print(f"[BACKGROUND_CHECKER] Started (check every {self.check_interval/60:.1f} minutes)")

    def stop(self):
        """Stop background checking"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)

    def _monitor_loop(self):
        """Background monitoring loop"""
        while self.running:
            try:
                # Check license status
                is_valid, message = self.license_manager.is_license_valid(force_online_check=True)

                if not is_valid:
                    print(f"[BACKGROUND_CHECKER] License invalid: {message}")
                    # Force exit if running as background service
                    if __name__ == "__main__":
                        print("[BACKGROUND_CHECKER] Terminating background service")
                        sys.exit(1)
                    return
                else:
                    print(f"[BACKGROUND_CHECKER] License valid")

                # Wait for next check
                time.sleep(self.check_interval)

            except Exception as e:
                print(f"[BACKGROUND_CHECKER] Error: {e}")
                time.sleep(60)  # Wait 1 minute on error

if __name__ == "__main__":
    print("VocaLive - License Monitor (Background Mode)")
    print("=" * 50)

    # Run as background service
    checker = BackgroundLicenseChecker(check_interval=7200)  # 2 hours

    try:
        checker.start()

        # Keep running
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n[SHUTDOWN] License monitor stopped")
        checker.stop()