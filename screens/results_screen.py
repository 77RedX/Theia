"""
Theia Video Enhancer — Results Screen
Shows enhancement statistics, before/after info, and lets user export.
"""

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFileDialog, QMessageBox, QSizePolicy,
    QSpacerItem
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from theme import COLORS
from widgets import TitleLabel, CaptionLabel, Card, AppHeader, Badge, make_separator


class ResultsScreen(QWidget):
    """
    Screen 4: Results
    Emits `export_done` with saved path on successful export.
    Emits `new_video` to restart from home.
    """
    export_done = pyqtSignal(str)
    new_video   = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._output_path = None
        self._input_path  = None
        self._quality     = "Balanced"
        self._fps_label   = "30 → 60 fps"
        self._build_ui()

    # ── UI construction ────────────────────────────────────────────────────
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.header = AppHeader("Results")
        root.addWidget(self.header)

        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(60, 44, 60, 44)
        body_layout.setSpacing(20)

        # ── Success banner ──
        banner = _SuccessBanner()
        body_layout.addWidget(banner)

        # ── Stats grid ──
        stats_card = Card()
        stats_layout = QVBoxLayout(stats_card)
        stats_layout.setContentsMargins(28, 22, 28, 22)
        stats_layout.setSpacing(16)

        sec_lbl = QLabel("ENHANCEMENT SUMMARY")
        sec_lbl.setStyleSheet(f"""
            color: {COLORS['text_secondary']};
            font-size: 10px;
            font-weight: 800;
            letter-spacing: 2px;
            background: transparent;
        """)
        stats_layout.addWidget(sec_lbl)

        # Stats row
        self.stats_row = QHBoxLayout()
        self.stats_row.setSpacing(0)

        self.orig_fps_stat  = _BigStat("Original FPS",  "—")
        self.new_fps_stat   = _BigStat("Enhanced FPS",  "—", accent=True)
        self.quality_stat   = _BigStat("Quality",       "—")
        self.size_stat      = _BigStat("Output Size",   "—")

        for i, stat in enumerate([self.orig_fps_stat, self.new_fps_stat,
                                   self.quality_stat, self.size_stat]):
            self.stats_row.addWidget(stat)
            if i < 3:
                div = QFrame_div()
                self.stats_row.addWidget(div)

        stats_layout.addLayout(self.stats_row)

        body_layout.addWidget(stats_card)

        # ── Before / After comparison ──
        compare_card = Card()
        compare_layout = QVBoxLayout(compare_card)
        compare_layout.setContentsMargins(28, 22, 28, 22)
        compare_layout.setSpacing(14)

        comp_hdr = QLabel("BEFORE  /  AFTER")
        comp_hdr.setStyleSheet(f"""
            color: {COLORS['text_secondary']};
            font-size: 10px;
            font-weight: 800;
            letter-spacing: 2px;
            background: transparent;
        """)
        compare_layout.addWidget(comp_hdr)

        panels = QHBoxLayout()
        panels.setSpacing(12)

        self.before_panel = _VideoPanel("Before", "Original video")
        self.after_panel  = _VideoPanel("After",  "Enhanced video", accent=True)
        panels.addWidget(self.before_panel)
        panels.addWidget(self.after_panel)
        compare_layout.addLayout(panels)

        note = CaptionLabel(
            "Video preview will be available once multimedia support is integrated.\n"
            "Export to play the enhanced video in your media player.",
            11
        )
        note.setAlignment(Qt.AlignmentFlag.AlignCenter)
        compare_layout.addWidget(note)

        body_layout.addWidget(compare_card)

        # ── File info ──
        self.file_card = _FileCard()
        body_layout.addWidget(self.file_card)

        body_layout.addStretch()

        # ── Action buttons ──
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        self.new_btn = QPushButton("+ Enhance Another Video")
        self.new_btn.setFixedHeight(48)
        self.new_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {COLORS['accent_light']};
                border: 1.5px solid {COLORS['accent']};
                border-radius: 10px;
                font-size: 14px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent']}22;
            }}
        """)
        self.new_btn.clicked.connect(self.new_video.emit)

        self.export_btn = QPushButton("⬇  Export Enhanced Video")
        self.export_btn.setFixedHeight(48)
        self.export_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['accent']};
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 15px;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent_light']};
            }}
        """)
        self.export_btn.clicked.connect(self._on_export)

        btn_row.addWidget(self.new_btn)
        btn_row.addWidget(self.export_btn)
        body_layout.addLayout(btn_row)

        root.addWidget(body)

    # ── Public: load result data ───────────────────────────────────────────
    def set_result(self, input_path, output_path, quality, fps_label):
        self._input_path  = input_path
        self._output_path = output_path
        self._quality     = quality
        self._fps_label   = fps_label

        src_fps = fps_label.split("→")[0].strip().replace(" fps", "")
        dst_fps = fps_label.split("→")[1].strip().replace(" fps", "")

        self.orig_fps_stat.set_value(f"{src_fps} fps")
        self.new_fps_stat.set_value(f"{dst_fps} fps")
        self.quality_stat.set_value(quality)

        # Try to get file size
        try:
            size_mb = os.path.getsize(output_path) / (1024 * 1024)
            self.size_stat.set_value(f"{size_mb:.1f} MB")
        except Exception:
            self.size_stat.set_value("—")

        self.before_panel.set_label(os.path.basename(input_path))
        self.after_panel.set_label(os.path.basename(output_path))
        self.file_card.set_paths(input_path, output_path)

    # ── Export ────────────────────────────────────────────────────────────
    def _on_export(self):
        if not self._output_path or not os.path.exists(self._output_path):
            QMessageBox.critical(
                self, "Export Error",
                "The processed output file was not found.\n"
                "Please try processing the video again."
            )
            return

        default_name = os.path.splitext(os.path.basename(self._input_path))[0]
        default_name += "_theia_enhanced.mp4"

        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Enhanced Video",
            os.path.join(os.path.expanduser("~"), default_name),
            "MP4 Video (*.mp4);;MKV Video (*.mkv);;All Files (*)"
        )

        if save_path:
            try:
                import shutil
                shutil.copy2(self._output_path, save_path)
                QMessageBox.information(
                    self, "Export Successful",
                    f"Your enhanced video has been saved to:\n{save_path}"
                )
                self.export_done.emit(save_path)
            except Exception as e:
                QMessageBox.critical(
                    self, "Export Failed",
                    f"Could not save the file:\n{str(e)}"
                )


