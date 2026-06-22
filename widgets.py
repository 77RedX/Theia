"""
Theia Video Enhancer — Shared Widgets
Reusable components used across multiple screens.
"""

from PyQt6.QtWidgets import (
    QLabel, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QPainter, QColor, QPen, QBrush, QLinearGradient

from theme import COLORS


# ── Utility: make a horizontal separator line ──────────────────────────────
def make_separator():
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    line.setFixedHeight(1)
    line.setStyleSheet(f"background-color: {COLORS['bg_border']}; border: none;")
    return line


# ── Title label ────────────────────────────────────────────────────────────
class TitleLabel(QLabel):
    def __init__(self, text, size=28, color=None):
        super().__init__(text)
        font = QFont("Segoe UI", size, QFont.Weight.Bold)
        self.setFont(font)
        c = color or COLORS["text_primary"]
        self.setStyleSheet(f"color: {c}; background: transparent;")


# ── Sub-label / caption ────────────────────────────────────────────────────
class CaptionLabel(QLabel):
    def __init__(self, text, size=13):
        super().__init__(text)
        font = QFont("Segoe UI", size)
        self.setFont(font)
        self.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent;")
        self.setWordWrap(True)


# ── Card container ─────────────────────────────────────────────────────────
class Card(QFrame):
    """A dark elevated card with rounded corners."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setStyleSheet(f"""
            QFrame#card {{
                background-color: {COLORS['bg_surface']};
                border: 1px solid {COLORS['bg_border']};
                border-radius: 14px;
            }}
        """)


# ── Accent badge ───────────────────────────────────────────────────────────
class Badge(QLabel):
    """Small pill-shaped label for status or tags."""
    def __init__(self, text, color=None):
        super().__init__(text)
        c = color or COLORS["accent"]
        self.setStyleSheet(f"""
            background-color: {c}22;
            color: {c};
            border: 1px solid {c}55;
            border-radius: 10px;
            padding: 2px 10px;
            font-size: 11px;
            font-weight: 600;
        """)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)


# ── Icon button (text + emoji icon) ───────────────────────────────────────
class IconButton(QPushButton):
    """Button with an emoji/icon prefix."""
    def __init__(self, icon, label, secondary=False):
        super().__init__(f"  {icon}  {label}")
        if secondary:
            self.setProperty("secondary", True)
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {COLORS['accent_light']};
                    border: 1.5px solid {COLORS['accent']};
                    border-radius: 8px;
                    padding: 10px 24px;
                    font-size: 14px;
                    font-weight: 600;
                }}
                QPushButton:hover {{
                    background-color: {COLORS['accent_glow']};
                }}
            """)


# ── Stat block (number + label) ────────────────────────────────────────────
class StatBlock(QWidget):
    """Shows a big number with a small label below it."""
    def __init__(self, value, label, accent=False):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        color = COLORS["accent"] if accent else COLORS["text_primary"]
        val_lbl = QLabel(value)
        val_lbl.setFont(QFont("Segoe UI", 26, QFont.Weight.Bold))
        val_lbl.setStyleSheet(f"color: {color}; background: transparent;")
        val_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lbl = QLabel(label)
        lbl.setFont(QFont("Segoe UI", 11))
        lbl.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(val_lbl)
        layout.addWidget(lbl)


# ── Branded app header bar ─────────────────────────────────────────────────
class AppHeader(QWidget):
    """Top bar showing Theia logo and current screen name."""
    def __init__(self, screen_name=""):
        super().__init__()
        self.setFixedHeight(56)
        self.setStyleSheet(f"""
            background-color: {COLORS['bg_surface']};
            border-bottom: 1px solid {COLORS['bg_border']};
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 0, 24, 0)

        # Logo
        logo = QLabel("◈ THEIA")
        logo.setFont(QFont("Segoe UI", 15, QFont.Weight.ExtraBold))
        logo.setStyleSheet(f"""
            color: {COLORS['accent_light']};
            background: transparent;
            letter-spacing: 3px;
        """)

        # Screen name
        self.screen_lbl = QLabel(screen_name.upper())
        self.screen_lbl.setFont(QFont("Segoe UI", 10))
        self.screen_lbl.setStyleSheet(f"""
            color: {COLORS['text_secondary']};
            background: transparent;
            letter-spacing: 2px;
        """)

        layout.addWidget(logo)
        layout.addStretch()
        layout.addWidget(self.screen_lbl)

    def set_screen(self, name):
        self.screen_lbl.setText(name.upper())


# ── Drop zone visual widget ────────────────────────────────────────────────
class DropZoneWidget(QWidget):
    """Dashed border drop area for video upload."""
    def __init__(self, label="Drop video here", parent=None):
        super().__init__(parent)
        self._label = label
        self._hovered = False
        self.setMinimumHeight(160)
        self.setAcceptDrops(True)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Background fill
        accent_rgb = (124, 58, 237)
        alpha = 40 if self._hovered else 20
        fill_color = QColor(*accent_rgb, alpha)
        painter.setBrush(QBrush(fill_color))

        # Dashed border
        border_color = QColor(COLORS["accent"] if self._hovered else COLORS["bg_border"])
        pen = QPen(border_color, 2, Qt.PenStyle.DashLine)
        painter.setPen(pen)
        painter.drawRoundedRect(4, 4, self.width() - 8, self.height() - 8, 12, 12)

        # Icon + text
        painter.setPen(QPen(QColor(COLORS["text_secondary"])))
        icon_font = QFont("Segoe UI", 28)
        painter.setFont(icon_font)
        painter.drawText(
            self.rect().adjusted(0, -20, 0, -20),
            Qt.AlignmentFlag.AlignCenter,
            "⬆"
        )
        txt_font = QFont("Segoe UI", 13)
        painter.setFont(txt_font)
        painter.drawText(
            self.rect().adjusted(0, 40, 0, 40),
            Qt.AlignmentFlag.AlignCenter,
            self._label
        )

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            self._hovered = True
            self.update()
            event.acceptProposedAction()

    def dragLeaveEvent(self, event):
        self._hovered = False
        self.update()

    def dropEvent(self, event):
        self._hovered = False
        self.update()
        if event.mimeData().hasUrls():
            url = event.mimeData().urls()[0].toLocalFile()
            self.parent().handle_drop(url)
