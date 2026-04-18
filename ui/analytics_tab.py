# ui/analytics_tab.py
"""
Live Analytics Tab - Real-time streaming performance analytics
Support: YouTube & TikTok
"""

import logging
from datetime import datetime

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QFileDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

logger = logging.getLogger('VocaLive.AnalyticsTab')

from modules_client.i18n import t

try:
    from modules_client.analytics_manager import get_analytics_manager
    ANALYTICS_AVAILABLE = True
except ImportError:
    ANALYTICS_AVAILABLE = False
    logger.warning("[AnalyticsTab] analytics_manager not available")

try:
    from ui.theme import (
        ACCENT,
        BG_BASE,
        BG_ELEVATED,
        BG_SURFACE,
        BORDER,
        BORDER_GOLD,
        CARD_ELEVATED_STYLE,
        ERROR,
        INFO,
        LOG_TEXTEDIT_STYLE,
        PRIMARY,
        RADIUS,
        RADIUS_SM,
        SECONDARY,
        SUCCESS,
        TEXT_DIM,
        TEXT_MUTED,
        TEXT_PRIMARY,
        WARNING,
        btn_danger,
        btn_ghost,
        btn_success,
        label_muted,
        label_subtitle,
        label_value,
    )
except ImportError:
    PRIMARY = "#2563EB"; BG_BASE = "#0F1623"; BG_SURFACE = "#162032"; BG_ELEVATED = "#1E2A3B"
    TEXT_PRIMARY = "#F0F6FF"; TEXT_MUTED = "#93C5FD"; TEXT_DIM = "#4B7BBA"
    ERROR = "#EF4444"; SUCCESS = "#22C55E"; WARNING = "#F59E0B"; INFO = "#38BDF8"
    BORDER_GOLD = "#1E4585"; BORDER = "#1A2E4A"; ACCENT = "#60A5FA"
    SECONDARY = "#1E3A5F"; RADIUS = "10px"; RADIUS_SM = "6px"
    def btn_success(extra=""): return f"QPushButton {{ background-color: {SUCCESS}; color: white; border: none; border-radius: 6px; padding: 8px 18px; font-weight: 700; {extra} }} QPushButton:hover {{ background-color: #16A34A; }}"
    def btn_danger(extra=""): return f"QPushButton {{ background-color: {ERROR}; color: white; border: none; border-radius: 6px; padding: 8px 18px; font-weight: 700; {extra} }} QPushButton:hover {{ background-color: #DC2626; }}"
    def btn_ghost(extra=""): return f"QPushButton {{ background-color: {BG_ELEVATED}; color: {TEXT_MUTED}; border: 1px solid {BORDER}; border-radius: 6px; padding: 7px 18px; {extra} }}"
    CARD_ELEVATED_STYLE = f"QFrame {{ background-color: {BG_ELEVATED}; border: 1px solid {BORDER_GOLD}; border-radius: 10px; }}"
    def label_value(size=22): return f"font-size: {size}pt; font-weight: 700; color: {ACCENT}; background: transparent;"
    def label_subtitle(size=11): return f"font-size: {size}px; color: {TEXT_MUTED}; background: transparent;"
    def label_muted(size=11): return f"font-size: {size}px; color: {TEXT_DIM}; background: transparent;"
    LOG_TEXTEDIT_STYLE = f"QTextEdit {{ background-color: {BG_ELEVATED}; color: {TEXT_MUTED}; border: 1px solid {BORDER_GOLD}; border-radius: 6px; padding: 8px; font-family: Consolas, monospace; font-size: 11px; }}"

# Try to import pyqtgraph for charts
try:
    import pyqtgraph as pg
    from pyqtgraph import PlotWidget
    CHARTS_AVAILABLE = True
    # Configure pyqtgraph for Ocean Blue dark theme
    pg.setConfigOption('background', '#1E2A3B')   # BG_ELEVATED
    pg.setConfigOption('foreground', '#F0F6FF')   # TEXT_PRIMARY