# ── Internal widgets ───────────────────────────────────────────────────────

class _SuccessBanner(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"""
            background-color: {COLORS['success']}18;
            border: 1px solid {COLORS['success']}44;
            border-radius: 12px;
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 14, 20, 14)

        icon = QLabel("✓")
        icon.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        icon.setStyleSheet(f"color: {COLORS['success']}; background: transparent;")

        col = QVBoxLayout()
        title = QLabel("Enhancement Complete")
        title.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {COLORS['success']}; background: transparent;")
        sub = QLabel("Your video has been successfully processed with Theia's AI model.")
        sub.setFont(QFont("Segoe UI", 12))
        sub.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent;")
        col.addWidget(title)
        col.addWidget(sub)

        layout.addWidget(icon)
        layout.addSpacing(10)
        layout.addLayout(col)
        layout.addStretch()


class _BigStat(QWidget):
    def __init__(self, label, value, accent=False):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        color = COLORS["accent"] if accent else COLORS["text_primary"]
        self._val = QLabel(value)
        self._val.setFont(QFont("Segoe UI", 22, QFont.Weight.ExtraBold))
        self._val.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._val.setStyleSheet(f"color: {color}; background: transparent;")

        lbl = QLabel(label.upper())
        lbl.setFont(QFont("Segoe UI", 9))
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent; letter-spacing: 1.5px;")

        layout.addWidget(self._val)
        layout.addWidget(lbl)

    def set_value(self, v):
        self._val.setText(v)


class QFrame_div(QWidget):
    """Thin vertical divider."""
    def __init__(self):
        super().__init__()
        self.setFixedWidth(1)
        self.setStyleSheet(f"background-color: {COLORS['bg_border']};")
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)


class _VideoPanel(QWidget):
    def __init__(self, tag, filename, accent=False):
        super().__init__()
        color = COLORS["accent"] if accent else COLORS["bg_border"]
        self.setStyleSheet(f"""
            background-color: {COLORS['bg_raised']};
            border: 1.5px solid {color};
            border-radius: 10px;
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        badge_color = COLORS["accent"] if accent else COLORS["text_secondary"]
        tag_lbl = QLabel(tag.upper())
        tag_lbl.setStyleSheet(f"""
            background-color: {badge_color}22;
            color: {badge_color};
            border: 1px solid {badge_color}44;
            border-radius: 8px;
            padding: 2px 10px;
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 1.5px;
        """)
        tag_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._icon = QLabel("🎬")
        self._icon.setFont(QFont("Segoe UI", 30))
        self._icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._icon.setStyleSheet("background: transparent;")

        self._name = QLabel(filename)
        self._name.setFont(QFont("Segoe UI", 11))
        self._name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._name.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent;")
        self._name.setWordWrap(True)

        note = QLabel("Preview available after integration")
        note.setFont(QFont("Segoe UI", 10))
        note.setAlignment(Qt.AlignmentFlag.AlignCenter)
        note.setStyleSheet(f"color: {COLORS['text_disabled']}; background: transparent;")

        layout.addWidget(tag_lbl)
        layout.addSpacing(12)
        layout.addWidget(self._icon)
        layout.addSpacing(6)
        layout.addWidget(self._name)
        layout.addWidget(note)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.setMinimumHeight(150)

    def set_label(self, name):
        self._name.setText(name)


class _FileCard(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"""
            background-color: {COLORS['bg_surface']};
            border: 1px solid {COLORS['bg_border']};
            border-radius: 10px;
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 14, 20, 14)
        layout.setSpacing(8)

        hdr = QLabel("OUTPUT FILE")
        hdr.setStyleSheet(f"""
            color: {COLORS['text_secondary']};
            font-size: 9px; font-weight: 800;
            letter-spacing: 2px; background: transparent;
        """)
        self._path_lbl = QLabel("—")
        self._path_lbl.setFont(QFont("Cascadia Code", 11))
        self._path_lbl.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")
        self._path_lbl.setWordWrap(True)

        layout.addWidget(hdr)
        layout.addWidget(self._path_lbl)

    def set_paths(self, inp, out):
        self._path_lbl.setText(out)
