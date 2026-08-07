"""Reusable Component Library for Theia Desktop Suite."""

from PyQt6.QtWidgets import QPushButton, QLabel, QFrame, QHBoxLayout, QVBoxLayout, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QCursor, QColor, QFont
from styles.theme_manager import ThemeManager

# ── Buttons ──

class BaseButton(QPushButton):
    """A baseline button with common scaling and styling."""
    def __init__(self, text: str = "", scale: float = 1.0, parent=None):
        super().__init__(text, parent)
        self.scale = scale
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        
    def si(self, val: int) -> int:
        return max(1, int(val * self.scale))

class PrimaryButton(BaseButton):
    """The main Call-to-Action button with subtle glow hover effect."""
    def __init__(self, text: str, scale: float = 1.0, parent=None):
        super().__init__(text, scale, parent)
        self.setMinimumHeight(self.si(36))
        self._apply_style()

    def _apply_style(self):
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {ThemeManager.PRIMARY};
                color: #FFFFFF;
                border: 1px solid {ThemeManager.PRIMARY_HOVER};
                border-radius: {self.si(6)}px;
                padding: {self.si(8)}px {self.si(20)}px;
                font-size: {self.si(13)}px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {ThemeManager.PRIMARY_HOVER};
                border: 1px solid #93C5FD;
            }}
            QPushButton:pressed {{
                background-color: {ThemeManager.PRIMARY_PRESSED};
            }}
            QPushButton:disabled {{
                background-color: {ThemeManager.BG_PANEL_HOVER};
                border: 1px solid {ThemeManager.BORDER_SUBTLE};
                color: {ThemeManager.TEXT_MUTED};
            }}
        """)

class SecondaryButton(BaseButton):
    """A high-contrast secondary button with sharp visible borders."""
    def __init__(self, text: str, scale: float = 1.0, parent=None):
        super().__init__(text, scale, parent)
        self.setMinimumHeight(self.si(34))
        self._apply_style()

    def _apply_style(self):
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: #131728;
                color: #F8FAFC;
                border: 1px solid rgba(255, 255, 255, 0.22);
                border-radius: {self.si(6)}px;
                padding: {self.si(8)}px {self.si(18)}px;
                font-size: {self.si(13)}px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: #1E2638;
                border: 1px solid {ThemeManager.PRIMARY};
                color: #FFFFFF;
            }}
            QPushButton:pressed {{
                background-color: {ThemeManager.BG_BASE};
            }}
            QPushButton:disabled {{
                background-color: {ThemeManager.BG_SURFACE};
                border: 1px solid {ThemeManager.BORDER_SUBTLE};
                color: {ThemeManager.TEXT_DISABLED};
            }}
        """)

class DangerButton(BaseButton):
    """A button for destructive actions."""
    def __init__(self, text: str, scale: float = 1.0, parent=None):
        super().__init__(text, scale, parent)
        self.setMinimumHeight(self.si(34))
        self._apply_style()

    def _apply_style(self):
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {ThemeManager.DANGER_BG};
                color: {ThemeManager.DANGER};
                border: 1px solid rgba(239, 68, 68, 0.4);
                border-radius: {self.si(6)}px;
                padding: {self.si(8)}px {self.si(18)}px;
                font-size: {self.si(13)}px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: rgba(239, 68, 68, 0.25);
                border: 1px solid rgba(239, 68, 68, 0.8);
            }}
            QPushButton:pressed {{
                background-color: rgba(239, 68, 68, 0.35);
            }}
        """)

class IconButton(BaseButton):
    """A compact icon button for headers, toolbars, and title bar."""
    def __init__(self, icon_text: str, tooltip: str = "", scale: float = 1.0, parent=None):
        super().__init__(icon_text, scale, parent)
        if tooltip:
            self.setToolTip(tooltip)
        self._apply_style()

    def _apply_style(self):
        sz = self.si(30)
        self.setFixedSize(QSize(sz, sz))
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {ThemeManager.TEXT_SECONDARY};
                border: none;
                border-radius: {self.si(4)}px;
                font-size: {self.si(14)}px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {ThemeManager.BTN_HOVER_BG};
                color: {ThemeManager.TEXT_PRIMARY};
            }}
            QPushButton:pressed {{
                background-color: {ThemeManager.BG_PANEL_HOVER};
            }}
        """)

