#!/usr/bin/env python3
"""
VocaLive - Professional License Dialog
Modern license activation interface dengan real-time validation
"""

import sys
import os
import threading
import time
from pathlib import Path
from typing import Optional, Tuple

from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QPropertyAnimation, QEasingCurve, QRect
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QProgressBar, QTextEdit, QFrame, QSpacerItem, QSizePolicy, QApplication,
    QWidget, QGraphicsDropShadowEffect, QMessageBox
)
from PyQt6.QtGui import (
    QFont, QPalette, QColor, QPainter, QBrush, QLinearGradient, 
    QPixmap, QPen, QIcon, QMovie
)

# Import license manager
try:
    from modules_client.license_manager import LicenseManager
except ImportError:
    # Fallback for development/local import
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'modules_client'))
    from license_manager import LicenseManager


class LicenseValidationWorker(QThread):
    """Worker thread for license validation"""
    
    validation_complete = pyqtSignal(bool, str, dict)  # success, message, data
    progress_update = pyqtSignal(str)  # status message
    
    def __init__(self, license_key: str, license_manager: LicenseManager):
        super().__init__()
        self.license_key = license_key
        self.license_manager = license_manager
    
    def run(self):
        """Run license validation in background"""
        try:
            self.progress_update.emit("Validating license format...")
            time.sleep(0.5)
            
            if not self.license_key.strip():
                self.validation_complete.emit(False, "License key cannot be empty", {})
                return
            
            self.progress_update.emit("Connecting to license server...")
            time.sleep(1.0)
            
            self.progress_update.emit("Checking license status...")
            time.sleep(0.5)
            
            # Actual validation
            is_valid, message, data = self.license_manager.validate_license_online(self.license_key)
            
            if is_valid:
                self.progress_update.emit("License validated successfully!")
                time.sleep(0.5)
                
                self.progress_update.emit("Saving license data...")
                time.sleep(0.5)
                
                # Save license data
                if self.license_manager.save_license_data(self.license_key, data):
                    self.validation_complete.emit(True, "License activated successfully!", data)
                else:
                    self.validation_complete.emit(False, "Failed to save license data", {})
            else:
                self.validation_complete.emit(False, message, data)
                
        except Exception as e:
            self.validation_complete.emit(False, f"Validation error: {str(e)}", {})


class AnimatedButton(QPushButton):
    """Custom animated button with hover effects"""
    
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setMinimumHeight(45)
        self.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        
        # Animation setup
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(150)
        self.animation.setEasingCurve(QEasingCurve.Type.OutQuad)
        
        self.original_geometry = None
        
        # Style
        self.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4CAF50, stop:1 #45a049);
                border: none;
                border-radius: 8px;
                color: white;
                padding: 12px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5CBF60, stop:1 #52b055);
                transform: scale(1.02);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3e8e41, stop:1 #367c39);
            }
            QPushButton:disabled {
                background: #cccccc;
                color: #666666;
            }
        """)
    
    def enterEvent(self, event):
        """Mouse enter animation"""
        if self.original_geometry is None:
            self.original_geometry = self.geometry()
        
        # Scale up slightly
        new_geo = QRect(
            self.original_geometry.x() - 2,
            self.original_geometry.y() - 2,
            self.original_geometry.width() + 4,
            self.original_geometry.height() + 4
        )
        
        self.animation.setStartValue(self.geometry())
        self.animation.setEndValue(new_geo)
        self.animation.start()
        
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Mouse leave animation"""
        if self.original_geometry:
            self.animation.setStartValue(self.geometry())
            self.animation.setEndValue(self.original_geometry)
            self.animation.start()
        
        super().leaveEvent(event)


class ModernProgressBar(QProgressBar):
    """Custom modern progress bar"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(8)
        self.setMaximumHeight(8)
        self.setTextVisible(False)
        
        self.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 4px;
                background-color: #E0E0E0;
            }
            QProgressBar::chunk {
                border-radius: 4px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4CAF50, stop:0.5 #8BC34A, stop:1 #4CAF50);
            }
        """)


