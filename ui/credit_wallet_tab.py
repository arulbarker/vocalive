import json
import logging
from datetime import datetime
from typing import Dict, Optional
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QGroupBox, QGridLayout, QMessageBox, QProgressBar, QFrame
)
from PyQt6.QtCore import QTimer, pyqtSignal, Qt
from PyQt6.QtGui import QFont

from modules_client.supabase_client import SupabaseClient
from modules_client.subscription_checker import get_today_usage

logger = logging.getLogger(__name__)

class CreditWalletTab(QWidget):
    """Simplified Credit Wallet Tab with only essential features"""
    
    balance_updated = pyqtSignal(int)
    purchase_completed = pyqtSignal(str, int)
    
    def __init__(self):
        super().__init__()
        self.supabase = SupabaseClient()
        self.current_mode = "Basic"
        
        # Data storage
        self.wallet_data = {
            'basic_credits': 0,
            'pro_credits': 0,
            'wallet_balance': 0,
            'total_usage': 0
        }
        
        self.setup_ui()
        self.setup_timer()
        self.refresh_data()
    
    def setup_ui(self):
        """Setup simplified UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # Header
        header = QLabel("💰 Credit Wallet")
        header.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("color: #2E7D32; margin: 20px;")
        layout.addWidget(header)
        
        # Balance Display
        balance_group = self.create_balance_display()
        layout.addWidget(balance_group)
        
        # Action Buttons
        actions_group = self.create_action_buttons()
        layout.addWidget(actions_group)
        
        # Usage Statistics
        usage_group = self.create_usage_stats()
        layout.addWidget(usage_group)
        
        layout.addStretch()
    
    def create_balance_display(self) -> QWidget:
        """Create balance display section"""
        group = QGroupBox("💳 Current Balance")
        group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                border: 2px solid #4CAF50;
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        layout = QGridLayout(group)
        layout.setSpacing(15)
        
        # Basic Credits
        basic_label = QLabel("🤖 Basic Credits:")
        basic_label.setFont(QFont("Arial", 14))
        self.basic_credits_display = QLabel("0")
        self.basic_credits_display.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.basic_credits_display.setStyleSheet("color: #1976D2;")
        layout.addWidget(basic_label, 0, 0)
        layout.addWidget(self.basic_credits_display, 0, 1)
        
        # Pro Credits
        pro_label = QLabel("⭐ Pro Credits:")
        pro_label.setFont(QFont("Arial", 14))
        self.pro_credits_display = QLabel("0")
        self.pro_credits_display.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.pro_credits_display.setStyleSheet("color: #FF6B35;")
        layout.addWidget(pro_label, 1, 0)
        layout.addWidget(self.pro_credits_display, 1, 1)
        
        # Wallet Balance
        wallet_label = QLabel("💰 Wallet Balance:")
        wallet_label.setFont(QFont("Arial", 14))
        self.wallet_balance_display = QLabel("0")
        self.wallet_balance_display.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.wallet_balance_display.setStyleSheet("color: #4CAF50;")
        layout.addWidget(wallet_label, 2, 0)
        layout.addWidget(self.wallet_balance_display, 2, 1)
        
        return group
    
    def create_action_buttons(self) -> QWidget:
        """Create action buttons section"""
        group = QGroupBox("🎯 Quick Actions")
        group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                border: 2px solid #FF9800;
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 10px;
            }
        """)
        
        layout = QVBoxLayout(group)
        layout.setSpacing(15)
        
        # Top-up Wallet Button
        topup_btn = QPushButton("💳 Top-up Wallet")
        topup_btn.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        topup_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 15px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        topup_btn.clicked.connect(self.topup_wallet)
        layout.addWidget(topup_btn)
        
        # Purchase buttons row
        purchase_layout = QHBoxLayout()
        
        # Purchase Basic Mode
        basic_btn = QPushButton("🤖 Buy Basic Mode\n(100,000 Credits)")
        basic_btn.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        basic_btn.setStyleSheet("""
            QPushButton {
                background-color: #1976D2;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 15px;
                min-height: 60px;
            }
            QPushButton:hover {
                background-color: #1565C0;
            }
        """)
        basic_btn.clicked.connect(self.purchase_basic_mode)
        purchase_layout.addWidget(basic_btn)
        
        # Purchase Pro Mode
        pro_btn = QPushButton("⭐ Buy Pro Mode\n(100,000 Credits)")
        pro_btn.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        pro_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF6B35;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 15px;
                min-height: 60px;
            }
            QPushButton:hover {
                background-color: #E55A2B;
            }
        """)
        pro_btn.clicked.connect(self.purchase_pro_mode)
        purchase_layout.addWidget(pro_btn)
        
        layout.addLayout(purchase_layout)
        
        return group
    
    def create_usage_stats(self) -> QWidget:
        """Create usage statistics section"""
        group = QGroupBox("📊 Usage Statistics")
        group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                border: 2px solid #9C27B0;
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 10px;
            }
        """)
        
        layout = QGridLayout(group)
        layout.setSpacing(15)
        
        # Total Usage
        usage_label = QLabel("📈 Total Credit Usage:")
        usage_label.setFont(QFont("Arial", 14))
        self.total_usage_display = QLabel("0")
        self.total_usage_display.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.total_usage_display.setStyleSheet("color: #9C27B0;")
        layout.addWidget(usage_label, 0, 0)
        layout.addWidget(self.total_usage_display, 0, 1)
        
        # Current Mode
        mode_label = QLabel("🎯 Current Mode:")
        mode_label.setFont(QFont("Arial", 14))
        self.current_mode_display = QLabel("Basic")
        self.current_mode_display.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.current_mode_display.setStyleSheet("color: #1976D2;")
        layout.addWidget(mode_label, 1, 0)
        layout.addWidget(self.current_mode_display, 1, 1)
        
        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh Data")
        refresh_btn.setFont(QFont("Arial", 12))
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #607D8B;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #546E7A;
            }
        """)
        refresh_btn.clicked.connect(self.refresh_data)
        layout.addWidget(refresh_btn, 2, 0, 1, 2)
        
        return group
    
    def setup_timer(self):
        """Setup auto-refresh timer"""
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_data)
        self.refresh_timer.start(30000)  # Refresh every 30 seconds
    
    def refresh_data(self):
        """Refresh wallet data from Supabase"""
        try:
            # Get user email
            from modules_client.config_manager import ConfigManager
            cfg = ConfigManager()
            email = cfg.get("user_data", {}).get("email", "")
            
            if not email:
                return
            
            # Get balance data
            balance_data = self.supabase.get_credit_balance(email)
            
            if balance_data and balance_data.get("status") == "success":
                data = balance_data.get("data", {})
                
                self.wallet_data['basic_credits'] = data.get('basic_credits', 0)
                self.wallet_data['pro_credits'] = data.get('pro_credits', 0)
                self.wallet_data['wallet_balance'] = data.get('wallet_balance', 0)
                
                # Calculate total usage (this would need to be tracked separately)
                self.wallet_data['total_usage'] = data.get('total_spent', 0)
                
                self.update_displays()
                
        except Exception as e:
            logger.error(f"Error refreshing data: {e}")
    
    def update_displays(self):
        """Update all display labels"""
        self.basic_credits_display.setText(f"{self.wallet_data['basic_credits']:,}")
        self.pro_credits_display.setText(f"{self.wallet_data['pro_credits']:,}")
        self.wallet_balance_display.setText(f"{self.wallet_data['wallet_balance']:,}")
        self.total_usage_display.setText(f"{self.wallet_data['total_usage']:,}")
        
        # Update current mode based on subscription
        try:
            tier, used_hours, limit_hours = get_today_usage()
            mode = tier.title()  # Convert to title case (basic -> Basic, pro -> Pro)
            self.current_mode_display.setText(mode)
            
            if mode == "Pro":
                self.current_mode_display.setStyleSheet("color: #FF6B35;")
            else:
                self.current_mode_display.setStyleSheet("color: #1976D2;")
                
        except:
            pass
    
    def topup_wallet(self):
        """Handle wallet top-up"""
        # Show simple top-up options
        reply = QMessageBox.question(
            self,
            "Top-up Wallet",
            "Choose top-up amount:\n\n"
            "💰 50,000 Credits - Rp 50,000\n"
            "💰 100,000 Credits - Rp 100,000\n"
            "💰 250,000 Credits - Rp 250,000\n"
            "💰 500,000 Credits - Rp 500,000\n\n"
            "This will open payment gateway.",
            QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel
        )
        
        if reply == QMessageBox.StandardButton.Ok:
            QMessageBox.information(
                self,
                "Payment Gateway",
                "Payment gateway integration will be implemented here.\n"
                "For now, this is a placeholder."
            )
    
    def purchase_basic_mode(self):
        """Purchase Basic mode credits"""
        if self.wallet_data['wallet_balance'] < 100000:
            QMessageBox.warning(
                self,
                "Insufficient Balance",
                "You need at least 100,000 wallet credits to purchase Basic mode.\n"
                "Please top-up your wallet first."
            )
            return
        
        reply = QMessageBox.question(
            self,
            "Purchase Basic Mode",
            "Purchase Basic Mode for 100,000 credits?\n\n"
            "This will convert 100,000 wallet credits to Basic credits.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.process_purchase("basic", 100000)
    
    def purchase_pro_mode(self):
        """Purchase Pro mode credits"""
        if self.wallet_data['wallet_balance'] < 100000:
            QMessageBox.warning(
                self,
                "Insufficient Balance",
                "You need at least 100,000 wallet credits to purchase Pro mode.\n"
                "Please top-up your wallet first."
            )
            return
        
        reply = QMessageBox.question(
            self,
            "Purchase Pro Mode",
            "Purchase Pro Mode for 100,000 credits?\n\n"
            "This will convert 100,000 wallet credits to Pro credits.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.process_purchase("pro", 100000)
    
    def process_purchase(self, mode: str, amount: int):
        """Process credit purchase"""
        try:
            # Get user email
            from modules_client.config_manager import ConfigManager
            cfg = ConfigManager()
            email = cfg.get("user_data", {}).get("email", "")
            
            if not email:
                QMessageBox.warning(self, "Login Required", "Please login first")
                return
            
            # Deduct from wallet
            deduct_result = self.supabase.deduct_credits(
                email, amount, f"Purchase {mode.title()} mode"
            )
            
            if deduct_result and deduct_result.get("status") == "success":
                # Add to specific mode credits
                credit_type = f"{mode}_credits"
                add_result = self.supabase.add_specific_credits(
                    email, credit_type, amount, f"{mode.title()} mode purchase"
                )
                
                if add_result and add_result.get("status") == "success":
                    QMessageBox.information(
                        self,
                        "Purchase Successful",
                        f"Successfully purchased {mode.title()} mode!\n"
                        f"{amount:,} credits added to your {mode} account."
                    )
                    self.refresh_data()
                    self.purchase_completed.emit(mode, amount)
                else:
                    QMessageBox.warning(self, "Purchase Failed", "Failed to add credits")
            else:
                QMessageBox.warning(self, "Purchase Failed", "Insufficient wallet balance")
                
        except Exception as e:
            logger.error(f"Error processing purchase: {e}")
            QMessageBox.warning(self, "Purchase Failed", f"Error: {str(e)}")