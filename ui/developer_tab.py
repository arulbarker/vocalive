# ui/developer_tab.py - Developer Social Media Links Tab

import webbrowser
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QGridLayout, QScrollArea, QFrame, QTextEdit
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QFont, QPixmap, QDesktopServices

try:
    from ui.theme import (PRIMARY, SECONDARY, ACCENT, BG_BASE, BG_SURFACE, BG_ELEVATED,
        TEXT_PRIMARY, TEXT_MUTED, TEXT_DIM, BORDER_GOLD, BORDER,
        SUCCESS, ERROR, WARNING, INFO, RADIUS, RADIUS_SM)
except ImportError:
    PRIMARY = "#D97706"; BG_BASE = "#1c1208"; BG_SURFACE = "#261509"; BG_ELEVATED = "#2E1A0A"
    TEXT_PRIMARY = "#FFFBEB"; TEXT_MUTED = "#D6B97B"; TEXT_DIM = "#92734A"
    ERROR = "#EF4444"; SUCCESS = "#22C55E"; WARNING = "#F59E0B"; INFO = "#38BDF8"
    BORDER_GOLD = "#92400E"; BORDER = "#3D2010"; ACCENT = "#FCD34D"
    SECONDARY = "#92400E"; RADIUS = "10px"; RADIUS_SM = "6px"

class DeveloperTab(QWidget):
    """Tab untuk menampilkan link media sosial developer dengan UI yang menarik."""
    
    def __init__(self):
        super().__init__()
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup user interface untuk Developer Tab."""
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Create content widget
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(25)
        
        # Header section
        self._create_header_section(content_layout)
        
        # Social media links section
        self._create_social_media_section(content_layout)
        
        # About section
        self._create_about_section(content_layout)
        
        # Footer
        self._create_footer_section(content_layout)
        
        # Add stretch to push content to top
        content_layout.addStretch()
        
        # Set content widget to scroll area
        scroll_area.setWidget(content_widget)
        
        # Add scroll area to main layout
        main_layout.addWidget(scroll_area)
        
        # Apply main layout
        self.setLayout(main_layout)
        
        # Apply styling
        self._apply_styling()
    
    def _create_header_section(self, layout):
        """Create header section with developer info."""
        header_group = QGroupBox("👨‍💻 Developer Information")
        header_layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("VocaLive Developer")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet(f"color: {PRIMARY}; margin: 10px;")
        
        # Subtitle
        subtitle_label = QLabel("Arul CG - Full Stack Developer & Content Creator")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_font = QFont()
        subtitle_font.setPointSize(14)
        subtitle_label.setFont(subtitle_font)
        subtitle_label.setStyleSheet(f"color: {TEXT_PRIMARY}; margin-bottom: 20px;")
        
        header_layout.addWidget(title_label)
        header_layout.addWidget(subtitle_label)
        header_group.setLayout(header_layout)
        
        layout.addWidget(header_group)
    
    def _create_social_media_section(self, layout):
        """Create social media links section."""
        social_group = QGroupBox("🌐 Follow Me On Social Media")
        social_layout = QGridLayout()
        social_layout.setSpacing(15)
        
        # Social media data with icons and colors
        social_media = [
            {
                "name": "YouTube",
                "url": "https://www.youtube.com/@arulcg",
                "icon": "🎥",
                "color": "#FF0000",
                "description": "Tech tutorials & coding content"
            },
            {
                "name": "Instagram", 
                "url": "https://www.instagram.com/arul.cg/",
                "icon": "📷",
                "color": "#E4405F",
                "description": "Daily updates & behind the scenes"
            },
            {
                "name": "Facebook",
                "url": "https://www.facebook.com/profile.php?id=61578938703730",
                "icon": "👥",
                "color": "#1877F2", 
                "description": "Community & discussions"
            },
            {
                "name": "Threads",
                "url": "https://www.threads.com/@arul.cg",
                "icon": "🧵",
                "color": "#000000",
                "description": "Quick thoughts & updates"
            },
            {
                "name": "X (Twitter)",
                "url": "https://x.com/ArulCg",
                "icon": "🐦",
                "color": "#1DA1F2",
                "description": "Tech news & quick updates"
            },
            {
                "name": "LYNK.ID",
                "url": "https://lynk.id/arullagi", 
                "icon": "🔗",
                "color": "#00D4AA",
                "description": "All my links in one place"
            }
        ]
        
        # Create buttons for each social media
        for i, social in enumerate(social_media):
            button = self._create_social_button(
                social["name"],
                social["url"], 
                social["icon"],
                social["color"],
                social["description"]
            )
            
            # Add to grid layout (2 columns)
            row = i // 2
            col = i % 2
            social_layout.addWidget(button, row, col)
        
        social_group.setLayout(social_layout)
        layout.addWidget(social_group)
    
    def _create_social_button(self, name, url, icon, color, description):
        """Create styled social media button."""
        button_frame = QFrame()
        button_frame.setFrameStyle(QFrame.Shape.Box)
        button_layout = QVBoxLayout(button_frame)
        button_layout.setSpacing(8)
        
        # Icon and name
        header_layout = QHBoxLayout()
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 24px;")
        
        name_label = QLabel(name)
        name_font = QFont()
        name_font.setPointSize(14)
        name_font.setBold(True)
        name_label.setFont(name_font)
        name_label.setStyleSheet(f"color: {color};")
        
        header_layout.addWidget(icon_label)
        header_layout.addWidget(name_label)
        header_layout.addStretch()
        
        # Description
        desc_label = QLabel(description)
        desc_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
        desc_label.setWordWrap(True)
        
        # Visit button
        visit_btn = QPushButton(f"Visit {name}")
        visit_btn.clicked.connect(lambda: self._open_url(url))
        visit_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {self._darken_color(color)};
            }}
            QPushButton:pressed {{
                background-color: {self._darken_color(color, 0.3)};
            }}
        """)
        
        button_layout.addLayout(header_layout)
        button_layout.addWidget(desc_label)
        button_layout.addWidget(visit_btn)
        
        # Frame styling
        button_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_ELEVATED};
                border: 2px solid {BORDER_GOLD};
                border-radius: 12px;
                padding: 10px;
                margin: 5px;
            }}
            QFrame:hover {{
                border-color: {PRIMARY};
                background-color: {BG_SURFACE};
            }}
        """)
        
        return button_frame
    
    def _create_about_section(self, layout):
        """Create about section."""
        about_group = QGroupBox("ℹ️ About VocaLive")
        about_layout = QVBoxLayout()
        
        about_text = QTextEdit()
        about_text.setMaximumHeight(150)
        about_text.setReadOnly(True)
        about_content = """VocaLive adalah aplikasi live streaming assistant yang dikembangkan oleh Arul CG untuk membantu content creator berinteraksi dengan audience secara otomatis menggunakan AI.

