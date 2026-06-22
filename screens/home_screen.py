"""
Theia Video Enhancer — Home Screen
Entry point: upload a video to begin.
"""

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFileDialog, QMessageBox, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QDragEnterEvent, QDropEvent

from theme import COLORS
from widgets import TitleLabel, CaptionLabel, Card, Badge, AppHeader, make_separator


# Supported formats
SUPPORTED_EXTS = {".mp4", ".mkv", ".avi", ".mov", ".webm", ".flv"}


class HomeScreen(QWidget):
    """
    Screen 1: Home
    User uploads a video file. Shows file info once selected.
    Emits `proceed` signal with the file path when user clicks Continue.
    """
    proceed = pyqtSignal(str)   # carries: selected video path

    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_video = None
        self._build_ui()

    # ── UI construction ────────────────────────────────────────────────────
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header bar
        self.header = AppHeader("Home")
        root.addWidget(self.header)

        # Body
        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(60, 48, 60, 48)
        body_layout.setSpacing(0)

        # ── Hero ──
        hero_lbl = QLabel("◈")
        hero_lbl.setFont(QFont("Segoe UI", 48))
        hero_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hero_lbl.setStyleSheet(f"color: {COLORS['accent']}; background: transparent;")

        title = TitleLabel("Theia Video Enhancer", size=32)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        tagline = CaptionLabel(
            "Elevate your footage with AI-powered frame interpolation.\n"
            "Turn 24 fps into 48. Turn 30 fps into 60. All locally, all private.",
            size=14
        )
        tagline.setAlignment(Qt.AlignmentFlag.AlignCenter)

        body_layout.addWidget(hero_lbl)
        body_layout.addSpacing(8)
        body_layout.addWidget(title)
        body_layout.addSpacing(10)
        body_layout.addWidget(tagline)
        body_layout.addSpacing(36)

        # ── Upload Card ──
        upload_card = Card()
        upload_layout = QVBoxLayout(upload_card)
        upload_layout.setContentsMargins(32, 28, 32, 28)
        upload_layout.setSpacing(16)

        section_label = QLabel("SELECT A VIDEO")
        section_label.setStyleSheet(f"""
            color: {COLORS['text_secondary']};
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 2px;
            background: transparent;
        """)

        # Drop zone visual
        self.drop_zone = _DropZone(parent_screen=self)
        self.drop_zone.setMinimumHeight(150)

        # Or: browse button
        self.browse_btn = QPushButton("  ⬆  Browse for Video")
        self.browse_btn.setFixedHeight(44)
        self.browse_btn.clicked.connect(self._browse_file)
        self.browse_btn.setToolTip("Supported: MP4, MKV, AVI, MOV, WEBM, FLV")

        # File info row (hidden until file selected)
        self.file_card = _FileInfoCard()
        self.file_card.hide()

        upload_layout.addWidget(section_label)
        upload_layout.addWidget(self.drop_zone)
        upload_layout.addWidget(self.browse_btn)
        upload_layout.addWidget(self.file_card)

        body_layout.addWidget(upload_card)
        body_layout.addSpacing(24)

        # ── Continue button ──
        self.continue_btn = QPushButton("Continue →")
        self.continue_btn.setFixedHeight(50)
        self.continue_btn.setEnabled(False)
        self.continue_btn.clicked.connect(self._on_continue)
        self.continue_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['accent']};
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 16px;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent_light']};
            }}
            QPushButton:disabled {{
                background-color: {COLORS['bg_raised']};
                color: {COLORS['text_disabled']};
            }}
        """)
        body_layout.addWidget(self.continue_btn)

        # ── Format badges ──
        fmt_row = QHBoxLayout()
        fmt_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        fmt_row.setSpacing(8)
        for fmt in ["MP4", "MKV", "AVI", "MOV", "WEBM"]:
            badge = Badge(fmt, COLORS["text_secondary"])
            fmt_row.addWidget(badge)
        body_layout.addSpacing(20)
        body_layout.addLayout(fmt_row)

        body_layout.addStretch()
        root.addWidget(body)

    # ── Handlers ──────────────────────────────────────────────────────────
    def _browse_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Video File",
            os.path.expanduser("~"),
            "Video Files (*.mp4 *.mkv *.avi *.mov *.webm *.flv);;All Files (*)"
        )
        if path:
            self._set_video(path)

    def _set_video(self, path):
        ext = os.path.splitext(path)[1].lower()
        if ext not in SUPPORTED_EXTS:
            QMessageBox.warning(
                self, "Unsupported Format",
                f"The file format '{ext}' is not supported.\n\n"
                f"Supported formats: {', '.join(SUPPORTED_EXTS)}"
            )
            return

        self.selected_video = path
        self.file_card.set_file(path)
        self.file_card.show()
        self.drop_zone.hide()
        self.browse_btn.setText("  ↺  Choose a Different Video")
        self.continue_btn.setEnabled(True)

    def handle_drop(self, path):
        """Called by drop zone when a file is dropped."""
        self._set_video(path)

    def _on_continue(self):
        if self.selected_video and os.path.exists(self.selected_video):
            self.proceed.emit(self.selected_video)
        else:
            QMessageBox.critical(self, "File Not Found",
                                  "The selected file no longer exists. Please choose another.")


# ── Internal helper widgets ────────────────────────────────────────────────

class _DropZone(QWidget):
    """Visual drop target."""
    def __init__(self, parent_screen=None):
        super().__init__()
        self.parent_screen = parent_screen
        self.setAcceptDrops(True)
        self._hovered = False

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon = QLabel("⬆")
        icon.setFont(QFont("Segoe UI", 32))
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet(f"color: {COLORS['accent_dim']}; background: transparent;")

        lbl = QLabel("Drop your video file here")
        lbl.setFont(QFont("Segoe UI", 14))
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent;")

        layout.addWidget(icon)
        layout.addSpacing(4)
        layout.addWidget(lbl)

        self._update_style()

    def _update_style(self):
        border_color = COLORS["accent"] if self._hovered else COLORS["bg_border"]
        bg_alpha = "30" if self._hovered else "00"
        self.setStyleSheet(f"""
            background-color: {COLORS['accent']}{bg_alpha};
            border: 2px dashed {border_color};
            border-radius: 12px;
        """)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            self._hovered = True
            self._update_style()
            event.acceptProposedAction()

    def dragLeaveEvent(self, event):
        self._hovered = False
        self._update_style()

    def dropEvent(self, event):
        self._hovered = False
        self._update_style()
        if event.mimeData().hasUrls():
            path = event.mimeData().urls()[0].toLocalFile()
            if self.parent_screen:
                self.parent_screen.handle_drop(path)


class _FileInfoCard(QWidget):
    """Shows file name, size, and a checkmark once a video is selected."""
    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"""
            background-color: {COLORS['bg_raised']};
            border: 1px solid {COLORS['bg_border']};
            border-radius: 10px;
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)

        self.icon_lbl = QLabel("🎬")
        self.icon_lbl.setFont(QFont("Segoe UI", 20))
        self.icon_lbl.setStyleSheet("background: transparent;")

        info_col = QVBoxLayout()
        info_col.setSpacing(2)

        self.name_lbl = QLabel("—")
        self.name_lbl.setFont(QFont("Segoe UI", 13, QFont.Weight.DemiBold))
        self.name_lbl.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")

        self.size_lbl = QLabel("—")
        self.size_lbl.setFont(QFont("Segoe UI", 11))
        self.size_lbl.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent;")

        info_col.addWidget(self.name_lbl)
        info_col.addWidget(self.size_lbl)

        check = QLabel("✓ Ready")
        check.setStyleSheet(f"""
            color: {COLORS['success']};
            background-color: {COLORS['success']}22;
            border: 1px solid {COLORS['success']}44;
            border-radius: 8px;
            padding: 3px 10px;
            font-size: 12px;
            font-weight: 700;
        """)

        layout.addWidget(self.icon_lbl)
        layout.addSpacing(8)
        layout.addLayout(info_col)
        layout.addStretch()
        layout.addWidget(check)

    def set_file(self, path):
        name = os.path.basename(path)
        size_bytes = os.path.getsize(path)
        size_mb = size_bytes / (1024 * 1024)
        size_str = f"{size_mb:.1f} MB" if size_mb < 1024 else f"{size_mb/1024:.2f} GB"
        self.name_lbl.setText(name)
        self.size_lbl.setText(f"{size_str}  ·  {os.path.splitext(name)[1].upper()[1:]} file")