# ── Status Badges ──

class StatusBadge(QFrame):
    """A pill-shaped badge displaying operational state (Ready, Engine Active, Error, etc.)."""

    STATE_SUCCESS = "success"
    STATE_WARNING = "warning"
    STATE_DANGER = "danger"
    STATE_INFO = "info"
    STATE_MUTED = "muted"

    def __init__(self, text: str = "READY", state: str = STATE_SUCCESS, scale: float = 1.0, parent=None):
        super().__init__(parent)
        self.scale = scale
        self._state = state
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(max(1, int(8 * scale)), max(1, int(3 * scale)), max(1, int(8 * scale)), max(1, int(3 * scale)))
        layout.setSpacing(max(1, int(6 * scale)))

        self.dot = QLabel("●")
        self.lbl_text = QLabel(text)

        layout.addWidget(self.dot)
        layout.addWidget(self.lbl_text)

        self.set_state(text, state)

    def set_state(self, text: str, state: str = STATE_SUCCESS):
        self._state = state
        self.lbl_text.setText(text.upper())

        bg_color = ThemeManager.SUCCESS_BG
        fg_color = ThemeManager.SUCCESS
        border_color = "rgba(16, 185, 129, 0.4)"

        if state == self.STATE_WARNING:
            bg_color = ThemeManager.WARNING_BG
            fg_color = ThemeManager.WARNING
            border_color = "rgba(245, 158, 11, 0.4)"
        elif state == self.STATE_DANGER:
            bg_color = ThemeManager.DANGER_BG
            fg_color = ThemeManager.DANGER
            border_color = "rgba(239, 68, 68, 0.4)"
        elif state == self.STATE_INFO:
            bg_color = ThemeManager.INFO_BG
            fg_color = ThemeManager.INFO
            border_color = "rgba(56, 189, 248, 0.4)"
        elif state == self.STATE_MUTED:
            bg_color = "rgba(255, 255, 255, 0.06)"
            fg_color = ThemeManager.TEXT_MUTED
            border_color = ThemeManager.BORDER

        r = max(1, int(10 * self.scale))
        fs = max(1, int(10 * self.scale))
        dot_fs = max(1, int(8 * self.scale))

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: {r}px;
            }}
        """)
        self.dot.setStyleSheet(f"color: {fg_color}; font-size: {dot_fs}px; border: none; background: transparent;")
        self.lbl_text.setStyleSheet(f"color: {fg_color}; font-size: {fs}px; font-weight: 700; border: none; background: transparent; letter-spacing: 0.5px;")

# ── Pipeline Badge ──

class PipelineBadge(QFrame):
    """Pipeline stage stepper badge (Pending ◯, Active ●, Completed ✓)."""

    STATE_PENDING = "pending"
    STATE_ACTIVE = "active"
    STATE_COMPLETED = "completed"

    def __init__(self, title: str, state: str = STATE_PENDING, scale: float = 1.0, parent=None):
        super().__init__(parent)
        self.scale = scale
        self.title_text = title
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(max(1, int(14 * scale)), max(1, int(6 * scale)), max(1, int(14 * scale)), max(1, int(6 * scale)))
        layout.setSpacing(max(1, int(8 * scale)))

        self.lbl_icon = QLabel("◯")
        self.lbl_title = QLabel(title)

        layout.addWidget(self.lbl_icon)
        layout.addWidget(self.lbl_title)

        self.set_stage_state(state)

    def set_stage_state(self, state: str):
        fs = max(1, int(12 * self.scale))
        r = max(1, int(14 * self.scale))

        if state == self.STATE_COMPLETED:
            self.lbl_icon.setText("✓")
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {ThemeManager.SUCCESS_BG};
                    border: 1px solid rgba(16, 185, 129, 0.4);
                    border-radius: {r}px;
                }}
            """)
            self.lbl_icon.setStyleSheet(f"color: {ThemeManager.SUCCESS}; font-size: {fs}px; font-weight: bold; background: transparent; border: none;")
            self.lbl_title.setStyleSheet(f"color: {ThemeManager.SUCCESS}; font-size: {fs}px; font-weight: 600; background: transparent; border: none;")

        elif state == self.STATE_ACTIVE:
            self.lbl_icon.setText("●")
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {ThemeManager.PRIMARY};
                    border: 1px solid {ThemeManager.PRIMARY_HOVER};
                    border-radius: {r}px;
                }}
            """)
            self.lbl_icon.setStyleSheet(f"color: #FFFFFF; font-size: {fs}px; font-weight: bold; background: transparent; border: none;")
            self.lbl_title.setStyleSheet(f"color: #FFFFFF; font-size: {fs}px; font-weight: 700; background: transparent; border: none;")

        else: # PENDING
            self.lbl_icon.setText("◯")
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {ThemeManager.BG_SURFACE};
                    border: 1px solid {ThemeManager.BORDER};
                    border-radius: {r}px;
                }}
            """)
            self.lbl_icon.setStyleSheet(f"color: {ThemeManager.TEXT_MUTED}; font-size: {fs}px; background: transparent; border: none;")
            self.lbl_title.setStyleSheet(f"color: {ThemeManager.TEXT_MUTED}; font-size: {fs}px; font-weight: 500; background: transparent; border: none;")

