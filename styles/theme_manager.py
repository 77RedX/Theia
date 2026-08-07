"""Centralized Theme Manager and Design System for Theia."""

class ThemeManager:
    """Manages design tokens and generates global QSS stylesheets."""

    # ── Design System Tokens (OLED Ultra Dark Mode) ──
    BG_BASE = "#030407"          # Pitch black / deep space canvas
    BG_SURFACE = "#090A0F"       # Primary container background
    BG_PANEL = "#0F1117"         # Elevated panel card background
    BG_PANEL_HOVER = "#181B24"   # Panel hover background
    BG_PANEL_ACTIVE = "#202533"  # Active/Selected panel state

    PRIMARY = "#3B82F6"          # Vibrant modern blue (Blue 500)
    PRIMARY_HOVER = "#60A5FA"    # Light blue (Blue 400)
    PRIMARY_PRESSED = "#2563EB"  # Deep blue (Blue 600)
    PRIMARY_GLOW = "rgba(59, 130, 246, 0.25)"

    ACCENT = "#F43F5E"           # Neon Rose / Pink Accent
    ACCENT_HOVER = "#FB7185"
    ACCENT_GLOW = "rgba(244, 63, 94, 0.25)"

    # Status Indicators
    SUCCESS = "#10B981"          # Emerald green
    SUCCESS_BG = "rgba(16, 185, 129, 0.14)"
    WARNING = "#F59E0B"          # Amber warning
    WARNING_BG = "rgba(245, 158, 11, 0.14)"
    DANGER = "#EF4444"           # Red alert
    DANGER_BG = "rgba(239, 68, 68, 0.14)"
    INFO = "#38BDF8"             # Sky blue info
    INFO_BG = "rgba(56, 189, 248, 0.14)"

    # Typography / Colors
    TEXT_PRIMARY = "#F8FAFC"     # High-contrast bright white
    TEXT_SECONDARY = "#CBD5E1"   # Soft slate body text
    TEXT_MUTED = "#94A3B8"       # Clear slate muted text
    TEXT_DISABLED = "#64748B"    # Disabled text

    # Glass & High-Contrast Borders
    BORDER = "rgba(255, 255, 255, 0.18)"
    BORDER_SUBTLE = "rgba(255, 255, 255, 0.10)"
    BORDER_ACTIVE = "#3B82F6"
    BORDER_GLOW = "rgba(59, 130, 246, 0.4)"

    # Window Title Bar Controls
    TITLEBAR_BG = "#06070B"
    BTN_HOVER_BG = "rgba(255, 255, 255, 0.10)"
    BTN_CLOSE_HOVER_BG = "#E11D48"

    # Typography Fonts
    FONT_FAMILY = '"Segoe UI Variable", "Segoe UI", "Inter", "Roboto", sans-serif'
    FONT_MONO = '"Cascadia Code", "Consolas", "Fira Code", monospace'

    @classmethod
    def generate_stylesheet(cls, scale_factor: float = 1.0) -> str:
        """Generate the global QSS stylesheet with scaled metrics."""
        
        def si(v: int) -> int:
            return max(1, int(v * scale_factor))

        return f"""
        /* ── Global Base ── */
        QMainWindow {{
            background-color: {cls.BG_BASE};
        }}
        QWidget {{
            background-color: transparent;
            font-family: {cls.FONT_FAMILY};
            color: {cls.TEXT_PRIMARY};
            font-size: {si(13)}px;
            selection-background-color: {cls.PRIMARY};
            selection-color: #FFFFFF;
        }}

        /* ── Window Title Bar & Toolbars ── */
        QToolBar {{
            background-color: {cls.BG_SURFACE};
            border-bottom: 1px solid {cls.BORDER};
            spacing: {si(6)}px;
            padding: {si(4)}px;
        }}

        /* ── Status Bar ── */
        QStatusBar {{
            background-color: {cls.BG_BASE};
            color: {cls.TEXT_SECONDARY};
            border-top: 1px solid {cls.BORDER};
            font-size: {si(12)}px;
            padding: {si(4)}px {si(10)}px;
        }}
        QStatusBar::item {{
            border: none;
        }}

        /* ── Scrollbars ── */
        QScrollBar:vertical {{
            background: {cls.BG_BASE};
            width: {si(10)}px;
            border-radius: {si(5)}px;
            margin: 0px;
        }}
        QScrollBar::handle:vertical {{
            background: {cls.BG_PANEL_HOVER};
            min-height: {si(30)}px;
            border-radius: {si(5)}px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {cls.TEXT_MUTED};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        QScrollBar:horizontal {{
            background: {cls.BG_BASE};
            height: {si(10)}px;
            border-radius: {si(5)}px;
            margin: 0px;
        }}
        QScrollBar::handle:horizontal {{
            background: {cls.BG_PANEL_HOVER};
            min-width: {si(30)}px;
            border-radius: {si(5)}px;
        }}
        QScrollBar::handle:horizontal:hover {{
            background: {cls.TEXT_MUTED};
        }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0px;
        }}

        /* ── Tooltips ── */
        QToolTip {{
            background-color: {cls.BG_PANEL};
            color: {cls.TEXT_PRIMARY};
            border: 1px solid {cls.BORDER_ACTIVE};
            border-radius: {si(6)}px;
            padding: {si(6)}px {si(10)}px;
            font-size: {si(12)}px;
        }}

        /* ── Input Fields ── */
        QLineEdit, QTextEdit, QPlainTextEdit {{
            background-color: {cls.BG_SURFACE};
            border: 1px solid {cls.BORDER};
            border-radius: {si(6)}px;
            padding: {si(8)}px {si(12)}px;
            color: {cls.TEXT_PRIMARY};
        }}
        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
            border: 1px solid {cls.PRIMARY};
            background-color: {cls.BG_PANEL};
        }}

        /* ── ComboBox ── */
        QComboBox {{
            background-color: {cls.BG_SURFACE};
            border: 1px solid {cls.BORDER};
            border-radius: {si(6)}px;
            padding: {si(6)}px {si(14)}px;
            color: {cls.TEXT_PRIMARY};
            font-weight: 500;
        }}
        QComboBox:hover {{
            border: 1px solid {cls.PRIMARY};
            background-color: {cls.BG_PANEL_HOVER};
        }}
        QComboBox::drop-down {{
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: {si(24)}px;
            border-left: none;
        }}
        QComboBox QAbstractItemView {{
            background-color: {cls.BG_PANEL};
            border: 1px solid {cls.PRIMARY};
            selection-background-color: {cls.PRIMARY};
            selection-color: #FFFFFF;
            border-radius: {si(6)}px;
            padding: {si(4)}px;
        }}

        /* ── Menus ── */
        QMenuBar {{
            background-color: {cls.BG_BASE};
            color: {cls.TEXT_PRIMARY};
            border-bottom: 1px solid {cls.BORDER};
        }}
        QMenuBar::item {{
            padding: {si(6)}px {si(12)}px;
            background: transparent;
            border-radius: {si(4)}px;
        }}
        QMenuBar::item:selected {{
            background-color: {cls.BG_PANEL_HOVER};
        }}
        QMenu {{
            background-color: {cls.BG_PANEL};
            color: {cls.TEXT_PRIMARY};
            border: 1px solid {cls.BORDER};
            border-radius: {si(6)}px;
            padding: {si(4)}px;
        }}
        QMenu::item {{
            padding: {si(6)}px {si(24)}px {si(6)}px {si(12)}px;
            border-radius: {si(4)}px;
        }}
        QMenu::item:selected {{
            background-color: {cls.PRIMARY};
            color: #FFFFFF;
        }}

        /* ── Checkboxes & Radio Buttons ── */
        QCheckBox, QRadioButton {{
            color: {cls.TEXT_PRIMARY};
            spacing: {si(8)}px;
            font-weight: 500;
        }}
        QCheckBox::indicator, QRadioButton::indicator {{
            width: {si(16)}px;
            height: {si(16)}px;
        }}
        QCheckBox::indicator:unchecked, QRadioButton::indicator:unchecked {{
            border: 1px solid {cls.BORDER};
            background-color: {cls.BG_SURFACE};
            border-radius: {si(4)}px;
        }}
        QCheckBox::indicator:unchecked:hover, QRadioButton::indicator:unchecked:hover {{
            border: 1px solid {cls.PRIMARY};
        }}
        QCheckBox::indicator:checked, QRadioButton::indicator:checked {{
            border: 1px solid {cls.PRIMARY};
            background-color: {cls.PRIMARY};
            border-radius: {si(4)}px;
        }}
        """
