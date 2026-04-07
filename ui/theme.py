# ui/theme.py — VocaLive Ocean Blue Design System
"""
Centralized design system untuk VocaLive v1.0.0.
Semua warna, QSS stylesheet, dan helper functions ada di sini.
Import dari file ini — jangan hardcode warna di file UI lain.

Branding: Ocean Blue 🌊
"""

# ── Color Tokens ──────────────────────────────────────────────
BG_BASE       = "#0F1623"   # Dark navy background utama
BG_SURFACE    = "#162032"   # Card / panel surface
BG_ELEVATED   = "#1E2A3B"   # Elevated card / header

PRIMARY       = "#2563EB"   # Biru cerah — CTA, active, highlight
PRIMARY_DARK  = "#1D4ED8"   # Biru gelap — hover/pressed
PRIMARY_LIGHT = "#3B82F6"   # Biru terang — hover light

SECONDARY     = "#1E3A5F"   # Biru tua — border, depth, table header
ACCENT        = "#60A5FA"   # Biru muda — badge, notif, subtitle value

TEXT_PRIMARY  = "#F0F6FF"   # Teks utama (putih biru)
TEXT_MUTED    = "#93C5FD"   # Teks sekunder / placeholder
TEXT_DIM      = "#4B7BBA"   # Teks sangat redup / disabled

BORDER        = "#1A2E4A"   # Border default (navy gelap)
BORDER_GOLD   = "#1E4585"   # Border aksen biru (nama dipertahankan untuk kompatibilitas)

SUCCESS       = "#22C55E"   # Hijau
SUCCESS_DARK  = "#16A34A"
ERROR         = "#EF4444"   # Merah
ERROR_DARK    = "#DC2626"
WARNING       = "#F59E0B"   # Kuning amber
INFO          = "#38BDF8"   # Biru sky

RADIUS        = "10px"
RADIUS_SM     = "6px"
RADIUS_LG     = "14px"


