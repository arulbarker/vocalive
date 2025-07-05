"""
CoHost Seller Tab - Live Selling AI with OBS Integration
Advanced tab for e-commerce live streaming with automatic scene switching
"""

import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTextEdit,
    QGroupBox, QGridLayout, QLineEdit, QSpinBox, QComboBox, QTabWidget,
    QScrollArea, QFrame, QMessageBox, QProgressBar, QCheckBox, QSplitter,
    QTableWidget, QTableWidgetItem, QHeaderView, QFormLayout, QDialog,
    QDialogButtonBox, QPlainTextEdit, QInputDialog
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, pyqtSlot
from PyQt6.QtGui import QFont, QColor, QPalette

from modules_client.config_manager import ConfigManager
from modules_client.obs_integration import get_obs_integration
from modules_client.product_manager import get_product_manager

logger = logging.getLogger('StreamMate.CohostSeller')

class CohostSellerTab(QWidget):
    """CoHost Seller Tab for live selling with AI and OBS integration"""
    
    # Signals
    demo_expired = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.cfg = ConfigManager()
        
        # Core components
        self.obs_integration = get_obs_integration()
        self.product_manager = get_product_manager()
        
        # Demo mode tracking
        self.demo_active = False
        self.demo_start_time = None
        self.demo_duration_minutes = 30
        self.demo_timer = None
        
        # UI components
        self.status_label = None
        self.obs_status_label = None
        self.product_table = None
        self.demo_progress = None
        
        # Setup UI
        self.setup_ui()
        self.setup_timers()
        self.check_access_status()
        
    def setup_ui(self):
        """Setup the main UI layout"""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Header section
        header_widget = self.create_header_section()
        main_layout.addWidget(header_widget)
        
        # Create splitter for main content
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel - Product Management
        left_panel = self.create_product_management_panel()
        splitter.addWidget(left_panel)
        
        # Right panel - OBS & Analytics
        right_panel = self.create_obs_analytics_panel()
        splitter.addWidget(right_panel)
        
        # Set splitter proportions
        splitter.setSizes([400, 300])
        main_layout.addWidget(splitter)
        
        # Bottom status bar
        status_bar = self.create_status_bar()
        main_layout.addWidget(status_bar)
        
    def create_header_section(self) -> QWidget:
        """Create header with title and access status"""
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                            stop:0 #E91E63, stop:1 #AD1457);
                border-radius: 10px;
                padding: 15px;
            }
            QLabel {
                color: white;
            }
        """)
        
        layout = QHBoxLayout(header)
        
        # Title and description
        title_layout = QVBoxLayout()
        
        title = QLabel("🛍️ CoHost Seller - Live Selling AI")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        title_layout.addWidget(title)
        
        subtitle = QLabel("Advanced AI for e-commerce live streaming with automatic OBS scene switching")
        subtitle.setStyleSheet("font-size: 14px; opacity: 0.9;")
        title_layout.addWidget(subtitle)
        
        layout.addLayout(title_layout)
        layout.addStretch()
        
        # Status indicator
        self.status_label = QLabel("🔴 Access Required")
        self.status_label.setStyleSheet("""
            QLabel {
                background-color: rgba(255,255,255,0.2);
                padding: 8px 15px;
                border-radius: 15px;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.status_label)
        
        return header
        
    def create_product_management_panel(self) -> QWidget:
        """Create left panel for product management"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Product slots info
        slots_info = self.create_slots_info_widget()
        layout.addWidget(slots_info)
        
        # Product table
        products_group = QGroupBox("🛒 Product Management")
        products_layout = QVBoxLayout(products_group)
        
        # Add/Edit product button
        btn_layout = QHBoxLayout()
        self.add_product_btn = QPushButton("➕ Add Product")
        self.add_product_btn.clicked.connect(self.add_edit_product)
        self.add_product_btn.setEnabled(False)
        btn_layout.addWidget(self.add_product_btn)
        
        self.upgrade_slots_btn = QPushButton("💰 Upgrade Slots")
        self.upgrade_slots_btn.clicked.connect(self.upgrade_slots)
        self.upgrade_slots_btn.setEnabled(False)
        btn_layout.addWidget(self.upgrade_slots_btn)
        
        btn_layout.addStretch()
        products_layout.addLayout(btn_layout)
        
        # Product table
        self.product_table = QTableWidget()
        self.product_table.setColumnCount(6)
        self.product_table.setHorizontalHeaderLabels([
            "Slot", "Product", "Trigger", "Scene", "Stock", "Actions"
        ])
        
        # Table styling
        self.product_table.horizontalHeader().setStretchLastSection(True)
        self.product_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.product_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        
        products_layout.addWidget(self.product_table)
        layout.addWidget(products_group)
        
        return panel
        
    def create_obs_analytics_panel(self) -> QWidget:
        """Create right panel for OBS integration and analytics"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # OBS Integration
        obs_group = QGroupBox("📺 OBS Integration")
        obs_layout = QVBoxLayout(obs_group)
        
        # OBS Status
        obs_status_layout = QHBoxLayout()
        obs_status_layout.addWidget(QLabel("Status:"))
        self.obs_status_label = QLabel("🔴 Not Connected")
        obs_status_layout.addWidget(self.obs_status_label)
        obs_status_layout.addStretch()
        obs_layout.addLayout(obs_status_layout)
        
        # OBS Controls
        obs_controls = QHBoxLayout()
        self.test_obs_btn = QPushButton("🔍 Test Connection")
        self.test_obs_btn.clicked.connect(self.test_obs_connection)
        self.test_obs_btn.setEnabled(False)
        obs_controls.addWidget(self.test_obs_btn)
        
        self.obs_settings_btn = QPushButton("⚙️ OBS Settings")
        self.obs_settings_btn.clicked.connect(self.show_obs_settings)
        self.obs_settings_btn.setEnabled(False)
        obs_controls.addWidget(self.obs_settings_btn)
        
        obs_layout.addLayout(obs_controls)
        
        # Scene validation
        self.validate_scenes_btn = QPushButton("✅ Validate Scenes")
        self.validate_scenes_btn.clicked.connect(self.validate_scenes)
        self.validate_scenes_btn.setEnabled(False)
        obs_layout.addWidget(self.validate_scenes_btn)
        
        layout.addWidget(obs_group)
        
        # Analytics (placeholder)
        analytics_group = QGroupBox("📊 Sales Analytics")
        analytics_layout = QVBoxLayout(analytics_group)
        
        self.analytics_text = QTextEdit()
        self.analytics_text.setMaximumHeight(150)
        self.analytics_text.setPlainText("Analytics will be available when CoHost Seller is active...")
        self.analytics_text.setReadOnly(True)
        analytics_layout.addWidget(self.analytics_text)
        
        layout.addWidget(analytics_group)
        
        # Demo section
        demo_group = self.create_demo_section()
        layout.addWidget(demo_group)
        
        layout.addStretch()
        return panel
        
    def create_slots_info_widget(self) -> QWidget:
        """Create widget showing slot usage information"""
        info_widget = QFrame()
        info_widget.setStyleSheet("""
            QFrame {
                background-color: #F5F5F5;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        
        layout = QHBoxLayout(info_widget)
        
        self.slots_info_label = QLabel("Slots: 0/0")
        self.slots_info_label.setStyleSheet("font-weight: bold; color: #333;")
        layout.addWidget(self.slots_info_label)
        
        layout.addStretch()
        
        self.slots_cost_label = QLabel("Upgrade: 100,000 credits/slot")
        self.slots_cost_label.setStyleSheet("font-size: 12px; color: #666;")
        layout.addWidget(self.slots_cost_label)
        
        return info_widget
        
    def create_demo_section(self) -> QWidget:
        """Create demo mode section"""
        demo_group = QGroupBox("🎯 Demo Mode")
        demo_layout = QVBoxLayout(demo_group)
        
        demo_info = QLabel("Try CoHost Seller for 30 minutes")
        demo_info.setStyleSheet("color: #666; font-size: 12px;")
        demo_layout.addWidget(demo_info)
        
        self.start_demo_btn = QPushButton("▶️ Start Demo (30 min)")
        self.start_demo_btn.clicked.connect(self.start_demo)
        demo_layout.addWidget(self.start_demo_btn)
        
        # Demo progress
        self.demo_progress = QProgressBar()
        self.demo_progress.setVisible(False)
        demo_layout.addWidget(self.demo_progress)
        
        self.demo_time_label = QLabel("")
        self.demo_time_label.setVisible(False)
        demo_layout.addWidget(self.demo_time_label)
        
        return demo_group
        
    def create_status_bar(self) -> QWidget:
        """Create bottom status bar"""
        status_bar = QFrame()
        status_bar.setStyleSheet("""
            QFrame {
                background-color: #FAFAFA;
                border-top: 1px solid #E0E0E0;
                padding: 8px 15px;
            }
        """)
        
        layout = QHBoxLayout(status_bar)
        
        self.bottom_status_label = QLabel("Ready")
        layout.addWidget(self.bottom_status_label)
        
        layout.addStretch()
        
        # Version info
        version_label = QLabel("CoHost Seller v1.0")
        version_label.setStyleSheet("color: #999; font-size: 11px;")
        layout.addWidget(version_label)
        
        return status_bar
        
    def setup_timers(self):
        """Setup timers for demo mode and updates"""
        # Demo timer
        self.demo_timer = QTimer()
        self.demo_timer.timeout.connect(self.update_demo_progress)
        
        # Refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_data)
        self.refresh_timer.start(30000)  # 30 seconds
        
    def check_access_status(self):
        """Check if user has access to CoHost Seller"""
        try:
            subscription_file = Path("config/subscription_status.json")
            if subscription_file.exists():
                with open(subscription_file, 'r', encoding='utf-8') as f:
                    sub_data = json.load(f)
                
                seller_data = sub_data.get("cohost_seller", {})
                if seller_data.get("active", False):
                    self.enable_cohost_seller()
                    return
            
            # Check demo status
            if self.check_demo_available():
                self.enable_demo_mode()
            else:
                self.show_access_required()
                
        except Exception as e:
            logger.error(f"Error checking access status: {e}")
            self.show_access_required()
            
    def enable_cohost_seller(self):
        """Enable full CoHost Seller functionality"""
        self.status_label.setText("✅ CoHost Seller Active")
        self.status_label.setStyleSheet("""
            QLabel {
                background-color: rgba(76,175,80,0.8);
                padding: 8px 15px;
                border-radius: 15px;
                font-weight: bold;
                color: white;
            }
        """)
        
        # Enable all controls
        self.add_product_btn.setEnabled(True)
        self.upgrade_slots_btn.setEnabled(True)
        self.test_obs_btn.setEnabled(True)
        self.obs_settings_btn.setEnabled(True)
        self.validate_scenes_btn.setEnabled(True)
        
        # Hide demo section
        self.start_demo_btn.setVisible(False)
        
        # Load data
        self.refresh_data()
        self.update_slots_info()
        
    def enable_demo_mode(self):
        """Enable demo mode"""
        self.status_label.setText("🎯 Demo Available")
        self.status_label.setStyleSheet("""
            QLabel {
                background-color: rgba(255,152,0,0.8);
                padding: 8px 15px;
                border-radius: 15px;
                font-weight: bold;
                color: white;
            }
        """)
        
        self.start_demo_btn.setEnabled(True)
        
    def show_access_required(self):
        """Show access required state"""
        self.status_label.setText("🔴 Purchase Required")
        self.bottom_status_label.setText("Purchase CoHost Seller package to access these features")
        
        # Disable all controls
        self.add_product_btn.setEnabled(False)
        self.upgrade_slots_btn.setEnabled(False)
        self.test_obs_btn.setEnabled(False)
        self.obs_settings_btn.setEnabled(False)
        self.validate_scenes_btn.setEnabled(False)
        self.start_demo_btn.setEnabled(False)
        
    def check_demo_available(self) -> bool:
        """Check if demo is available for user"""
        # Implementation similar to other tabs
        # Check if user hasn't used demo before or if daily reset applies
        return True  # Simplified for now
        
    def start_demo(self):
        """Start 30-minute demo mode"""
        try:
            reply = QMessageBox.question(
                self, "Start Demo",
                "Start 30-minute CoHost Seller demo?\n\n"
                "During demo you can:\n"
                "• Add up to 2 products\n"
                "• Test OBS integration\n"
                "• Experience live selling features\n\n"
                "Demo will automatically end after 30 minutes.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.demo_active = True
                self.demo_start_time = datetime.now()
                
                # Enable demo features
                self.enable_demo_features()
                
                # Start demo timer
                self.demo_timer.start(1000)  # Update every second
                
                # Show demo UI
                self.demo_progress.setVisible(True)
                self.demo_time_label.setVisible(True)
                self.start_demo_btn.setText("⏹️ Stop Demo")
                self.start_demo_btn.clicked.disconnect()
                self.start_demo_btn.clicked.connect(self.stop_demo)
                
                self.status_label.setText("🎯 Demo Active")
                self.bottom_status_label.setText("Demo mode active - 30 minutes remaining")
                
                QMessageBox.information(
                    self, "Demo Started",
                    "CoHost Seller demo is now active for 30 minutes!\n\n"
                    "You can now test all features."
                )
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to start demo: {str(e)}")
            
    def enable_demo_features(self):
        """Enable features during demo mode"""
        self.add_product_btn.setEnabled(True)
        self.test_obs_btn.setEnabled(True)
        self.obs_settings_btn.setEnabled(True)
        self.validate_scenes_btn.setEnabled(True)
        # Note: upgrade_slots_btn stays disabled in demo
        
    def stop_demo(self):
        """Stop demo mode"""
        self.demo_active = False
        self.demo_timer.stop()
        
        # Reset UI
        self.demo_progress.setVisible(False)
        self.demo_time_label.setVisible(False)
        self.start_demo_btn.setText("▶️ Start Demo (30 min)")
        self.start_demo_btn.clicked.disconnect()
        self.start_demo_btn.clicked.connect(self.start_demo)
        
        # Disable features
        self.show_access_required()
        
        QMessageBox.information(self, "Demo Ended", "CoHost Seller demo has ended.")
        
    def update_demo_progress(self):
        """Update demo progress and timer"""
        if not self.demo_active or not self.demo_start_time:
            return
            
        elapsed = datetime.now() - self.demo_start_time
        elapsed_minutes = elapsed.total_seconds() / 60
        remaining_minutes = max(0, self.demo_duration_minutes - elapsed_minutes)
        
        # Update progress bar
        progress = int((elapsed_minutes / self.demo_duration_minutes) * 100)
        self.demo_progress.setValue(min(100, progress))
        
        # Update time label
        remaining_time = timedelta(minutes=remaining_minutes)
        self.demo_time_label.setText(f"Time remaining: {str(remaining_time).split('.')[0]}")
        
        # Check if demo expired
        if remaining_minutes <= 0:
            self.stop_demo()
            
    def refresh_data(self):
        """Refresh all data displays"""
        self.update_product_table()
        self.update_slots_info()
        self.update_obs_status()
        
    def update_slots_info(self):
        """Update slot usage information"""
        upgrade_info = self.product_manager.get_slot_upgrade_info()
        
        used = upgrade_info["used_slots"]
        available = upgrade_info["available_slots"]
        
        self.slots_info_label.setText(f"Slots: {used}/{available}")
        
        # Update upgrade button
        if upgrade_info["can_upgrade"]:
            remaining = upgrade_info["slots_available_for_purchase"]
            self.upgrade_slots_btn.setText(f"💰 Buy +{remaining} Slots")
            self.upgrade_slots_btn.setEnabled(True and (self.demo_active or self.is_full_access()))
        else:
            self.upgrade_slots_btn.setText("💰 Max Slots Reached")
            self.upgrade_slots_btn.setEnabled(False)
            
    def update_product_table(self):
        """Update product table with current products"""
        products = self.product_manager.get_all_products()
        
        self.product_table.setRowCount(len(products))
        
        for row, (slot_id, product) in enumerate(products.items()):
            self.product_table.setItem(row, 0, QTableWidgetItem(slot_id))
            self.product_table.setItem(row, 1, QTableWidgetItem(product.get("judul_barang", "")))
            self.product_table.setItem(row, 2, QTableWidgetItem(product.get("trigger_keyword", "")))
            self.product_table.setItem(row, 3, QTableWidgetItem(product.get("scene_obs", "")))
            self.product_table.setItem(row, 4, QTableWidgetItem(str(product.get("jumlah_stok", 0))))
            
            # Actions column with edit/delete buttons
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(2, 2, 2, 2)
            
            edit_btn = QPushButton("✏️")
            edit_btn.setMaximumWidth(30)
            edit_btn.clicked.connect(lambda checked, sid=slot_id: self.edit_product(sid))
            
            delete_btn = QPushButton("🗑️")
            delete_btn.setMaximumWidth(30)
            delete_btn.clicked.connect(lambda checked, sid=slot_id: self.delete_product(sid))
            
            actions_layout.addWidget(edit_btn)
            actions_layout.addWidget(delete_btn)
            actions_layout.addStretch()
            
            self.product_table.setCellWidget(row, 5, actions_widget)
            
    def update_obs_status(self):
        """Update OBS connection status"""
        if self.obs_integration.connected:
            self.obs_status_label.setText("🟢 Connected")
            self.obs_status_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.obs_status_label.setText("🔴 Not Connected")
            self.obs_status_label.setStyleSheet("color: red; font-weight: bold;")
            
    def is_full_access(self) -> bool:
        """Check if user has full access (not demo)"""
        try:
            subscription_file = Path("config/subscription_status.json")
            if subscription_file.exists():
                with open(subscription_file, 'r', encoding='utf-8') as f:
                    sub_data = json.load(f)
                return sub_data.get("cohost_seller", {}).get("active", False)
        except:
            pass
        return False
        
    # Event handlers
    def add_edit_product(self):
        """Open add/edit product dialog"""
        dialog = ProductEditDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_data()
            
    def edit_product(self, slot_id: str):
        """Edit existing product"""
        product = self.product_manager.get_product(slot_id)
        if product:
            dialog = ProductEditDialog(self, slot_id, product)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.refresh_data()
                
    def delete_product(self, slot_id: str):
        """Delete product"""
        product = self.product_manager.get_product(slot_id)
        if product:
            reply = QMessageBox.question(
                self, "Delete Product",
                f"Delete product '{product.get('judul_barang', 'Unknown')}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                if self.product_manager.remove_product(slot_id):
                    self.refresh_data()
                    QMessageBox.information(self, "Success", "Product deleted successfully")
                else:
                    QMessageBox.warning(self, "Error", "Failed to delete product")
                    
    def upgrade_slots(self):
        """Handle slot upgrade purchase"""
        upgrade_info = self.product_manager.get_slot_upgrade_info()
        
        if not upgrade_info["can_upgrade"]:
            QMessageBox.information(self, "Max Slots", "You already have the maximum number of slots")
            return
            
        available_to_buy = upgrade_info["slots_available_for_purchase"]
        cost_per_slot = upgrade_info["upgrade_cost_per_slot"]
        
        slots_to_buy, ok = QInputDialog.getInt(
            self, "Upgrade Slots",
            f"How many slots to purchase?\n\n"
            f"Available: {available_to_buy} slots\n"
            f"Cost: {cost_per_slot:,} credits per slot",
            1, 1, available_to_buy
        )
        
        if ok:
            total_cost = slots_to_buy * cost_per_slot
            
            reply = QMessageBox.question(
                self, "Confirm Purchase",
                f"Purchase {slots_to_buy} slot(s) for {total_cost:,} credits?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                result = self.product_manager.purchase_slot_upgrade(slots_to_buy)
                
                if result["success"]:
                    QMessageBox.information(
                        self, "Purchase Successful",
                        f"Successfully purchased {slots_to_buy} slot(s)!\n\n"
                        f"New total slots: {result['new_total_slots']}\n"
                        f"Credits used: {result['cost']:,}\n"
                        f"Remaining balance: {result['remaining_balance']:,}"
                    )
                    self.refresh_data()
                else:
                    QMessageBox.warning(self, "Purchase Failed", result["error"])
                    
    def test_obs_connection(self):
        """Test OBS WebSocket connection"""
        self.bottom_status_label.setText("Testing OBS connection...")
        
        try:
            result = self.obs_integration.test_connection()
            
            if result["connected"]:
                scenes = result.get("scenes", [])
                current_scene = result.get("current_scene", "Unknown")
                
                QMessageBox.information(
                    self, "OBS Connection Test",
                    f"✅ Successfully connected to OBS!\n\n"
                    f"Current scene: {current_scene}\n"
                    f"Available scenes: {len(scenes)}\n\n"
                    f"Scenes: {', '.join(scenes[:5])}"
                    f"{'...' if len(scenes) > 5 else ''}"
                )
                self.update_obs_status()
            else:
                QMessageBox.warning(
                    self, "OBS Connection Failed",
                    f"❌ Failed to connect to OBS\n\n"
                    f"Error: {result.get('error', 'Unknown error')}\n\n"
                    f"Make sure:\n"
                    f"• OBS Studio is running\n"
                    f"• WebSocket plugin is installed\n"
                    f"• WebSocket server is enabled\n"
                    f"• Connection settings are correct"
                )
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Connection test failed: {str(e)}")
            
        self.bottom_status_label.setText("Ready")
        
    def show_obs_settings(self):
        """Show OBS connection settings dialog"""
        dialog = OBSSettingsDialog(self, self.obs_integration)
        dialog.exec()
        self.update_obs_status()
        
    def validate_scenes(self):
        """Validate that all product scenes exist in OBS"""
        try:
            # Get available scenes from OBS
            if not self.obs_integration.connect():
                QMessageBox.warning(self, "OBS Not Connected", "Please connect to OBS first")
                return
                
            available_scenes = self.obs_integration.get_scene_list()
            validation_result = self.product_manager.validate_obs_scenes(available_scenes)
            
            valid_scenes = validation_result["valid"]
            invalid_scenes = validation_result["invalid"]
            
            message = "Scene Validation Results:\n\n"
            
            if valid_scenes:
                message += "✅ Valid Scenes:\n"
                for scene in valid_scenes:
                    message += f"  • {scene}\n"
                message += "\n"
                
            if invalid_scenes:
                message += "❌ Invalid Scenes:\n"
                for scene in invalid_scenes:
                    message += f"  • {scene}\n"
                message += "\n"
                
            if not invalid_scenes:
                message += "🎉 All product scenes are valid!"
                
            QMessageBox.information(self, "Scene Validation", message)
            
        except Exception as e:
            QMessageBox.critical(self, "Validation Error", f"Failed to validate scenes: {str(e)}")


class ProductEditDialog(QDialog):
    """Dialog for adding/editing products"""
    
    def __init__(self, parent, slot_id: str = None, product_data: Dict = None):
        super().__init__(parent)
        self.parent = parent
        self.slot_id = slot_id
        self.product_data = product_data or {}
        self.is_edit = slot_id is not None
        
        self.setup_ui()
        self.load_data()
        
    def setup_ui(self):
        """Setup dialog UI"""
        self.setWindowTitle("Edit Product" if self.is_edit else "Add Product")
        self.setModal(True)
        self.resize(500, 400)
        
        layout = QVBoxLayout(self)
        
        # Form
        form_layout = QFormLayout()
        
        # Product title
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("e.g., Premium Leather Bag")
        form_layout.addRow("Product Title:", self.title_edit)
        
        # OBS Scene
        self.scene_edit = QLineEdit()
        self.scene_edit.setPlaceholderText("e.g., Product_1_Display")
        form_layout.addRow("OBS Scene Name:", self.scene_edit)
        
        # Trigger keyword
        self.trigger_edit = QLineEdit()
        self.trigger_edit.setPlaceholderText("e.g., spill tas, show bag")
        form_layout.addRow("Trigger Keyword:", self.trigger_edit)
        
        # Stock
        self.stock_spin = QSpinBox()
        self.stock_spin.setRange(0, 9999)
        self.stock_spin.setValue(1)
        form_layout.addRow("Stock Quantity:", self.stock_spin)
        
        # Description
        self.description_edit = QPlainTextEdit()
        self.description_edit.setPlaceholderText(
            "Detailed product description that AI will use when explaining the product to viewers..."
        )
        self.description_edit.setMaximumHeight(150)
        form_layout.addRow("Product Description:", self.description_edit)
        
        layout.addLayout(form_layout)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
    def load_data(self):
        """Load existing product data for editing"""
        if self.product_data:
            self.title_edit.setText(self.product_data.get("judul_barang", ""))
            self.scene_edit.setText(self.product_data.get("scene_obs", ""))
            self.trigger_edit.setText(self.product_data.get("trigger_keyword", ""))
            self.stock_spin.setValue(self.product_data.get("jumlah_stok", 1))
            self.description_edit.setPlainText(self.product_data.get("keterangan_produk", ""))
            
    def accept(self):
        """Save product data"""
        try:
            # Validate input
            if not self.title_edit.text().strip():
                QMessageBox.warning(self, "Validation Error", "Product title is required")
                return
                
            if not self.scene_edit.text().strip():
                QMessageBox.warning(self, "Validation Error", "OBS scene name is required")
                return
                
            if not self.trigger_edit.text().strip():
                QMessageBox.warning(self, "Validation Error", "Trigger keyword is required")
                return
                
            if not self.description_edit.toPlainText().strip():
                QMessageBox.warning(self, "Validation Error", "Product description is required")
                return
            
            # Prepare product data
            product_data = {
                "judul_barang": self.title_edit.text().strip(),
                "scene_obs": self.scene_edit.text().strip(),
                "trigger_keyword": self.trigger_edit.text().strip(),
                "jumlah_stok": self.stock_spin.value(),
                "keterangan_produk": self.description_edit.toPlainText().strip()
            }
            
            # Generate slot ID if adding new product
            if not self.slot_id:
                # Find available slot
                product_manager = get_product_manager()
                used_slots = set(product_manager.get_all_products().keys())
                
                for i in range(1, 11):
                    slot_id = str(i)
                    if slot_id not in used_slots:
                        self.slot_id = slot_id
                        break
                        
                if not self.slot_id:
                    QMessageBox.warning(self, "Error", "No available slots")
                    return
            
            # Save product
            product_manager = get_product_manager()
            if product_manager.add_product(self.slot_id, product_data):
                super().accept()
            else:
                QMessageBox.warning(self, "Error", "Failed to save product")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save product: {str(e)}")


class OBSSettingsDialog(QDialog):
    """Dialog for OBS connection settings"""
    
    def __init__(self, parent, obs_integration):
        super().__init__(parent)
        self.obs_integration = obs_integration
        self.setup_ui()
        self.load_settings()
        
    def setup_ui(self):
        """Setup dialog UI"""
        self.setWindowTitle("OBS WebSocket Settings")
        self.setModal(True)
        self.resize(400, 250)
        
        layout = QVBoxLayout(self)
        
        # Form
        form_layout = QFormLayout()
        
        self.host_edit = QLineEdit()
        form_layout.addRow("Host:", self.host_edit)
        
        self.port_spin = QSpinBox()
        self.port_spin.setRange(1, 65535)
        form_layout.addRow("Port:", self.port_spin)
        
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addRow("Password:", self.password_edit)
        
        layout.addLayout(form_layout)
        
        # Test button
        test_btn = QPushButton("🔍 Test Connection")
        test_btn.clicked.connect(self.test_connection)
        layout.addWidget(test_btn)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.save_settings)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
    def load_settings(self):
        """Load current OBS settings"""
        self.host_edit.setText(self.obs_integration.host)
        self.port_spin.setValue(self.obs_integration.port)
        self.password_edit.setText(self.obs_integration.password)
        
    def test_connection(self):
        """Test connection with current settings"""
        # Temporarily update settings
        original_host = self.obs_integration.host
        original_port = self.obs_integration.port
        original_password = self.obs_integration.password
        
        try:
            self.obs_integration.update_connection_settings(
                self.host_edit.text(),
                self.port_spin.value(),
                self.password_edit.text()
            )
            
            result = self.obs_integration.test_connection()
            
            if result["connected"]:
                QMessageBox.information(self, "Success", "✅ Connection successful!")
            else:
                QMessageBox.warning(self, "Failed", f"❌ Connection failed:\n{result.get('error', 'Unknown error')}")
                
        finally:
            # Restore original settings if test failed
            if not result.get("connected", False):
                self.obs_integration.update_connection_settings(
                    original_host, original_port, original_password
                )
                
    def save_settings(self):
        """Save OBS settings"""
        self.obs_integration.update_connection_settings(
            self.host_edit.text(),
            self.port_spin.value(),
            self.password_edit.text()
        )
        self.accept()
