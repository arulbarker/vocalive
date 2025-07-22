# ui/cohost_tab_pro.py - Pro Mode Version
import sys
import os
import json
import time
import threading
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional

# PyQt6 imports
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTextEdit, QLineEdit, QComboBox, QCheckBox, QSpinBox,
    QGroupBox, QTabWidget, QProgressBar, QSlider, QFrame,
    QMessageBox, QFileDialog, QListWidget, QListWidgetItem
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

logger = setup_logger('CohostTabPro')

class CohostTabPro(QWidget):
    """Advanced Cohost Tab untuk Pro Mode dengan fitur tambahan"""
    
    replyGenerated = pyqtSignal(str, str, str)  # author, message, reply
    
    def __init__(self):
        super().__init__()
        self.api_client = APIClient()
        self.config_manager = ConfigManager()
        self.settings = self.config_manager.load_settings()
        
        # Pro mode features
        self.advanced_ai_enabled = True
        self.multi_language_support = True
        self.context_memory = True
        self.auto_moderation = True
        
        self.setup_ui()
        self.load_settings()
        
    def setup_ui(self):
        """Setup UI untuk Pro mode dengan fitur advanced"""
        layout = QVBoxLayout()
        
        # Header dengan status Pro
        header_layout = QHBoxLayout()
        title_label = QLabel("🤖 Cohost Pro - Advanced AI Assistant")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #1877F2;")
        header_layout.addWidget(title_label)
        
        status_label = QLabel("🟢 Pro Mode Active")
        status_label.setStyleSheet("color: #42B72A; font-weight: bold;")
        header_layout.addWidget(status_label)
        layout.addLayout(header_layout)
        
        # Main content dengan tabs
        self.tab_widget = QTabWidget()
        
        # Tab 1: Chat Interface
        self.setup_chat_tab()
        
        # Tab 2: Advanced Settings
        self.setup_advanced_tab()
        
        # Tab 3: Analytics
        self.setup_analytics_tab()
        
        # Tab 4: Memory & Context
        self.setup_memory_tab()
        
        layout.addWidget(self.tab_widget)
        self.setLayout(layout)
        
    def setup_chat_tab(self):
        """Setup chat interface tab"""
        chat_widget = QWidget()
        chat_layout = QVBoxLayout()
        
        # Chat display area
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet("""
            QTextEdit {
                background-color: #242526;
                color: #FFFFFF;
                border: 1px solid #3A3B3C;
                border-radius: 8px;
                padding: 10px;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 14px;
            }
        """)
        chat_layout.addWidget(QLabel("💬 Live Chat Display"))
        chat_layout.addWidget(self.chat_display)
        
        # Input area
        input_group = QGroupBox("📝 AI Response Input")
        input_layout = QVBoxLayout()
        
        # Context input
        context_label = QLabel("🎯 Context (Pro Feature):")
        self.context_input = QTextEdit()
        self.context_input.setMaximumHeight(80)
        self.context_input.setPlaceholderText("Enter advanced context for AI responses...")
        input_layout.addWidget(context_label)
        input_layout.addWidget(self.context_input)
        
        # Personality selector
        personality_layout = QHBoxLayout()
        personality_layout.addWidget(QLabel("🎭 Personality:"))
        self.personality_combo = QComboBox()
        self.personality_combo.addItems([
            "Gaming Coach (Default)",
            "Entertainment Host",
            "Educational Teacher",
            "Comedy Streamer",
            "Professional Analyst",
            "Custom Personality"
        ])
        personality_layout.addWidget(self.personality_combo)
        input_layout.addLayout(personality_layout)
        
        # Advanced options
        options_layout = QHBoxLayout()
        
        self.auto_reply_check = QCheckBox("🤖 Auto Reply")
        self.auto_reply_check.setChecked(True)
        options_layout.addWidget(self.auto_reply_check)
        
        self.context_memory_check = QCheckBox("🧠 Context Memory")
        self.context_memory_check.setChecked(True)
        options_layout.addWidget(self.context_memory_check)
        
        self.moderation_check = QCheckBox("🛡️ Auto Moderation")
        self.moderation_check.setChecked(True)
        options_layout.addWidget(self.moderation_check)
        
        input_layout.addLayout(options_layout)
        
        # Response length slider
        length_layout = QHBoxLayout()
        length_layout.addWidget(QLabel("📏 Response Length:"))
        self.length_slider = QSlider(Qt.Orientation.Horizontal)
        self.length_slider.setRange(50, 500)
        self.length_slider.setValue(200)
        self.length_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.length_slider.setTickInterval(50)
        length_layout.addWidget(self.length_slider)
        
        self.length_label = QLabel("200 chars")
        self.length_slider.valueChanged.connect(
            lambda v: self.length_label.setText(f"{v} chars")
        )
        length_layout.addWidget(self.length_label)
        input_layout.addLayout(length_layout)
        
        # Generate button
        self.generate_btn = QPushButton("🚀 Generate Pro Response")
        self.generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #1877F2;
                color: white;
                border: none;
                padding: 12px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #166FE5;
            }
            QPushButton:pressed {
                background-color: #1464CC;
            }
        """)
        self.generate_btn.clicked.connect(self.generate_pro_response)
        input_layout.addWidget(self.generate_btn)
        
        input_group.setLayout(input_layout)
        chat_layout.addWidget(input_group)
        
        chat_widget.setLayout(chat_layout)
        self.tab_widget.addTab(chat_widget, "💬 Chat Interface")
        
    def setup_advanced_tab(self):
        """Setup advanced settings tab"""
        advanced_widget = QWidget()
        advanced_layout = QVBoxLayout()
        
        # AI Configuration
        ai_group = QGroupBox("🧠 AI Configuration (Pro)")
        ai_layout = QVBoxLayout()
        
        # Model selection
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("🤖 AI Model:"))
        self.model_combo = QComboBox()
        self.model_combo.addItems([
            "DeepSeek Chat (Default)",
            "DeepSeek Pro",
            "Custom Model"
        ])
        model_layout.addWidget(self.model_combo)
        ai_layout.addLayout(model_layout)
        
        # Temperature setting
        temp_layout = QHBoxLayout()
        temp_layout.addWidget(QLabel("🌡️ Creativity:"))
        self.temp_slider = QSlider(Qt.Orientation.Horizontal)
        self.temp_slider.setRange(0, 100)
        self.temp_slider.setValue(70)
        self.temp_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.temp_slider.setTickInterval(10)
        temp_layout.addWidget(self.temp_slider)
        
        self.temp_label = QLabel("0.7")
        self.temp_slider.valueChanged.connect(
            lambda v: self.temp_label.setText(f"{v/100:.1f}")
        )
        temp_layout.addWidget(self.temp_label)
        ai_layout.addLayout(temp_layout)
        
        # Language settings
        lang_layout = QHBoxLayout()
        lang_layout.addWidget(QLabel("🌍 Language:"))
        self.lang_combo = QComboBox()
        self.lang_combo.addItems([
            "Indonesian (Default)",
            "English",
            "Mixed Language",
            "Auto Detect"
        ])
        lang_layout.addWidget(self.lang_combo)
        ai_layout.addLayout(lang_layout)
        
        ai_group.setLayout(ai_layout)
        advanced_layout.addWidget(ai_group)
        
        # Response Templates
        template_group = QGroupBox("📝 Response Templates (Pro)")
        template_layout = QVBoxLayout()
        
        self.template_list = QListWidget()
        self.template_list.addItems([
            "🎮 Gaming Response",
            "🎭 Entertainment Response", 
            "📚 Educational Response",
            "😂 Comedy Response",
            "📊 Analysis Response"
        ])
        template_layout.addWidget(self.template_list)
        
        template_btn_layout = QHBoxLayout()
        template_btn_layout.addWidget(QPushButton("➕ Add Template"))
        template_btn_layout.addWidget(QPushButton("✏️ Edit Template"))
        template_btn_layout.addWidget(QPushButton("🗑️ Delete Template"))
        template_layout.addLayout(template_btn_layout)
        
        template_group.setLayout(template_layout)
        advanced_layout.addWidget(template_group)
        
        # Performance Settings
        perf_group = QGroupBox("⚡ Performance Settings")
        perf_layout = QVBoxLayout()
        
        self.cache_check = QCheckBox("💾 Enable Response Caching")
        self.cache_check.setChecked(True)
        perf_layout.addWidget(self.cache_check)
        
        self.parallel_check = QCheckBox("🔄 Parallel Processing")
        self.parallel_check.setChecked(True)
        perf_layout.addWidget(self.parallel_check)
        
        self.optimization_check = QCheckBox("🚀 AI Optimization")
        self.optimization_check.setChecked(True)
        perf_layout.addWidget(self.optimization_check)
        
        perf_group.setLayout(perf_layout)
        advanced_layout.addWidget(perf_group)
        
        advanced_widget.setLayout(advanced_layout)
        self.tab_widget.addTab(advanced_widget, "⚙️ Advanced Settings")
        
    def setup_analytics_tab(self):
        """Setup analytics tab"""
        analytics_widget = QWidget()
        analytics_layout = QVBoxLayout()
        
        # Statistics
        stats_group = QGroupBox("📊 Response Statistics")
        stats_layout = QVBoxLayout()
        
        # Stats display
        self.stats_display = QTextEdit()
        self.stats_display.setReadOnly(True)
        self.stats_display.setMaximumHeight(200)
        self.stats_display.setStyleSheet("""
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
        stats_layout.addWidget(self.stats_display)
        
        # Update stats button
        update_stats_btn = QPushButton("🔄 Update Statistics")
        update_stats_btn.clicked.connect(self.update_analytics)
        stats_layout.addWidget(update_stats_btn)
        
        stats_group.setLayout(stats_layout)
        analytics_layout.addWidget(stats_group)
        
        # Performance metrics
        perf_group = QGroupBox("⚡ Performance Metrics")
        perf_layout = QVBoxLayout()
        
        # Response time
        time_layout = QHBoxLayout()
        time_layout.addWidget(QLabel("⏱️ Avg Response Time:"))
        self.response_time_label = QLabel("0.0s")
        time_layout.addWidget(self.response_time_label)
        perf_layout.addLayout(time_layout)
        
        # Success rate
        success_layout = QHBoxLayout()
        success_layout.addWidget(QLabel("✅ Success Rate:"))
        self.success_rate_label = QLabel("0%")
        success_layout.addWidget(self.success_rate_label)
        perf_layout.addLayout(success_layout)
        
        # Credit usage
        credit_layout = QHBoxLayout()
        credit_layout.addWidget(QLabel("💰 Credits Used:"))
        self.credits_used_label = QLabel("0")
        credit_layout.addWidget(self.credits_used_label)
        perf_layout.addLayout(credit_layout)
        
        perf_group.setLayout(perf_layout)
        analytics_layout.addWidget(perf_group)
        
        analytics_widget.setLayout(analytics_layout)
        self.tab_widget.addTab(analytics_widget, "📊 Analytics")
        
    def setup_memory_tab(self):
        """Setup memory and context tab"""
        memory_widget = QWidget()
        memory_layout = QVBoxLayout()
        
        # Context Memory
        memory_group = QGroupBox("🧠 Context Memory (Pro Feature)")
        memory_layout = QVBoxLayout()
        
        # Memory display
        self.memory_display = QTextEdit()
        self.memory_display.setReadOnly(True)
        self.memory_display.setPlaceholderText("Context memory will appear here...")
        memory_layout.addWidget(self.memory_display)
        
        # Memory controls
        memory_controls = QHBoxLayout()
        memory_controls.addWidget(QPushButton("🧹 Clear Memory"))
        memory_controls.addWidget(QPushButton("💾 Save Memory"))
        memory_controls.addWidget(QPushButton("📂 Load Memory"))
        memory_layout.addLayout(memory_controls)
        
        memory_group.setLayout(memory_layout)
        memory_layout.addWidget(memory_group)
        
        # Conversation History
        history_group = QGroupBox("📜 Conversation History")
        history_layout = QVBoxLayout()
        
        self.history_list = QListWidget()
        history_layout.addWidget(self.history_list)
        
        history_controls = QHBoxLayout()
        history_controls.addWidget(QPushButton("📥 Export History"))
        history_controls.addWidget(QPushButton("🗑️ Clear History"))
        history_layout.addLayout(history_controls)
        
        history_group.setLayout(history_layout)
        memory_layout.addWidget(history_group)
        
        memory_widget.setLayout(memory_layout)
        self.tab_widget.addTab(memory_widget, "🧠 Memory & Context")
        
    def load_settings(self):
        """Load settings from config"""
        try:
            # Load pro-specific settings
            self.context_input.setPlainText(
                self.settings.get("pro_context", "Kamu adalah gaming coach dan streamer expert MOBA dengan personality yang engaging dan knowledgeable.")
            )
            
            # Load personality
            personality = self.settings.get("pro_personality", "Gaming Coach (Default)")
            index = self.personality_combo.findText(personality)
            if index >= 0:
                self.personality_combo.setCurrentIndex(index)
                
            # Load model
            model = self.settings.get("pro_model", "DeepSeek Chat (Default)")
            index = self.model_combo.findText(model)
            if index >= 0:
                self.model_combo.setCurrentIndex(index)
                
        except Exception as e:
            logger.error(f"Error loading pro settings: {e}")
            
    def save_settings(self):
        """Save settings to config"""
        try:
            self.settings["pro_context"] = self.context_input.toPlainText()
            self.settings["pro_personality"] = self.personality_combo.currentText()
            self.settings["pro_model"] = self.model_combo.currentText()
            self.settings["pro_auto_reply"] = self.auto_reply_check.isChecked()
            self.settings["pro_context_memory"] = self.context_memory_check.isChecked()
            self.settings["pro_moderation"] = self.moderation_check.isChecked()
            self.settings["pro_response_length"] = self.length_slider.value()
            self.settings["pro_temperature"] = self.temp_slider.value() / 100
            
            self.config_manager.save_settings()
            
        except Exception as e:
            logger.error(f"Error saving pro settings: {e}")
            
    def generate_pro_response(self):
        """Generate advanced AI response dengan fitur pro"""
        try:
            # Get input data
            context = self.context_input.toPlainText()
            personality = self.personality_combo.currentText()
            model = self.model_combo.currentText()
            max_length = self.length_slider.value()
            temperature = self.temp_slider.value() / 100
            
            # Pro mode enhancements
            enhanced_context = f"""
            [PRO MODE ENABLED]
            Personality: {personality}
            Model: {model}
            Context Memory: {'Enabled' if self.context_memory_check.isChecked() else 'Disabled'}
            Auto Moderation: {'Enabled' if self.moderation_check.isChecked() else 'Disabled'}
            
            Original Context: {context}
            """
            
            # Call API dengan pro features
            response_data = {
                "text": "Test message for pro response",
                "context": enhanced_context,
                "personality": personality,
                "max_length": max_length,
                "temperature": temperature,
                "pro_mode": True,
                "features": {
                    "context_memory": self.context_memory_check.isChecked(),
                    "auto_moderation": self.moderation_check.isChecked(),
                    "advanced_ai": True
                }
            }
            
            # Simulate API call
            response = "🎮 Pro Response Generated! This is an advanced AI response with enhanced features including context memory, auto moderation, and optimized performance."
            
            # Emit signal
            self.replyGenerated.emit("TestUser", "Test message", response)
            
            # Update chat display
            self.chat_display.append(f"<b>🤖 Pro AI:</b> {response}")
            
            # Update analytics
            self.update_analytics()
            
        except Exception as e:
            logger.error(f"Error generating pro response: {e}")
            QMessageBox.warning(self, "Error", f"Failed to generate pro response: {e}")
            
    def update_analytics(self):
        """Update analytics display"""
        try:
            # Simulate analytics data
            stats_text = """
📊 PRO MODE ANALYTICS
=====================
🤖 Total Responses: 1,247
⏱️ Avg Response Time: 0.8s
✅ Success Rate: 98.5%
💰 Credits Used: 1,247
🎯 Context Hits: 89%
🛡️ Moderation Actions: 12
🧠 Memory Efficiency: 94%
            """
            
            self.stats_display.setPlainText(stats_text)
            self.response_time_label.setText("0.8s")
            self.success_rate_label.setText("98.5%")
            self.credits_used_label.setText("1,247")
            
        except Exception as e:
            logger.error(f"Error updating analytics: {e}")
            
    def closeEvent(self, event):
        """Save settings when closing"""
        self.save_settings()
        super().closeEvent(event)
