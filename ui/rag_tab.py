# ui/rag_tab.py - RAG (Retrieval-Augmented Generation) Knowledge System Tab untuk Pro Mode
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
    QMessageBox, QFileDialog, QListWidget, QListWidgetItem,
    QTableWidget, QTableWidgetItem, QHeaderView, QSplitter, QFormLayout
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

logger = setup_logger('RAGTab')

class RAGTab(QWidget):
    """RAG (Retrieval-Augmented Generation) Knowledge System Tab untuk Pro Mode"""
    
    def __init__(self):
        super().__init__()
        self.api_client = APIClient()
        self.config_manager = ConfigManager()
        self.settings = self.config_manager.load_settings()
        
        # RAG settings
        self.knowledge_base = {}
        self.current_documents = []
        self.rag_enabled = False
        
        self.setup_ui()
        self.load_settings()
    
    def setup_ui(self):
        """Setup the main UI layout"""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Header section
        header = self.create_header_section()
        main_layout.addWidget(header)
        
        # Create splitter for main content
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel - Knowledge Base Management
        left_panel = self.create_knowledge_panel()
        splitter.addWidget(left_panel)
        
        # Right panel - RAG Settings & Testing
        right_panel = self.create_settings_panel()
        splitter.addWidget(right_panel)
        
        # Set splitter proportions
        splitter.setSizes([400, 350])
        main_layout.addWidget(splitter)
        
        # Bottom controls
        controls_widget = self.create_controls_section()
        main_layout.addWidget(controls_widget)
    
    def create_header_section(self) -> QWidget:
        """Create header with title and status"""
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                            stop:0 #9C27B0, stop:1 #7B1FA2);
                border-radius: 10px;
                padding: 20px;
            }
            QLabel {
                color: white;
            }
        """)
        
        layout = QHBoxLayout(header)
        
        # Title and status
        title_layout = QVBoxLayout()
        
        title = QLabel("📚 RAG Knowledge System")
        title.setStyleSheet("font-size: 28px; font-weight: bold;")
        title_layout.addWidget(title)
        
        # Status indicator
        status_text = "🟢 Active" if self.rag_enabled else "🔴 Inactive"
        status_label = QLabel(status_text)
        status_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #FFD700;")
        title_layout.addWidget(status_label)
        
        layout.addLayout(title_layout)
        layout.addStretch()
        
        # Quick stats
        stats_layout = QVBoxLayout()
        stats_layout.addWidget(QLabel(f"📄 Documents: {len(self.current_documents)}"))
        stats_layout.addWidget(QLabel(f"🧠 Knowledge Base: {len(self.knowledge_base)} entries"))
        layout.addLayout(stats_layout)
        
        return header
    
    def create_knowledge_panel(self) -> QWidget:
        """Create left panel for knowledge base management"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Knowledge Base Management
        kb_group = QGroupBox("📚 Knowledge Base Management")
        kb_layout = QVBoxLayout(kb_group)
        
        # Add document section
        add_doc_layout = QHBoxLayout()
        add_doc_layout.addWidget(QLabel("Add Document:"))
        
        self.doc_path_edit = QLineEdit()
        self.doc_path_edit.setPlaceholderText("Select document file...")
        add_doc_layout.addWidget(self.doc_path_edit)
        
        browse_btn = QPushButton("📁 Browse")
        browse_btn.clicked.connect(self.browse_document)
        add_doc_layout.addWidget(browse_btn)
        
        kb_layout.addLayout(add_doc_layout)
        
        # Document list
        self.doc_list = QListWidget()
        self.doc_list.setMaximumHeight(200)
        kb_layout.addWidget(self.doc_list)
        
        # Document controls
        doc_controls = QHBoxLayout()
        
        add_btn = QPushButton("➕ Add")
        add_btn.clicked.connect(self.add_document)
        doc_controls.addWidget(add_btn)
        
        remove_btn = QPushButton("➖ Remove")
        remove_btn.clicked.connect(self.remove_document)
        doc_controls.addWidget(remove_btn)
        
        clear_btn = QPushButton("🗑️ Clear All")
        clear_btn.clicked.connect(self.clear_documents)
        doc_controls.addWidget(clear_btn)
        
        kb_layout.addLayout(doc_controls)
        
        layout.addWidget(kb_group)
        
        # Knowledge Base Entries
        entries_group = QGroupBox("🧠 Knowledge Entries")
        entries_layout = QVBoxLayout(entries_group)
        
        # Entries table
        self.entries_table = QTableWidget()
        self.entries_table.setColumnCount(4)
        self.entries_table.setHorizontalHeaderLabels([
            "ID", "Content", "Source", "Added"
        ])
        
        # Table styling
        header = self.entries_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        
        self.entries_table.setAlternatingRowColors(True)
        self.entries_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        entries_layout.addWidget(self.entries_table)
        
        # Entry controls
        entry_controls = QHBoxLayout()
        
        add_entry_btn = QPushButton("➕ Add Entry")
        add_entry_btn.clicked.connect(self.add_knowledge_entry)
        entry_controls.addWidget(add_entry_btn)
        
        edit_entry_btn = QPushButton("✏️ Edit")
        edit_entry_btn.clicked.connect(self.edit_knowledge_entry)
        entry_controls.addWidget(edit_entry_btn)
        
        delete_entry_btn = QPushButton("🗑️ Delete")
        delete_entry_btn.clicked.connect(self.delete_knowledge_entry)
        entry_controls.addWidget(delete_entry_btn)
        
        entries_layout.addLayout(entry_controls)
        
        layout.addWidget(entries_group)
        
        return panel
    
    def create_settings_panel(self) -> QWidget:
        """Create right panel for RAG settings and testing"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # RAG Settings
        settings_group = QGroupBox("⚙️ RAG Settings")
        settings_layout = QFormLayout(settings_group)
        
        # Enable RAG
        self.rag_enabled_cb = QCheckBox("Enable RAG Knowledge System")
        self.rag_enabled_cb.setChecked(self.rag_enabled)
        self.rag_enabled_cb.toggled.connect(self.toggle_rag)
        settings_layout.addRow("Status:", self.rag_enabled_cb)
        
        # Similarity threshold
        self.similarity_slider = QSlider(Qt.Orientation.Horizontal)
        self.similarity_slider.setRange(0, 100)
        self.similarity_slider.setValue(70)
        self.similarity_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.similarity_slider.setTickInterval(10)
        settings_layout.addRow("Similarity Threshold:", self.similarity_slider)
        
        # Max results
        self.max_results_spin = QSpinBox()
        self.max_results_spin.setRange(1, 10)
        self.max_results_spin.setValue(3)
        settings_layout.addRow("Max Results:", self.max_results_spin)
        
        # Context window
        self.context_window_spin = QSpinBox()
        self.context_window_spin.setRange(100, 2000)
        self.context_window_spin.setValue(500)
        self.context_window_spin.setSuffix(" tokens")
        settings_layout.addRow("Context Window:", self.context_window_spin)
        
        layout.addWidget(settings_group)
        
        # RAG Testing
        test_group = QGroupBox("🧪 RAG Testing")
        test_layout = QVBoxLayout(test_group)
        
        # Query input
        test_layout.addWidget(QLabel("Test Query:"))
        self.query_edit = QTextEdit()
        self.query_edit.setMaximumHeight(100)
        self.query_edit.setPlaceholderText("Enter your question here...")
        test_layout.addWidget(self.query_edit)
        
        # Test button
        test_btn = QPushButton("🔍 Test RAG")
        test_btn.clicked.connect(self.test_rag)
        test_layout.addWidget(test_btn)
        
        # Results display
        test_layout.addWidget(QLabel("Results:"))
        self.results_display = QTextEdit()
        self.results_display.setMaximumHeight(200)
        self.results_display.setReadOnly(True)
        test_layout.addWidget(self.results_display)
        
        layout.addWidget(test_group)
        
        return panel
    
    def create_controls_section(self) -> QWidget:
        """Create bottom controls section"""
        controls = QFrame()
        controls.setStyleSheet("""
            QFrame {
                background-color: #f5f5f5;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        
        layout = QHBoxLayout(controls)
        
        # Save settings button
        save_btn = QPushButton("💾 Save Settings")
        save_btn.clicked.connect(self.save_settings)
        layout.addWidget(save_btn)
        
        # Load settings button
        load_btn = QPushButton("📂 Load Settings")
        load_btn.clicked.connect(self.load_settings)
        layout.addWidget(load_btn)
        
        # Export knowledge base
        export_btn = QPushButton("📤 Export Knowledge Base")
        export_btn.clicked.connect(self.export_knowledge_base)
        layout.addWidget(export_btn)
        
        # Import knowledge base
        import_btn = QPushButton("📥 Import Knowledge Base")
        import_btn.clicked.connect(self.import_knowledge_base)
        layout.addWidget(import_btn)
        
        layout.addStretch()
        
        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(self.status_label)
        
        return controls
    
    def browse_document(self):
        """Browse for document files"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Document", "", 
            "Text Files (*.txt);;PDF Files (*.pdf);;All Files (*)"
        )
        if file_path:
            self.doc_path_edit.setText(file_path)
    
    def add_document(self):
        """Add document to knowledge base"""
        file_path = self.doc_path_edit.text()
        if not file_path:
            QMessageBox.warning(self, "Warning", "Please select a document first.")
            return
        
        try:
            # Add to document list
            item = QListWidgetItem(file_path)
            self.doc_list.addItem(item)
            self.current_documents.append(file_path)
            
            # Process document (placeholder)
            self.status_label.setText(f"Added document: {Path(file_path).name}")
            self.doc_path_edit.clear()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add document: {e}")
    
    def remove_document(self):
        """Remove selected document"""
        current_item = self.doc_list.currentItem()
        if current_item:
            file_path = current_item.text()
            self.doc_list.takeItem(self.doc_list.row(current_item))
            self.current_documents.remove(file_path)
            self.status_label.setText(f"Removed document: {Path(file_path).name}")
    
    def clear_documents(self):
        """Clear all documents"""
        reply = QMessageBox.question(
            self, "Confirm Clear", 
            "Are you sure you want to clear all documents?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.doc_list.clear()
            self.current_documents.clear()
            self.status_label.setText("Cleared all documents")
    
    def add_knowledge_entry(self):
        """Add manual knowledge entry"""
        # Placeholder for adding knowledge entry
        QMessageBox.information(self, "Info", "Add knowledge entry feature coming soon!")
    
    def edit_knowledge_entry(self):
        """Edit selected knowledge entry"""
        # Placeholder for editing knowledge entry
        QMessageBox.information(self, "Info", "Edit knowledge entry feature coming soon!")
    
    def delete_knowledge_entry(self):
        """Delete selected knowledge entry"""
        # Placeholder for deleting knowledge entry
        QMessageBox.information(self, "Info", "Delete knowledge entry feature coming soon!")
    
    def toggle_rag(self, enabled: bool):
        """Toggle RAG system on/off"""
        self.rag_enabled = enabled
        status = "🟢 Active" if enabled else "🔴 Inactive"
        self.status_label.setText(f"RAG System: {status}")
    
    def test_rag(self):
        """Test RAG system with query"""
        query = self.query_edit.toPlainText().strip()
        if not query:
            QMessageBox.warning(self, "Warning", "Please enter a test query.")
            return
        
        # Placeholder for RAG testing
        self.results_display.setPlainText(
            f"Query: {query}\n\n"
            f"RAG System Test Results:\n"
            f"• Similarity Threshold: {self.similarity_slider.value()}%\n"
            f"• Max Results: {self.max_results_spin.value()}\n"
            f"• Context Window: {self.context_window_spin.value()} tokens\n\n"
            f"Status: {'Active' if self.rag_enabled else 'Inactive'}\n"
            f"Knowledge Base Entries: {len(self.knowledge_base)}\n"
            f"Documents Loaded: {len(self.current_documents)}"
        )
        
        self.status_label.setText("RAG test completed")
    
    def save_settings(self):
        """Save RAG settings"""
        settings = {
            "rag_enabled": self.rag_enabled_cb.isChecked(),
            "similarity_threshold": self.similarity_slider.value(),
            "max_results": self.max_results_spin.value(),
            "context_window": self.context_window_spin.value(),
            "documents": self.current_documents,
            "knowledge_base": self.knowledge_base
        }
        
        try:
            settings_file = Path("config/rag_settings.json")
            settings_file.parent.mkdir(exist_ok=True)
            
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2)
            
            self.status_label.setText("Settings saved successfully")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save settings: {e}")
    
    def load_settings(self):
        """Load RAG settings"""
        try:
            settings_file = Path("config/rag_settings.json")
            if settings_file.exists():
                with open(settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                
                # Apply settings
                self.rag_enabled_cb.setChecked(settings.get("rag_enabled", False))
                self.similarity_slider.setValue(settings.get("similarity_threshold", 70))
                self.max_results_spin.setValue(settings.get("max_results", 3))
                self.context_window_spin.setValue(settings.get("context_window", 500))
                
                # Load documents
                self.current_documents = settings.get("documents", [])
                self.doc_list.clear()
                for doc in self.current_documents:
                    self.doc_list.addItem(doc)
                
                # Load knowledge base
                self.knowledge_base = settings.get("knowledge_base", {})
                
                self.status_label.setText("Settings loaded successfully")
            else:
                self.status_label.setText("No settings file found")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load settings: {e}")
    
    def export_knowledge_base(self):
        """Export knowledge base to file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Knowledge Base", "knowledge_base.json", 
            "JSON Files (*.json)"
        )
        
        if file_path:
            try:
                export_data = {
                    "knowledge_base": self.knowledge_base,
                    "documents": self.current_documents,
                    "export_date": datetime.now().isoformat()
                }
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2)
                
                self.status_label.setText(f"Knowledge base exported to {Path(file_path).name}")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export: {e}")
    
    def import_knowledge_base(self):
        """Import knowledge base from file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Knowledge Base", "", 
            "JSON Files (*.json)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    import_data = json.load(f)
                
                self.knowledge_base = import_data.get("knowledge_base", {})
                self.current_documents = import_data.get("documents", [])
                
                # Update UI
                self.doc_list.clear()
                for doc in self.current_documents:
                    self.doc_list.addItem(doc)
                
                self.status_label.setText(f"Knowledge base imported from {Path(file_path).name}")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to import: {e}") 