"""Comparison Screen (Hero VFX Review Workspace) for Theia Desktop Application."""

import cv2
import numpy as np
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QFrame, QComboBox, QSizePolicy, QSlider
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QRect, QPoint
from PyQt6.QtGui import QImage, QPixmap, QPainter, QMouseEvent, QPen, QColor, QFont

from widgets.components import (
    BaseCard, PrimaryButton, SecondaryButton, TitleLabel, SubtitleLabel, 
    SectionHeader, StatusBadge, MetadataItem
)
from styles.theme_manager import ThemeManager


class SplitVideoPlayer(QFrame):
    """Custom VFX-style split comparison video player with time-synchronized dual video playback."""

    frame_changed = pyqtSignal(int, int) # (current_frame, total_frames)

    MODE_SPLIT = "split"
    MODE_SIDE = "side"
    MODE_ORIGINAL = "original"
    MODE_ENHANCED = "enhanced"
    MODE_HEATMAP = "heatmap"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setMinimumHeight(320)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setStyleSheet(f"background-color: {ThemeManager.BG_BASE}; border: 1px solid {ThemeManager.BORDER}; border-radius: 8px;")

        self._cap_a = None
        self._cap_b = None
        self._frame_a = None
        self._frame_b = None

        self._fps_a = 30.0
        self._fps_b = 30.0
        self._total_frames_a = 0
        self._total_frames_b = 0

        self._total_frames = 0
        self._current_idx = 0
        self._current_idx_a = -1

        self.split_ratio = 0.5
        self.is_dragging = False
        self.view_mode = self.MODE_SPLIT

        self.lbl_info = QLabel("No video pair loaded", self)
        self.lbl_info.setStyleSheet(f"color: {ThemeManager.TEXT_MUTED}; border: none; font-size: 14px; background: transparent;")
        self.lbl_info.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def load_videos(self, path_a: str, path_b: str):
        """Load original (A) and enhanced (B) video streams and extract metadata."""
        self.release()
        self._cap_a = cv2.VideoCapture(path_a)
        self._cap_b = cv2.VideoCapture(path_b)

        if not self._cap_a.isOpened() or not self._cap_b.isOpened():
            self.lbl_info.setText("Failed to open video streams.")
            return

        self._fps_a = self._cap_a.get(cv2.CAP_PROP_FPS) or 30.0
        self._fps_b = self._cap_b.get(cv2.CAP_PROP_FPS) or 30.0

        self._total_frames_a = int(self._cap_a.get(cv2.CAP_PROP_FRAME_COUNT))
        self._total_frames_b = int(self._cap_b.get(cv2.CAP_PROP_FRAME_COUNT))

        self._total_frames = self._total_frames_b
        self._current_idx = 0
        self._current_idx_a = -1

        self.lbl_info.hide()
        self.seek_to_frame(0)

    def release(self):
        """Release VideoCapture instances."""
        if self._cap_a: self._cap_a.release()
        if self._cap_b: self._cap_b.release()
        self._cap_a = None
        self._cap_b = None
        self._frame_a = None
        self._frame_b = None
        self._current_idx_a = -1
        self.lbl_info.show()
        self.update()

    def advance_frame(self) -> bool:
        """Advance playback by 1 frame, synchronizing Video A to Video B's time position."""
        if not self._cap_b or not self._cap_b.isOpened():
            return False

        ret_b, f_b = self._cap_b.read()
        if not ret_b:
            self.seek_to_frame(0)
            return False

        self._frame_b = f_b
        self._current_idx += 1

        # Physical time timestamp based on Master Video B
        t = self._current_idx / max(1.0, self._fps_b)

        # Synchronized frame index for Video A
        target_a = min(int(t * self._fps_a), max(0, self._total_frames_a - 1))

        if target_a != self._current_idx_a and self._cap_a:
            if target_a == self._current_idx_a + 1:
                ret_a, f_a = self._cap_a.read()
                if ret_a:
                    self._frame_a = f_a
            else:
                self._cap_a.set(cv2.CAP_PROP_POS_FRAMES, target_a)
                ret_a, f_a = self._cap_a.read()
                if ret_a:
                    self._frame_a = f_a
            self._current_idx_a = target_a

        self.frame_changed.emit(self._current_idx, self._total_frames)
        self.update()
        return True

    def seek_to_frame(self, idx: int):
        """Seek both video streams synchronously based on physical time timestamp."""
        if not self._cap_a or not self._cap_b:
            return

        idx = max(0, min(idx, max(0, self._total_frames_b - 1)))
        self._current_idx = idx

        # Seek Master Video B
        self._cap_b.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret_b, f_b = self._cap_b.read()
        if ret_b:
            self._frame_b = f_b

        # Synchronize Video A to time t
        t = idx / max(1.0, self._fps_b)
        target_a = min(int(t * self._fps_a), max(0, self._total_frames_a - 1))

        self._cap_a.set(cv2.CAP_PROP_POS_FRAMES, target_a)
        ret_a, f_a = self._cap_a.read()
        if ret_a:
            self._frame_a = f_a
        self._current_idx_a = target_a

        self.frame_changed.emit(self._current_idx, self._total_frames_b)
        self.update()

    def _cv_to_qimage(self, cv_img):
        if cv_img is None: return QImage()
        rgb = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        return QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888).copy()

    def _generate_heatmap(self, f_a, f_b):
        """Generate pixel-level difference heatmap."""
        if f_a.shape != f_b.shape:
            f_a = cv2.resize(f_a, (f_b.shape[1], f_b.shape[0]))
        diff = cv2.absdiff(f_a, f_b)
        gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
        heatmap = cv2.applyColorMap(gray, cv2.COLORMAP_JET)
        return cv2.addWeighted(heatmap, 0.6, f_b, 0.4, 0)

    # ── Canvas Paint Event ──

    def paintEvent(self, event):
        super().paintEvent(event)
        if self._frame_a is None or self._frame_b is None:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        w, h = self.width(), self.height()
        f_a = self._frame_a
        f_b = self._frame_b

        if self.view_mode == self.MODE_HEATMAP:
            disp = self._generate_heatmap(f_a, f_b)
            img = self._cv_to_qimage(disp)
            pix = QPixmap.fromImage(img).scaled(w, h, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            x_off = (w - pix.width()) // 2
            y_off = (h - pix.height()) // 2
            painter.drawPixmap(x_off, y_off, pix)

            self._draw_label_overlay(painter, "HEATMAP DIFFERENCE OVERLAY", x_off + 16, y_off + 24)
            return

        if self.view_mode == self.MODE_ORIGINAL:
            img_a = self._cv_to_qimage(f_a)
            pix_a = QPixmap.fromImage(img_a).scaled(w, h, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            x_off = (w - pix_a.width()) // 2
            y_off = (h - pix_a.height()) // 2
            painter.drawPixmap(x_off, y_off, pix_a)

            self._draw_label_overlay(painter, "ORIGINAL INPUT (SOURCE)", x_off + 16, y_off + 24)
            return

        if self.view_mode == self.MODE_ENHANCED:
            img_b = self._cv_to_qimage(f_b)
            pix_b = QPixmap.fromImage(img_b).scaled(w, h, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            x_off = (w - pix_b.width()) // 2
            y_off = (h - pix_b.height()) // 2
            painter.drawPixmap(x_off, y_off, pix_b)

            self._draw_label_overlay(painter, "ENHANCED OUTPUT (AI RENDER)", x_off + 16, y_off + 24)
            return

        if self.view_mode == self.MODE_SIDE:
            half_w = w // 2
            img_a = self._cv_to_qimage(f_a)
            img_b = self._cv_to_qimage(f_b)

            pix_a = QPixmap.fromImage(img_a).scaled(half_w, h, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            pix_b = QPixmap.fromImage(img_b).scaled(half_w, h, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

            painter.drawPixmap(0, (h - pix_a.height()) // 2, pix_a)
            painter.drawPixmap(half_w, (h - pix_b.height()) // 2, pix_b)

            self._draw_label_overlay(painter, "ORIGINAL A", 16, 24)
            self._draw_label_overlay(painter, "ENHANCED B", half_w + 16, 24)
            return

        # Default: MODE_SPLIT
        img_a = self._cv_to_qimage(f_a)
        img_b = self._cv_to_qimage(f_b)

        pix_a = QPixmap.fromImage(img_a).scaled(w, h, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.FastTransformation)
        pix_b = QPixmap.fromImage(img_b).scaled(w, h, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.FastTransformation)

        x_off = (w - pix_a.width()) // 2
        y_off = (h - pix_a.height()) // 2

        # Render B fully
        painter.drawPixmap(x_off, y_off, pix_b)

        # Render A clipped by split_ratio
        split_x = int(pix_a.width() * self.split_ratio)
        source_rect = QRect(0, 0, split_x, pix_a.height())
        target_rect = QRect(x_off, y_off, split_x, pix_a.height())
        painter.drawPixmap(target_rect, pix_a, source_rect)

        # Draw vertical split slider line
        pen = QPen(QColor(ThemeManager.PRIMARY))
        pen.setWidth(2)
        painter.setPen(pen)
        line_x = x_off + split_x
        painter.drawLine(line_x, y_off, line_x, y_off + pix_a.height())

        # Badges
        self._draw_label_overlay(painter, "[ ORIGINAL A ]", x_off + 16, y_off + 28)
        self._draw_label_overlay(painter, "[ ENHANCED B ]", x_off + pix_a.width() - 120, y_off + 28)

    def _draw_label_overlay(self, painter: QPainter, text: str, x: int, y: int):
        painter.save()
        font = QFont("Segoe UI", 10, QFont.Weight.Bold)
        painter.setFont(font)
        
        fm = painter.fontMetrics()
        txt_w = fm.horizontalAdvance(text)
        painter.fillRect(x - 6, y - 16, txt_w + 12, 20, QColor(0, 0, 0, 160))

        painter.setPen(QColor(ThemeManager.TEXT_PRIMARY))
        painter.drawText(x, y - 2, text)
        painter.restore()

    # ── Mouse Dragging ──

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = True
            self._update_split(event.pos().x())

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.is_dragging:
            self._update_split(event.pos().x())

    def mouseReleaseEvent(self, event: QMouseEvent):
        self.is_dragging = False

    def _update_split(self, x: int):
        w = self.width()
        self.split_ratio = max(0.0, min(1.0, x / max(1, w)))
        self.update()


class ComparisonScreen(QWidget):
    """VFX Review Workspace Screen."""

    request_home = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_playing = False
        self._scale = 1.0
        self.playback_speed = 1.0

        self.original_path = None
        self.enhanced_path = None

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_tick)
        self.init_ui()

    def si(self, v: int) -> int:
        return max(1, int(v * self._scale))

    def init_ui(self):
        """Build review workspace layout."""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(self.si(20), self.si(16), self.si(20), self.si(16))
        self.main_layout.setSpacing(self.si(12))

        # ── Header Bar ──
        header = QHBoxLayout()
        header.setSpacing(self.si(12))

        title_layout = QVBoxLayout()
        title_layout.setSpacing(self.si(2))
        title_layout.addWidget(TitleLabel("Review Workspace", self._scale))
        title_layout.addWidget(SubtitleLabel("Compare original source against enhanced neural output.", self._scale))
        header.addLayout(title_layout)

        header.addStretch()

        # View Mode Selector Dropdown
        header.addWidget(QLabel("View Mode:"))
        self.combo_view_mode = QComboBox()
        self.combo_view_mode.addItem("Split Comparison A/B", userData=SplitVideoPlayer.MODE_SPLIT)
        self.combo_view_mode.addItem("Side-by-Side View", userData=SplitVideoPlayer.MODE_SIDE)
        self.combo_view_mode.addItem("Original Only", userData=SplitVideoPlayer.MODE_ORIGINAL)
        self.combo_view_mode.addItem("Enhanced Only", userData=SplitVideoPlayer.MODE_ENHANCED)
        self.combo_view_mode.addItem("Heatmap Difference", userData=SplitVideoPlayer.MODE_HEATMAP)
        self.combo_view_mode.currentIndexChanged.connect(self._on_view_mode_changed)

        header.addWidget(self.combo_view_mode)

        self.main_layout.addLayout(header)

        # ── VFX Split Video Player ──
        self.viewer = SplitVideoPlayer()
        self.viewer.frame_changed.connect(self._on_viewer_frame_changed)
        self.main_layout.addWidget(self.viewer, stretch=1)

        # ── Interactive Timeline Seek Scrub Slider ──
        self.timeline_slider = QSlider(Qt.Orientation.Horizontal)
        self.timeline_slider.setRange(0, 100)
        self.timeline_slider.setValue(0)
        self.timeline_slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                height: {self.si(6)}px;
                background: {ThemeManager.BG_SURFACE};
                border: 1px solid {ThemeManager.BORDER};
                border-radius: {self.si(3)}px;
            }}
            QSlider::sub-page:horizontal {{
                background: {ThemeManager.PRIMARY};
                border-radius: {self.si(3)}px;
            }}
            QSlider::handle:horizontal {{
                background: {ThemeManager.TEXT_PRIMARY};
                border: 1px solid {ThemeManager.PRIMARY};
                width: {self.si(14)}px;
                margin-top: -{self.si(4)}px;
                margin-bottom: -{self.si(4)}px;
                border-radius: {self.si(7)}px;
            }}
        """)
        self.timeline_slider.sliderMoved.connect(self._on_timeline_seek)
        self.main_layout.addWidget(self.timeline_slider)

        # ── Transport Controls Bar ──
        self.controls_card = BaseCard(self._scale)
        c_layout = QHBoxLayout(self.controls_card)
        c_layout.setContentsMargins(self.si(20), self.si(8), self.si(20), self.si(8))
        c_layout.setSpacing(self.si(12))

        self.btn_prev = SecondaryButton("Step Back", self._scale)
        self.btn_prev.clicked.connect(self.step_prev)

        self.btn_play = PrimaryButton("Play", self._scale)
        self.btn_play.clicked.connect(self.toggle_playback)

        self.btn_next = SecondaryButton("Step Forward", self._scale)
        self.btn_next.clicked.connect(self.step_next)

        self.lbl_frame_counter = QLabel("Frame: 0 / 0")
        self.lbl_frame_counter.setStyleSheet(f"color: {ThemeManager.TEXT_MUTED}; font-size: {self.si(12)}px; font-weight: 600;")

        self.speed_combo = QComboBox()
        self.speed_combo.addItems(["0.25x", "0.5x", "1.0x", "2.0x"])
        self.speed_combo.setCurrentText("1.0x")
        self.speed_combo.currentTextChanged.connect(self._change_speed)

        c_layout.addWidget(self.btn_prev)
        c_layout.addWidget(self.btn_play)
        c_layout.addWidget(self.btn_next)
        c_layout.addSpacing(self.si(12))
        c_layout.addWidget(self.lbl_frame_counter)

        c_layout.addStretch()

        c_layout.addWidget(QLabel("Speed:"))
        c_layout.addWidget(self.speed_combo)
        c_layout.addSpacing(self.si(12))

        self.btn_home = SecondaryButton("Close Project", self._scale)
        self.btn_home.clicked.connect(self._on_close)
        c_layout.addWidget(self.btn_home)

        self.main_layout.addWidget(self.controls_card)

    # ── Public API Methods (Controller Integration) ────────────

    def load_videos(self, original_path: str, processed_path: str):
        """Load original and enhanced video streams."""
        self.original_path = original_path
        self.enhanced_path = processed_path
        self.viewer.load_videos(original_path, processed_path)
        self.timeline_slider.setRange(0, max(0, self.viewer._total_frames_b - 1))
        self._change_speed(self.speed_combo.currentText())

    def set_original_video(self, path: str):
        self.original_path = path

    def set_enhanced_video(self, path: str):
        self.enhanced_path = path

    def set_preset(self, preset: str):
        pass

    def set_output_format(self, fmt: str):
        pass

    def set_original_fps(self, fps: str):
        pass

    def set_enhanced_fps(self, fps: str):
        pass

    def start_playback(self):
        if not self._is_playing:
            self.toggle_playback()

    def toggle_playback(self):
        if self._is_playing:
            self._timer.stop()
            self.btn_play.setText("Play")
            self._is_playing = False
        else:
            self._timer.start()
            self.btn_play.setText("Pause")
            self._is_playing = True

    def step_prev(self):
        if self._is_playing: self.toggle_playback()
        self.viewer.seek_to_frame(self.viewer._current_idx - 1)

    def step_next(self):
        if self._is_playing: self.toggle_playback()
        self.viewer.advance_frame()

    # ── Event Handlers ──

    def _on_tick(self):
        if not self.viewer.advance_frame():
            self.toggle_playback()

    def _on_viewer_frame_changed(self, current: int, total: int):
        self.lbl_frame_counter.setText(f"Frame: {current} / {total}")
        self.timeline_slider.blockSignals(True)
        self.timeline_slider.setValue(current)
        self.timeline_slider.blockSignals(False)

    def _on_timeline_seek(self, value: int):
        if self._is_playing: self.toggle_playback()
        self.viewer.seek_to_frame(value)

    def _change_speed(self, text: str):
        self.playback_speed = float(text.replace("x", ""))
        fps = self.viewer._fps_b
        if fps > 0:
            interval = int(1000.0 / (fps * self.playback_speed))
            self._timer.setInterval(max(10, interval))

    def _on_view_mode_changed(self, index: int):
        mode = self.combo_view_mode.currentData()
        if mode:
            self.viewer.view_mode = mode
            self.viewer.update()

    def _on_close(self):
        self._timer.stop()
        self._is_playing = False
        self.btn_play.setText("Play")
        self.viewer.release()
        self.request_home.emit()

    def apply_scale(self, s: float):
        self._scale = s
