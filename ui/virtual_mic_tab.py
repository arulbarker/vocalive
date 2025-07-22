# ui/virtual_mic_tab.py - Virtual Microphone Tab untuk Pro Mode
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

logger = setup_logger('VirtualMicTab')

class VirtualMicTab(QWidget):
    """Virtual Microphone Tab untuk Pro Mode"""
    
    def __init__(self):
        super().__init__()
        self.api_client = APIClient()
        self.config_manager = ConfigManager()
        self.settings = self.config_manager.load_settings()
        
        # Virtual mic settings
        self.is_recording = False
        self.is_playing = False
        self.audio_devices = []
        self.voice_profiles = []
        
        self.setup_ui()
        self.load_settings()
        self.scan_audio_devices()
        
    def setup_ui(self):
        """Setup UI untuk virtual microphone"""
        layout = QVBoxLayout()
        
        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel("🎤 Virtual Microphone Pro")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #1877F2;")
        header_layout.addWidget(title_label)
        
        status_label = QLabel("🟢 Virtual Mic Ready")
        status_label.setStyleSheet("color: #42B72A; font-weight: bold;")
        header_layout.addWidget(status_label)
        layout.addLayout(header_layout)
        
        # Main content dengan tabs
        self.tab_widget = QTabWidget()
        
        # Tab 1: Voice Recording
        self.setup_recording_tab()
        
        # Tab 2: Voice Synthesis
        self.setup_synthesis_tab()
        
        # Tab 3: Voice Effects
        self.setup_effects_tab()
        
        # Tab 4: Voice Profiles
        self.setup_profiles_tab()
        
        layout.addWidget(self.tab_widget)
        self.setLayout(layout)
        
    def setup_recording_tab(self):
        """Setup voice recording tab"""
        recording_widget = QWidget()
        recording_layout = QVBoxLayout()
        
        # Audio Device Selection
        device_group = QGroupBox("🎧 Audio Device Configuration")
        device_layout = QVBoxLayout()
        
        # Input device
        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("🎤 Input Device:"))
        self.input_device_combo = QComboBox()
        self.input_device_combo.addItems([
            "Default Microphone",
            "Realtek HD Audio",
            "USB Microphone",
            "Virtual Audio Cable",
            "System Audio"
        ])
        input_layout.addWidget(self.input_device_combo)
        device_layout.addLayout(input_layout)
        
        # Output device
        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel("🔊 Output Device:"))
        self.output_device_combo = QComboBox()
        self.output_device_combo.addItems([
            "Default Speakers",
            "Realtek HD Audio",
            "USB Headphones",
            "Virtual Audio Cable",
            "System Audio"
        ])
        output_layout.addWidget(self.output_device_combo)
        device_layout.addLayout(output_layout)
        
        # Device controls
        device_controls = QHBoxLayout()
        device_controls.addWidget(QPushButton("🔄 Refresh Devices"))
        device_controls.addWidget(QPushButton("⚙️ Device Settings"))
        device_controls.addWidget(QPushButton("🎛️ Audio Mixer"))
        device_layout.addLayout(device_controls)
        
        device_group.setLayout(device_layout)
        recording_layout.addWidget(device_group)
        
        # Recording Controls
        recording_group = QGroupBox("🎙️ Recording Controls")
        recording_layout_v = QVBoxLayout()
        
        # Recording buttons
        record_controls = QHBoxLayout()
        
        self.record_btn = QPushButton("🎙️ Start Recording")
        self.record_btn.setStyleSheet("""
            QPushButton {
                background-color: #FA383E;
                color: white;
                border: none;
                padding: 12px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #E62E34;
            }
        """)
        self.record_btn.clicked.connect(self.toggle_recording)
        record_controls.addWidget(self.record_btn)
        
        self.stop_btn = QPushButton("⏹️ Stop Recording")
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #3A3B3C;
                color: white;
                border: none;
                padding: 12px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
        """)
        self.stop_btn.clicked.connect(self.stop_recording)
        record_controls.addWidget(self.stop_btn)
        
        self.play_btn = QPushButton("▶️ Play Recording")
        self.play_btn.setStyleSheet("""
            QPushButton {
                background-color: #42B72A;
                color: white;
                border: none;
                padding: 12px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #36A420;
            }
        """)
        self.play_btn.clicked.connect(self.play_recording)
        record_controls.addWidget(self.play_btn)
        
        recording_layout_v.addLayout(record_controls)
        
        # Recording options
        options_layout = QVBoxLayout()
        
        self.auto_record_check = QCheckBox("🤖 Auto Record on Stream")
        self.auto_record_check.setChecked(True)
        options_layout.addWidget(self.auto_record_check)
        
        self.noise_reduction_check = QCheckBox("🔇 Noise Reduction")
        self.noise_reduction_check.setChecked(True)
        options_layout.addWidget(self.noise_reduction_check)
        
        self.echo_cancellation_check = QCheckBox("🔄 Echo Cancellation")
        self.echo_cancellation_check.setChecked(True)
        options_layout.addWidget(self.echo_cancellation_check)
        
        self.auto_gain_check = QCheckBox("📈 Auto Gain Control")
        self.auto_gain_check.setChecked(True)
        options_layout.addWidget(self.auto_gain_check)
        
        recording_layout_v.addLayout(options_layout)
        
        # Recording display
        self.recording_display = QTextEdit()
        self.recording_display.setMaximumHeight(100)
        self.recording_display.setReadOnly(True)
        self.recording_display.setPlaceholderText("Recording status and information will appear here...")
        recording_layout_v.addWidget(self.recording_display)
        
        recording_group.setLayout(recording_layout_v)
        recording_layout.addWidget(recording_group)
        
        recording_widget.setLayout(recording_layout)
        self.tab_widget.addTab(recording_widget, "🎙️ Voice Recording")
        
    def setup_synthesis_tab(self):
        """Setup voice synthesis tab"""
        synthesis_widget = QWidget()
        synthesis_layout = QVBoxLayout()
        
        # Text-to-Speech
        tts_group = QGroupBox("🗣️ Text-to-Speech Synthesis")
        tts_layout = QVBoxLayout()
        
        # Voice selection
        voice_layout = QHBoxLayout()
        voice_layout.addWidget(QLabel("🎭 Voice:"))
        self.voice_combo = QComboBox()
        self.voice_combo.addItems([
            "Indonesian - Male (Default)",
            "Indonesian - Female",
            "English - Male",
            "English - Female",
            "Japanese - Male",
            "Japanese - Female",
            "Custom Voice 1",
            "Custom Voice 2"
        ])
        voice_layout.addWidget(self.voice_combo)
        tts_layout.addLayout(voice_layout)
        
        # Text input
        text_layout = QVBoxLayout()
        text_layout.addWidget(QLabel("📝 Text to Synthesize:"))
        self.tts_text_input = QTextEdit()
        self.tts_text_input.setMaximumHeight(100)
        self.tts_text_input.setPlaceholderText("Enter text to convert to speech...")
        text_layout.addWidget(self.tts_text_input)
        tts_layout.addLayout(text_layout)
        
        # TTS options
        tts_options = QHBoxLayout()
        
        self.real_time_check = QCheckBox("⚡ Real-time Synthesis")
        self.real_time_check.setChecked(True)
        tts_options.addWidget(self.real_time_check)
        
        self.high_quality_check = QCheckBox("⭐ High Quality")
        self.high_quality_check.setChecked(True)
        tts_options.addWidget(self.high_quality_check)
        
        self.emotion_check = QCheckBox("😊 Emotion Control")
        self.emotion_check.setChecked(True)
        tts_options.addWidget(self.emotion_check)
        
        tts_layout.addLayout(tts_options)
        
        # Synthesis button
        self.synthesize_btn = QPushButton("🗣️ Synthesize Speech")
        self.synthesize_btn.setStyleSheet("""
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
        self.synthesize_btn.clicked.connect(self.synthesize_speech)
        tts_layout.addWidget(self.synthesize_btn)
        
        tts_group.setLayout(tts_layout)
        synthesis_layout.addWidget(tts_group)
        
        # Voice Cloning
        cloning_group = QGroupBox("🎭 Voice Cloning (Pro Feature)")
        cloning_layout = QVBoxLayout()
        
        # Clone voice
        clone_layout = QHBoxLayout()
        clone_layout.addWidget(QLabel("🎤 Clone Voice:"))
        self.clone_voice_input = QLineEdit()
        self.clone_voice_input.setPlaceholderText("Enter voice name to clone...")
        clone_layout.addWidget(self.clone_voice_input)
        
        self.clone_btn = QPushButton("🎭 Clone Voice")
        self.clone_btn.setStyleSheet("""
            QPushButton {
                background-color: #F5B800;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
        """)
        self.clone_btn.clicked.connect(self.clone_voice)
        clone_layout.addWidget(self.clone_btn)
        cloning_layout.addLayout(clone_layout)
        
        # Clone options
        clone_options = QVBoxLayout()
        
        self.voice_training_check = QCheckBox("🧠 Voice Training Mode")
        self.voice_training_check.setChecked(True)
        clone_options.addWidget(self.voice_training_check)
        
        self.voice_adaptation_check = QCheckBox("🔄 Voice Adaptation")
        self.voice_adaptation_check.setChecked(True)
        clone_options.addWidget(self.voice_adaptation_check)
        
        cloning_layout.addLayout(clone_options)
        
        cloning_group.setLayout(cloning_layout)
        synthesis_layout.addWidget(cloning_group)
        
        synthesis_widget.setLayout(synthesis_layout)
        self.tab_widget.addTab(synthesis_widget, "🗣️ Voice Synthesis")
        
    def setup_effects_tab(self):
        """Setup voice effects tab"""
        effects_widget = QWidget()
        effects_layout = QVBoxLayout()
        
        # Voice Effects
        effects_group = QGroupBox("🎛️ Voice Effects")
        effects_layout_v = QVBoxLayout()
        
        # Pitch control
        pitch_layout = QHBoxLayout()
        pitch_layout.addWidget(QLabel("🎵 Pitch:"))
        self.pitch_slider = QSlider(Qt.Orientation.Horizontal)
        self.pitch_slider.setRange(-12, 12)
        self.pitch_slider.setValue(0)
        self.pitch_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.pitch_slider.setTickInterval(2)
        pitch_layout.addWidget(self.pitch_slider)
        
        self.pitch_label = QLabel("0")
        self.pitch_slider.valueChanged.connect(
            lambda v: self.pitch_label.setText(str(v))
        )
        pitch_layout.addWidget(self.pitch_label)
        effects_layout_v.addLayout(pitch_layout)
        
        # Speed control
        speed_layout = QHBoxLayout()
        speed_layout.addWidget(QLabel("⏱️ Speed:"))
        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setRange(50, 200)
        self.speed_slider.setValue(100)
        self.speed_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.speed_slider.setTickInterval(25)
        speed_layout.addWidget(self.speed_slider)
        
        self.speed_label = QLabel("100%")
        self.speed_slider.valueChanged.connect(
            lambda v: self.speed_label.setText(f"{v}%")
        )
        speed_layout.addWidget(self.speed_label)
        effects_layout_v.addLayout(speed_layout)
        
        # Volume control
        volume_layout = QHBoxLayout()
        volume_layout.addWidget(QLabel("🔊 Volume:"))
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(80)
        self.volume_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.volume_slider.setTickInterval(10)
        volume_layout.addWidget(self.volume_slider)
        
        self.volume_label = QLabel("80%")
        self.volume_slider.valueChanged.connect(
            lambda v: self.volume_label.setText(f"{v}%")
        )
        volume_layout.addWidget(self.volume_label)
        effects_layout_v.addLayout(volume_layout)
        
        effects_group.setLayout(effects_layout_v)
        effects_layout.addWidget(effects_group)
        
        # Effect Presets
        presets_group = QGroupBox("🎭 Effect Presets")
        presets_layout = QVBoxLayout()
        
        # Preset buttons
        preset_buttons = QHBoxLayout()
        
        self.deep_voice_btn = QPushButton("🎤 Deep Voice")
        self.deep_voice_btn.setStyleSheet("""
            QPushButton {
                background-color: #3A3B3C;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
        """)
        self.deep_voice_btn.clicked.connect(lambda: self.apply_preset("deep"))
        preset_buttons.addWidget(self.deep_voice_btn)
        
        self.high_pitch_btn = QPushButton("🎵 High Pitch")
        self.high_pitch_btn.setStyleSheet("""
            QPushButton {
                background-color: #F5B800;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
        """)
        self.high_pitch_btn.clicked.connect(lambda: self.apply_preset("high"))
        preset_buttons.addWidget(self.high_pitch_btn)
        
        self.robot_btn = QPushButton("🤖 Robot Voice")
        self.robot_btn.setStyleSheet("""
            QPushButton {
                background-color: #42B72A;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
        """)
        self.robot_btn.clicked.connect(lambda: self.apply_preset("robot"))
        preset_buttons.addWidget(self.robot_btn)
        
        self.echo_btn = QPushButton("🔄 Echo Effect")
        self.echo_btn.setStyleSheet("""
            QPushButton {
                background-color: #1877F2;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
        """)
        self.echo_btn.clicked.connect(lambda: self.apply_preset("echo"))
        preset_buttons.addWidget(self.echo_btn)
        
        presets_layout.addLayout(preset_buttons)
        
        # Custom effects
        custom_layout = QHBoxLayout()
        custom_layout.addWidget(QLabel("🎛️ Custom Effect:"))
        self.custom_effect_input = QLineEdit()
        self.custom_effect_input.setPlaceholderText("Enter custom effect parameters...")
        custom_layout.addWidget(self.custom_effect_input)
        
        self.apply_custom_btn = QPushButton("✅ Apply Custom")
        self.apply_custom_btn.clicked.connect(self.apply_custom_effect)
        custom_layout.addWidget(self.apply_custom_btn)
        presets_layout.addLayout(custom_layout)
        
        presets_group.setLayout(presets_layout)
        effects_layout.addWidget(presets_group)
        
        effects_widget.setLayout(effects_layout)
        self.tab_widget.addTab(effects_widget, "🎛️ Voice Effects")
        
    def setup_profiles_tab(self):
        """Setup voice profiles tab"""
        profiles_widget = QWidget()
        profiles_layout = QVBoxLayout()
        
        # Voice Profiles
        profiles_group = QGroupBox("👤 Voice Profiles")
        profiles_layout_v = QVBoxLayout()
        
        # Profile list
        self.profile_list = QListWidget()
        self.profile_list.setStyleSheet("""
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
        profiles_layout_v.addWidget(self.profile_list)
        
        # Profile controls
        profile_controls = QHBoxLayout()
        profile_controls.addWidget(QPushButton("➕ Add Profile"))
        profile_controls.addWidget(QPushButton("✏️ Edit Profile"))
        profile_controls.addWidget(QPushButton("🗑️ Delete Profile"))
        profile_controls.addWidget(QPushButton("💾 Save Profile"))
        profiles_layout_v.addLayout(profile_controls)
        
        profiles_group.setLayout(profiles_layout_v)
        profiles_layout.addWidget(profiles_group)
        
        # Profile Details
        details_group = QGroupBox("📋 Profile Details")
        details_layout = QVBoxLayout()
        
        self.profile_details_display = QTextEdit()
        self.profile_details_display.setReadOnly(True)
        self.profile_details_display.setMaximumHeight(200)
        self.profile_details_display.setStyleSheet("""
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
        details_layout.addWidget(self.profile_details_display)
        
        details_group.setLayout(details_layout)
        profiles_layout.addWidget(details_group)
        
        profiles_widget.setLayout(profiles_layout)
        self.tab_widget.addTab(profiles_widget, "👤 Voice Profiles")
        
    def load_settings(self):
        """Load virtual mic settings"""
        try:
            # Load virtual mic-specific settings
            input_device = self.settings.get("virtual_mic_input", "Default Microphone")
            output_device = self.settings.get("virtual_mic_output", "Default Speakers")
            
            input_index = self.input_device_combo.findText(input_device)
            if input_index >= 0:
                self.input_device_combo.setCurrentIndex(input_index)
                
            output_index = self.output_device_combo.findText(output_device)
            if output_index >= 0:
                self.output_device_combo.setCurrentIndex(output_index)
                
            # Load effect settings
            self.pitch_slider.setValue(self.settings.get("virtual_mic_pitch", 0))
            self.speed_slider.setValue(self.settings.get("virtual_mic_speed", 100))
            self.volume_slider.setValue(self.settings.get("virtual_mic_volume", 80))
            
        except Exception as e:
            logger.error(f"Error loading virtual mic settings: {e}")
            
    def save_settings(self):
        """Save virtual mic settings"""
        try:
            self.settings["virtual_mic_input"] = self.input_device_combo.currentText()
            self.settings["virtual_mic_output"] = self.output_device_combo.currentText()
            self.settings["virtual_mic_pitch"] = self.pitch_slider.value()
            self.settings["virtual_mic_speed"] = self.speed_slider.value()
            self.settings["virtual_mic_volume"] = self.volume_slider.value()
            self.settings["virtual_mic_auto_record"] = self.auto_record_check.isChecked()
            self.settings["virtual_mic_noise_reduction"] = self.noise_reduction_check.isChecked()
            self.settings["virtual_mic_echo_cancellation"] = self.echo_cancellation_check.isChecked()
            self.settings["virtual_mic_auto_gain"] = self.auto_gain_check.isChecked()
            
            self.config_manager.save_settings()
            
        except Exception as e:
            logger.error(f"Error saving virtual mic settings: {e}")
            
    def scan_audio_devices(self):
        """Scan available audio devices"""
        try:
            # Simulate device scanning
            self.audio_devices = [
                "Default Microphone",
                "Realtek HD Audio",
                "USB Microphone", 
                "Virtual Audio Cable",
                "System Audio"
            ]
            
        except Exception as e:
            logger.error(f"Error scanning audio devices: {e}")
            
    def toggle_recording(self):
        """Toggle recording state"""
        try:
            if not self.is_recording:
                self.start_recording()
            else:
                self.stop_recording()
                
        except Exception as e:
            logger.error(f"Error toggling recording: {e}")
            
    def start_recording(self):
        """Start voice recording"""
        try:
            self.is_recording = True
            self.record_btn.setText("⏸️ Pause Recording")
            self.record_btn.setStyleSheet("""
                QPushButton {
                    background-color: #F5B800;
                    color: white;
                    border: none;
                    padding: 12px;
                    border-radius: 6px;
                    font-weight: bold;
                    font-size: 14px;
                }
            """)
            self.stop_btn.setEnabled(True)
            
            self.recording_display.append("🎙️ Recording started...")
            
        except Exception as e:
            logger.error(f"Error starting recording: {e}")
            
    def stop_recording(self):
        """Stop voice recording"""
        try:
            self.is_recording = False
            self.record_btn.setText("🎙️ Start Recording")
            self.record_btn.setStyleSheet("""
                QPushButton {
                    background-color: #FA383E;
                    color: white;
                    border: none;
                    padding: 12px;
                    border-radius: 6px;
                    font-weight: bold;
                    font-size: 14px;
                }
            """)
            self.stop_btn.setEnabled(False)
            
            self.recording_display.append("⏹️ Recording stopped.")
            
        except Exception as e:
            logger.error(f"Error stopping recording: {e}")
            
    def play_recording(self):
        """Play recorded audio"""
        try:
            if self.is_playing:
                self.is_playing = False
                self.play_btn.setText("▶️ Play Recording")
                self.recording_display.append("⏸️ Playback paused.")
            else:
                self.is_playing = True
                self.play_btn.setText("⏸️ Pause Playback")
                self.recording_display.append("▶️ Playing recording...")
                
        except Exception as e:
            logger.error(f"Error playing recording: {e}")
            
    def synthesize_speech(self):
        """Synthesize speech from text"""
        try:
            text = self.tts_text_input.toPlainText()
            if not text.strip():
                QMessageBox.warning(self, "Warning", "Please enter text to synthesize")
                return
                
            voice = self.voice_combo.currentText()
            
            # Simulate synthesis
            synthesis_info = f"""
🗣️ Speech Synthesis Started

📝 Text: "{text[:50]}..."
🎭 Voice: {voice}
⚡ Real-time: {'Yes' if self.real_time_check.isChecked() else 'No'}
⭐ High Quality: {'Yes' if self.high_quality_check.isChecked() else 'No'}
😊 Emotion Control: {'Yes' if self.emotion_check.isChecked() else 'No'}

🎤 Synthesis in progress...
            """
            
            QMessageBox.information(self, "Synthesis", "Speech synthesis completed successfully!")
            
        except Exception as e:
            logger.error(f"Error synthesizing speech: {e}")
            QMessageBox.warning(self, "Error", f"Failed to synthesize speech: {e}")
            
    def clone_voice(self):
        """Clone voice"""
        try:
            voice_name = self.clone_voice_input.text()
            if not voice_name.strip():
                QMessageBox.warning(self, "Warning", "Please enter a voice name")
                return
                
            QMessageBox.information(self, "Voice Cloning", f"Voice cloning started for: {voice_name}")
            self.clone_voice_input.clear()
            
        except Exception as e:
            logger.error(f"Error cloning voice: {e}")
            
    def apply_preset(self, preset_type):
        """Apply voice effect preset"""
        try:
            if preset_type == "deep":
                self.pitch_slider.setValue(-6)
                self.speed_slider.setValue(90)
                QMessageBox.information(self, "Preset Applied", "Deep Voice preset applied!")
            elif preset_type == "high":
                self.pitch_slider.setValue(6)
                self.speed_slider.setValue(110)
                QMessageBox.information(self, "Preset Applied", "High Pitch preset applied!")
            elif preset_type == "robot":
                self.pitch_slider.setValue(0)
                self.speed_slider.setValue(80)
                QMessageBox.information(self, "Preset Applied", "Robot Voice preset applied!")
            elif preset_type == "echo":
                self.pitch_slider.setValue(0)
                self.speed_slider.setValue(100)
                QMessageBox.information(self, "Preset Applied", "Echo Effect preset applied!")
                
        except Exception as e:
            logger.error(f"Error applying preset: {e}")
            
    def apply_custom_effect(self):
        """Apply custom voice effect"""
        try:
            effect_params = self.custom_effect_input.text()
            if not effect_params.strip():
                QMessageBox.warning(self, "Warning", "Please enter custom effect parameters")
                return
                
            QMessageBox.information(self, "Custom Effect", f"Custom effect applied: {effect_params}")
            self.custom_effect_input.clear()
            
        except Exception as e:
            logger.error(f"Error applying custom effect: {e}")
            
    def closeEvent(self, event):
        """Save settings when closing"""
        self.save_settings()
        super().closeEvent(event)