class LicenseDialog(QDialog):
    """Professional License Activation Dialog"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.license_manager = LicenseManager()
        self.validation_worker = None
        
        self.setWindowTitle("VocaLive - License Activation")
        self.setFixedSize(500, 650)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowCloseButtonHint)
        self.setModal(True)
        
        # Apply modern styling
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f8f9fa, stop:1 #e9ecef);
                border-radius: 15px;
            }
        """)
        
        self.init_ui()
        self.center_on_screen()
        
        # Add drop shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 5)
        shadow.setColor(QColor(0, 0, 0, 80))
        self.setGraphicsEffect(shadow)
    
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(25)
        
        # Header section
        header_frame = self.create_header_section()
        layout.addWidget(header_frame)
        
        # License input section
        input_frame = self.create_input_section()
        layout.addWidget(input_frame)
        
        # Progress section
        progress_frame = self.create_progress_section()
        layout.addWidget(progress_frame)
        
        # Status section
        status_frame = self.create_status_section()
        layout.addWidget(status_frame)
        
        # Button section
        button_frame = self.create_button_section()
        layout.addWidget(button_frame)
        
        # Add stretch
        layout.addStretch()
        
        self.setLayout(layout)
    
    def create_header_section(self) -> QFrame:
        """Create header section with logo and title"""
        frame = QFrame()
        frame.setMaximumHeight(120)
        
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(10)
        
        # Logo/Icon (using text for now)
        logo_label = QLabel("🚀")
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_label.setStyleSheet("""
            QLabel {
                font-size: 48px;
                color: #4CAF50;
                margin: 10px;
            }
        """)
        layout.addWidget(logo_label)
        
        # Title
        title_label = QLabel("VocaLive License Activation")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title_label.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                margin: 5px;
            }
        """)
        layout.addWidget(title_label)
        
        # Subtitle
        subtitle_label = QLabel("Enter your license key to activate VocaLive")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setFont(QFont("Segoe UI", 10))
        subtitle_label.setStyleSheet("""
            QLabel {
                color: #6c757d;
                margin-bottom: 10px;
            }
        """)
        layout.addWidget(subtitle_label)
        
        frame.setLayout(layout)
        return frame
    
    def create_input_section(self) -> QFrame:
        """Create license input section"""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background: white;
                border-radius: 12px;
                padding: 20px;
                margin: 5px;
            }
        """)
        
        # Add subtle shadow to frame
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setOffset(0, 2)
        shadow.setColor(QColor(0, 0, 0, 20))
        frame.setGraphicsEffect(shadow)
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Input label
        label = QLabel("License Key:")
        label.setFont(QFont("Segoe UI", 11, QFont.Weight.Medium))
        label.setStyleSheet("color: #495057; margin-bottom: 5px;")
        layout.addWidget(label)
        
        # License input field
        self.license_input = QLineEdit()
        self.license_input.setPlaceholderText("Enter your license key...")
        self.license_input.setMinimumHeight(45)
        self.license_input.setFont(QFont("Segoe UI", 11))
        self.license_input.setStyleSheet("""
            QLineEdit {
                border: 2px solid #e9ecef;
                border-radius: 8px;
                padding: 12px 15px;
                font-size: 11pt;
                background: #f8f9fa;
                color: #000000;
            }
            QLineEdit:focus {
                border: 2px solid #4CAF50;
                background: white;
                color: #000000;
            }
            QLineEdit:hover {
                border: 2px solid #ced4da;
            }
        """)
        
        # Connect enter key to validation
        self.license_input.returnPressed.connect(self.start_validation)
        layout.addWidget(self.license_input)
        
        # Help text
        help_label = QLabel("💡 Contact support if you don't have a license key")
        help_label.setFont(QFont("Segoe UI", 9))
        help_label.setStyleSheet("color: #6c757d; margin-top: 5px;")
        layout.addWidget(help_label)
        
        frame.setLayout(layout)
        return frame
    
    def create_progress_section(self) -> QFrame:
        """Create progress section"""
        self.progress_frame = QFrame()
        self.progress_frame.hide()  # Initially hidden
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Progress bar
        self.progress_bar = ModernProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate
        layout.addWidget(self.progress_bar)
        
        # Progress label
        self.progress_label = QLabel("Initializing...")
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_label.setFont(QFont("Segoe UI", 10))
        self.progress_label.setStyleSheet("""
            QLabel {
                color: #495057;
                padding: 5px;
            }
        """)
        layout.addWidget(self.progress_label)
        
        self.progress_frame.setLayout(layout)
        return self.progress_frame
    
    def create_status_section(self) -> QFrame:
        """Create status display section"""
        self.status_frame = QFrame()
        self.status_frame.hide()  # Initially hidden
        
        layout = QVBoxLayout()
        
        # Status text area
        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(120)
        self.status_text.setReadOnly(True)
        self.status_text.setFont(QFont("Consolas", 9))
        self.status_text.setStyleSheet("""
            QTextEdit {
                background: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 10px;
                color: #495057;
            }
        """)
        layout.addWidget(self.status_text)
        
        self.status_frame.setLayout(layout)
        return self.status_frame
    
    def create_button_section(self) -> QFrame:
        """Create button section"""
        frame = QFrame()
        
        layout = QHBoxLayout()
        layout.setSpacing(15)
        
        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setMinimumHeight(45)
        self.cancel_button.setFont(QFont("Segoe UI", 11))
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background: #6c757d;
                border: none;
                border-radius: 8px;
                color: white;
                padding: 12px 20px;
            }
            QPushButton:hover {
                background: #5a6268;
            }
            QPushButton:pressed {
                background: #545b62;
            }
        """)
        self.cancel_button.clicked.connect(self.reject)
        layout.addWidget(self.cancel_button)
        
        # Validate button
        self.validate_button = AnimatedButton("Activate License")
        self.validate_button.clicked.connect(self.start_validation)
        layout.addWidget(self.validate_button)
        
        frame.setLayout(layout)
        return frame
    
    def center_on_screen(self):
        """Center dialog on screen"""
        if self.parent():
            # Center on parent
            parent_geo = self.parent().geometry()
            x = parent_geo.x() + (parent_geo.width() - self.width()) // 2
            y = parent_geo.y() + (parent_geo.height() - self.height()) // 2
            self.move(x, y)
        else:
            # Center on screen
            screen = QApplication.primaryScreen().geometry()
            x = (screen.width() - self.width()) // 2
            y = (screen.height() - self.height()) // 2
            self.move(x, y)
    
    def start_validation(self):
        """Start license validation process"""
        license_key = self.license_input.text().strip()
        
        if not license_key:
            self.show_error("Please enter a license key")
            return
        
        # Disable input during validation
        self.license_input.setEnabled(False)
        self.validate_button.setEnabled(False)
        
        # Show progress
        self.progress_frame.show()
        self.status_frame.show()
        self.status_text.clear()
        
        # Start validation worker
        self.validation_worker = LicenseValidationWorker(license_key, self.license_manager)
        self.validation_worker.validation_complete.connect(self.on_validation_complete)
        self.validation_worker.progress_update.connect(self.on_progress_update)
        self.validation_worker.start()
    
    def on_progress_update(self, message: str):
        """Handle progress updates"""
        self.progress_label.setText(message)
        self.status_text.append(f"• {message}")
        
        # Auto-scroll to bottom
        cursor = self.status_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.status_text.setTextCursor(cursor)
    
    def on_validation_complete(self, success: bool, message: str, data: dict):
        """Handle validation completion"""
        # Hide progress bar
        self.progress_frame.hide()
        
        # Re-enable input
        self.license_input.setEnabled(True)
        self.validate_button.setEnabled(True)
        
        if success:
            self.show_success(message, data)
            QTimer.singleShot(1500, self.accept)  # Close after 1.5 seconds
        else:
            self.show_error(message)
    
    def show_success(self, message: str, data: dict):
        """Show success message"""
        self.status_text.append(f"\n✅ SUCCESS: {message}")
        
        # Show license info
        if data:
            self.status_text.append("\n📋 License Information:")
            if data.get('EXPIRY_DATE'):
                self.status_text.append(f"   Expires: {data.get('EXPIRY_DATE')}")
            if data.get('NOTES'):
                self.status_text.append(f"   Notes: {data.get('NOTES')}")
        
        # Auto-scroll to bottom
        cursor = self.status_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.status_text.setTextCursor(cursor)
    
    def show_error(self, message: str):
        """Show error message"""
        self.status_text.append(f"\n❌ ERROR: {message}")
        
        # Auto-scroll to bottom
        cursor = self.status_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.status_text.setTextCursor(cursor)
        
        # Flash the input field
        self.flash_input_error()
    
    def flash_input_error(self):
        """Flash input field red to indicate error"""
        original_style = self.license_input.styleSheet()
        error_style = original_style.replace(
            "border: 2px solid #e9ecef;",
            "border: 2px solid #dc3545;"
        )
        
        self.license_input.setStyleSheet(error_style)
        
        # Reset after 1 second
        QTimer.singleShot(1000, lambda: self.license_input.setStyleSheet(original_style))
    
    def closeEvent(self, event):
        """Handle dialog close event"""
        if self.validation_worker and self.validation_worker.isRunning():
            self.validation_worker.terminate()
            self.validation_worker.wait()
        event.accept()


def show_license_dialog(parent=None) -> Tuple[bool, Optional[str]]:
    """
    Show license dialog and return result
    Returns: (success, license_key)
    """
    dialog = LicenseDialog(parent)
    result = dialog.exec()
    
    if result == QDialog.DialogCode.Accepted:
        return True, dialog.license_input.text().strip()
    else:
        return False, None


# Test function
def test_license_dialog():
    """Test the license dialog"""
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    success, license_key = show_license_dialog()
    
    if success:
        print(f"License activated: {license_key}")
    else:
        print("License activation cancelled")
    
    return success


if __name__ == "__main__":
    test_license_dialog()