except ImportError:
    CHARTS_AVAILABLE = False
    logger.warning("[AnalyticsTab] pyqtgraph not available - charts disabled")


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
            error_label = QLabel(t("analytics.err.unavailable"))
            error_label.setStyleSheet(f"color: {ERROR}; font-size: 14px; padding: 20px;")
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            main_layout.addWidget(error_label)
            self.setLayout(main_layout)
            return

        # Tab untuk different views
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {BORDER_GOLD};
                background-color: {BG_BASE};
            }}
            QTabBar::tab {{
                background-color: {BG_SURFACE};
                color: {TEXT_MUTED};
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }}
            QTabBar::tab:selected {{
                background-color: {PRIMARY};
                color: white;
            }}
        """)

        # Tab 1: Real-time Overview
        self.overview_tab = self._create_overview_tab()
        self.tabs.addTab(self.overview_tab, t("analytics.tab.overview"))

        # Tab 2: Top Viewers
        self.viewers_tab = self._create_viewers_tab()
        self.tabs.addTab(self.viewers_tab, t("analytics.tab.viewers"))

        # Tab 3: Keywords
        self.keywords_tab = self._create_keywords_tab()
        self.tabs.addTab(self.keywords_tab, t("analytics.tab.keywords"))

        # Tab 4: History
        self.history_tab = self._create_history_tab()
        self.tabs.addTab(self.history_tab, t("analytics.tab.history"))

        # Tab 5: Charts (if pyqtgraph available)
        if CHARTS_AVAILABLE:
            self.charts_tab = self._create_charts_tab()
            self.tabs.addTab(self.charts_tab, t("analytics.tab.charts"))

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
        header.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_ELEVATED};
                border-radius: 8px;
                padding: 10px;
                border: 1px solid {BORDER_GOLD};
            }}
        """)

        layout = QHBoxLayout()

        # Title
        title = QLabel(t("analytics.header.title"))
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {PRIMARY};")
        layout.addWidget(title)

        layout.addStretch()

        # Session info
        self.session_label = QLabel(t("analytics.session.none"))
        self.session_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
        layout.addWidget(self.session_label)

        # Export CSV button
        export_btn = QPushButton(t("analytics.btn.export_csv"))
        export_btn.clicked.connect(self.export_current_session)
        export_btn.setStyleSheet(btn_success())
        layout.addWidget(export_btn)

        # Export PDF button
        pdf_btn = QPushButton(t("analytics.btn.export_pdf"))
        pdf_btn.clicked.connect(self.export_to_pdf)
        pdf_btn.setStyleSheet(btn_ghost())
        layout.addWidget(pdf_btn)

        # Clear data button
        clear_btn = QPushButton(t("analytics.btn.clear_all"))
        clear_btn.clicked.connect(self.clear_all_data)
        clear_btn.setStyleSheet(btn_danger())
        layout.addWidget(clear_btn)

        header.setLayout(layout)
        return header

    def _create_overview_tab(self):
        """Create overview statistics tab"""
        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: {BG_BASE};
            }}
            QScrollBar:vertical {{
                background-color: {BG_SURFACE};
                width: 12px;
                border-radius: 6px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {BORDER_GOLD};
                border-radius: 6px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {PRIMARY};
            }}
        """)

        widget = QWidget()
        layout = QVBoxLayout()

        # Stats cards
        stats_layout = QHBoxLayout()

        # Card 1: Comments
        self.comments_card = self._create_stat_card(
            t("analytics.card.comments"), "0", t("analytics.card.comments_sub_initial")
        )
        stats_layout.addWidget(self.comments_card)

        # Card 2: Viewers
        self.viewers_card = self._create_stat_card(
            t("analytics.card.viewers"), "0", t("analytics.card.viewers_sub_initial")
        )
        stats_layout.addWidget(self.viewers_card)

        # Card 3: Engagement
        self.engagement_card = self._create_stat_card(
            t("analytics.card.engagement"),
            t("analytics.card.engagement_value_initial"),
            t("analytics.card.engagement_sub"),
        )
        stats_layout.addWidget(self.engagement_card)

        # Card 4: Duration
        self.duration_card = self._create_stat_card(
            t("analytics.card.duration"),
            t("analytics.card.duration_value_initial"),
            t("analytics.card.duration_sub_active"),
        )
        stats_layout.addWidget(self.duration_card)

        layout.addLayout(stats_layout)

        # Additional stats
        stats_group = QGroupBox(t("analytics.group.detailed_stats"))
        stats_group.setStyleSheet(f"""
            QGroupBox {{
                color: {ACCENT};
                border: 1px solid {BORDER_GOLD};
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
                background-color: {BG_ELEVATED};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: {ACCENT};
                background-color: {BG_ELEVATED};
            }}
        """)

        stats_layout_inner = QVBoxLayout()

        # Stats labels
        self.stats_labels = {}
        stat_items = [
            ("total_gifts", t("analytics.stat.total_gifts"), t("analytics.stat.total_gifts_value")),
            ("total_shares", t("analytics.stat.total_shares"), t("analytics.stat.value_zero")),
            ("total_likes", t("analytics.stat.total_likes"), t("analytics.stat.value_zero")),
            ("total_follows", t("analytics.stat.total_follows"), t("analytics.stat.value_zero")),
        ]

        for key, label, default in stat_items:
            row = QHBoxLayout()
            label_widget = QLabel(label)
            label_widget.setStyleSheet(f"color: {TEXT_MUTED}; font-weight: normal;")

            value_widget = QLabel(default)
            value_widget.setStyleSheet(f"color: {TEXT_PRIMARY}; font-weight: bold; font-size: 14px;")
            value_widget.setAlignment(Qt.AlignmentFlag.AlignRight)

            row.addWidget(label_widget)
            row.addWidget(value_widget)

            stats_layout_inner.addLayout(row)
            self.stats_labels[key] = value_widget

        stats_group.setLayout(stats_layout_inner)
        layout.addWidget(stats_group)

        # Timeline
        timeline_group = QGroupBox(t("analytics.group.session_timeline"))
        timeline_group.setStyleSheet(stats_group.styleSheet())
        timeline_layout = QVBoxLayout()

        self.timeline_text = QTextEdit()
        self.timeline_text.setReadOnly(True)
        self.timeline_text.setMaximumHeight(150)
        self.timeline_text.setStyleSheet(LOG_TEXTEDIT_STYLE)

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
        card.setStyleSheet(CARD_ELEVATED_STYLE + "QFrame { padding: 15px; }")

        layout = QVBoxLayout()
        layout.setSpacing(4)

        title_label = QLabel(title)
        title_label.setStyleSheet(label_subtitle())
        layout.addWidget(title_label)

        value_label = QLabel(value)
        value_label.setStyleSheet(label_value(size=20))
        value_label.setObjectName("value")
        layout.addWidget(value_label)

        subtitle_label = QLabel(subtitle)
        subtitle_label.setStyleSheet(label_muted())
        subtitle_label.setObjectName("subtitle")
        layout.addWidget(subtitle_label)

        card.setLayout(layout)
        return card

    def _create_viewers_tab(self):
        """Create top viewers table"""
        widget = QWidget()
        layout = QVBoxLayout()

        # Description
        desc = QLabel(t("analytics.viewers.desc"))
        desc.setStyleSheet(f"color: {TEXT_MUTED}; margin-bottom: 10px;")
        layout.addWidget(desc)

        # Table
        self.viewers_table = QTableWidget()
        self.viewers_table.setColumnCount(7)
        self.viewers_table.setHorizontalHeaderLabels([
            t("analytics.viewers.col.rank"),
            t("analytics.viewers.col.username"),
            t("analytics.viewers.col.comments"),
            t("analytics.viewers.col.replied"),
            t("analytics.viewers.col.gifts"),
            t("analytics.viewers.col.shares"),
            t("analytics.viewers.col.likes"),
        ])

        # Table styling
        self.viewers_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {BG_ELEVATED};
                color: {TEXT_PRIMARY};
                border: 1px solid {BORDER_GOLD};
                border-radius: 4px;
                gridline-color: {BORDER};
            }}
            QTableWidget::item {{
                padding: 8px;
            }}
            QTableWidget::item:selected {{
                background-color: {PRIMARY};
                color: white;
            }}
            QHeaderView::section {{
                background-color: {SECONDARY};
                color: {TEXT_PRIMARY};
                padding: 8px;
                border: 1px solid {BORDER_GOLD};
                font-weight: bold;
            }}
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
        desc = QLabel(t("analytics.keywords.desc"))
        desc.setStyleSheet(f"color: {TEXT_MUTED}; margin-bottom: 10px;")
        layout.addWidget(desc)

        # Table
        self.keywords_table = QTableWidget()
        self.keywords_table.setColumnCount(3)
        self.keywords_table.setHorizontalHeaderLabels([
            t("analytics.keywords.col.rank"),
            t("analytics.keywords.col.keyword"),
            t("analytics.keywords.col.mentions"),
        ])

        self.keywords_table.setStyleSheet(self.viewers_table.styleSheet())
        self.keywords_table.horizontalHeader().setStretchLastSection(True)
        self.keywords_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.keywords_table.verticalHeader().setVisible(False)

        layout.addWidget(self.keywords_table)

        # Action suggestions
        suggestions_group = QGroupBox(t("analytics.group.suggested_actions"))
        suggestions_group.setStyleSheet(f"""
            QGroupBox {{
                color: {ACCENT};
                border: 1px solid {BORDER_GOLD};
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
                background-color: {BG_ELEVATED};
            }}
        """)

        suggestions_layout = QVBoxLayout()
        self.suggestions_text = QTextEdit()
        self.suggestions_text.setReadOnly(True)
        self.suggestions_text.setMaximumHeight(100)
        self.suggestions_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: {BG_ELEVATED};
                color: {TEXT_MUTED};
                border: 1px solid {BORDER_GOLD};
                border-radius: 4px;
                padding: 8px;
            }}
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
        desc = QLabel(t("analytics.history.desc"))
        desc.setStyleSheet(f"color: {TEXT_MUTED}; margin-bottom: 10px;")
        layout.addWidget(desc)

        # Table
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(6)
        self.history_table.setHorizontalHeaderLabels([
            t("analytics.history.col.session_id"),
            t("analytics.history.col.platform"),
            t("analytics.history.col.duration"),
            t("analytics.history.col.comments"),
            t("analytics.history.col.viewers"),
            t("analytics.history.col.gifts"),
        ])

        self.history_table.setStyleSheet(self.viewers_table.styleSheet())
        self.history_table.horizontalHeader().setStretchLastSection(True)
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.history_table.verticalHeader().setVisible(False)

        layout.addWidget(self.history_table)

        # Buttons
        btn_layout = QHBoxLayout()

        refresh_btn = QPushButton(t("analytics.btn.refresh_history"))
        refresh_btn.clicked.connect(self.refresh_history)
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {PRIMARY};
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {ACCENT};
                color: {BG_BASE};
            }}
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
        desc = QLabel(t("analytics.charts.desc"))
        desc.setStyleSheet(f"color: {TEXT_MUTED}; margin-bottom: 10px;")
        layout.addWidget(desc)

        # Chart 1: Viewers over time
        viewers_group = QGroupBox(t("analytics.group.viewers_chart"))
        viewers_group.setStyleSheet(f"""
            QGroupBox {{
                color: {ACCENT};
                border: 1px solid {BORDER_GOLD};
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
                background-color: {BG_ELEVATED};
            }}
        """)
        viewers_layout = QVBoxLayout()

        self.viewers_chart = PlotWidget()
        self.viewers_chart.setBackground(BG_ELEVATED)
        self.viewers_chart.setLabel('left', t("analytics.charts.axis.viewers"), color=PRIMARY)
        self.viewers_chart.setLabel('bottom', t("analytics.charts.axis.time"), color=TEXT_MUTED)
        self.viewers_chart.showGrid(x=True, y=True, alpha=0.3)
        self.viewers_chart.setMinimumHeight(150)
        self.viewers_plot = self.viewers_chart.plot([], [], pen=pg.mkPen(PRIMARY, width=2), symbol='o', symbolSize=5, symbolBrush=PRIMARY)

        viewers_layout.addWidget(self.viewers_chart)
        viewers_group.setLayout(viewers_layout)
        layout.addWidget(viewers_group)

        # Chart 2: Comments over time
        comments_group = QGroupBox(t("analytics.group.comments_chart"))
        comments_group.setStyleSheet(viewers_group.styleSheet())
        comments_layout = QVBoxLayout()

        self.comments_chart = PlotWidget()
        self.comments_chart.setBackground(BG_ELEVATED)
        self.comments_chart.setLabel('left', t("analytics.charts.axis.comments"), color=SUCCESS)
        self.comments_chart.setLabel('bottom', t("analytics.charts.axis.time"), color=TEXT_MUTED)
        self.comments_chart.showGrid(x=True, y=True, alpha=0.3)
        self.comments_chart.setMinimumHeight(150)
        self.comments_plot = self.comments_chart.plot([], [], pen=pg.mkPen(SUCCESS, width=2), symbol='o', symbolSize=5, symbolBrush=SUCCESS)

        comments_layout.addWidget(self.comments_chart)
        comments_group.setLayout(comments_layout)
        layout.addWidget(comments_group)

        # Clear charts button
        btn_layout = QHBoxLayout()

        clear_btn = QPushButton(t("analytics.btn.clear_charts"))
        clear_btn.clicked.connect(self._clear_charts)
        clear_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ERROR};
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {WARNING};
                color: {BG_BASE};
            }}
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
            self.session_label.setText(
                t("analytics.session.live", platform=platform, session_id=session_id)
            )
            self.session_label.setStyleSheet(f"color: {SUCCESS}; font-size: 12px; font-weight: bold;")
        else:
            self.session_label.setText(t("analytics.session.offline"))
            self.session_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")

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
        self.comments_card.findChild(QLabel, "subtitle").setText(
            t("analytics.card.comments_sub", count=replied_comments)
        )

        # Viewers card
        unique_viewers = stats.get("unique_viewers", 0)
        peak_viewers = stats.get("peak_viewers", 0)
        self.viewers_card.findChild(QLabel, "value").setText(str(unique_viewers))
        self.viewers_card.findChild(QLabel, "subtitle").setText(
            t("analytics.card.viewers_sub", peak=peak_viewers)
        )

        # Engagement card
        if total_comments > 0:
            reply_rate = (replied_comments / total_comments) * 100
        else:
            reply_rate = 0
        self.engagement_card.findChild(QLabel, "value").setText(
            t("analytics.card.engagement_value", rate=reply_rate)
        )
        self.engagement_card.findChild(QLabel, "subtitle").setText(
            t("analytics.card.engagement_sub")
        )

        # Duration card
        duration = self.analytics.get_session_duration()
        self.duration_card.findChild(QLabel, "value").setText(
            t("analytics.card.duration_value", minutes=duration)
        )
        status = (
            t("analytics.card.duration_sub_active")
            if stats.get("is_active")
            else t("analytics.card.duration_sub_ended")
        )
        self.duration_card.findChild(QLabel, "subtitle").setText(status)

        # Additional stats
        self.stats_labels["total_gifts"].setText(f"Rp {stats.get('total_gifts_value', 0):,}")
        self.stats_labels["total_shares"].setText(str(stats.get("total_shares", 0)))
        self.stats_labels["total_likes"].setText(str(stats.get("total_likes", 0)))
        self.stats_labels["total_follows"].setText(str(stats.get("total_follows", 0)))

        # Timeline (show last 10 events)
        timeline = self.analytics.current_session.get("timeline", [])
        if timeline:
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
                rank_item.setForeground(QColor(ACCENT))
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
            return t("analytics.suggest.empty")

        suggestions = []

        # Check for price mentions
        for keyword, count in top_keywords[:10]:
            if keyword == "_price_mention":
                suggestions.append(t("analytics.suggest.price", count=count))
            elif keyword in ["harga", "stock", "ready"]:
                suggestions.append(
                    t("analytics.suggest.availability", keyword=keyword, count=count)
                )
            elif keyword in ["diskon", "promo"]:
                suggestions.append(
                    t("analytics.suggest.promo", keyword=keyword, count=count)
                )

        # Check for product names
        product_keywords = ["hijab", "gamis", "dress", "baju"]
        for keyword, count in top_keywords[:10]:
            if keyword in product_keywords:
                suggestions.append(
                    t("analytics.suggest.product", keyword=keyword, count=count)
                )

        if not suggestions:
            suggestions.append(t("analytics.suggest.all_good"))

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
            duration_item = QTableWidgetItem(
                t("analytics.duration_minutes", minutes=summary["duration_minutes"])
            )
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
            QMessageBox.warning(
                self, t("analytics.export.fail_title"), t("analytics.export.no_manager")
            )
            return

        stats = self.analytics.get_current_stats()
        if not stats.get("is_active") and not stats.get("session_id"):
            QMessageBox.warning(
                self, t("analytics.export.fail_title"), t("analytics.export.no_data")
            )
            return

        # Ask for save location
        default_name = t(
            "analytics.export.csv_default_name",
            session_id=stats.get("session_id", "session"),
        )
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            t("analytics.export.csv_dialog_title"),
            default_name,
            t("analytics.export.csv_filter"),
        )

        if not file_path:
            return

        # Export
        result_path, message = self.analytics.export_to_csv(export_path=file_path)

        if result_path:
            QMessageBox.information(
                self,
                t("analytics.export.success_title"),
                t("analytics.export.csv_success", path=result_path),
            )
        else:
            QMessageBox.warning(
                self,
                t("analytics.export.fail_title"),
                t("analytics.export.csv_failed", reason=message),
            )

    def clear_all_data(self):
        """Clear all analytics data"""
        reply = QMessageBox.question(
            self,
            t("analytics.clear.confirm_title"),
            t("analytics.clear.confirm_text"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            if ANALYTICS_AVAILABLE and self.analytics:
                self.analytics.clear_all_data()
                self.refresh_analytics()
                self.refresh_history()
                QMessageBox.information(
                    self,
                    t("analytics.clear.success_title"),
                    t("analytics.clear.success_text"),
                )

    def showEvent(self, event):
        """Called when tab is shown"""
        super().showEvent(event)
        self.refresh_analytics()
        self.refresh_history()

    def export_to_pdf(self):
        """Export analytics ke PDF menggunakan QPrinter built-in PyQt6 — tanpa library tambahan"""
        if not ANALYTICS_AVAILABLE or not self.analytics:
            QMessageBox.warning(
                self, t("analytics.export.fail_title"), t("analytics.export.no_manager")
            )
            return

        stats = self.analytics.get_current_stats()
        if not stats.get("is_active") and not stats.get("session_id"):
            QMessageBox.warning(
                self, t("analytics.export.fail_title"), t("analytics.export.no_data")
            )
            return

        default_name = t(
            "analytics.export.pdf_default_name",
            session_id=stats.get("session_id", "session"),
        )
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            t("analytics.export.pdf_dialog_title"),
            default_name,
            t("analytics.export.pdf_filter"),
        )
        if not file_path:
            return

        try:
            from PyQt6.QtGui import QTextDocument
            from PyQt6.QtPrintSupport import QPrinter

            duration = self.analytics.get_session_duration()
            total = stats.get("total_comments", 0)
            replied = stats.get("total_comments_replied", 0)
            reply_rate = f"{(replied/total*100):.1f}%" if total > 0 else "0%"
            top_viewers = self.analytics.get_top_viewers(limit=10)
            top_keywords = self.analytics.get_top_keywords(limit=10)

            # Baris tabel top viewers
            viewer_rows = "".join(
                f"<tr><td style='padding:4px 8px;'>#{i+1}</td>"
                f"<td style='padding:4px 8px;'>{v['username']}</td>"
                f"<td style='padding:4px 8px;text-align:center'>{v['total_comments']}</td>"
                f"<td style='padding:4px 8px;text-align:center'>{v.get('replied_count',0)}</td></tr>"
                for i, v in enumerate(top_viewers)
            )
            # Baris tabel top keywords
            keyword_rows = "".join(
                f"<tr><td style='padding:4px 8px;'>#{i+1}</td>"
                f"<td style='padding:4px 8px;'>{kw}</td>"
                f"<td style='padding:4px 8px;text-align:center'>{cnt}</td></tr>"
                for i, (kw, cnt) in enumerate(top_keywords)
            )

            no_data_html_4col = f'<tr><td colspan="4">{t("analytics.pdf.no_data")}</td></tr>'
            no_data_html_3col = f'<tr><td colspan="3">{t("analytics.pdf.no_data")}</td></tr>'

            html = f"""
            <html><head><style>
                body {{ font-family: Arial, sans-serif; color: #111; margin: 24px; }}
                h1 {{ color: #2563EB; border-bottom: 2px solid #2563EB; padding-bottom: 6px; }}
                h2 {{ color: #1E3A5F; margin-top: 24px; border-left: 4px solid #60A5FA; padding-left: 8px; }}
                table {{ border-collapse: collapse; width: 100%; margin-top: 8px; }}
                th {{ background: #2563EB; color: white; padding: 6px 8px; text-align: left; }}
                tr:nth-child(even) {{ background: #f0f6ff; }}
                .stat-grid {{ display: flex; flex-wrap: wrap; gap: 12px; margin: 12px 0; }}
                .stat-box {{ border: 1px solid #60A5FA; border-radius: 6px; padding: 10px 16px; min-width: 140px; }}
                .stat-val {{ font-size: 22px; font-weight: bold; color: #2563EB; }}
                .stat-lbl {{ font-size: 11px; color: #666; }}
                .footer {{ color: #999; font-size: 10px; margin-top: 32px; border-top: 1px solid #ddd; padding-top: 8px; }}
            </style></head><body>
            <h1>{t("analytics.pdf.report_title")}</h1>
            <p><b>{t("analytics.pdf.session")}:</b> {stats.get('session_id','N/A')} &nbsp;|&nbsp;
               <b>{t("analytics.pdf.platform")}:</b> {stats.get('platform','N/A').upper()} &nbsp;|&nbsp;
               <b>{t("analytics.pdf.duration")}:</b> {duration:.0f} {t("analytics.pdf.minutes")} &nbsp;|&nbsp;
               <b>{t("analytics.pdf.created")}:</b> {datetime.now().strftime('%d %b %Y %H:%M')}</p>

            <h2>{t("analytics.pdf.section_stats")}</h2>
            <table>
                <tr><th>{t("analytics.pdf.col.metric")}</th><th>{t("analytics.pdf.col.value")}</th></tr>
                <tr><td>{t("analytics.pdf.stat.total_comments")}</td><td>{total}</td></tr>
                <tr><td>{t("analytics.pdf.stat.replied")}</td><td>{replied} ({reply_rate})</td></tr>
                <tr><td>{t("analytics.pdf.stat.unique_viewers")}</td><td>{stats.get('unique_viewers',0)}</td></tr>
                <tr><td>{t("analytics.pdf.stat.peak_viewers")}</td><td>{stats.get('peak_viewers',0)}</td></tr>
                <tr><td>{t("analytics.pdf.stat.total_gifts")}</td><td>Rp {stats.get('total_gifts_value',0):,}</td></tr>
                <tr><td>{t("analytics.pdf.stat.shares")}</td><td>{stats.get('total_shares',0)}</td></tr>
                <tr><td>{t("analytics.pdf.stat.likes")}</td><td>{stats.get('total_likes',0)}</td></tr>
                <tr><td>{t("analytics.pdf.stat.new_follows")}</td><td>{stats.get('total_follows',0)}</td></tr>
            </table>

            <h2>{t("analytics.pdf.section_top_viewers")}</h2>
            <table>
                <tr><th>{t("analytics.pdf.col.rank")}</th><th>{t("analytics.pdf.col.username")}</th><th>{t("analytics.pdf.col.comments")}</th><th>{t("analytics.pdf.col.replied")}</th></tr>
                {viewer_rows if viewer_rows else no_data_html_4col}
            </table>

            <h2>{t("analytics.pdf.section_top_keywords")}</h2>
            <table>
                <tr><th>{t("analytics.pdf.col.rank")}</th><th>{t("analytics.pdf.col.keyword")}</th><th>{t("analytics.pdf.col.mentions")}</th></tr>
                {keyword_rows if keyword_rows else no_data_html_3col}
            </table>

            <p class="footer">{t("analytics.pdf.footer", timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}</p>
            </body></html>
            """

            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(file_path)
            printer.setPageMargins(
                printer.pageLayout().margins()
            )

            doc = QTextDocument()
            doc.setHtml(html)
            doc.print_(printer)

            QMessageBox.information(
                self,
                t("analytics.export.success_title"),
                t("analytics.export.pdf_success", path=file_path),
            )

        except Exception as e:
            QMessageBox.warning(
                self,
                t("analytics.export.fail_title"),
                t("analytics.export.pdf_failed", reason=str(e)),
            )
