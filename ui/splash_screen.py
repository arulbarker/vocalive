"""
StreamMate AI Splash Screen
Loading screen for application startup
"""

import sys
from PyQt6.QtWidgets import QApplication, QSplashScreen, QLabel, QVBoxLayout, QWidget, QProgressBar
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont
from pathlib import Path


class SplashScreen(QSplashScreen):
    """Simple splash screen with progress bar and loading messages"""
    
    def __init__(self):
        # Create a simple colored pixmap since we don't have a logo
        pixmap = QPixmap(400, 300)
        pixmap.fill(QColor(45, 45, 45))  # Dark gray background
        
        super().__init__(pixmap)
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint)
        
        # Setup UI
        self.setup_ui()
        
        # Progress tracking
        self.progress = 0
        self.max_progress = 100
        
    def setup_ui(self):
        """Setup the splash screen UI"""
        # Draw text on the pixmap
        painter = QPainter(self.pixmap())
        painter.setPen(QColor(255, 255, 255))  # White text
        
        # Title
        title_font = QFont("Arial", 24, QFont.Weight.Bold)
        painter.setFont(title_font)
        painter.drawText(50, 80, "StreamMate AI")
        
        # Subtitle
        subtitle_font = QFont("Arial", 12)
        painter.setFont(subtitle_font)
        painter.drawText(50, 110, "Live Streaming Automation Platform")
        
        # Version
        version_font = QFont("Arial", 10)
        painter.setFont(version_font)
        painter.drawText(50, 130, "Version 1.0.0")
        
        painter.end()
        
    def show_message(self, message):
        """Show loading message"""
        self.showMessage(
            f"\n\n\n\n\n\n\n\n\n{message}", 
            Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignBottom, 
            QColor(255, 255, 255)
        )
        QApplication.processEvents()
        
    def set_progress(self, value):
        """Update progress (0-100)"""
        self.progress = min(max(value, 0), 100)
        # Draw progress bar
        painter = QPainter(self.pixmap())
        
        # Clear previous progress bar area
        painter.fillRect(50, 200, 300, 20, QColor(45, 45, 45))
        
        # Draw progress bar background
        painter.fillRect(50, 200, 300, 20, QColor(60, 60, 60))
        
        # Draw progress bar fill
        progress_width = int((self.progress / 100) * 300)
        painter.fillRect(50, 200, progress_width, 20, QColor(0, 150, 255))
        
        # Draw progress text
        painter.setPen(QColor(255, 255, 255))
        font = QFont("Arial", 9)
        painter.setFont(font)
        painter.drawText(50, 240, f"Loading... {self.progress}%")
        
        painter.end()
        self.update()
        QApplication.processEvents()


class LoadingWorker(QThread):
    """Background worker for loading tasks"""
    progress_updated = pyqtSignal(int, str)
    finished = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.steps = [
            (10, "Initializing application..."),
            (20, "Loading configuration..."),
            (30, "Setting up database connections..."),
            (40, "Loading UI components..."),
            (50, "Initializing speech recognition..."),
            (60, "Setting up TTS engine..."),
            (70, "Loading tabs and features..."),
            (80, "Checking licenses and subscriptions..."),
            (90, "Finalizing setup..."),
            (100, "Ready to launch!")
        ]
        
    def run(self):
        """Simulate loading process"""
        import time
        
        for progress, message in self.steps:
            self.progress_updated.emit(progress, message)
            time.sleep(0.3)  # Simulate work being done
            
        self.finished.emit()


def show_splash_screen():
    """Show splash screen and return it for manual control"""
    splash = SplashScreen()
    splash.show()
    splash.show_message("Initializing StreamMate AI...")
    splash.set_progress(0)
    return splash


if __name__ == "__main__":
    # Test the splash screen
    app = QApplication(sys.argv)
    
    splash = show_splash_screen()
    
    # Simulate loading
    worker = LoadingWorker()
    worker.progress_updated.connect(lambda p, msg: (splash.set_progress(p), splash.show_message(msg)))
    worker.finished.connect(lambda: (splash.close(), app.quit()))
    worker.start()
    
    sys.exit(app.exec())