# ui/translate_tab_pro.py - Advanced Translation Tab untuk Pro Mode
import sys
import os
import json
import time
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

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

logger = setup_logger('TranslateTabPro')

class TranslateTabPro(QWidget):
    """Advanced Translation Tab untuk Pro Mode"""
    
    def __init__(self):
        super().__init__()
        self.api_client = APIClient()
        self.config_manager = ConfigManager()
        self.settings = self.config_manager.load_settings()
        
        # Translation settings
        self.supported_languages = {
            "Indonesian": "id",
            "English": "en", 
            "Japanese": "ja",
            "Korean": "ko",
            "Chinese (Simplified)": "zh-CN",
            "Chinese (Traditional)": "zh-TW",
            "Spanish": "es",
            "French": "fr",
            "German": "de",
            "Italian": "it",
            "Portuguese": "pt",
            "Russian": "ru",
            "Arabic": "ar",
            "Hindi": "hi",
            "Thai": "th",
            "Vietnamese": "vi"
        }
        
        self.setup_ui()
        self.load_settings()
        
    def setup_ui(self):
        """Setup UI untuk advanced translation"""
        layout = QVBoxLayout()
        
        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel("🌍 Advanced Translation Pro")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #1877F2;")
        header_layout.addWidget(title_label)
        
        status_label = QLabel("🟢 Pro Translation Active")
        status_label.setStyleSheet("color: #42B72A; font-weight: bold;")
        header_layout.addWidget(status_label)
        layout.addLayout(header_layout)
        
        # Main content dengan tabs
        self.tab_widget = QTabWidget()
        
        # Tab 1: Real-time Translation
        self.setup_realtime_tab()
        
        # Tab 2: Batch Translation
        self.setup_batch_tab()
        
        # Tab 3: Voice Translation
        self.setup_voice_tab()
        
        # Tab 4: Translation Memory
        self.setup_memory_tab()
        
        layout.addWidget(self.tab_widget)
        self.setLayout(layout)
        
    def setup_realtime_tab(self):
        """Setup real-time translation tab"""
        realtime_widget = QWidget()
        realtime_layout = QVBoxLayout()
        
        # Source Language
        source_group = QGroupBox("📤 Source Language")
        source_layout = QVBoxLayout()
        
        self.source_lang_combo = QComboBox()
        self.source_lang_combo.addItems(list(self.supported_languages.keys()))
        self.source_lang_combo.setCurrentText("Indonesian")
        source_layout.addWidget(self.source_lang_combo)
        
        self.source_text = QTextEdit()
        self.source_text.setMaximumHeight(150)
        self.source_text.setPlaceholderText("Enter text to translate...")
        source_layout.addWidget(self.source_text)
        
        source_group.setLayout(source_layout)
        realtime_layout.addWidget(source_group)
        
        # Translation Options
        options_group = QGroupBox("⚙️ Translation Options")
        options_layout = QVBoxLayout()
        
        # Translation mode
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("🎯 Translation Mode:"))
        self.translation_mode_combo = QComboBox()
        self.translation_mode_combo.addItems([
            "Neural Machine Translation",
            "Statistical Translation", 
            "Hybrid Translation",
            "Context-Aware Translation",
            "Professional Translation"
        ])
        mode_layout.addWidget(self.translation_mode_combo)
        options_layout.addLayout(mode_layout)
        
        # Quality settings
        quality_layout = QHBoxLayout()
        quality_layout.addWidget(QLabel("⭐ Quality Level:"))
        self.quality_slider = QSlider(Qt.Orientation.Horizontal)
        self.quality_slider.setRange(1, 5)
        self.quality_slider.setValue(4)
        self.quality_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.quality_slider.setTickInterval(1)
        quality_layout.addWidget(self.quality_slider)
        
        self.quality_label = QLabel("High Quality")
        self.quality_slider.valueChanged.connect(self.update_quality_label)
        quality_layout.addWidget(self.quality_label)
        options_layout.addLayout(quality_layout)
        
        # Advanced options
        advanced_layout = QVBoxLayout()
        
        self.preserve_formatting_check = QCheckBox("📝 Preserve Formatting")
        self.preserve_formatting_check.setChecked(True)
        advanced_layout.addWidget(self.preserve_formatting_check)
        
        self.context_aware_check = QCheckBox("🧠 Context-Aware Translation")
        self.context_aware_check.setChecked(True)
        advanced_layout.addWidget(self.context_aware_check)
        
        self.cultural_adaptation_check = QCheckBox("🌍 Cultural Adaptation")
        self.cultural_adaptation_check.setChecked(True)
        advanced_layout.addWidget(self.cultural_adaptation_check)
        
        self.technical_terms_check = QCheckBox("🔧 Technical Terms Dictionary")
        self.technical_terms_check.setChecked(True)
        advanced_layout.addWidget(self.technical_terms_check)
        
        options_layout.addLayout(advanced_layout)
        options_group.setLayout(options_layout)
        realtime_layout.addWidget(options_group)
        
        # Target Language
        target_group = QGroupBox("📥 Target Language")
        target_layout = QVBoxLayout()
        
        self.target_lang_combo = QComboBox()
        self.target_lang_combo.addItems(list(self.supported_languages.keys()))
        self.target_lang_combo.setCurrentText("English")
        target_layout.addWidget(self.target_lang_combo)
        
        self.target_text = QTextEdit()
        self.target_text.setMaximumHeight(150)
        self.target_text.setReadOnly(True)
        self.target_text.setPlaceholderText("Translation will appear here...")
        target_layout.addWidget(self.target_text)
        
        target_group.setLayout(target_layout)
        realtime_layout.addWidget(target_group)
        
        # Translate button
        self.translate_btn = QPushButton("🌍 Translate")
        self.translate_btn.setStyleSheet("""
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
        """)
        self.translate_btn.clicked.connect(self.translate_text)
        realtime_layout.addWidget(self.translate_btn)
        
        realtime_widget.setLayout(realtime_layout)
        self.tab_widget.addTab(realtime_widget, "🌍 Real-time Translation")
        
    def setup_batch_tab(self):
        """Setup batch translation tab"""
        batch_widget = QWidget()
        batch_layout = QVBoxLayout()
        
        # File Upload
        upload_group = QGroupBox("📄 File Upload")
        upload_layout = QVBoxLayout()
        
        # File selection
        file_layout = QHBoxLayout()
        file_layout.addWidget(QLabel("📁 Select Files:"))
        self.batch_file_label = QLabel("No files selected")
        file_layout.addWidget(self.batch_file_label)
        
        browse_btn = QPushButton("📂 Browse Files")
        browse_btn.clicked.connect(self.browse_batch_files)
        file_layout.addWidget(browse_btn)
        upload_layout.addLayout(file_layout)
        
        # Supported formats
        formats_label = QLabel("📋 Supported formats: TXT, DOCX, PDF, JSON, CSV")
        formats_label.setStyleSheet("color: #888; font-size: 12px;")
        upload_layout.addWidget(formats_label)
        
        upload_group.setLayout(upload_layout)
        batch_layout.addWidget(upload_group)
        
        # Batch Settings
        settings_group = QGroupBox("⚙️ Batch Settings")
        settings_layout = QVBoxLayout()
        
        # Language pairs
        lang_layout = QHBoxLayout()
        lang_layout.addWidget(QLabel("📤 From:"))
        self.batch_source_combo = QComboBox()
        self.batch_source_combo.addItems(list(self.supported_languages.keys()))
        self.batch_source_combo.setCurrentText("Indonesian")
        lang_layout.addWidget(self.batch_source_combo)
        
        lang_layout.addWidget(QLabel("📥 To:"))
        self.batch_target_combo = QComboBox()
        self.batch_target_combo.addItems(list(self.supported_languages.keys()))
        self.batch_target_combo.setCurrentText("English")
        lang_layout.addWidget(self.batch_target_combo)
        settings_layout.addLayout(lang_layout)
        
        # Batch options
        batch_options_layout = QVBoxLayout()
        
        self.parallel_processing_check = QCheckBox("🔄 Parallel Processing")
        self.parallel_processing_check.setChecked(True)
        batch_options_layout.addWidget(self.parallel_processing_check)
        
        self.preserve_structure_check = QCheckBox("📋 Preserve Document Structure")
        self.preserve_structure_check.setChecked(True)
        batch_options_layout.addWidget(self.preserve_structure_check)
        
        self.quality_check_check = QCheckBox("✅ Quality Check")
        self.quality_check_check.setChecked(True)
        batch_options_layout.addWidget(self.quality_check_check)
        
        settings_layout.addLayout(batch_options_layout)
        settings_group.setLayout(settings_layout)
        batch_layout.addWidget(settings_group)
        
        # Progress
        progress_group = QGroupBox("📊 Progress")
        progress_layout = QVBoxLayout()
        
        self.batch_progress_bar = QProgressBar()
        self.batch_progress_bar.setVisible(False)
        progress_layout.addWidget(self.batch_progress_bar)
        
        self.batch_status_label = QLabel("Ready to process")
        progress_layout.addWidget(self.batch_status_label)
        
        # Process button
        self.batch_process_btn = QPushButton("🚀 Start Batch Translation")
        self.batch_process_btn.setStyleSheet("""
            QPushButton {
                background-color: #42B72A;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #36A420;
            }
        """)
        self.batch_process_btn.clicked.connect(self.start_batch_translation)
        progress_layout.addWidget(self.batch_process_btn)
        
        progress_group.setLayout(progress_layout)
        batch_layout.addWidget(progress_group)
        
        batch_widget.setLayout(batch_layout)
        self.tab_widget.addTab(batch_widget, "📄 Batch Translation")
        
    def setup_voice_tab(self):
        """Setup voice translation tab"""
        voice_widget = QWidget()
        voice_layout = QVBoxLayout()
        
        # Voice Input
        input_group = QGroupBox("🎤 Voice Input")
        input_layout = QVBoxLayout()
        
        # Source voice
        source_voice_layout = QHBoxLayout()
        source_voice_layout.addWidget(QLabel("🎤 Source Voice:"))
        self.source_voice_combo = QComboBox()
        self.source_voice_combo.addItems([
            "Indonesian - Male",
            "Indonesian - Female", 
            "English - Male",
            "English - Female",
            "Japanese - Male",
            "Japanese - Female"
        ])
        source_voice_layout.addWidget(self.source_voice_combo)
        input_layout.addLayout(source_voice_layout)
        
        # Voice controls
        voice_controls = QHBoxLayout()
        
        self.record_btn = QPushButton("🎙️ Record")
        self.record_btn.setStyleSheet("""
            QPushButton {
                background-color: #FA383E;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #E62E34;
            }
        """)
        voice_controls.addWidget(self.record_btn)
        
        self.stop_btn = QPushButton("⏹️ Stop")
        self.stop_btn.setEnabled(False)
        voice_controls.addWidget(self.stop_btn)
        
        input_layout.addLayout(voice_controls)
        
        # Voice display
        self.voice_display = QTextEdit()
        self.voice_display.setMaximumHeight(100)
        self.voice_display.setPlaceholderText("Voice input will appear here...")
        input_layout.addWidget(self.voice_display)
        
        input_group.setLayout(input_layout)
        voice_layout.addWidget(input_group)
        
        # Voice Translation
        translation_group = QGroupBox("🌍 Voice Translation")
        translation_layout = QVBoxLayout()
        
        # Target voice
        target_voice_layout = QHBoxLayout()
        target_voice_layout.addWidget(QLabel("🔊 Target Voice:"))
        self.target_voice_combo = QComboBox()
        self.target_voice_combo.addItems([
            "Indonesian - Male",
            "Indonesian - Female",
            "English - Male", 
            "English - Female",
            "Japanese - Male",
            "Japanese - Female"
        ])
        target_voice_layout.addWidget(self.target_voice_combo)
        translation_layout.addLayout(target_voice_layout)
        
        # Translation display
        self.voice_translation_display = QTextEdit()
        self.voice_translation_display.setMaximumHeight(100)
        self.voice_translation_display.setReadOnly(True)
        self.voice_translation_display.setPlaceholderText("Translation will appear here...")
        translation_layout.addWidget(self.voice_translation_display)
        
        # Voice translation button
        self.voice_translate_btn = QPushButton("🌍 Translate Voice")
        self.voice_translate_btn.setStyleSheet("""
            QPushButton {
                background-color: #1877F2;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #166FE5;
            }
        """)
        self.voice_translate_btn.clicked.connect(self.translate_voice)
        translation_layout.addWidget(self.voice_translate_btn)
        
        translation_group.setLayout(translation_layout)
        voice_layout.addWidget(translation_group)
        
        voice_widget.setLayout(voice_layout)
        self.tab_widget.addTab(voice_widget, "🎤 Voice Translation")
        
    def setup_memory_tab(self):
        """Setup translation memory tab"""
        memory_widget = QWidget()
        memory_layout = QVBoxLayout()
        
        # Translation Memory
        memory_group = QGroupBox("🧠 Translation Memory")
        memory_layout_v = QVBoxLayout()
        
        # Memory display
        self.memory_display = QTextEdit()
        self.memory_display.setReadOnly(True)
        self.memory_display.setMaximumHeight(200)
        self.memory_display.setStyleSheet("""
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
        memory_layout_v.addWidget(self.memory_display)
        
        # Memory controls
        memory_controls = QHBoxLayout()
        memory_controls.addWidget(QPushButton("🧹 Clear Memory"))
        memory_controls.addWidget(QPushButton("💾 Save Memory"))
        memory_controls.addWidget(QPushButton("📂 Load Memory"))
        memory_controls.addWidget(QPushButton("🔄 Update Memory"))
        memory_layout_v.addLayout(memory_controls)
        
        memory_group.setLayout(memory_layout_v)
        memory_layout.addWidget(memory_group)
        
        # Translation History
        history_group = QGroupBox("📜 Translation History")
        history_layout = QVBoxLayout()
        
        self.history_list = QListWidget()
        self.history_list.setStyleSheet("""
            QListWidget {
                background-color: #242526;
                color: #FFFFFF;
                border: 1px solid #3A3B3C;
                border-radius: 8px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #3A3B3C;
            }
            QListWidget::item:selected {
                background-color: #1877F2;
            }
        """)
        history_layout.addWidget(self.history_list)
        
        history_controls = QHBoxLayout()
        history_controls.addWidget(QPushButton("📥 Export History"))
        history_controls.addWidget(QPushButton("🗑️ Clear History"))
        history_layout.addLayout(history_controls)
        
        history_group.setLayout(history_layout)
        memory_layout.addWidget(history_group)
        
        memory_widget.setLayout(memory_layout)
        self.tab_widget.addTab(memory_widget, "🧠 Translation Memory")
        
    def load_settings(self):
        """Load translation settings"""
        try:
            # Load translation-specific settings
            source_lang = self.settings.get("translation_source_lang", "Indonesian")
            target_lang = self.settings.get("translation_target_lang", "English")
            
            source_index = self.source_lang_combo.findText(source_lang)
            if source_index >= 0:
                self.source_lang_combo.setCurrentIndex(source_index)
                
            target_index = self.target_lang_combo.findText(target_lang)
            if target_index >= 0:
                self.target_lang_combo.setCurrentIndex(target_index)
                
        except Exception as e:
            logger.error(f"Error loading translation settings: {e}")
            
    def save_settings(self):
        """Save translation settings"""
        try:
            self.settings["translation_source_lang"] = self.source_lang_combo.currentText()
            self.settings["translation_target_lang"] = self.target_lang_combo.currentText()
            self.settings["translation_mode"] = self.translation_mode_combo.currentText()
            self.settings["translation_quality"] = self.quality_slider.value()
            self.settings["translation_preserve_formatting"] = self.preserve_formatting_check.isChecked()
            self.settings["translation_context_aware"] = self.context_aware_check.isChecked()
            self.settings["translation_cultural_adaptation"] = self.cultural_adaptation_check.isChecked()
            self.settings["translation_technical_terms"] = self.technical_terms_check.isChecked()
            
            self.config_manager.save_settings()
            
        except Exception as e:
            logger.error(f"Error saving translation settings: {e}")
            
    def update_quality_label(self, value):
        """Update quality label berdasarkan slider value"""
        quality_labels = {
            1: "Basic",
            2: "Standard", 
            3: "Good",
            4: "High Quality",
            5: "Professional"
        }
        self.quality_label.setText(quality_labels.get(value, "Unknown"))
        
    def translate_text(self):
        """Translate text dengan advanced features"""
        try:
            source_text = self.source_text.toPlainText()
            if not source_text.strip():
                QMessageBox.warning(self, "Warning", "Please enter text to translate")
            return

            source_lang = self.supported_languages.get(self.source_lang_combo.currentText(), "id")
            target_lang = self.supported_languages.get(self.target_lang_combo.currentText(), "en")
            mode = self.translation_mode_combo.currentText()
            quality = self.quality_slider.value()
            
            # Simulate advanced translation
            translation = f"""
🌍 Advanced Translation Result

📤 Source ({self.source_lang_combo.currentText()}): {source_text}
📥 Target ({self.target_lang_combo.currentText()}): "This is a professional translation with advanced features including context awareness, cultural adaptation, and technical term optimization."

⚙️ Translation Details:
- Mode: {mode}
- Quality: {quality}/5 stars
- Context-Aware: {'Yes' if self.context_aware_check.isChecked() else 'No'}
- Cultural Adaptation: {'Yes' if self.cultural_adaptation_check.isChecked() else 'No'}
- Technical Terms: {'Yes' if self.technical_terms_check.isChecked() else 'No'}
            """
            
            self.target_text.setPlainText(translation)
            
            # Add to history
            self.add_to_history(source_text, translation)
            
        except Exception as e:
            logger.error(f"Error translating text: {e}")
            QMessageBox.warning(self, "Error", f"Failed to translate text: {e}")
            
    def browse_batch_files(self):
        """Browse untuk memilih file batch"""
        try:
            files, _ = QFileDialog.getOpenFileNames(
                self,
                "Select Files for Batch Translation",
                "",
                "Documents (*.txt *.docx *.pdf *.json *.csv);;All Files (*)"
            )
            
            if files:
                self.batch_file_label.setText(f"{len(files)} files selected")
                
        except Exception as e:
            logger.error(f"Error browsing batch files: {e}")
            
    def start_batch_translation(self):
        """Start batch translation process"""
        try:
            self.batch_progress_bar.setVisible(True)
            self.batch_progress_bar.setValue(0)
            self.batch_status_label.setText("Processing files...")
            self.batch_process_btn.setEnabled(False)
            
            # Simulate batch processing
            for i in range(101):
                self.batch_progress_bar.setValue(i)
                self.batch_status_label.setText(f"Processing file {i+1}/100...")
                time.sleep(0.05)
                
            self.batch_status_label.setText("Batch translation completed!")
            self.batch_process_btn.setEnabled(True)
            self.batch_progress_bar.setVisible(False)
            
            QMessageBox.information(self, "Success", "Batch translation completed successfully!")
            
        except Exception as e:
            logger.error(f"Error in batch translation: {e}")
            QMessageBox.warning(self, "Error", f"Failed to process batch translation: {e}")
            
    def translate_voice(self):
        """Translate voice input"""
        try:
            voice_input = self.voice_display.toPlainText()
            if not voice_input.strip():
                QMessageBox.warning(self, "Warning", "Please record or enter voice input")
            return

            # Simulate voice translation
            translation = f"""
🎤 Voice Translation Result

🎙️ Source Voice: {self.source_voice_combo.currentText()}
🔊 Target Voice: {self.target_voice_combo.currentText()}

📝 Original: "{voice_input}"
🌍 Translation: "This is a professional voice translation with advanced speech recognition and natural language processing."

⚙️ Features Used:
- Speech-to-Text
- Neural Translation
- Text-to-Speech
- Voice Cloning
            """
            
            self.voice_translation_display.setPlainText(translation)
            
                except Exception as e:
            logger.error(f"Error translating voice: {e}")
            QMessageBox.warning(self, "Error", f"Failed to translate voice: {e}")
            
    def add_to_history(self, source, translation):
        """Add translation ke history"""
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            history_item = f"[{timestamp}] {source[:50]}... → {translation[:50]}..."
            
            self.history_list.addItem(history_item)
            
        except Exception as e:
            logger.error(f"Error adding to history: {e}")
            
    def closeEvent(self, event):
        """Save settings when closing"""
        self.save_settings()
        super().closeEvent(event)