# ── Global QSS Stylesheet ─────────────────────────────────────
GLOBAL_QSS = f"""
/* ── Base ── */
QMainWindow, QWidget {{
    background-color: {BG_BASE};
    color: {TEXT_PRIMARY};
    font-family: 'Segoe UI', Arial, sans-serif;
}}

/* ── Tab Bar ── */
QTabWidget::pane {{
    border: 1px solid {BORDER_GOLD};
    background-color: {BG_BASE};
    border-radius: {RADIUS};
}}
QTabBar::tab {{
    background-color: {BG_SURFACE};
    color: {TEXT_MUTED};
    padding: 9px 16px;
    border: 1px solid {BORDER};
    border-bottom: none;
    border-top-left-radius: {RADIUS_SM};
    border-top-right-radius: {RADIUS_SM};
    margin-right: 2px;
    font-size: 12px;
    font-weight: 500;
    min-width: 80px;
}}
QTabBar::tab:selected {{
    background-color: {PRIMARY};
    color: {BG_BASE};
    font-weight: 700;
    border-color: {PRIMARY};
}}
QTabBar::tab:hover:!selected {{
    background-color: {BG_ELEVATED};
    color: {TEXT_PRIMARY};
    border-color: {BORDER_GOLD};
}}

/* ── Inputs ── */
QLineEdit, QTextEdit, QPlainTextEdit {{
    background-color: {BG_SURFACE};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_GOLD};
    border-radius: {RADIUS_SM};
    padding: 6px 10px;
    selection-background-color: {PRIMARY};
    selection-color: {BG_BASE};
}}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
    border: 1px solid {PRIMARY};
    background-color: {BG_ELEVATED};
}}
QLineEdit:disabled, QTextEdit:disabled {{
    background-color: {BG_BASE};
    color: {TEXT_DIM};
    border-color: {BORDER};
}}

/* ── ComboBox ── */
QComboBox {{
    background-color: {BG_SURFACE};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_GOLD};
    border-radius: {RADIUS_SM};
    padding: 6px 10px;
    min-height: 28px;
}}
QComboBox:focus {{
    border-color: {PRIMARY};
}}
QComboBox::drop-down {{
    border: none;
    width: 24px;
}}
QComboBox::down-arrow {{
    width: 10px;
    height: 10px;
}}
QComboBox QAbstractItemView {{
    background-color: {BG_ELEVATED};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_GOLD};
    selection-background-color: {PRIMARY};
    selection-color: {BG_BASE};
    outline: none;
}}
QComboBox:disabled {{
    background-color: {BG_BASE};
    color: {TEXT_DIM};
    border-color: {BORDER};
}}

/* ── SpinBox ── */
QSpinBox, QDoubleSpinBox {{
    background-color: {BG_SURFACE};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_GOLD};
    border-radius: {RADIUS_SM};
    padding: 5px 8px;
    min-height: 28px;
}}
QSpinBox:focus, QDoubleSpinBox:focus {{
    border-color: {PRIMARY};
}}
QSpinBox::up-button, QSpinBox::down-button,
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
    background-color: {SECONDARY};
    border-left: 1px solid {BORDER_GOLD};
    width: 22px;
}}
QSpinBox::up-button:hover, QSpinBox::down-button:hover,
QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover {{
    background-color: {PRIMARY};
}}
QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {{
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-bottom: 6px solid {ACCENT};
    width: 0px;
    height: 0px;
}}
QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {{
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid {ACCENT};
    width: 0px;
    height: 0px;
}}
QSpinBox::up-arrow:hover, QDoubleSpinBox::up-arrow:hover {{
    border-bottom-color: {TEXT_PRIMARY};
}}
QSpinBox::down-arrow:hover, QDoubleSpinBox::down-arrow:hover {{
    border-top-color: {TEXT_PRIMARY};
}}

/* ── CheckBox ── */
QCheckBox {{
    color: {TEXT_PRIMARY};
    spacing: 8px;
    font-size: 12px;
}}
QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 2px solid {BORDER_GOLD};
    border-radius: 4px;
    background-color: {BG_SURFACE};
}}
QCheckBox::indicator:checked {{
    background-color: {PRIMARY};
    border-color: {PRIMARY};
}}
QCheckBox::indicator:hover {{
    border-color: {PRIMARY};
}}

/* ── GroupBox ── */
QGroupBox {{
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_GOLD};
    border-radius: {RADIUS};
    margin-top: 14px;
    padding-top: 12px;
    font-weight: 600;
    font-size: 12px;
    background-color: {BG_SURFACE};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: {PRIMARY};
    font-size: 12px;
    font-weight: 700;
    background-color: {BG_BASE};
}}

/* ── ScrollBar ── */
QScrollBar:vertical {{
    background-color: {BG_BASE};
    width: 8px;
    border-radius: 4px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background-color: {SECONDARY};
    border-radius: 4px;
    min-height: 24px;
}}
QScrollBar::handle:vertical:hover {{
    background-color: {PRIMARY};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
    background: none;
}}
QScrollBar:horizontal {{
    background-color: {BG_BASE};
    height: 8px;
    border-radius: 4px;
}}
QScrollBar::handle:horizontal {{
    background-color: {SECONDARY};
    border-radius: 4px;
    min-width: 24px;
}}
QScrollBar::handle:horizontal:hover {{
    background-color: {PRIMARY};
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
    background: none;
}}

/* ── Table ── */
QTableWidget {{
    background-color: {BG_SURFACE};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_GOLD};
    border-radius: {RADIUS_SM};
    gridline-color: {BORDER};
    alternate-background-color: {BG_ELEVATED};
    outline: none;
}}
QTableWidget::item {{
    padding: 7px 10px;
    border: none;
}}
QTableWidget::item:selected {{
    background-color: {PRIMARY};
    color: {BG_BASE};
}}
QHeaderView::section {{
    background-color: {SECONDARY};
    color: {TEXT_PRIMARY};
    padding: 8px 10px;
    border: none;
    border-right: 1px solid {BORDER};
    font-weight: 700;
    font-size: 11px;
    letter-spacing: 0.03em;
}}
QHeaderView::section:last {{
    border-right: none;
}}

/* ── ListWidget ── */
QListWidget {{
    background-color: {BG_SURFACE};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_GOLD};
    border-radius: {RADIUS_SM};
    outline: none;
}}
QListWidget::item {{
    padding: 8px 10px;
    border-bottom: 1px solid {BORDER};
}}
QListWidget::item:last {{
    border-bottom: none;
}}
QListWidget::item:selected {{
    background-color: {PRIMARY};
    color: {BG_BASE};
}}
QListWidget::item:hover:!selected {{
    background-color: {BG_ELEVATED};
}}

/* ── StatusBar ── */
QStatusBar {{
    background-color: {BG_ELEVATED};
    color: {TEXT_MUTED};
    border-top: 1px solid {BORDER_GOLD};
    font-size: 11px;
    padding: 2px 8px;
}}

/* ── ProgressBar ── */
QProgressBar {{
    background-color: {BG_SURFACE};
    border: 1px solid {BORDER_GOLD};
    border-radius: {RADIUS_SM};
    text-align: center;
    color: {TEXT_PRIMARY};
    font-size: 10px;
    max-height: 10px;
}}
QProgressBar::chunk {{
    background-color: {PRIMARY};
    border-radius: {RADIUS_SM};
}}

/* ── MessageBox ── */
QMessageBox {{
    background-color: {BG_ELEVATED};
}}
QMessageBox QLabel {{
    color: {TEXT_PRIMARY};
    font-size: 12px;
}}
QMessageBox QPushButton {{
    background-color: {PRIMARY};
    color: {BG_BASE};
    border: none;
    border-radius: {RADIUS_SM};
    padding: 7px 18px;
    font-weight: 700;
    min-width: 80px;
}}
QMessageBox QPushButton:hover {{
    background-color: {PRIMARY_LIGHT};
}}

/* ── Splitter ── */
QSplitter::handle {{
    background-color: {BORDER_GOLD};
}}
QSplitter::handle:horizontal {{
    width: 1px;
}}
QSplitter::handle:vertical {{
    height: 1px;
}}

/* ── ScrollArea ── */
QScrollArea {{
    border: none;
    background-color: {BG_BASE};
}}

/* ── Slider ── */
QSlider::groove:horizontal {{
    background: {BG_SURFACE};
    height: 4px;
    border-radius: 2px;
    border: 1px solid {BORDER};
}}
QSlider::handle:horizontal {{
    background: {PRIMARY};
    width: 14px;
    height: 14px;
    border-radius: 7px;
    margin: -5px 0;
}}
QSlider::handle:horizontal:hover {{
    background: {PRIMARY_LIGHT};
}}

/* ── ToolTip ── */
QToolTip {{
    background-color: {BG_ELEVATED};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_GOLD};
    border-radius: {RADIUS_SM};
    padding: 4px 8px;
    font-size: 11px;
}}

/* ── Label ── */
QLabel {{
    color: {TEXT_PRIMARY};
    background: transparent;
}}

/* ── Frame ── */
QFrame[frameShape="4"], QFrame[frameShape="5"] {{
    color: {BORDER_GOLD};
}}
"""