🚀 Features:
• AI-powered auto reply untuk YouTube & TikTok Live
• OBS integration untuk scene switching otomatis  
• Text-to-Speech dengan berbagai pilihan suara
• Smart trigger system untuk product explanation
• Multi-platform support dan real-time monitoring

💡 Dikembangkan dengan Python, PyQt6, dan berbagai AI APIs untuk memberikan pengalaman streaming yang lebih interaktif dan engaging!"""
        
        about_text.setPlainText(about_content)
        about_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: {BG_ELEVATED};
                color: {TEXT_PRIMARY};
                border: 2px solid {BORDER_GOLD};
                border-radius: 8px;
                padding: 10px;
                font-size: 12px;
                line-height: 1.4;
            }}
        """)
        
        about_layout.addWidget(about_text)
        about_group.setLayout(about_layout)
        
        layout.addWidget(about_group)
    
    def _create_footer_section(self, layout):
        """Create footer section."""
        footer_frame = QFrame()
        footer_layout = QVBoxLayout(footer_frame)
        
        # Support message
        support_label = QLabel("💖 Jika aplikasi ini membantu, jangan lupa follow dan subscribe!")
        support_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        support_label.setStyleSheet(f"color: {ACCENT}; font-weight: bold; font-size: 14px; margin: 10px;")
        
        # Copyright
        copyright_label = QLabel("© 2024 Arul CG - VocaLive Developer")
        copyright_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        copyright_label.setStyleSheet(f"color: {TEXT_DIM}; font-size: 10px; margin: 5px;")
        
        footer_layout.addWidget(support_label)
        footer_layout.addWidget(copyright_label)
        
        footer_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_BASE};
                border-radius: 8px;
                border: 1px solid {BORDER_GOLD};
                margin-top: 10px;
            }}
        """)
        
        layout.addWidget(footer_frame)
    
    def _apply_styling(self):
        """Apply global styling to the tab."""
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {BG_BASE};
                color: {TEXT_PRIMARY};
                font-family: 'Segoe UI', Arial, sans-serif;
            }}

            QGroupBox {{
                font-weight: bold;
                border: 2px solid {BORDER_GOLD};
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 10px;
                background-color: {BG_ELEVATED};
            }}

            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
                color: {ACCENT};
                font-size: 14px;
                font-weight: bold;
                background-color: {BG_ELEVATED};
            }}

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
    
    def _darken_color(self, color, factor=0.2):
        """Darken a hex color for hover effects."""
        # Remove # if present
        color = color.lstrip('#')
        
        # Convert hex to RGB
        r = int(color[0:2], 16)
        g = int(color[2:4], 16) 
        b = int(color[4:6], 16)
        
        # Darken
        r = max(0, int(r * (1 - factor)))
        g = max(0, int(g * (1 - factor)))
        b = max(0, int(b * (1 - factor)))
        
        # Convert back to hex
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def _open_url(self, url):
        """Open URL in default browser."""
        try:
            QDesktopServices.openUrl(QUrl(url))
        except Exception as e:
            print(f"Error opening URL {url}: {e}")
            # Fallback to webbrowser
            try:
                webbrowser.open(url)
            except Exception as fallback_e:
                print(f"Fallback error opening URL {url}: {fallback_e}")