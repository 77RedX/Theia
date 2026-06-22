"""
Theia Video Enhancer — Settings Screen
User selects quality preset and target FPS multiplier.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QRadioButton, QButtonGroup, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from theme import COLORS
from widgets import TitleLabel, CaptionLabel, Card, AppHeader, make_separator


# Quality presets
PRESETS = {
    "Fast": {
        "desc": "Fastest processing. Best for quick previews.",
        "icon": "⚡",
        "detail": "Lower quality interpolation. Ideal for testing.",
    },
    "Balanced": {
        "desc": "Good quality with reasonable processing time.",
        "icon": "⚖",
        "detail": "Recommended for most use cases.",
    },
    "High Quality": {
        "desc": "Maximum quality. Slower, but best results.",
        "icon": "✦",
        "detail": "Best for final exports and professional work.",
    },
}

FPS_OPTIONS = {
    "24 → 48 fps": ("24", "48", 2),
    "30 → 60 fps": ("30", "60", 2),
    "60 → 120 fps": ("60", "120", 2),
}


class SettingsScreen(QWidget):
    """
    Screen 2: Settings
    User picks quality preset + target FPS.
    Emits `proceed` with (quality, fps_label) when Start is clicked.
    Emits `back` to return to home.
    """
    proceed = pyqtSignal(str, str)   # quality, fps_label
    back    = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._selected_quality = "Balanced"
        self._selected_fps     = "30 → 60 fps"
        self._build_ui()

    # ── UI construction ────────────────────────────────────────────────────
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.header = AppHeader("Settings")
        root.addWidget(self.header)

        scroll_area = QWidget()
        scroll_layout = QVBoxLayout(scroll_area)
        scroll_layout.setContentsMargins(60, 40, 60, 40)
        scroll_layout.setSpacing(24)

        # Back button row
        back_row = QHBoxLayout()
        back_btn = QPushButton("← Back")
        back_btn.setFixedWidth(100)
        back_btn.setFixedHeight(36)
        back_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {COLORS['text_secondary']};
                border: 1px solid {COLORS['bg_border']};
                border-radius: 8px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                color: {COLORS['text_primary']};
                border-color: {COLORS['accent']};
            }}
        """)
        back_btn.clicked.connect(self.back.emit)
        back_row.addWidget(back_btn)
        back_row.addStretch()
        scroll_layout.addLayout(back_row)

        # Title
        title = TitleLabel("Enhancement Settings", size=26)
        sub   = CaptionLabel("Choose how Theia will process your video. These settings affect quality and speed.", 13)
        scroll_layout.addWidget(title)
        scroll_layout.addSpacing(4)
        scroll_layout.addWidget(sub)
        scroll_layout.addWidget(make_separator())
        scroll_layout.addSpacing(8)

        # ── Quality Preset Section ──
        quality_lbl = _SectionLabel("QUALITY PRESET")
        scroll_layout.addWidget(quality_lbl)

        self._quality_cards = {}
        self._quality_group = QButtonGroup(self)

        for name, info in PRESETS.items():
            card = _QualityCard(name, info["icon"], info["desc"], info["detail"])
            self._quality_cards[name] = card
            card.radio.toggled.connect(
                lambda checked, n=name: self._on_quality_changed(n) if checked else None
            )
            self._quality_group.addButton(card.radio)
            scroll_layout.addWidget(card)

        scroll_layout.addSpacing(8)
        scroll_layout.addWidget(make_separator())
        scroll_layout.addSpacing(8)

        # ── FPS Section ──
        fps_lbl = _SectionLabel("TARGET FRAME RATE")
        scroll_layout.addWidget(fps_lbl)

        fps_sub = CaptionLabel("Select the frame rate conversion for your video.", 12)
        scroll_layout.addWidget(fps_sub)
        scroll_layout.addSpacing(8)

        self._fps_cards = {}
        self._fps_group = QButtonGroup(self)

        fps_row = QHBoxLayout()
        fps_row.setSpacing(12)

        for label, (src, dst, mult) in FPS_OPTIONS.items():
            card = _FpsCard(label, src, dst)
            self._fps_cards[label] = card
            card.radio.toggled.connect(
                lambda checked, lbl=label: self._on_fps_changed(lbl) if checked else None
            )
            self._fps_group.addButton(card.radio)
            fps_row.addWidget(card)

        scroll_layout.addLayout(fps_row)

        scroll_layout.addSpacing(16)
        scroll_layout.addWidget(make_separator())
        scroll_layout.addSpacing(16)

        # ── Summary row (must exist before setting radio defaults) ──
        self.summary_card = _SummaryCard()
        scroll_layout.addWidget(self.summary_card)

        # Set defaults AFTER summary_card is ready (signals fire immediately)
        self._quality_cards["Balanced"].radio.setChecked(True)
        self._fps_cards["30 → 60 fps"].radio.setChecked(True)
        self._refresh_summary()

        scroll_layout.addSpacing(20)

        # ── Start button ──
        self.start_btn = QPushButton("▶  Start Enhancement")
        self.start_btn.setFixedHeight(52)
        self.start_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['accent']};
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 16px;
                font-weight: 700;
                letter-spacing: 0.5px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent_light']};
            }}
        """)
        self.start_btn.clicked.connect(self._on_start)
        scroll_layout.addWidget(self.start_btn)

        scroll_layout.addStretch()
        root.addWidget(scroll_area)

    # ── Handlers ──────────────────────────────────────────────────────────
    def _on_quality_changed(self, name):
        self._selected_quality = name
        for n, card in self._quality_cards.items():
            card.set_selected(n == name)
        self._refresh_summary()

    def _on_fps_changed(self, label):
        self._selected_fps = label
        for lbl, card in self._fps_cards.items():
            card.set_selected(lbl == label)
        self._refresh_summary()

    def _refresh_summary(self):
        self.summary_card.update_summary(self._selected_quality, self._selected_fps)

    def _on_start(self):
        self.proceed.emit(self._selected_quality, self._selected_fps)


# ── Internal helper widgets ────────────────────────────────────────────────

class _SectionLabel(QLabel):
    def __init__(self, text):
        super().__init__(text)
        self.setStyleSheet(f"""
            color: {COLORS['text_secondary']};
            font-size: 10px;
            font-weight: 800;
            letter-spacing: 2.5px;
            background: transparent;
        """)


class _QualityCard(QWidget):
    """Selectable quality preset card."""
    def __init__(self, name, icon, desc, detail):
        super().__init__()
        self._name = name
        self.setStyleSheet(self._style(False))
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)

        # Radio
        self.radio = QRadioButton()

        # Icon
        icon_lbl = QLabel(icon)
        icon_lbl.setFont(QFont("Segoe UI", 22))
        icon_lbl.setStyleSheet("background: transparent; color: inherit;")
        icon_lbl.setFixedWidth(36)

        # Text group
        text_col = QVBoxLayout()
        text_col.setSpacing(2)

        name_lbl = QLabel(name)
        name_lbl.setFont(QFont("Segoe UI", 14, QFont.Weight.DemiBold))
        name_lbl.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")

        desc_lbl = QLabel(desc)
        desc_lbl.setFont(QFont("Segoe UI", 12))
        desc_lbl.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent;")

        detail_lbl = QLabel(detail)
        detail_lbl.setFont(QFont("Segoe UI", 11))
        detail_lbl.setStyleSheet(f"color: {COLORS['text_disabled']}; background: transparent;")

        text_col.addWidget(name_lbl)
        text_col.addWidget(desc_lbl)
        text_col.addWidget(detail_lbl)

        layout.addWidget(self.radio)
        layout.addSpacing(4)
        layout.addWidget(icon_lbl)
        layout.addSpacing(6)
        layout.addLayout(text_col)
        layout.addStretch()

    def _style(self, selected):
        if selected:
            return f"""
                background-color: {COLORS['accent']}22;
                border: 1.5px solid {COLORS['accent']};
                border-radius: 12px;
            """
        return f"""
            background-color: {COLORS['bg_surface']};
            border: 1.5px solid {COLORS['bg_border']};
            border-radius: 12px;
        """

    def set_selected(self, sel):
        self.setStyleSheet(self._style(sel))

    def mousePressEvent(self, event):
        self.radio.setChecked(True)


class _FpsCard(QWidget):
    """FPS option card."""
    def __init__(self, label, src, dst):
        super().__init__()
        self.setMinimumWidth(130)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(self._style(False))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.radio = QRadioButton()
        self.radio.setStyleSheet("margin: 0 auto;")

        src_lbl = QLabel(f"{src} fps")
        src_lbl.setFont(QFont("Segoe UI", 11))
        src_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        src_lbl.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent;")

        arrow_lbl = QLabel("↓")
        arrow_lbl.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        arrow_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        arrow_lbl.setStyleSheet(f"color: {COLORS['accent']}; background: transparent;")

        dst_lbl = QLabel(f"{dst} fps")
        dst_lbl.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        dst_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dst_lbl.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")

        layout.addWidget(self.radio, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(src_lbl)
        layout.addWidget(arrow_lbl)
        layout.addWidget(dst_lbl)

    def _style(self, selected):
        if selected:
            return f"""
                background-color: {COLORS['accent']}22;
                border: 1.5px solid {COLORS['accent']};
                border-radius: 12px;
            """
        return f"""
            background-color: {COLORS['bg_surface']};
            border: 1.5px solid {COLORS['bg_border']};
            border-radius: 12px;
        """

    def set_selected(self, sel):
        self.setStyleSheet(self._style(sel))

    def mousePressEvent(self, event):
        self.radio.setChecked(True)


class _SummaryCard(QWidget):
    """Shows currently selected settings at a glance."""
    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"""
            background-color: {COLORS['bg_raised']};
            border: 1px solid {COLORS['bg_border']};
            border-radius: 10px;
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 14, 20, 14)

        icon = QLabel("📋")
        icon.setFont(QFont("Segoe UI", 18))
        icon.setStyleSheet("background: transparent;")

        col = QVBoxLayout()
        summary_hdr = QLabel("CURRENT SETTINGS")
        summary_hdr.setStyleSheet(f"""
            color: {COLORS['text_secondary']};
            font-size: 9px;
            font-weight: 800;
            letter-spacing: 2px;
            background: transparent;
        """)
        self.summary_lbl = QLabel("—")
        self.summary_lbl.setFont(QFont("Segoe UI", 13, QFont.Weight.DemiBold))
        self.summary_lbl.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")
        col.addWidget(summary_hdr)
        col.addWidget(self.summary_lbl)

        layout.addWidget(icon)
        layout.addSpacing(10)
        layout.addLayout(col)
        layout.addStretch()

    def update_summary(self, quality, fps):
        self.summary_lbl.setText(f"{quality}  ·  {fps}")