# ── Button Helpers ────────────────────────────────────────────

def btn_primary(extra=""):
    """Tombol utama — background emas, teks gelap."""
    return f"""
        QPushButton {{
            background-color: {PRIMARY};
            color: {BG_BASE};
            border: none;
            border-radius: {RADIUS_SM};
            padding: 8px 18px;
            font-weight: 700;
            font-size: 12px;
            {extra}
        }}
        QPushButton:hover {{
            background-color: {PRIMARY_LIGHT};
        }}
        QPushButton:pressed {{
            background-color: {PRIMARY_DARK};
        }}
        QPushButton:disabled {{
            background-color: {BORDER};
            color: {TEXT_DIM};
        }}
    """


def btn_secondary(extra=""):
    """Tombol outline emas — transparan dengan border gold."""
    return f"""
        QPushButton {{
            background-color: transparent;
            color: {PRIMARY};
            border: 1px solid {PRIMARY};
            border-radius: {RADIUS_SM};
            padding: 7px 18px;
            font-weight: 600;
            font-size: 12px;
            {extra}
        }}
        QPushButton:hover {{
            background-color: {PRIMARY};
            color: {BG_BASE};
        }}
        QPushButton:pressed {{
            background-color: {PRIMARY_DARK};
            color: {BG_BASE};
        }}
        QPushButton:disabled {{
            border-color: {BORDER};
            color: {TEXT_DIM};
        }}
    """


def btn_success(extra=""):
    """Tombol sukses — hijau."""
    return f"""
        QPushButton {{
            background-color: {SUCCESS};
            color: white;
            border: none;
            border-radius: {RADIUS_SM};
            padding: 8px 18px;
            font-weight: 700;
            font-size: 12px;
            {extra}
        }}
        QPushButton:hover {{ background-color: {SUCCESS_DARK}; }}
        QPushButton:pressed {{ background-color: {SUCCESS_DARK}; }}
        QPushButton:disabled {{ background-color: {BORDER}; color: {TEXT_DIM}; }}
    """


