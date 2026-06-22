"""
Theia Video Enhancer — Design System
Dark cinematic palette with electric violet accents.
Typography: clean, technical, futuristic.
"""

COLORS = {
    # Backgrounds
    "bg_deep":    "#0A0A0F",   # Near-black, almost space
    "bg_surface": "#111118",   # Card surfaces
    "bg_raised":  "#1A1A25",   # Elevated elements
    "bg_border":  "#252535",   # Borders / dividers

    # Accent — Electric Violet
    "accent":     "#7C3AED",   # Primary actions
    "accent_light":"#9D5CF0",  # Hover state
    "accent_dim": "#3D1F7A",   # Disabled / muted accent
    "accent_glow": "rgba(124,58,237,0.18)",  # Glow effect bg

    # Text
    "text_primary":   "#F0EFF8",  # Main text
    "text_secondary":  "#8B8BA0", # Muted / labels
    "text_disabled":   "#454558", # Greyed out

    # Status
    "success":  "#22C55E",
    "warning":  "#F59E0B",
    "error":    "#EF4444",
    "info":     "#38BDF8",
}

FONTS = {
    "display":  "font-family: 'Segoe UI', 'SF Pro Display', 'Helvetica Neue', sans-serif;",
    "mono":     "font-family: 'Cascadia Code', 'Consolas', 'Courier New', monospace;",
}

# Full application stylesheet
APP_STYLESHEET = f"""
    /* ── Global ── */
    QWidget {{
        background-color: {COLORS['bg_deep']};
        color: {COLORS['text_primary']};
        font-family: 'Segoe UI', 'SF Pro Display', 'Helvetica Neue', sans-serif;
        font-size: 14px;
    }}

    QMainWindow {{
        background-color: {COLORS['bg_deep']};
    }}

    /* ── Buttons ── */
    QPushButton {{
        background-color: {COLORS['accent']};
        color: #FFFFFF;
        border: none;
        border-radius: 8px;
        padding: 10px 24px;
        font-size: 14px;
        font-weight: 600;
        letter-spacing: 0.3px;
    }}
    QPushButton:hover {{
        background-color: {COLORS['accent_light']};
    }}
    QPushButton:pressed {{
        background-color: {COLORS['accent_dim']};
        padding-top: 11px;
        padding-bottom: 9px;
    }}
    QPushButton:disabled {{
        background-color: {COLORS['bg_raised']};
        color: {COLORS['text_disabled']};
    }}

    /* ── Secondary Button ── */
    QPushButton[secondary="true"] {{
        background-color: transparent;
        color: {COLORS['accent_light']};
        border: 1.5px solid {COLORS['accent']};
        border-radius: 8px;
    }}
    QPushButton[secondary="true"]:hover {{
        background-color: {COLORS['accent_glow']};
    }}

    /* ── Labels ── */
    QLabel {{
        color: {COLORS['text_primary']};
        background-color: transparent;
    }}

    /* ── Progress Bar ── */
    QProgressBar {{
        background-color: {COLORS['bg_raised']};
        border-radius: 6px;
        border: none;
        height: 12px;
        text-align: center;
        color: transparent;
    }}
    QProgressBar::chunk {{
        background: qlineargradient(
            x1:0, y1:0, x2:1, y2:0,
            stop:0 {COLORS['accent']},
            stop:1 {COLORS['accent_light']}
        );
        border-radius: 6px;
    }}

    /* ── TextEdit / Log ── */
    QTextEdit {{
        background-color: {COLORS['bg_surface']};
        color: {COLORS['text_secondary']};
        border: 1px solid {COLORS['bg_border']};
        border-radius: 8px;
        padding: 10px;
        font-family: 'Cascadia Code', 'Consolas', monospace;
        font-size: 12px;
    }}

    /* ── ComboBox ── */
    QComboBox {{
        background-color: {COLORS['bg_raised']};
        color: {COLORS['text_primary']};
        border: 1.5px solid {COLORS['bg_border']};
        border-radius: 8px;
        padding: 8px 14px;
        font-size: 14px;
        min-width: 160px;
    }}
    QComboBox:hover {{
        border-color: {COLORS['accent']};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 32px;
    }}
    QComboBox::down-arrow {{
        image: none;
        width: 0;
        height: 0;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 6px solid {COLORS['text_secondary']};
    }}
    QComboBox QAbstractItemView {{
        background-color: {COLORS['bg_raised']};
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['bg_border']};
        border-radius: 8px;
        selection-background-color: {COLORS['accent']};
        padding: 4px;
    }}

    /* ── Radio Buttons ── */
    QRadioButton {{
        color: {COLORS['text_primary']};
        spacing: 10px;
        font-size: 14px;
    }}
    QRadioButton::indicator {{
        width: 18px;
        height: 18px;
        border-radius: 9px;
        border: 2px solid {COLORS['bg_border']};
        background-color: {COLORS['bg_raised']};
    }}
    QRadioButton::indicator:hover {{
        border-color: {COLORS['accent']};
    }}
    QRadioButton::indicator:checked {{
        border: 2px solid {COLORS['accent']};
        background-color: {COLORS['accent']};
    }}

    /* ── Scrollbars ── */
    QScrollBar:vertical {{
        background: {COLORS['bg_surface']};
        width: 8px;
        border-radius: 4px;
        margin: 0;
    }}
    QScrollBar::handle:vertical {{
        background: {COLORS['bg_border']};
        border-radius: 4px;
        min-height: 20px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {COLORS['accent_dim']};
    }}
    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {{
        height: 0;
    }}

    /* ── GroupBox ── */
    QGroupBox {{
        border: 1px solid {COLORS['bg_border']};
        border-radius: 10px;
        margin-top: 12px;
        padding-top: 8px;
        color: {COLORS['text_secondary']};
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 1.2px;
        text-transform: uppercase;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 0 8px;
        left: 12px;
        color: {COLORS['text_secondary']};
    }}

    /* ── Splitter ── */
    QSplitter::handle {{
        background-color: {COLORS['bg_border']};
    }}
"""
