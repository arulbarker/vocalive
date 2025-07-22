# ui/viewers_tab.py - Viewer Management Tab untuk Pro Mode
import sys
import os
import json
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List

# PyQt6 imports
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTextEdit, QLineEdit, QComboBox, QCheckBox, QSpinBox,
    QGroupBox, QTabWidget, QProgressBar, QSlider, QFrame,
    QMessageBox, QFileDialog, QListWidget, QListWidgetItem,
    QTableWidget, QTableWidgetItem, QSplitter
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, pyqtSlot
from PyQt6.QtGui import QFont, QPixmap, QIcon

# Setup project root
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

# Import modules
try:
    from modules_client.api import APIClient
    from modules_client.config_manager import ConfigManager
    from modules_client.logger import setup_logger
except ImportError as e:
    print(f"Import error: {e}")

logger = setup_logger('ViewersTab')

class ViewersTab(QWidget):
    """Advanced Viewer Management Tab untuk Pro Mode"""
    
    def __init__(self):
        super().__init__()
        self.api_client = APIClient()
        self.config_manager = ConfigManager()
        self.settings = self.config_manager.load_settings()
        
        # Viewer data
        self.viewers_data = []
        self.active_viewers = []
        self.viewer_stats = {}
        
        self.setup_ui()
        self.load_settings()
        self.start_viewer_monitoring()
        
    def setup_ui(self):
        """Setup UI untuk viewer management"""
        layout = QVBoxLayout()
        
        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel("👥 Viewer Management Pro")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #1877F2;")
        header_layout.addWidget(title_label)
        
        status_label = QLabel("🟢 Live Monitoring Active")
        status_label.setStyleSheet("color: #42B72A; font-weight: bold;")
        header_layout.addWidget(status_label)
        layout.addLayout(header_layout)
        
        # Main content dengan tabs
        self.tab_widget = QTabWidget()
        
        # Tab 1: Live Viewers
        self.setup_live_tab()
        
        # Tab 2: Viewer Analytics
        self.setup_analytics_tab()
        
        # Tab 3: Engagement Tools
        self.setup_engagement_tab()
        
        # Tab 4: Viewer Database
        self.setup_database_tab()
        
        layout.addWidget(self.tab_widget)
        self.setLayout(layout)
        
    def setup_live_tab(self):
        """Setup live viewers monitoring tab"""
        live_widget = QWidget()
        live_layout = QVBoxLayout()
        
        # Live Viewer Stats
        stats_group = QGroupBox("📊 Live Viewer Statistics")
        stats_layout = QVBoxLayout()
        
        # Stats grid
        stats_grid = QHBoxLayout()
        
        # Current viewers
        current_layout = QVBoxLayout()
        current_layout.addWidget(QLabel("👥 Current Viewers"))
        self.current_viewers_label = QLabel("0")
        self.current_viewers_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #1877F2;")
        current_layout.addWidget(self.current_viewers_label)
        stats_grid.addLayout(current_layout)
        
        # Peak viewers
        peak_layout = QVBoxLayout()
        peak_layout.addWidget(QLabel("📈 Peak Viewers"))
        self.peak_viewers_label = QLabel("0")
        self.peak_viewers_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #42B72A;")
        peak_layout.addWidget(self.peak_viewers_label)
        stats_grid.addLayout(peak_layout)
        
        # Average viewers
        avg_layout = QVBoxLayout()
        avg_layout.addWidget(QLabel("📊 Average Viewers"))
        self.avg_viewers_label = QLabel("0")
        self.avg_viewers_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #F5B800;")
        avg_layout.addWidget(self.avg_viewers_label)
        stats_grid.addLayout(avg_layout)
        
        # Total unique viewers
        total_layout = QVBoxLayout()
        total_layout.addWidget(QLabel("🎯 Total Unique"))
        self.total_viewers_label = QLabel("0")
        self.total_viewers_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #FA383E;")
        total_layout.addWidget(self.total_viewers_label)
        stats_grid.addLayout(total_layout)
        
        stats_layout.addLayout(stats_grid)
        stats_group.setLayout(stats_layout)
        live_layout.addWidget(stats_group)
        
        # Live Viewer List
        list_group = QGroupBox("👥 Live Viewers")
        list_layout = QVBoxLayout()
        
        # Viewer table
        self.viewer_table = QTableWidget()
        self.viewer_table.setColumnCount(6)
        self.viewer_table.setHorizontalHeaderLabels([
            "👤 Username", "⏱️ Watch Time", "💬 Messages", "🎁 Gifts", 
            "⭐ Engagement", "📊 Status"
        ])
        self.viewer_table.setStyleSheet("""
            QTableWidget {
                background-color: #242526;
                color: #FFFFFF;
                border: 1px solid #3A3B3C;
                border-radius: 8px;
                gridline-color: #3A3B3C;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #3A3B3C;
            }
            QTableWidget::item:selected {
                background-color: #1877F2;
            }
            QHeaderView::section {
                background-color: #3A3B3C;
                color: #FFFFFF;
                padding: 8px;
                border: none;
                border-bottom: 1px solid #4E4F50;
            }
        """)
        list_layout.addWidget(self.viewer_table)
        
        # Viewer controls
        controls_layout = QHBoxLayout()
        controls_layout.addWidget(QPushButton("🔄 Refresh List"))
        controls_layout.addWidget(QPushButton("📥 Export Data"))
        controls_layout.addWidget(QPushButton("🎯 Highlight VIP"))
        controls_layout.addWidget(QPushButton("📊 View Details"))
        list_layout.addLayout(controls_layout)
        
        list_group.setLayout(list_layout)
        live_layout.addWidget(list_group)
        
        live_widget.setLayout(live_layout)
        self.tab_widget.addTab(live_widget, "👥 Live Viewers")
        
    def setup_analytics_tab(self):
        """Setup viewer analytics tab"""
        analytics_widget = QWidget()
        analytics_layout = QVBoxLayout()
        
        # Viewer Demographics
        demo_group = QGroupBox("📊 Viewer Demographics")
        demo_layout = QVBoxLayout()
        
        # Demographics display
        self.demo_display = QTextEdit()
        self.demo_display.setReadOnly(True)
        self.demo_display.setMaximumHeight(150)
        self.demo_display.setStyleSheet("""
            QTextEdit {
                background-color: #242526;
                color: #FFFFFF;
                border: 1px solid #3A3B3C;
                border-radius: 8px;
                padding: 10px;
                font-family: 'Consolas', monospace;
                font-size: 12px;
            }
        """)
        demo_layout.addWidget(self.demo_display)
        
        # Update demographics button
        update_demo_btn = QPushButton("🔄 Update Demographics")
        update_demo_btn.clicked.connect(self.update_demographics)
        demo_layout.addWidget(update_demo_btn)
        
        demo_group.setLayout(demo_layout)
        analytics_layout.addWidget(demo_group)
        
        # Engagement Metrics
        engagement_group = QGroupBox("📈 Engagement Metrics")
        engagement_layout = QVBoxLayout()
        
        # Engagement stats
        engagement_stats = QHBoxLayout()
        
        # Chat engagement
        chat_layout = QVBoxLayout()
        chat_layout.addWidget(QLabel("💬 Chat Engagement"))
        self.chat_engagement_label = QLabel("0%")
        self.chat_engagement_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #1877F2;")
        chat_layout.addWidget(self.chat_engagement_label)
        engagement_stats.addLayout(chat_layout)
        
        # Gift engagement
        gift_layout = QVBoxLayout()
        gift_layout.addWidget(QLabel("🎁 Gift Engagement"))
        self.gift_engagement_label = QLabel("0%")
        self.gift_engagement_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #42B72A;")
        gift_layout.addWidget(self.gift_engagement_label)
        engagement_stats.addLayout(gift_layout)
        
        # Subscription engagement
        sub_layout = QVBoxLayout()
        sub_layout.addWidget(QLabel("⭐ Subscription Rate"))
        self.sub_engagement_label = QLabel("0%")
        self.sub_engagement_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #F5B800;")
        sub_layout.addWidget(self.sub_engagement_label)
        engagement_stats.addLayout(sub_layout)
        
        # Retention rate
        retention_layout = QVBoxLayout()
        retention_layout.addWidget(QLabel("⏱️ Retention Rate"))
        self.retention_label = QLabel("0%")
        self.retention_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #FA383E;")
        retention_layout.addWidget(self.retention_label)
        engagement_stats.addLayout(retention_layout)
        
        engagement_layout.addLayout(engagement_stats)
        engagement_group.setLayout(engagement_layout)
        analytics_layout.addWidget(engagement_group)
        
        # Viewer Behavior
        behavior_group = QGroupBox("🎯 Viewer Behavior Analysis")
        behavior_layout = QVBoxLayout()
        
        self.behavior_display = QTextEdit()
        self.behavior_display.setReadOnly(True)
        self.behavior_display.setMaximumHeight(200)
        self.behavior_display.setStyleSheet("""
            QTextEdit {
                background-color: #242526;
                color: #FFFFFF;
                border: 1px solid #3A3B3C;
                border-radius: 8px;
                padding: 10px;
                font-family: 'Consolas', monospace;
                font-size: 12px;
            }
        """)
        behavior_layout.addWidget(self.behavior_display)
        
        behavior_group.setLayout(behavior_layout)
        analytics_layout.addWidget(behavior_group)
        
        analytics_widget.setLayout(analytics_layout)
        self.tab_widget.addTab(analytics_widget, "📊 Viewer Analytics")
        
    def setup_engagement_tab(self):
        """Setup engagement tools tab"""
        engagement_widget = QWidget()
        engagement_layout = QVBoxLayout()
        
        # Auto Engagement
        auto_group = QGroupBox("🤖 Auto Engagement Tools")
        auto_layout = QVBoxLayout()
        
        # Auto welcome
        welcome_layout = QHBoxLayout()
        self.auto_welcome_check = QCheckBox("👋 Auto Welcome New Viewers")
        self.auto_welcome_check.setChecked(True)
        welcome_layout.addWidget(self.auto_welcome_check)
        
        self.welcome_message_input = QLineEdit()
        self.welcome_message_input.setPlaceholderText("Welcome message template...")
        self.welcome_message_input.setText("Welcome {username} to the stream! 🎉")
        welcome_layout.addWidget(self.welcome_message_input)
        auto_layout.addLayout(welcome_layout)
        
        # Auto shoutout
        shoutout_layout = QHBoxLayout()
        self.auto_shoutout_check = QCheckBox("📢 Auto Shoutout VIP Viewers")
        self.auto_shoutout_check.setChecked(True)
        shoutout_layout.addWidget(self.auto_shoutout_check)
        
        self.shoutout_interval_spin = QSpinBox()
        self.shoutout_interval_spin.setRange(5, 60)
        self.shoutout_interval_spin.setValue(15)
        self.shoutout_interval_spin.setSuffix(" min")
        shoutout_layout.addWidget(QLabel("Interval:"))
        shoutout_layout.addWidget(self.shoutout_interval_spin)
        auto_layout.addLayout(shoutout_layout)
        
        # Auto thank you
        thank_layout = QHBoxLayout()
        self.auto_thank_check = QCheckBox("🙏 Auto Thank for Gifts")
        self.auto_thank_check.setChecked(True)
        thank_layout.addWidget(self.auto_thank_check)
        
        self.thank_message_input = QLineEdit()
        self.thank_message_input.setPlaceholderText("Thank you message template...")
        self.thank_message_input.setText("Thank you {username} for the {gift}! ❤️")
        thank_layout.addWidget(self.thank_message_input)
        auto_layout.addLayout(thank_layout)
        
        auto_group.setLayout(auto_layout)
        engagement_layout.addWidget(auto_group)
        
        # Interactive Tools
        interactive_group = QGroupBox("🎮 Interactive Tools")
        interactive_layout = QVBoxLayout()
        
        # Polls
        poll_layout = QHBoxLayout()
        poll_layout.addWidget(QLabel("📊 Quick Poll:"))
        self.poll_question_input = QLineEdit()
        self.poll_question_input.setPlaceholderText("Enter poll question...")
        poll_layout.addWidget(self.poll_question_input)
        
        self.create_poll_btn = QPushButton("📊 Create Poll")
        self.create_poll_btn.setStyleSheet("""
            QPushButton {
                background-color: #1877F2;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
        """)
        self.create_poll_btn.clicked.connect(self.create_poll)
        poll_layout.addWidget(self.create_poll_btn)
        interactive_layout.addLayout(poll_layout)
        
        # Giveaways
        giveaway_layout = QHBoxLayout()
        giveaway_layout.addWidget(QLabel("🎁 Giveaway:"))
        self.giveaway_prize_input = QLineEdit()
        self.giveaway_prize_input.setPlaceholderText("Enter prize...")
        giveaway_layout.addWidget(self.giveaway_prize_input)
        
        self.start_giveaway_btn = QPushButton("🎁 Start Giveaway")
        self.start_giveaway_btn.setStyleSheet("""
            QPushButton {
                background-color: #42B72A;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
        """)
        self.start_giveaway_btn.clicked.connect(self.start_giveaway)
        giveaway_layout.addWidget(self.start_giveaway_btn)
        interactive_layout.addLayout(giveaway_layout)
        
        # Challenges
        challenge_layout = QHBoxLayout()
        challenge_layout.addWidget(QLabel("🏆 Challenge:"))
        self.challenge_input = QLineEdit()
        self.challenge_input.setPlaceholderText("Enter challenge...")
        challenge_layout.addWidget(self.challenge_input)
        
        self.start_challenge_btn = QPushButton("🏆 Start Challenge")
        self.start_challenge_btn.setStyleSheet("""
            QPushButton {
                background-color: #F5B800;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
        """)
        self.start_challenge_btn.clicked.connect(self.start_challenge)
        challenge_layout.addWidget(self.start_challenge_btn)
        interactive_layout.addLayout(challenge_layout)
        
        interactive_group.setLayout(interactive_layout)
        engagement_layout.addWidget(interactive_group)
        
        engagement_widget.setLayout(engagement_layout)
        self.tab_widget.addTab(engagement_widget, "🎮 Engagement Tools")
        
    def setup_database_tab(self):
        """Setup viewer database tab"""
        database_widget = QWidget()
        database_layout = QVBoxLayout()
        
        # Viewer Database
        db_group = QGroupBox("🗄️ Viewer Database")
        db_layout = QVBoxLayout()
        
        # Search functionality
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("🔍 Search Viewer:"))
        self.viewer_search_input = QLineEdit()
        self.viewer_search_input.setPlaceholderText("Enter username...")
        search_layout.addWidget(self.viewer_search_input)
        
        self.search_btn = QPushButton("🔍 Search")
        self.search_btn.clicked.connect(self.search_viewer)
        search_layout.addWidget(self.search_btn)
        db_layout.addLayout(search_layout)
        
        # Viewer details
        details_group = QGroupBox("👤 Viewer Details")
        details_layout = QVBoxLayout()
        
        self.viewer_details_display = QTextEdit()
        self.viewer_details_display.setReadOnly(True)
        self.viewer_details_display.setMaximumHeight(200)
        self.viewer_details_display.setStyleSheet("""
            QTextEdit {
                background-color: #242526;
                color: #FFFFFF;
                border: 1px solid #3A3B3C;
                border-radius: 8px;
                padding: 10px;
                font-family: 'Consolas', monospace;
                font-size: 12px;
            }
        """)
        details_layout.addWidget(self.viewer_details_display)
        
        details_group.setLayout(details_layout)
        db_layout.addWidget(details_group)
        
        # Database controls
        db_controls = QHBoxLayout()
        db_controls.addWidget(QPushButton("📥 Export Database"))
        db_controls.addWidget(QPushButton("🔄 Backup Database"))
        db_controls.addWidget(QPushButton("🗑️ Clear Database"))
        db_controls.addWidget(QPushButton("📊 Database Stats"))
        db_layout.addLayout(db_controls)
        
        db_group.setLayout(db_layout)
        database_layout.addWidget(db_group)
        
        database_widget.setLayout(database_layout)
        self.tab_widget.addTab(database_widget, "🗄️ Viewer Database")
        
    def load_settings(self):
        """Load viewer settings"""
        try:
            # Load viewer-specific settings
            self.auto_welcome_check.setChecked(
                self.settings.get("viewer_auto_welcome", True)
            )
            self.auto_shoutout_check.setChecked(
                self.settings.get("viewer_auto_shoutout", True)
            )
            self.auto_thank_check.setChecked(
                self.settings.get("viewer_auto_thank", True)
            )
            
            welcome_message = self.settings.get("viewer_welcome_message", "Welcome {username} to the stream! 🎉")
            self.welcome_message_input.setText(welcome_message)
            
            thank_message = self.settings.get("viewer_thank_message", "Thank you {username} for the {gift}! ❤️")
            self.thank_message_input.setText(thank_message)
            
        except Exception as e:
            logger.error(f"Error loading viewer settings: {e}")
            
    def save_settings(self):
        """Save viewer settings"""
        try:
            self.settings["viewer_auto_welcome"] = self.auto_welcome_check.isChecked()
            self.settings["viewer_auto_shoutout"] = self.auto_shoutout_check.isChecked()
            self.settings["viewer_auto_thank"] = self.auto_thank_check.isChecked()
            self.settings["viewer_welcome_message"] = self.welcome_message_input.text()
            self.settings["viewer_thank_message"] = self.thank_message_input.text()
            self.settings["viewer_shoutout_interval"] = self.shoutout_interval_spin.value()
            
            self.config_manager.save_settings()
            
        except Exception as e:
            logger.error(f"Error saving viewer settings: {e}")
            
    def start_viewer_monitoring(self):
        """Start monitoring viewers"""
        try:
            # Simulate viewer data
            self.update_viewer_stats()
            
            # Start timer untuk update berkala
            self.monitor_timer = QTimer()
            self.monitor_timer.timeout.connect(self.update_viewer_stats)
            self.monitor_timer.start(5000)  # Update setiap 5 detik
            
        except Exception as e:
            logger.error(f"Error starting viewer monitoring: {e}")
            
    def update_viewer_stats(self):
        """Update viewer statistics"""
        try:
            # Simulate live viewer data
            current_viewers = 125
            peak_viewers = 342
            avg_viewers = 156
            total_unique = 1247
            
            self.current_viewers_label.setText(str(current_viewers))
            self.peak_viewers_label.setText(str(peak_viewers))
            self.avg_viewers_label.setText(str(avg_viewers))
            self.total_viewers_label.setText(str(total_unique))
            
            # Update viewer table
            self.update_viewer_table()
            
        except Exception as e:
            logger.error(f"Error updating viewer stats: {e}")
            
    def update_viewer_table(self):
        """Update viewer table dengan data live"""
        try:
            # Simulate viewer data
            viewers = [
                ("GamingPro123", "2h 15m", "47", "3", "High", "Active"),
                ("StreamFan456", "1h 30m", "23", "1", "Medium", "Active"),
                ("VIPViewer789", "3h 45m", "89", "12", "Very High", "VIP"),
                ("NewUser001", "0h 15m", "2", "0", "Low", "New"),
                ("RegularViewer", "1h 20m", "34", "2", "Medium", "Regular")
            ]
            
            self.viewer_table.setRowCount(len(viewers))
            
            for row, viewer in enumerate(viewers):
                for col, data in enumerate(viewer):
                    item = QTableWidgetItem(data)
                    self.viewer_table.setItem(row, col, item)
                    
        except Exception as e:
            logger.error(f"Error updating viewer table: {e}")
            
    def update_demographics(self):
        """Update demographics display"""
        try:
            demo_text = """
📊 VIEWER DEMOGRAPHICS
======================
🌍 Geographic Distribution:
   - Indonesia: 65%
   - Malaysia: 15%
   - Singapore: 10%
   - Other: 10%

👥 Age Groups:
   - 13-17: 25%
   - 18-24: 45%
   - 25-34: 20%
   - 35+: 10%

🎮 Gaming Preferences:
   - MOBA: 60%
   - FPS: 20%
   - RPG: 15%
   - Other: 5%

⏰ Peak Activity Times:
   - 19:00-22:00: 40%
   - 15:00-18:00: 30%
   - 22:00-01:00: 20%
   - Other: 10%
            """
            
            self.demo_display.setPlainText(demo_text)
            
            # Update engagement metrics
            self.chat_engagement_label.setText("78%")
            self.gift_engagement_label.setText("23%")
            self.sub_engagement_label.setText("12%")
            self.retention_label.setText("85%")
            
        except Exception as e:
            logger.error(f"Error updating demographics: {e}")
            
    def create_poll(self):
        """Create interactive poll"""
        try:
            question = self.poll_question_input.text()
            if not question.strip():
                QMessageBox.warning(self, "Warning", "Please enter a poll question")
                return
                
            QMessageBox.information(self, "Poll Created", f"Poll created: {question}")
            self.poll_question_input.clear()
            
        except Exception as e:
            logger.error(f"Error creating poll: {e}")
            
    def start_giveaway(self):
        """Start giveaway"""
        try:
            prize = self.giveaway_prize_input.text()
            if not prize.strip():
                QMessageBox.warning(self, "Warning", "Please enter a prize")
                return
                
            QMessageBox.information(self, "Giveaway Started", f"Giveaway started for: {prize}")
            self.giveaway_prize_input.clear()
            
        except Exception as e:
            logger.error(f"Error starting giveaway: {e}")
            
    def start_challenge(self):
        """Start viewer challenge"""
        try:
            challenge = self.challenge_input.text()
            if not challenge.strip():
                QMessageBox.warning(self, "Warning", "Please enter a challenge")
                return
                
            QMessageBox.information(self, "Challenge Started", f"Challenge started: {challenge}")
            self.challenge_input.clear()
            
        except Exception as e:
            logger.error(f"Error starting challenge: {e}")
            
    def search_viewer(self):
        """Search viewer in database"""
        try:
            username = self.viewer_search_input.text()
            if not username.strip():
                QMessageBox.warning(self, "Warning", "Please enter a username")
                return
                
            # Simulate viewer details
            details = f"""
👤 VIEWER DETAILS: {username}
===============================
📅 First Seen: 2025-01-15
⏱️ Total Watch Time: 45h 23m
💬 Total Messages: 1,247
🎁 Total Gifts: 23
⭐ Engagement Level: High
🏆 VIP Status: Regular
📊 Last Activity: 2 hours ago
🎮 Favorite Games: MOBA, FPS
🌍 Location: Indonesia
📱 Platform: Mobile
            """
            
            self.viewer_details_display.setPlainText(details)
            
        except Exception as e:
            logger.error(f"Error searching viewer: {e}")
            
    def closeEvent(self, event):
        """Save settings when closing"""
        self.save_settings()
        super().closeEvent(event)