def btn_danger(extra=""):
    """Tombol bahaya — merah."""
    return f"""
        QPushButton {{
            background-color: {ERROR};
            color: white;
            border: none;
            border-radius: {RADIUS_SM};
            padding: 8px 18px;
            font-weight: 700;
            font-size: 12px;
            {extra}
        }}
        QPushButton:hover {{ background-color: {ERROR_DARK}; }}
        QPushButton:pressed {{ background-color: {ERROR_DARK}; }}
        QPushButton:disabled {{ background-color: {BORDER}; color: {TEXT_DIM}; }}
    """


def btn_ghost(extra=""):
    """Tombol ghost — transparan, subtle."""
    return f"""
        QPushButton {{
            background-color: {BG_ELEVATED};
            color: {TEXT_MUTED};
            border: 1px solid {BORDER};
            border-radius: {RADIUS_SM};
            padding: 7px 18px;
            font-weight: 600;
            font-size: 12px;
            {extra}
        }}
        QPushButton:hover {{
            border-color: {BORDER_GOLD};
            color: {TEXT_PRIMARY};
            background-color: {BG_SURFACE};
        }}
        QPushButton:pressed {{
            background-color: {BG_BASE};
        }}
        QPushButton:disabled {{
            color: {TEXT_DIM};
            border-color: {BORDER};
        }}
    """


def btn_accent(extra=""):
    """Tombol accent — kuning cerah untuk emphasis."""
    return f"""
        QPushButton {{
            background-color: {ACCENT};
            color: {BG_BASE};
            border: none;
            border-radius: {RADIUS_SM};
            padding: 8px 18px;
            font-weight: 700;
            font-size: 12px;
            {extra}
        }}
        QPushButton:hover {{ background-color: {WARNING}; }}
        QPushButton:pressed {{ background-color: {PRIMARY}; color: {BG_BASE}; }}
        QPushButton:disabled {{ background-color: {BORDER}; color: {TEXT_DIM}; }}
    """


# ── Frame / Card Helpers ──────────────────────────────────────

CARD_STYLE = f"""
    QFrame {{
        background-color: {BG_SURFACE};
        border: 1px solid {BORDER_GOLD};
        border-radius: {RADIUS};
    }}
"""

CARD_ELEVATED_STYLE = f"""
    QFrame {{
        background-color: {BG_ELEVATED};
        border: 1px solid {BORDER_GOLD};
        border-radius: {RADIUS};
    }}
"""

HEADER_FRAME_STYLE = f"""
    QFrame {{
        background-color: {BG_ELEVATED};
        border: none;
        border-bottom: 2px solid {PRIMARY};
    }}
"""


# ── Label Helpers ─────────────────────────────────────────────

def label_title(size=16):
    return f"font-size: {size}pt; font-weight: 700; color: {PRIMARY}; background: transparent;"


def label_subtitle(size=11):
    return f"font-size: {size}px; color: {TEXT_MUTED}; background: transparent;"


def label_muted(size=11):
    return f"font-size: {size}px; color: {TEXT_DIM}; background: transparent;"


def label_value(size=22):
    return f"font-size: {size}pt; font-weight: 700; color: {PRIMARY}; background: transparent;"


def label_accent(size=11):
    return f"font-size: {size}px; color: {ACCENT}; font-weight: 600; background: transparent;"


def status_badge(color=None, size=11):
    """Badge status dengan border berwarna."""
    c = color or PRIMARY
    return (
        f"color: {c}; font-weight: 600; font-size: {size}px; "
        f"padding: 4px 10px; "
        f"background-color: {BG_ELEVATED}; "
        f"border: 1px solid {c}; "
        f"border-radius: {RADIUS_SM};"
    )


# ── TextEdit Helpers ──────────────────────────────────────────

LOG_TEXTEDIT_STYLE = f"""
    QTextEdit, QPlainTextEdit {{
        background-color: {BG_ELEVATED};
        color: {TEXT_MUTED};
        border: 1px solid {BORDER_GOLD};
        border-radius: {RADIUS_SM};
        padding: 8px;
        font-family: 'Consolas', 'Courier New', monospace;
        font-size: 11px;
    }}
"""
