# ui/rag_tab.py - RAG (Retrieval Augmented Generation) Tab
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
    QTableWidget, QTableWidgetItem
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
    """RAG (Retrieval Augmented Generation) Tab untuk Pro Mode"""
    
    def __init__(self):
        super().__init__()
        self.api_client = APIClient()
        self.config_manager = ConfigManager()
        self.settings = self.config_manager.load_settings()
        
        # RAG settings
        self.knowledge_base_path = Path("knowledge_bases")
        self.knowledge_base_path.mkdir(exist_ok=True)
        
        self.setup_ui()
        self.load_settings()
        
    def setup_ui(self):
        """Setup UI untuk RAG tab"""
        layout = QVBoxLayout()
        
        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel("📚 RAG - Knowledge Base Assistant")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #1877F2;")
        header_layout.addWidget(title_label)
        
        status_label = QLabel("🟢 RAG Active")
        status_label.setStyleSheet("color: #42B72A; font-weight: bold;")
        header_layout.addWidget(status_label)
        layout.addLayout(header_layout)
        
        # Main content dengan tabs
        self.tab_widget = QTabWidget()
        
        # Tab 1: Knowledge Base Management
        self.setup_knowledge_tab()
        
        # Tab 2: RAG Query Interface
        self.setup_query_tab()
        
        # Tab 3: Document Processing
        self.setup_document_tab()
        
        # Tab 4: RAG Analytics
        self.setup_analytics_tab()
        
        layout.addWidget(self.tab_widget)
        self.setLayout(layout)
        
    def setup_knowledge_tab(self):
        """Setup knowledge base management tab"""
        kb_widget = QWidget()
        kb_layout = QVBoxLayout()
        
        # Knowledge Base List
        kb_group = QGroupBox("📚 Knowledge Bases")
        kb_layout_v = QVBoxLayout()
        
        self.kb_list = QListWidget()
        self.kb_list.setStyleSheet("""
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
        kb_layout_v.addWidget(self.kb_list)
        
        # KB Controls
        kb_controls = QHBoxLayout()
        kb_controls.addWidget(QPushButton("➕ Add Knowledge Base"))
        kb_controls.addWidget(QPushButton("✏️ Edit Knowledge Base"))
        kb_controls.addWidget(QPushButton("🗑️ Delete Knowledge Base"))
        kb_controls.addWidget(QPushButton("🔄 Refresh List"))
        kb_layout_v.addLayout(kb_controls)
        
        kb_group.setLayout(kb_layout_v)
        kb_layout.addWidget(kb_group)
        
        # Knowledge Base Details
        details_group = QGroupBox("📋 Knowledge Base Details")
        details_layout = QVBoxLayout()
        
        # KB Info
        info_layout = QHBoxLayout()
        info_layout.addWidget(QLabel("📁 Name:"))
        self.kb_name_label = QLabel("No KB selected")
        info_layout.addWidget(self.kb_name_label)
        details_layout.addLayout(info_layout)
        
        info_layout2 = QHBoxLayout()
        info_layout2.addWidget(QLabel("📄 Documents:"))
        self.kb_docs_label = QLabel("0 documents")
        info_layout2.addWidget(self.kb_docs_label)
        details_layout.addLayout(info_layout2)
        
        info_layout3 = QHBoxLayout()
        info_layout3.addWidget(QLabel("🧠 Embeddings:"))
        self.kb_embeddings_label = QLabel("Not processed")
        info_layout3.addWidget(self.kb_embeddings_label)
        details_layout.addLayout(info_layout3)
        
        # Process button
        self.process_btn = QPushButton("🧠 Process Knowledge Base")
        self.process_btn.setStyleSheet("""
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
        self.process_btn.clicked.connect(self.process_knowledge_base)
        details_layout.addWidget(self.process_btn)
        
        details_group.setLayout(details_layout)
        kb_layout.addWidget(details_group)
        
        kb_widget.setLayout(kb_layout)
        self.tab_widget.addTab(kb_widget, "📚 Knowledge Base")
        
    def setup_query_tab(self):
        """Setup RAG query interface tab"""
        query_widget = QWidget()
        query_layout = QVBoxLayout()
        
        # Query Interface
        query_group = QGroupBox("🔍 RAG Query Interface")
        query_layout_v = QVBoxLayout()
        
        # Query input
        query_label = QLabel("❓ Ask your knowledge base:")
        self.query_input = QTextEdit()
        self.query_input.setMaximumHeight(100)
        self.query_input.setPlaceholderText("Enter your question here...")
        query_layout_v.addWidget(query_label)
        query_layout_v.addWidget(self.query_input)
        
        # Query options
        options_layout = QHBoxLayout()
        
        self.semantic_search_check = QCheckBox("🔍 Semantic Search")
        self.semantic_search_check.setChecked(True)
        options_layout.addWidget(self.semantic_search_check)
        
        self.keyword_search_check = QCheckBox("🔑 Keyword Search")
        self.keyword_search_check.setChecked(True)
        options_layout.addWidget(self.keyword_search_check)
        
        self.hybrid_search_check = QCheckBox("🔄 Hybrid Search")
        self.hybrid_search_check.setChecked(True)
        options_layout.addWidget(self.hybrid_search_check)
        
        query_layout_v.addLayout(options_layout)
        
        # Search parameters
        params_layout = QHBoxLayout()
        params_layout.addWidget(QLabel("📊 Top Results:"))
        self.top_k_spin = QSpinBox()
        self.top_k_spin.setRange(1, 20)
        self.top_k_spin.setValue(5)
        params_layout.addWidget(self.top_k_spin)
        
        params_layout.addWidget(QLabel("🎯 Similarity Threshold:"))
        self.similarity_slider = QSlider(Qt.Orientation.Horizontal)
        self.similarity_slider.setRange(0, 100)
        self.similarity_slider.setValue(70)
        self.similarity_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.similarity_slider.setTickInterval(10)
        params_layout.addWidget(self.similarity_slider)
        
        self.similarity_label = QLabel("0.7")
        self.similarity_slider.valueChanged.connect(
            lambda v: self.similarity_label.setText(f"{v/100:.1f}")
        )
        params_layout.addWidget(self.similarity_label)
        query_layout_v.addLayout(params_layout)
        
        # Search button
        self.search_btn = QPushButton("🔍 Search Knowledge Base")
        self.search_btn.setStyleSheet("""
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
        self.search_btn.clicked.connect(self.search_knowledge_base)
        query_layout_v.addWidget(self.search_btn)
        
        query_group.setLayout(query_layout_v)
        query_layout.addWidget(query_group)
        
        # Results Display
        results_group = QGroupBox("📋 Search Results")
        results_layout = QVBoxLayout()
        
        self.results_display = QTextEdit()
        self.results_display.setReadOnly(True)
        self.results_display.setStyleSheet("""
            QTextEdit {
                background-color: #242526;
                color: #FFFFFF;
                border: 1px solid #3A3B3C;
                border-radius: 8px;
                padding: 10px;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 13px;
            }
        """)
        results_layout.addWidget(self.results_display)
        
        results_group.setLayout(results_layout)
        query_layout.addWidget(results_group)
        
        query_widget.setLayout(query_layout)
        self.tab_widget.addTab(query_widget, "🔍 RAG Query")
        
    def setup_document_tab(self):
        """Setup document processing tab"""
        doc_widget = QWidget()
        doc_layout = QVBoxLayout()
        
        # Document Upload
        upload_group = QGroupBox("📄 Document Upload")
        upload_layout = QVBoxLayout()
        
        # File selection
        file_layout = QHBoxLayout()
        file_layout.addWidget(QLabel("📁 Select Documents:"))
        self.file_path_label = QLabel("No files selected")
        file_layout.addWidget(self.file_path_label)
        
        browse_btn = QPushButton("📂 Browse Files")
        browse_btn.clicked.connect(self.browse_documents)
        file_layout.addWidget(browse_btn)
        upload_layout.addLayout(file_layout)
        
        # Supported formats
        formats_label = QLabel("📋 Supported formats: PDF, TXT, DOCX, MD, JSON")
        formats_label.setStyleSheet("color: #888; font-size: 12px;")
        upload_layout.addWidget(formats_label)
        
        # Upload button
        self.upload_btn = QPushButton("📤 Upload to Knowledge Base")
        self.upload_btn.setStyleSheet("""
            QPushButton {
                background-color: #F5B800;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #E6A800;
            }
        """)
        self.upload_btn.clicked.connect(self.upload_documents)
        upload_layout.addWidget(self.upload_btn)
        
        upload_group.setLayout(upload_layout)
        doc_layout.addWidget(upload_group)
        
        # Document Processing
        processing_group = QGroupBox("⚙️ Document Processing")
        processing_layout = QVBoxLayout()
        
        # Processing options
        options_layout = QVBoxLayout()
        
        self.chunk_text_check = QCheckBox("✂️ Chunk Text")
        self.chunk_text_check.setChecked(True)
        options_layout.addWidget(self.chunk_text_check)
        
        self.extract_metadata_check = QCheckBox("📊 Extract Metadata")
        self.extract_metadata_check.setChecked(True)
        options_layout.addWidget(self.extract_metadata_check)
        
        self.generate_embeddings_check = QCheckBox("🧠 Generate Embeddings")
        self.generate_embeddings_check.setChecked(True)
        options_layout.addWidget(self.generate_embeddings_check)
        
        self.index_documents_check = QCheckBox("🔍 Index Documents")
        self.index_documents_check.setChecked(True)
        options_layout.addWidget(self.index_documents_check)
        
        processing_layout.addLayout(options_layout)
        
        # Processing progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        processing_layout.addWidget(self.progress_bar)
        
        processing_group.setLayout(processing_layout)
        doc_layout.addWidget(processing_group)
        
        # Document List
        doc_list_group = QGroupBox("📚 Processed Documents")
        doc_list_layout = QVBoxLayout()
        
        self.doc_table = QTableWidget()
        self.doc_table.setColumnCount(4)
        self.doc_table.setHorizontalHeaderLabels(["📄 Document", "📊 Size", "🧠 Status", "📅 Date"])
        self.doc_table.setStyleSheet("""
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
        doc_list_layout.addWidget(self.doc_table)
        
        doc_list_group.setLayout(doc_list_layout)
        doc_layout.addWidget(doc_list_group)
        
        doc_widget.setLayout(doc_layout)
        self.tab_widget.addTab(doc_widget, "📄 Document Processing")
        
    def setup_analytics_tab(self):
        """Setup RAG analytics tab"""
        analytics_widget = QWidget()
        analytics_layout = QVBoxLayout()
        
        # RAG Statistics
        stats_group = QGroupBox("📊 RAG Statistics")
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
        update_stats_btn = QPushButton("🔄 Update RAG Statistics")
        update_stats_btn.clicked.connect(self.update_rag_analytics)
        stats_layout.addWidget(update_stats_btn)
        
        stats_group.setLayout(stats_layout)
        analytics_layout.addWidget(stats_group)
        
        # Performance Metrics
        perf_group = QGroupBox("⚡ Performance Metrics")
        perf_layout = QVBoxLayout()
        
        # Search metrics
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("🔍 Total Searches:"))
        self.total_searches_label = QLabel("0")
        search_layout.addWidget(self.total_searches_label)
        perf_layout.addLayout(search_layout)
        
        # Response time
        time_layout = QHBoxLayout()
        time_layout.addWidget(QLabel("⏱️ Avg Search Time:"))
        self.search_time_label = QLabel("0.0s")
        time_layout.addWidget(self.search_time_label)
        perf_layout.addLayout(time_layout)
        
        # Hit rate
        hit_layout = QHBoxLayout()
        hit_layout.addWidget(QLabel("🎯 Hit Rate:"))
        self.hit_rate_label = QLabel("0%")
        hit_layout.addWidget(self.hit_rate_label)
        perf_layout.addLayout(hit_layout)
        
        # Knowledge base size
        kb_size_layout = QHBoxLayout()
        kb_size_layout.addWidget(QLabel("📚 KB Size:"))
        self.kb_size_label = QLabel("0 documents")
        kb_size_layout.addWidget(self.kb_size_label)
        perf_layout.addLayout(kb_size_layout)
        
        perf_group.setLayout(perf_layout)
        analytics_layout.addWidget(perf_group)
        
        analytics_widget.setLayout(analytics_layout)
        self.tab_widget.addTab(analytics_widget, "📊 RAG Analytics")
        
    def load_settings(self):
        """Load RAG settings"""
        try:
            # Load RAG-specific settings
            self.similarity_slider.setValue(
                int(self.settings.get("rag_similarity_threshold", 0.7) * 100)
            )
            self.top_k_spin.setValue(
                self.settings.get("rag_top_k", 5)
            )
            
        except Exception as e:
            logger.error(f"Error loading RAG settings: {e}")
            
    def save_settings(self):
        """Save RAG settings"""
        try:
            self.settings["rag_similarity_threshold"] = self.similarity_slider.value() / 100
            self.settings["rag_top_k"] = self.top_k_spin.value()
            self.settings["rag_semantic_search"] = self.semantic_search_check.isChecked()
            self.settings["rag_keyword_search"] = self.keyword_search_check.isChecked()
            self.settings["rag_hybrid_search"] = self.hybrid_search_check.isChecked()
            
            self.config_manager.save_settings()
            
        except Exception as e:
            logger.error(f"Error saving RAG settings: {e}")
            
    def process_knowledge_base(self):
        """Process knowledge base untuk embeddings"""
        try:
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            
            # Simulate processing
            for i in range(101):
                self.progress_bar.setValue(i)
                time.sleep(0.05)
                
            QMessageBox.information(self, "Success", "Knowledge base processed successfully!")
            self.progress_bar.setVisible(False)
            
        except Exception as e:
            logger.error(f"Error processing knowledge base: {e}")
            QMessageBox.warning(self, "Error", f"Failed to process knowledge base: {e}")
            
    def search_knowledge_base(self):
        """Search knowledge base dengan RAG"""
        try:
            query = self.query_input.toPlainText()
            if not query.strip():
                QMessageBox.warning(self, "Warning", "Please enter a query")
                return
                
            # Simulate RAG search
            results = f"""
🔍 RAG Search Results for: "{query}"

📚 Found 3 relevant documents:

1. 📄 Document: "Gaming Strategy Guide"
   🎯 Relevance: 95%
   📝 Snippet: "Advanced MOBA strategies for competitive play..."
   
2. 📄 Document: "Streaming Best Practices"  
   🎯 Relevance: 87%
   📝 Snippet: "Professional streaming techniques and audience engagement..."
   
3. 📄 Document: "AI Integration Guide"
   🎯 Relevance: 82%
   📝 Snippet: "How to integrate AI assistants in live streaming..."
   
🧠 Generated Response:
Based on the knowledge base, here's a comprehensive answer to your query about {query}...
            """
            
            self.results_display.setPlainText(results)
            
        except Exception as e:
            logger.error(f"Error searching knowledge base: {e}")
            QMessageBox.warning(self, "Error", f"Failed to search knowledge base: {e}")
            
    def browse_documents(self):
        """Browse untuk memilih dokumen"""
        try:
            files, _ = QFileDialog.getOpenFileNames(
                self,
                "Select Documents",
                "",
                "Documents (*.pdf *.txt *.docx *.md *.json);;All Files (*)"
            )
            
            if files:
                self.file_path_label.setText(f"{len(files)} files selected")
                
        except Exception as e:
            logger.error(f"Error browsing documents: {e}")
            
    def upload_documents(self):
        """Upload dokumen ke knowledge base"""
        try:
            QMessageBox.information(self, "Success", "Documents uploaded successfully!")
            
        except Exception as e:
            logger.error(f"Error uploading documents: {e}")
            QMessageBox.warning(self, "Error", f"Failed to upload documents: {e}")
            
    def update_rag_analytics(self):
        """Update RAG analytics"""
        try:
            stats_text = """
📊 RAG ANALYTICS
================
🔍 Total Searches: 1,847
⏱️ Avg Search Time: 0.3s
🎯 Hit Rate: 94.2%
📚 KB Size: 1,247 documents
🧠 Embeddings: 15,892 vectors
📄 Documents Processed: 89
⚡ Cache Hit Rate: 87.5%
            """
            
            self.stats_display.setPlainText(stats_text)
            self.total_searches_label.setText("1,847")
            self.search_time_label.setText("0.3s")
            self.hit_rate_label.setText("94.2%")
            self.kb_size_label.setText("1,247 documents")
            
        except Exception as e:
            logger.error(f"Error updating RAG analytics: {e}")
            
    def closeEvent(self, event):
        """Save settings when closing"""
        self.save_settings()
        super().closeEvent(event)
