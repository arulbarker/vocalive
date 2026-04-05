# ui/analytics_tab.py
"""
Live Analytics Tab - Real-time streaming performance analytics
Support: YouTube & TikTok
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QGroupBox, QTextEdit,
    QMessageBox, QFileDialog, QHeaderView, QTabWidget,
    QScrollArea, QFrame, QProgressBar
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QColor
from datetime import datetime
from pathlib import Path

try:
    from modules_client.analytics_manager import get_analytics_manager
    ANALYTICS_AVAILABLE = True
except ImportError:
    ANALYTICS_AVAILABLE = False
    print("[Analytics Tab] analytics_manager not available")

# Try to import pyqtgraph for charts
try:
    import pyqtgraph as pg
    from pyqtgraph import PlotWidget
    CHARTS_AVAILABLE = True
    # Configure pyqtgraph for dark theme
    pg.setConfigOption('background', '#18191A')
    pg.setConfigOption('foreground', '#FFFFFF')
except ImportError:
    CHARTS_AVAILABLE = False
    print("[Analytics Tab] pyqtgraph not available - charts disabled")


class AnalyticsTab(QWidget):
    """Tab untuk menampilkan live analytics dengan real-time updates"""

    # Signal untuk update dari listener
    analytics_updated = pyqtSignal()

    def __init__(self):
        super().__init__()

        # Get analytics manager instance
        if ANALYTICS_AVAILABLE:
            self.analytics = get_analytics_manager()
        else:
            self.analytics = None

        # Update timer untuk real-time refresh
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.refresh_analytics)
        self.update_timer.setInterval(2000)  # Update setiap 2 detik (performance friendly)

        self.init_ui()

    def init_ui(self):
        """Initialize UI components"""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # Header
        header = self._create_header()
        main_layout.addWidget(header)

        # Check if analytics available
        if not ANALYTICS_AVAILABLE:
            error_label = QLabel("⚠️ Analytics Manager tidak tersedia")
            error_label.setStyleSheet("color: #FA383E; font-size: 14px; padding: 20px;")
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            main_layout.addWidget(error_label)
            self.setLayout(main_layout)
            return

        # Tab untuk different views
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #3A3B3C;
                background-color: #18191A;
            }
            QTabBar::tab {
                background-color: #242526;
                color: #B0B3B8;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #1877F2;
                color: white;
            }
        """)

        # Tab 1: Real-time Overview
        self.overview_tab = self._create_overview_tab()
        self.tabs.addTab(self.overview_tab, "📊 Live Overview")

        # Tab 2: Top Viewers
        self.viewers_tab = self._create_viewers_tab()
        self.tabs.addTab(self.viewers_tab, "👥 Top Viewers")

        # Tab 3: Keywords
        self.keywords_tab = self._create_keywords_tab()
        self.tabs.addTab(self.keywords_tab, "🔥 Popular Keywords")

        # Tab 4: History
        self.history_tab = self._create_history_tab()
        self.tabs.addTab(self.history_tab, "📜 Session History")

        # Tab 5: Charts (if pyqtgraph available)
        if CHARTS_AVAILABLE:
            self.charts_tab = self._create_charts_tab()
            self.tabs.addTab(self.charts_tab, "📈 Charts")
        
        # Initialize chart data lists for real-time updates
        self.chart_time_data = []
        self.chart_viewers_data = []
        self.chart_comments_data = []

        main_layout.addWidget(self.tabs)

        self.setLayout(main_layout)

        # Start auto-refresh
        self.update_timer.start()

    def _create_header(self):
        """Create header with title and action buttons"""
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background-color: #242526;
                border-radius: 8px;
                padding: 10px;
            }
        """)

        layout = QHBoxLayout()

        # Title
        title = QLabel("📈 Live Analytics Dashboard")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #1877F2;")
        layout.addWidget(title)

        layout.addStretch()

        # Session info
        self.session_label = QLabel("No active session")
        self.session_label.setStyleSheet("color: #B0B3B8; font-size: 12px;")
        layout.addWidget(self.session_label)

        # Export CSV button
        export_btn = QPushButton("📥 Export CSV")
        export_btn.clicked.connect(self.export_current_session)
        export_btn.setStyleSheet("""
            QPushButton {
                background-color: #42B72A;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #36A420;
            }
        """)
        layout.addWidget(export_btn)

        # Export PDF button
        pdf_btn = QPushButton("📄 Export PDF")
        pdf_btn.clicked.connect(self.export_to_pdf)
        pdf_btn.setStyleSheet("""
            QPushButton {
                background-color: #9B59B6;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #8E44AD;
            }
        """)
        layout.addWidget(pdf_btn)

        # Clear data button
        clear_btn = QPushButton("🗑️ Clear All Data")
        clear_btn.clicked.connect(self.clear_all_data)
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #FA383E;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #E02D32;
            }
        """)
        layout.addWidget(clear_btn)

        header.setLayout(layout)
        return header

    def _create_overview_tab(self):
        """Create overview statistics tab"""
        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #18191A;
            }
            QScrollBar:vertical {
                background-color: #242526;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #3A3B3C;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #4E4F50;
            }
        """)

        widget = QWidget()
        layout = QVBoxLayout()

        # Stats cards
        stats_layout = QHBoxLayout()

        # Card 1: Comments
        self.comments_card = self._create_stat_card("💬 Comments", "0", "0 replied")
        stats_layout.addWidget(self.comments_card)

        # Card 2: Viewers
        self.viewers_card = self._create_stat_card("👥 Viewers", "0", "Peak: 0")
        stats_layout.addWidget(self.viewers_card)

        # Card 3: Engagement
        self.engagement_card = self._create_stat_card("⚡ Engagement", "0%", "Reply rate")
        stats_layout.addWidget(self.engagement_card)

        # Card 4: Duration
        self.duration_card = self._create_stat_card("⏱️ Duration", "0 min", "Active")
        stats_layout.addWidget(self.duration_card)

        layout.addLayout(stats_layout)

        # Additional stats
        stats_group = QGroupBox("📊 Detailed Statistics")
        stats_group.setStyleSheet("""
            QGroupBox {
                color: #FFFFFF;
                border: 1px solid #3A3B3C;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)

        stats_layout_inner = QVBoxLayout()

        # Stats labels
        self.stats_labels = {}
        stat_items = [
            ("total_gifts", "💝 Total Gifts/Donations", "Rp 0"),
            ("total_shares", "📤 Total Shares", "0"),
            ("total_likes", "❤️ Total Likes", "0"),
            ("total_follows", "➕ New Follows", "0"),
        ]

        for key, label, default in stat_items:
            row = QHBoxLayout()
            label_widget = QLabel(label)
            label_widget.setStyleSheet("color: #B0B3B8; font-weight: normal;")

            value_widget = QLabel(default)
            value_widget.setStyleSheet("color: #FFFFFF; font-weight: bold; font-size: 14px;")
            value_widget.setAlignment(Qt.AlignmentFlag.AlignRight)

            row.addWidget(label_widget)
            row.addWidget(value_widget)

            stats_layout_inner.addLayout(row)
            self.stats_labels[key] = value_widget

        stats_group.setLayout(stats_layout_inner)
        layout.addWidget(stats_group)

        # Timeline
        timeline_group = QGroupBox("📅 Session Timeline")
        timeline_group.setStyleSheet(stats_group.styleSheet())
        timeline_layout = QVBoxLayout()

        self.timeline_text = QTextEdit()
        self.timeline_text.setReadOnly(True)
        self.timeline_text.setMaximumHeight(150)
        self.timeline_text.setStyleSheet("""
            QTextEdit {
                background-color: #242526;
                color: #B0B3B8;
                border: 1px solid #3A3B3C;
                border-radius: 4px;
                padding: 8px;
                font-family: 'Consolas', monospace;
                font-size: 11px;
            }
        """)

        timeline_layout.addWidget(self.timeline_text)
        timeline_group.setLayout(timeline_layout)
        layout.addWidget(timeline_group)

        widget.setLayout(layout)

        # Set widget to scroll area
        scroll_area.setWidget(widget)
        return scroll_area

    def _create_stat_card(self, title, value, subtitle):
        """Create a statistics card"""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #242526;
                border-radius: 8px;
                border: 1px solid #3A3B3C;
                padding: 15px;
            }
        """)

        layout = QVBoxLayout()

        title_label = QLabel(title)
        title_label.setStyleSheet("color: #B0B3B8; font-size: 12px;")
        layout.addWidget(title_label)

        value_label = QLabel(value)
        value_label.setStyleSheet("color: #FFFFFF; font-size: 24px; font-weight: bold;")
        value_label.setObjectName("value")
        layout.addWidget(value_label)

        subtitle_label = QLabel(subtitle)
        subtitle_label.setStyleSheet("color: #65676B; font-size: 11px;")
        subtitle_label.setObjectName("subtitle")
        layout.addWidget(subtitle_label)

        card.setLayout(layout)
        return card

    def _create_viewers_tab(self):
        """Create top viewers table"""
        widget = QWidget()
        layout = QVBoxLayout()

        # Description
        desc = QLabel("🏆 Viewers ranked by engagement")
        desc.setStyleSheet("color: #B0B3B8; margin-bottom: 10px;")
        layout.addWidget(desc)

        # Table
        self.viewers_table = QTableWidget()
        self.viewers_table.setColumnCount(7)
        self.viewers_table.setHorizontalHeaderLabels([
            "Rank", "Username", "Comments", "Replied", "Gifts", "Shares", "Likes"
        ])

        # Table styling
        self.viewers_table.setStyleSheet("""
            QTableWidget {
                background-color: #242526;
                color: #FFFFFF;
                border: 1px solid #3A3B3C;
                border-radius: 4px;
                gridline-color: #3A3B3C;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QHeaderView::section {
                background-color: #1877F2;
                color: white;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
        """)

        self.viewers_table.horizontalHeader().setStretchLastSection(True)
        self.viewers_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.viewers_table.verticalHeader().setVisible(False)

        layout.addWidget(self.viewers_table)

        widget.setLayout(layout)
        return widget

    def _create_keywords_tab(self):
        """Create keywords analysis tab"""
        widget = QWidget()
        layout = QVBoxLayout()

        # Description
        desc = QLabel("🔥 Most mentioned keywords and topics")
        desc.setStyleSheet("color: #B0B3B8; margin-bottom: 10px;")
        layout.addWidget(desc)

        # Table
        self.keywords_table = QTableWidget()
        self.keywords_table.setColumnCount(3)
        self.keywords_table.setHorizontalHeaderLabels([
            "Rank", "Keyword", "Mentions"
        ])

        self.keywords_table.setStyleSheet(self.viewers_table.styleSheet())
        self.keywords_table.horizontalHeader().setStretchLastSection(True)
        self.keywords_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.keywords_table.verticalHeader().setVisible(False)

        layout.addWidget(self.keywords_table)

        # Action suggestions
        suggestions_group = QGroupBox("💡 Suggested Actions")
        suggestions_group.setStyleSheet("""
            QGroupBox {
                color: #FFFFFF;
                border: 1px solid #3A3B3C;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
            }
        """)

        suggestions_layout = QVBoxLayout()
        self.suggestions_text = QTextEdit()
        self.suggestions_text.setReadOnly(True)
        self.suggestions_text.setMaximumHeight(100)
        self.suggestions_text.setStyleSheet("""
            QTextEdit {
                background-color: #242526;
                color: #B0B3B8;
                border: 1px solid #3A3B3C;
                border-radius: 4px;
                padding: 8px;
            }
        """)
        suggestions_layout.addWidget(self.suggestions_text)
        suggestions_group.setLayout(suggestions_layout)

        layout.addWidget(suggestions_group)

        widget.setLayout(layout)
        return widget

    def _create_history_tab(self):
        """Create session history tab"""
        widget = QWidget()
        layout = QVBoxLayout()

        # Description
        desc = QLabel("📜 Past live session analytics")
        desc.setStyleSheet("color: #B0B3B8; margin-bottom: 10px;")
        layout.addWidget(desc)

        # Table
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(6)
        self.history_table.setHorizontalHeaderLabels([
            "Session ID", "Platform", "Duration", "Comments", "Viewers", "Gifts"
        ])

        self.history_table.setStyleSheet(self.viewers_table.styleSheet())
        self.history_table.horizontalHeader().setStretchLastSection(True)
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.history_table.verticalHeader().setVisible(False)

        layout.addWidget(self.history_table)

        # Buttons
        btn_layout = QHBoxLayout()

        refresh_btn = QPushButton("🔄 Refresh History")
        refresh_btn.clicked.connect(self.refresh_history)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #1877F2;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #166FE5;
            }
        """)
        btn_layout.addWidget(refresh_btn)

        btn_layout.addStretch()

        layout.addLayout(btn_layout)

        widget.setLayout(layout)
        return widget

    def _create_charts_tab(self):
        """Create charts tab with real-time line graphs"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Description
        desc = QLabel("📈 Real-time charts showing session performance over time")
        desc.setStyleSheet("color: #B0B3B8; margin-bottom: 10px;")
        layout.addWidget(desc)
        
        # Chart 1: Viewers over time
        viewers_group = QGroupBox("👥 Viewers Over Time")
        viewers_group.setStyleSheet("""
            QGroupBox {
                color: #FFFFFF;
                border: 1px solid #3A3B3C;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
            }
        """)
        viewers_layout = QVBoxLayout()
        
        self.viewers_chart = PlotWidget()
        self.viewers_chart.setBackground('#242526')
        self.viewers_chart.setLabel('left', 'Viewers', color='#1877F2')
        self.viewers_chart.setLabel('bottom', 'Time (minutes)', color='#B0B3B8')
        self.viewers_chart.showGrid(x=True, y=True, alpha=0.3)
        self.viewers_chart.setMinimumHeight(150)
        self.viewers_plot = self.viewers_chart.plot([], [], pen=pg.mkPen('#1877F2', width=2), symbol='o', symbolSize=5, symbolBrush='#1877F2')
        
        viewers_layout.addWidget(self.viewers_chart)
        viewers_group.setLayout(viewers_layout)
        layout.addWidget(viewers_group)
        
        # Chart 2: Comments over time
        comments_group = QGroupBox("💬 Comments Over Time")
        comments_group.setStyleSheet(viewers_group.styleSheet())
        comments_layout = QVBoxLayout()
        
        self.comments_chart = PlotWidget()
        self.comments_chart.setBackground('#242526')
        self.comments_chart.setLabel('left', 'Comments', color='#42B72A')
        self.comments_chart.setLabel('bottom', 'Time (minutes)', color='#B0B3B8')
        self.comments_chart.showGrid(x=True, y=True, alpha=0.3)
        self.comments_chart.setMinimumHeight(150)
        self.comments_plot = self.comments_chart.plot([], [], pen=pg.mkPen('#42B72A', width=2), symbol='o', symbolSize=5, symbolBrush='#42B72A')
        
        comments_layout.addWidget(self.comments_chart)
        comments_group.setLayout(comments_layout)
        layout.addWidget(comments_group)
        
        # Clear charts button
        btn_layout = QHBoxLayout()
        
        clear_btn = QPushButton("🗑️ Clear Charts")
        clear_btn.clicked.connect(self._clear_charts)
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #FA383E;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #E02D32;
            }
        """)
        btn_layout.addWidget(clear_btn)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
        
        widget.setLayout(layout)
        return widget
    
    def _clear_charts(self):
        """Clear chart data"""
        self.chart_time_data = []
        self.chart_viewers_data = []
        self.chart_comments_data = []
        if CHARTS_AVAILABLE and hasattr(self, 'viewers_plot'):
            self.viewers_plot.setData([], [])
            self.comments_plot.setData([], [])
    
    def _update_charts(self, stats):
        """Update chart data with current stats"""
        if not CHARTS_AVAILABLE or not hasattr(self, 'viewers_plot'):
            return
        
        # Get current time in minutes since session start
        duration = self.analytics.get_session_duration()
        
        # Add new data point
        self.chart_time_data.append(duration)
        self.chart_viewers_data.append(stats.get("unique_viewers", 0))
        self.chart_comments_data.append(stats.get("total_comments", 0))
        
        # Keep only last 60 data points (for performance)
        if len(self.chart_time_data) > 60:
            self.chart_time_data = self.chart_time_data[-60:]
            self.chart_viewers_data = self.chart_viewers_data[-60:]
            self.chart_comments_data = self.chart_comments_data[-60:]
        
        # Update plots
        self.viewers_plot.setData(self.chart_time_data, self.chart_viewers_data)
        self.comments_plot.setData(self.chart_time_data, self.chart_comments_data)

    def refresh_analytics(self):
        """Refresh all analytics data (called by timer)"""
        if not ANALYTICS_AVAILABLE or not self.analytics:
            return

        # Get current stats
        stats = self.analytics.get_current_stats()

        # Update session label
        if stats.get("is_active"):
            platform = stats.get("platform", "").upper()
            session_id = stats.get("session_id", "")
            self.session_label.setText(f"🔴 LIVE - {platform} | {session_id}")
            self.session_label.setStyleSheet("color: #42B72A; font-size: 12px; font-weight: bold;")
        else:
            self.session_label.setText("⚫ No active session")
            self.session_label.setStyleSheet("color: #B0B3B8; font-size: 12px;")

        # Update overview cards
        self._update_overview_stats(stats)

        # Update viewers table
        self._update_viewers_table()

        # Update keywords table
        self._update_keywords_table()
        
        # Update charts (if available)
        self._update_charts(stats)

    def _update_overview_stats(self, stats):
        """Update overview statistics"""
        # Comments card
        total_comments = stats.get("total_comments", 0)
        replied_comments = stats.get("total_comments_replied", 0)
        self.comments_card.findChild(QLabel, "value").setText(str(total_comments))
        self.comments_card.findChild(QLabel, "subtitle").setText(f"{replied_comments} replied")

        # Viewers card
        unique_viewers = stats.get("unique_viewers", 0)
        peak_viewers = stats.get("peak_viewers", 0)
        self.viewers_card.findChild(QLabel, "value").setText(str(unique_viewers))
        self.viewers_card.findChild(QLabel, "subtitle").setText(f"Peak: {peak_viewers}")

        # Engagement card
        if total_comments > 0:
            reply_rate = (replied_comments / total_comments) * 100
        else:
            reply_rate = 0
        self.engagement_card.findChild(QLabel, "value").setText(f"{reply_rate:.1f}%")
        self.engagement_card.findChild(QLabel, "subtitle").setText("Reply rate")

        # Duration card
        duration = self.analytics.get_session_duration()
        self.duration_card.findChild(QLabel, "value").setText(f"{duration:.0f} min")
        status = "Active" if stats.get("is_active") else "Ended"
        self.duration_card.findChild(QLabel, "subtitle").setText(status)

        # Additional stats
        self.stats_labels["total_gifts"].setText(f"Rp {stats.get('total_gifts_value', 0):,}")
        self.stats_labels["total_shares"].setText(str(stats.get("total_shares", 0)))
        self.stats_labels["total_likes"].setText(str(stats.get("total_likes", 0)))
        self.stats_labels["total_follows"].setText(str(stats.get("total_follows", 0)))

        # Timeline (show last 10 events)
        if hasattr(self.analytics.current_session, "timeline"):
            timeline = self.analytics.current_session.get("timeline", [])
            timeline_text = ""
            for event in timeline[-10:]:
                timestamp = datetime.fromisoformat(event["timestamp"]).strftime("%H:%M:%S")
                timeline_text += f"[{timestamp}] {event['description']}\n"
            self.timeline_text.setText(timeline_text)

    def _update_viewers_table(self):
        """Update top viewers table"""
        if not ANALYTICS_AVAILABLE or not self.analytics:
            return

        top_viewers = self.analytics.get_top_viewers(limit=50)

        self.viewers_table.setRowCount(len(top_viewers))

        for i, viewer in enumerate(top_viewers):
            # Rank
            rank_item = QTableWidgetItem(f"#{i+1}")
            rank_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if i < 3:  # Top 3 highlight
                rank_item.setForeground(QColor("#F5B800"))
            self.viewers_table.setItem(i, 0, rank_item)

            # Username
            username_item = QTableWidgetItem(viewer["username"])
            self.viewers_table.setItem(i, 1, username_item)

            # Comments
            comments_item = QTableWidgetItem(str(viewer["total_comments"]))
            comments_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.viewers_table.setItem(i, 2, comments_item)

            # Replied
            replied_item = QTableWidgetItem(str(viewer["replied_count"]))
            replied_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.viewers_table.setItem(i, 3, replied_item)

            # Gifts
            gifts_item = QTableWidgetItem(f"Rp {viewer['gifts_value']:,}")
            gifts_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.viewers_table.setItem(i, 4, gifts_item)

            # Shares
            shares_item = QTableWidgetItem(str(viewer["shares"]))
            shares_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.viewers_table.setItem(i, 5, shares_item)

            # Likes
            likes_item = QTableWidgetItem(str(viewer["likes"]))
            likes_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.viewers_table.setItem(i, 6, likes_item)

    def _update_keywords_table(self):
        """Update keywords table and suggestions"""
        if not ANALYTICS_AVAILABLE or not self.analytics:
            return

        top_keywords = self.analytics.get_top_keywords(limit=30)

        self.keywords_table.setRowCount(len(top_keywords))

        for i, (keyword, count) in enumerate(top_keywords):
            # Rank
            rank_item = QTableWidgetItem(f"#{i+1}")
            rank_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.keywords_table.setItem(i, 0, rank_item)

            # Keyword
            keyword_item = QTableWidgetItem(keyword)
            self.keywords_table.setItem(i, 1, keyword_item)

            # Mentions
            count_item = QTableWidgetItem(str(count))
            count_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.keywords_table.setItem(i, 2, count_item)

        # Generate suggestions based on keywords
        suggestions = self._generate_suggestions(top_keywords)
        self.suggestions_text.setText(suggestions)

    def _generate_suggestions(self, top_keywords):
        """Generate actionable suggestions based on keywords"""
        if not top_keywords:
            return "No data yet - start your live session to get insights!"

        suggestions = []

        # Check for price mentions
        for keyword, count in top_keywords[:10]:
            if keyword == "_price_mention":
                suggestions.append(f"💰 Many viewers asking about prices ({count}x) - consider showing price clearly")
            elif keyword in ["harga", "stock", "ready"]:
                suggestions.append(f"📦 '{keyword}' mentioned {count}x - viewers want to know availability")
            elif keyword in ["diskon", "promo"]:
                suggestions.append(f"🔥 '{keyword}' is hot ({count}x) - good time for flash sale!")

        # Check for product names
        product_keywords = ["hijab", "gamis", "dress", "baju"]
        for keyword, count in top_keywords[:10]:
            if keyword in product_keywords:
                suggestions.append(f"🛍️ '{keyword}' trending ({count}x) - make sure stock is ready!")

        if not suggestions:
            suggestions.append("✅ No specific action needed - engagement looks good!")

        return "\n".join(suggestions[:5])  # Max 5 suggestions

    def refresh_history(self):
        """Refresh session history"""
        if not ANALYTICS_AVAILABLE or not self.analytics:
            return

        sessions = self.analytics.get_all_sessions()

        self.history_table.setRowCount(len(sessions))

        for i, session in enumerate(reversed(sessions)):  # Newest first
            summary = self.analytics.get_session_summary(session["session_id"])
            if not summary:
                continue

            # Session ID
            id_item = QTableWidgetItem(summary["session_id"])
            self.history_table.setItem(i, 0, id_item)

            # Platform
            platform_item = QTableWidgetItem(summary["platform"].upper())
            platform_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.history_table.setItem(i, 1, platform_item)

            # Duration
            duration_item = QTableWidgetItem(f"{summary['duration_minutes']:.0f} min")
            duration_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.history_table.setItem(i, 2, duration_item)

            # Comments
            comments_item = QTableWidgetItem(str(summary["total_comments"]))
            comments_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.history_table.setItem(i, 3, comments_item)

            # Viewers
            viewers_item = QTableWidgetItem(str(summary["unique_viewers"]))
            viewers_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.history_table.setItem(i, 4, viewers_item)

            # Gifts
            gifts_item = QTableWidgetItem(f"Rp {summary['total_gifts']:,}")
            gifts_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.history_table.setItem(i, 5, gifts_item)

    def export_current_session(self):
        """Export current session to CSV"""
        if not ANALYTICS_AVAILABLE or not self.analytics:
            QMessageBox.warning(self, "Export Failed", "Analytics manager not available")
            return

        stats = self.analytics.get_current_stats()
        if not stats.get("is_active") and not stats.get("session_id"):
            QMessageBox.warning(self, "Export Failed", "No session data to export")
            return

        # Ask for save location
        default_name = f"{stats.get('session_id', 'session')}_analytics.csv"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Analytics",
            default_name,
            "CSV Files (*.csv)"
        )

        if not file_path:
            return

        # Export
        result_path, message = self.analytics.export_to_csv(export_path=file_path)

        if result_path:
            QMessageBox.information(
                self,
                "Export Success",
                f"Analytics exported to:\n{result_path}"
            )
        else:
            QMessageBox.warning(
                self,
                "Export Failed",
                f"Failed to export:\n{message}"
            )

    def clear_all_data(self):
        """Clear all analytics data"""
        reply = QMessageBox.question(
            self,
            "Confirm Clear Data",
            "Are you sure you want to delete ALL analytics data?\nThis action cannot be undone!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            if ANALYTICS_AVAILABLE and self.analytics:
                self.analytics.clear_all_data()
                self.refresh_analytics()
                self.refresh_history()
                QMessageBox.information(self, "Success", "All analytics data has been cleared")

    def showEvent(self, event):
        """Called when tab is shown"""
        super().showEvent(event)
        self.refresh_analytics()
        self.refresh_history()
    
    def export_to_pdf(self):
        """Export analytics to PDF report"""
        if not ANALYTICS_AVAILABLE or not self.analytics:
            QMessageBox.warning(self, "Export Failed", "Analytics manager not available")
            return
        
        stats = self.analytics.get_current_stats()
        if not stats.get("is_active") and not stats.get("session_id"):
            QMessageBox.warning(self, "Export Failed", "No session data to export")
            return
        
        # Ask for save location
        default_name = f"{stats.get('session_id', 'session')}_report.pdf"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export PDF Report",
            default_name,
            "PDF Files (*.pdf)"
        )
        
        if not file_path:
            return
        
        try:
            # Try to use reportlab if available
            try:
                from reportlab.lib.pagesizes import letter
                from reportlab.pdfgen import canvas
                from reportlab.lib.colors import HexColor
                
                c = canvas.Canvas(file_path, pagesize=letter)
                width, height = letter
                y = height - 50
                
                # Title
                c.setFont("Helvetica-Bold", 20)
                c.setFillColor(HexColor('#1877F2'))
                c.drawString(50, y, "VocaLive Analytics Report")
                y -= 30
                
                # Session info
                c.setFont("Helvetica-Bold", 12)
                c.setFillColor(HexColor('#000000'))
                c.drawString(50, y, f"Session: {stats.get('session_id', 'N/A')}")
                y -= 20
                c.setFont("Helvetica", 10)
                c.drawString(50, y, f"Platform: {stats.get('platform', 'N/A').upper()}")
                y -= 15
                c.drawString(50, y, f"Duration: {self.analytics.get_session_duration():.0f} minutes")
                y -= 30
                
                # Statistics section
                c.setFont("Helvetica-Bold", 14)
                c.drawString(50, y, "Session Statistics")
                y -= 20
                c.setFont("Helvetica", 10)
                
                stat_items = [
                    f"Total Comments: {stats.get('total_comments', 0)}",
                    f"Comments Replied: {stats.get('total_comments_replied', 0)}",
                    f"Unique Viewers: {stats.get('unique_viewers', 0)}",
                    f"Peak Viewers: {stats.get('peak_viewers', 0)}",
                    f"Total Gifts: Rp {stats.get('total_gifts_value', 0):,}",
                    f"Total Shares: {stats.get('total_shares', 0)}",
                    f"Total Likes: {stats.get('total_likes', 0)}",
                    f"New Follows: {stats.get('total_follows', 0)}",
                ]
                
                for item in stat_items:
                    c.drawString(70, y, item)
                    y -= 15
                
                y -= 20
                
                # Top viewers section
                c.setFont("Helvetica-Bold", 14)
                c.drawString(50, y, "Top Viewers")
                y -= 20
                c.setFont("Helvetica", 10)
                
                top_viewers = self.analytics.get_top_viewers(limit=10)
                for i, viewer in enumerate(top_viewers[:10]):
                    c.drawString(70, y, f"{i+1}. {viewer['username']} - {viewer['total_comments']} comments")
                    y -= 15
                    if y < 100:  # Page break if needed
                        c.showPage()
                        y = height - 50
                
                y -= 20
                
                # Top keywords section
                c.setFont("Helvetica-Bold", 14)
                c.drawString(50, y, "Popular Keywords")
                y -= 20
                c.setFont("Helvetica", 10)
                
                top_keywords = self.analytics.get_top_keywords(limit=10)
                for i, (keyword, count) in enumerate(top_keywords[:10]):
                    c.drawString(70, y, f"{i+1}. {keyword} - {count} mentions")
                    y -= 15
                
                # Footer
                c.setFont("Helvetica", 8)
                c.setFillColor(HexColor('#666666'))
                c.drawString(50, 30, f"Generated by VocaLive - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                c.save()
                
                QMessageBox.information(
                    self,
                    "Export Success",
                    f"PDF report exported to:\n{file_path}"
                )
                
            except ImportError:
                # Fallback: Create text file if reportlab not available
                text_path = file_path.replace('.pdf', '.txt')
                with open(text_path, 'w', encoding='utf-8') as f:
                    f.write("=" * 60 + "\n")
                    f.write("STREAMMATE AI ANALYTICS REPORT\n")
                    f.write("=" * 60 + "\n\n")
                    
                    f.write(f"Session: {stats.get('session_id', 'N/A')}\n")
                    f.write(f"Platform: {stats.get('platform', 'N/A').upper()}\n")
                    f.write(f"Duration: {self.analytics.get_session_duration():.0f} minutes\n\n")
                    
                    f.write("-" * 40 + "\n")
                    f.write("STATISTICS\n")
                    f.write("-" * 40 + "\n")
                    f.write(f"Total Comments: {stats.get('total_comments', 0)}\n")
                    f.write(f"Comments Replied: {stats.get('total_comments_replied', 0)}\n")
                    f.write(f"Unique Viewers: {stats.get('unique_viewers', 0)}\n")
                    f.write(f"Peak Viewers: {stats.get('peak_viewers', 0)}\n")
                    f.write(f"Total Gifts: Rp {stats.get('total_gifts_value', 0):,}\n")
                    f.write(f"Total Shares: {stats.get('total_shares', 0)}\n")
                    f.write(f"Total Likes: {stats.get('total_likes', 0)}\n")
                    f.write(f"New Follows: {stats.get('total_follows', 0)}\n\n")
                    
                    f.write("-" * 40 + "\n")
                    f.write("TOP VIEWERS\n")
                    f.write("-" * 40 + "\n")
                    top_viewers = self.analytics.get_top_viewers(limit=10)
                    for i, viewer in enumerate(top_viewers[:10]):
                        f.write(f"{i+1}. {viewer['username']} - {viewer['total_comments']} comments\n")
                    
                    f.write("\n" + "-" * 40 + "\n")
                    f.write("POPULAR KEYWORDS\n")
                    f.write("-" * 40 + "\n")
                    top_keywords = self.analytics.get_top_keywords(limit=10)
                    for i, (keyword, count) in enumerate(top_keywords[:10]):
                        f.write(f"{i+1}. {keyword} - {count} mentions\n")
                    
                    f.write("\n" + "=" * 60 + "\n")
                    f.write(f"Generated by VocaLive - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                
                QMessageBox.information(
                    self,
                    "Export Success",
                    f"Report exported to:\n{text_path}\n\n(Note: Install 'reportlab' for PDF export)"
                )
        
        except Exception as e:
            QMessageBox.warning(
                self,
                "Export Failed",
                f"Failed to export report:\n{str(e)}"
            )