# ── Metadata Specification Pill ──

class MetadataItem(QFrame):
    """Key-value technical metric display pill (e.g. Resolution: 1920x1080)."""

    def __init__(self, key: str, value: str = "—", scale: float = 1.0, parent=None):
        super().__init__(parent)
        self.scale = scale
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(max(1, int(10 * scale)), max(1, int(8 * scale)), max(1, int(10 * scale)), max(1, int(8 * scale)))
        layout.setSpacing(max(1, int(2 * scale)))

        self.lbl_key = QLabel(key.upper())
        self.lbl_val = QLabel(value)

        k_fs = max(1, int(10 * scale))
        v_fs = max(1, int(12 * scale))

        self.lbl_key.setStyleSheet(f"color: {ThemeManager.TEXT_MUTED}; font-size: {k_fs}px; font-weight: 700; border: none; background: transparent;")
        self.lbl_val.setStyleSheet(f"color: {ThemeManager.TEXT_PRIMARY}; font-size: {v_fs}px; font-weight: 600; border: none; background: transparent;")

        layout.addWidget(self.lbl_key)
        layout.addWidget(self.lbl_val)

        r = max(1, int(6 * scale))
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {ThemeManager.BG_SURFACE};
                border: 1px solid {ThemeManager.BORDER};
                border-radius: {r}px;
            }}
        """)

    def set_value(self, value: str):
        self.lbl_val.setText(value)

# ── Typography Labels ──

class TitleLabel(QLabel):
    """Large hero titles."""
    def __init__(self, text: str, scale: float = 1.0, parent=None):
        super().__init__(text, parent)
        s = max(1, int(22 * scale))
        self.setStyleSheet(f"font-size: {s}px; font-weight: 700; color: {ThemeManager.TEXT_PRIMARY}; border: none; background: transparent;")

class SubtitleLabel(QLabel):
    """Secondary body text below titles."""
    def __init__(self, text: str, scale: float = 1.0, parent=None):
        super().__init__(text, parent)
        s = max(1, int(13 * scale))
        self.setStyleSheet(f"font-size: {s}px; font-weight: 400; color: {ThemeManager.TEXT_MUTED}; border: none; background: transparent;")
        
class SectionHeader(QLabel):
    """Headers for panels and sections."""
    def __init__(self, text: str, scale: float = 1.0, parent=None):
        super().__init__(text, parent)
        s = max(1, int(11 * scale))
        self.setStyleSheet(f"font-size: {s}px; font-weight: 700; color: {ThemeManager.TEXT_MUTED}; text-transform: uppercase; letter-spacing: 1px; border: none; background: transparent;")

# ── Container Cards ──

class BaseCard(QFrame):
    """Elevated surface card panel."""
    def __init__(self, scale: float = 1.0, parent=None):
        super().__init__(parent)
        self.scale = scale
        r = max(1, int(10 * scale))
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {ThemeManager.BG_PANEL};
                border: 1px solid {ThemeManager.BORDER};
                border-radius: {r}px;
            }}
        """)
