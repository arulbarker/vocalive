"""
Credit Wallet Tab - UI for Credit Management
Tab untuk mengelola credit wallet user
"""

import json
import logging
from datetime import datetime
from typing import Dict, List

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTextEdit,
    QGroupBox, QGridLayout, QTableWidget, QTableWidgetItem, QHeaderView,
    QFrame, QMessageBox, QProgressBar, QSplitter, QScrollArea,
    QFormLayout, QSpinBox, QComboBox, QDialog, QDialogButtonBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, pyqtSlot
from PyQt6.QtGui import QFont, QColor, QPalette

from modules_client.credit_wallet_client import (
    get_credit_wallet_client, get_current_balance, format_current_balance,
    can_afford_purchase, make_purchase, add_credits_to_wallet,
    get_credit_packages, get_package_by_id
)

logger = logging.getLogger('StreamMate.CreditWalletTab')

class CreditWalletTab(QWidget):
    """Credit Wallet Management Tab"""
    
    # Signals
    balance_updated = pyqtSignal(int)
    purchase_completed = pyqtSignal(str, int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.wallet_client = get_credit_wallet_client()
        
        # UI components
        self.balance_label = None
        self.wallet_info_labels = {}
        self.transaction_table = None
        self.packages_layout = None
        
        # Setup UI
        self.setup_ui()
        self.setup_timers()
        self.refresh_data()
    
    def setup_ui(self):
        """Setup the main UI layout"""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Header section
        header_widget = self.create_header_section()
        main_layout.addWidget(header_widget)
        
        # Create splitter for main content
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel - Wallet Info & Transactions
        left_panel = self.create_wallet_info_panel()
        splitter.addWidget(left_panel)
        
        # Right panel - Credit Packages
        right_panel = self.create_packages_panel()
        splitter.addWidget(right_panel)
        
        # Set splitter proportions
        splitter.setSizes([400, 350])
        main_layout.addWidget(splitter)
        
        # Bottom controls
        controls_widget = self.create_controls_section()
        main_layout.addWidget(controls_widget)
    
    def create_header_section(self) -> QWidget:
        """Create header with balance display"""
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                            stop:0 #4CAF50, stop:1 #2E7D32);
                border-radius: 10px;
                padding: 20px;
            }
            QLabel {
                color: white;
            }
        """)
        
        layout = QHBoxLayout(header)
        
        # Title and balance
        title_layout = QVBoxLayout()
        
        title = QLabel("💰 Credit Wallet")
        title.setStyleSheet("font-size: 28px; font-weight: bold;")
        title_layout.addWidget(title)
        
        self.balance_label = QLabel("Balance: Loading...")
        self.balance_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-top: 5px;")
        title_layout.addWidget(self.balance_label)
        
        layout.addLayout(title_layout)
        layout.addStretch()
        
        # Quick actions
        actions_layout = QVBoxLayout()
        
        self.quick_topup_btn = QPushButton("⚡ Quick Top-up")
        self.quick_topup_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255,255,255,0.2);
                color: white;
                padding: 10px 20px;
                border-radius: 8px;
                font-weight: bold;
                border: 2px solid rgba(255,255,255,0.3);
            }
            QPushButton:hover {
                background-color: rgba(255,255,255,0.3);
            }
        """)
        self.quick_topup_btn.clicked.connect(self.quick_topup)
        actions_layout.addWidget(self.quick_topup_btn)
        
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255,255,255,0.1);
                color: white;
                padding: 8px 16px;
                border-radius: 6px;
                border: 1px solid rgba(255,255,255,0.2);
            }
            QPushButton:hover {
                background-color: rgba(255,255,255,0.2);
            }
        """)
        self.refresh_btn.clicked.connect(self.refresh_data)
        actions_layout.addWidget(self.refresh_btn)
        
        layout.addLayout(actions_layout)
        
        return header
    
    def create_wallet_info_panel(self) -> QWidget:
        """Create left panel with wallet info and transactions"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Wallet statistics
        stats_group = QGroupBox("📊 Wallet Statistics")
        stats_layout = QFormLayout(stats_group)
        
        self.wallet_info_labels = {
            'total_topup': QLabel("0"),
            'total_spent': QLabel("0"),
            'created_at': QLabel("N/A"),
            'updated_at': QLabel("N/A")
        }
        
        stats_layout.addRow("Total Top-up:", self.wallet_info_labels['total_topup'])
        stats_layout.addRow("Total Spent:", self.wallet_info_labels['total_spent'])
        stats_layout.addRow("Created:", self.wallet_info_labels['created_at'])
        stats_layout.addRow("Last Updated:", self.wallet_info_labels['updated_at'])
        
        layout.addWidget(stats_group)
        
        # Transaction history
        history_group = QGroupBox("📝 Transaction History")
        history_layout = QVBoxLayout(history_group)
        
        # Filter controls
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Type:"))
        
        self.type_filter = QComboBox()
        self.type_filter.addItems(["All", "Top-up", "Spend", "Refund", "Bonus"])
        self.type_filter.currentTextChanged.connect(self.filter_transactions)
        filter_layout.addWidget(self.type_filter)
        
        filter_layout.addStretch()
        history_layout.addLayout(filter_layout)
        
        # Transaction table
        self.transaction_table = QTableWidget()
        self.transaction_table.setColumnCount(5)
        self.transaction_table.setHorizontalHeaderLabels([
            "Date", "Type", "Amount", "Balance", "Description"
        ])
        
        # Table styling
        header = self.transaction_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        
        self.transaction_table.setAlternatingRowColors(True)
        self.transaction_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        history_layout.addWidget(self.transaction_table)
        layout.addWidget(history_group)
        
        return panel
    
    def create_packages_panel(self) -> QWidget:
        """Create right panel with credit packages FOR TOP-UP ONLY"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Packages header
        packages_header = QLabel("💰 Credit Top-up Packages")
        packages_header.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px; color: #4CAF50;")
        layout.addWidget(packages_header)
        
        # Top-up info
        info_label = QLabel("💡 Top-up your credits to purchase Basic or CoHost Seller packages")
        info_label.setStyleSheet("font-size: 12px; color: #666; margin-bottom: 15px; font-style: italic;")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Scroll area for packages
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        packages_widget = QWidget()
        self.packages_layout = QVBoxLayout(packages_widget)
        
        # Create package cards
        self.create_package_cards()
        
        scroll_area.setWidget(packages_widget)
        layout.addWidget(scroll_area)
        
        return panel
    
    def create_package_cards(self):
        """Create credit top-up package cards"""
        packages = get_credit_packages()
        
        for package in packages:
            card = self.create_package_card(package)
            self.packages_layout.addWidget(card)
        
        self.packages_layout.addStretch()
    
    def create_package_card(self, package: Dict) -> QWidget:
        """Create individual top-up package card"""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                border: 2px solid {'#4CAF50' if package['popular'] else '#E0E0E0'};
                border-radius: 10px;
                padding: 15px;
                margin: 5px;
                background-color: {'#F1F8E9' if package['popular'] else '#FAFAFA'};
            }}
        """)
        
        layout = QVBoxLayout(card)
        
        # Package header
        header_layout = QHBoxLayout()
        
        name_label = QLabel(package['name'])
        name_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        header_layout.addWidget(name_label)
        
        if package['popular']:
            popular_label = QLabel("🔥 POPULAR")
            popular_label.setStyleSheet("""
                background-color: #4CAF50;
                color: white;
                padding: 2px 8px;
                border-radius: 10px;
                font-size: 10px;
                font-weight: bold;
            """)
            header_layout.addWidget(popular_label)
        
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Package details
        price_label = QLabel(f"💵 Rp {package['price_idr']:,}")
        price_label.setStyleSheet("font-size: 14px; color: #2E7D32; font-weight: bold;")
        layout.addWidget(price_label)
        
        credits_label = QLabel(f"💰 {package['credits']:,} Credits")
        layout.addWidget(credits_label)
        
        if package['bonus'] > 0:
            bonus_label = QLabel(f"🎁 +{package['bonus']:,} Bonus")
            bonus_label.setStyleSheet("color: #FF6B35; font-weight: bold;")
            layout.addWidget(bonus_label)
        
        total_label = QLabel(f"📊 Total: {package['total_credits']:,} Credits")
        total_label.setStyleSheet("font-weight: bold; color: #1976D2;")
        layout.addWidget(total_label)
        
        desc_label = QLabel(package['description'])
        desc_label.setStyleSheet("font-size: 12px; color: #666; margin-top: 5px;")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        # Top-up button (changed from Purchase)
        buy_btn = QPushButton("💳 Top-up Credits")
        buy_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {'#4CAF50' if package['popular'] else '#2196F3'};
                color: white;
                padding: 10px;
                border-radius: 8px;
                font-weight: bold;
                margin-top: 10px;
            }}
            QPushButton:hover {{
                background-color: {'#45A049' if package['popular'] else '#1976D2'};
            }}
        """)
        buy_btn.clicked.connect(lambda checked, pkg=package: self.topup_credits(pkg))
        layout.addWidget(buy_btn)
        
        return card
    
    def create_controls_section(self) -> QWidget:
        """Create bottom controls section"""
        controls = QFrame()
        controls.setStyleSheet("""
            QFrame {
                background-color: #F5F5F5;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        
        layout = QHBoxLayout(controls)
        
        # Development tools (only in local mode)
        if self.wallet_client.local_mode:
            dev_label = QLabel("🔧 Development Tools:")
            dev_label.setStyleSheet("font-weight: bold; color: #FF9800;")
            layout.addWidget(dev_label)
            
            test_add_btn = QPushButton("Add 50K Credits (Test)")
            test_add_btn.clicked.connect(lambda: self.test_add_credits(50000))
            layout.addWidget(test_add_btn)
            
            test_spend_btn = QPushButton("Spend 10K Credits (Test)")
            test_spend_btn.clicked.connect(lambda: self.test_spend_credits(10000))
            layout.addWidget(test_spend_btn)
        
        layout.addStretch()
        
        # Status info
        status_label = QLabel(f"Mode: {'Local Development' if self.wallet_client.local_mode else 'Production'}")
        status_label.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(status_label)
        
        return controls
    
    def setup_timers(self):
        """Setup refresh timers"""
        # Auto-refresh every 30 seconds
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_balance)
        self.refresh_timer.start(30000)  # 30 seconds
    
    def refresh_data(self):
        """Refresh all wallet data"""
        self.refresh_balance()
        self.refresh_wallet_info()
        self.refresh_transactions()
    
    def refresh_balance(self):
        """Refresh balance display"""
        try:
            balance = self.wallet_client.get_balance()
            formatted_balance = self.wallet_client.format_balance(balance)
            self.balance_label.setText(f"Balance: {formatted_balance} Credits")
            self.balance_updated.emit(balance)
        except Exception as e:
            logger.error(f"Error refreshing balance: {e}")
            self.balance_label.setText("Balance: Error loading")
    
    def refresh_wallet_info(self):
        """Refresh wallet statistics"""
        try:
            wallet_info = self.wallet_client.get_wallet_info()
            if wallet_info:
                self.wallet_info_labels['total_topup'].setText(f"{wallet_info['total_topup']:,}")
                self.wallet_info_labels['total_spent'].setText(f"{wallet_info['total_spent']:,}")
                self.wallet_info_labels['created_at'].setText(wallet_info['created_at'][:19] if wallet_info['created_at'] else "N/A")
                self.wallet_info_labels['updated_at'].setText(wallet_info['updated_at'][:19] if wallet_info['updated_at'] else "N/A")
        except Exception as e:
            logger.error(f"Error refreshing wallet info: {e}")
    
    def refresh_transactions(self):
        """Refresh transaction history"""
        try:
            filter_type = self.type_filter.currentText()
            transaction_type = None if filter_type == "All" else filter_type.lower()
            
            transactions = self.wallet_client.get_transaction_history(50, transaction_type)
            
            self.transaction_table.setRowCount(len(transactions))
            
            for row, transaction in enumerate(transactions):
                # Date
                date_str = transaction['created_at'][:19] if transaction['created_at'] else "N/A"
                self.transaction_table.setItem(row, 0, QTableWidgetItem(date_str))
                
                # Type
                type_item = QTableWidgetItem(transaction['type'].title())
                if transaction['type'] == 'topup':
                    type_item.setForeground(QColor('#4CAF50'))
                elif transaction['type'] == 'spend':
                    type_item.setForeground(QColor('#F44336'))
                self.transaction_table.setItem(row, 1, type_item)
                
                # Amount
                amount_str = f"{transaction['amount']:,}"
                if transaction['type'] == 'spend':
                    amount_str = f"-{amount_str}"
                elif transaction['type'] == 'topup':
                    amount_str = f"+{amount_str}"
                self.transaction_table.setItem(row, 2, QTableWidgetItem(amount_str))
                
                # Balance after
                balance_str = f"{transaction['balance_after']:,}"
                self.transaction_table.setItem(row, 3, QTableWidgetItem(balance_str))
                
                # Description
                desc = transaction.get('description', 'N/A')
                self.transaction_table.setItem(row, 4, QTableWidgetItem(desc))
            
        except Exception as e:
            logger.error(f"Error refreshing transactions: {e}")
    
    def filter_transactions(self):
        """Filter transactions by type"""
        self.refresh_transactions()
    
    def quick_topup(self):
        """Show quick top-up dialog"""
        dialog = QuickTopupDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            amount = dialog.get_amount()
            success, message = self.wallet_client.add_credits(amount, "Quick top-up")
            
            if success:
                QMessageBox.information(self, "Top-up Successful", message)
                self.refresh_data()
            else:
                QMessageBox.warning(self, "Top-up Failed", message)
    
    def topup_credits(self, package: Dict):
        """Top-up credits for a package"""
        # In local mode, simulate top-up
        if self.wallet_client.local_mode:
            reply = QMessageBox.question(
                self, 
                "Top-up Credits",
                f"Top-up {package['name']}?\n"
                f"Price: Rp {package['price_idr']:,}\n"
                f"Credits: {package['total_credits']:,}\n\n"
                f"Note: This is a simulation in development mode.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                success, message = self.wallet_client.add_credits(
                    package['total_credits'], 
                    f"Top-up: {package['name']}"
                )
                
                if success:
                    QMessageBox.information(self, "Top-up Successful", 
                                          f"Successfully topped up {package['name']}!\n{message}")
                    self.refresh_data()
                    self.purchase_completed.emit(package['id'], package['total_credits'])
                else:
                    QMessageBox.warning(self, "Top-up Failed", message)
        else:
            QMessageBox.information(self, "Coming Soon", 
                                  "Top-up will be available in production mode.")
    
    def test_add_credits(self, amount: int):
        """Test function to add credits"""
        success, message = self.wallet_client.add_credits(amount, f"Test add {amount}")
        if success:
            QMessageBox.information(self, "Test Add", message)
            self.refresh_data()
        else:
            QMessageBox.warning(self, "Test Add Failed", message)
    
    def test_spend_credits(self, amount: int):
        """Test function to spend credits"""
        success, message = self.wallet_client.spend_credits(amount, f"Test spend {amount}")
        if success:
            QMessageBox.information(self, "Test Spend", message)
            self.refresh_data()
        else:
            QMessageBox.warning(self, "Test Spend Failed", message)

class QuickTopupDialog(QDialog):
    """Dialog for quick credit top-up"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Quick Top-up")
        self.setModal(True)
        self.resize(300, 200)
        
        layout = QVBoxLayout(self)
        
        # Amount selection
        layout.addWidget(QLabel("Select amount to add:"))
        
        self.amount_spin = QSpinBox()
        self.amount_spin.setRange(1000, 1000000)
        self.amount_spin.setValue(50000)
        self.amount_spin.setSuffix(" Credits")
        layout.addWidget(self.amount_spin)
        
        # Preset buttons
        preset_layout = QHBoxLayout()
        for amount in [10000, 50000, 100000, 250000]:
            btn = QPushButton(f"{amount:,}")
            btn.clicked.connect(lambda checked, amt=amount: self.amount_spin.setValue(amt))
            preset_layout.addWidget(btn)
        layout.addLayout(preset_layout)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def get_amount(self) -> int:
        """Get selected amount"""
        return self.amount_spin.value() 