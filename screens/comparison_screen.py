"""Comparison Screen for the Theia Video Enhancer."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QSlider
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QImage, QPixmap
from pathlib import Path

import cv2


class VideoPlayerWidget(QFrame):
    """A self-contained video player that displays frames via QTimer + OpenCV.

    Uses cv2.VideoCapture to read frames and a QTimer to display them at
    the video's native FPS. No external multimedia dependencies required.
    """

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            "background-color: #0a0a14; border: 1px solid #2a2a4a; border-radius: 10px;"
        )
        self.setMinimumHeight(240)

        self._cap = None
        self._fps = 30.0
        self._total_frames = 0
        self._current_frame_idx = 0

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Video display label
        self.lbl_video = QLabel("No video loaded")
        self.lbl_video.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_video.setStyleSheet("color: #555; border: none;")
        self.lbl_video.setMinimumHeight(180)
        layout.addWidget(self.lbl_video, stretch=1)

        # Filename label
        self.lbl_filename = QLabel("")
        self.lbl_filename.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_filename.setStyleSheet("color: #888; font-size: 11px; border: none;")
        layout.addWidget(self.lbl_filename)

    def load_video(self, path: str):
        """Open a video file and prepare for playback.

        Args:
            path: Absolute path to the video file.
        """
        self.release()

        self._cap = cv2.VideoCapture(path)
        if not self._cap.isOpened():
            self.lbl_video.setText("Failed to load video")
            self._cap = None
            return

        self._fps = self._cap.get(cv2.CAP_PROP_FPS) or 30.0
        self._total_frames = int(self._cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self._current_frame_idx = 0

        self.lbl_filename.setText(Path(path).name)

        # Show the first frame immediately
        self._display_current_frame()

    def get_fps(self) -> float:
        """Return the video's FPS."""
        return self._fps

    def get_total_frames(self) -> int:
        """Return the total frame count."""
        return self._total_frames

    def advance_frame(self) -> bool:
        """Read and display the next frame. Returns False if video ended."""
        if self._cap is None or not self._cap.isOpened():
            return False

        success, frame = self._cap.read()
        if not success or frame is None:
            # Loop back to start
            self._cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            self._current_frame_idx = 0
            success, frame = self._cap.read()
            if not success or frame is None:
                return False

        self._current_frame_idx += 1
        self._show_frame(frame)
        return True

    def seek_to_frame(self, frame_idx: int):
        """Seek to a specific frame index and display it."""
        if self._cap is None or not self._cap.isOpened():
            return
        frame_idx = max(0, min(frame_idx, self._total_frames - 1))
        self._cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        self._current_frame_idx = frame_idx
        self._display_current_frame()

    def _display_current_frame(self):
        """Read and display the current frame."""
        if self._cap is None:
            return
        success, frame = self._cap.read()
        if success and frame is not None:
            self._show_frame(frame)
            # Seek back so advance_frame reads this position next
            self._cap.set(cv2.CAP_PROP_POS_FRAMES, self._current_frame_idx)

    def _show_frame(self, frame):
        """Convert an OpenCV frame to QPixmap and display it."""
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        bytes_per_line = ch * w
        q_img = QImage(rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(q_img)

        # Scale to fit the label while keeping aspect ratio
        scaled = pixmap.scaled(
            self.lbl_video.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.lbl_video.setPixmap(scaled)

    def release(self):
        """Release the video capture resource."""
        if self._cap is not None:
            self._cap.release()
            self._cap = None
        self._current_frame_idx = 0
        self._total_frames = 0
        self.lbl_video.setPixmap(QPixmap())
        self.lbl_video.setText("No video loaded")
        self.lbl_filename.setText("")


class ComparisonScreen(QWidget):
    """Displays side-by-side video playback after processing completes."""

    request_home = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_playing = False
        self._original_frame_accumulator = 0.0
        self._playback_timer = QTimer(self)
        self._playback_timer.timeout.connect(self._on_timer_tick)
        self.init_ui()

    def init_ui(self):
        """Build the Comparison Screen layout."""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(60, 50, 60, 30)
        self.main_layout.setSpacing(10)

        self._setup_header()
        self.main_layout.addSpacing(20)
        self._setup_main_panel()
        self.main_layout.addStretch()
        self._setup_bottom_buttons()

    # ── Header ──────────────────────────────────────────────

    def _setup_header(self):
        """Create the title and subtitle."""
        self.title_label = QLabel("Processing Complete")
        self.title_label.setObjectName("Title")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.subtitle_label = QLabel("Your enhanced video is ready")
        self.subtitle_label.setObjectName("Subtitle")
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.main_layout.addWidget(self.title_label)
        self.main_layout.addWidget(self.subtitle_label)

    # ── Main Card ───────────────────────────────────────────

    def _setup_main_panel(self):
        """Create the card with comparison panels and info."""
        self.panel_frame = QFrame()
        self.panel_frame.setObjectName("CardPanel")

        self.panel_layout = QVBoxLayout(self.panel_frame)
        self.panel_layout.setContentsMargins(35, 30, 35, 30)
        self.panel_layout.setSpacing(16)

        self._setup_comparison_section()
        self._setup_playback_controls()
        self._setup_info_section()

        # Full-width card
        container = QHBoxLayout()
        container.addStretch(1)
        container.addWidget(self.panel_frame, stretch=8)
        container.addStretch(1)

        self.main_layout.addLayout(container)

    def _setup_comparison_section(self):
        """Create the side-by-side video player panels."""
        comparison_layout = QHBoxLayout()
        comparison_layout.setSpacing(20)

        # ── Left Panel (Original) ──
        left_panel = QVBoxLayout()
        left_panel.setSpacing(8)

        lbl_left_title = QLabel("Original Video")
        lbl_left_title.setObjectName("SectionTitle")
        lbl_left_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.player_original = VideoPlayerWidget("Original")

        left_panel.addWidget(lbl_left_title)
        left_panel.addWidget(self.player_original)

        # ── Right Panel (Enhanced) ──
        right_panel = QVBoxLayout()
        right_panel.setSpacing(8)

        lbl_right_title = QLabel("Enhanced Video")
        lbl_right_title.setObjectName("SectionTitle")
        lbl_right_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.player_enhanced = VideoPlayerWidget("Enhanced")

        right_panel.addWidget(lbl_right_title)
        right_panel.addWidget(self.player_enhanced)

        comparison_layout.addLayout(left_panel)
        comparison_layout.addLayout(right_panel)

        self.panel_layout.addLayout(comparison_layout)

    def _setup_playback_controls(self):
        """Create play/pause and restart controls."""
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(16)

        controls_layout.addStretch()

        self.btn_restart = QPushButton("⏮ Restart")
        self.btn_restart.setObjectName("SecondaryButton")
        self.btn_restart.setMinimumWidth(100)
        self.btn_restart.clicked.connect(self._on_restart)
        controls_layout.addWidget(self.btn_restart)

        self.btn_play_pause = QPushButton("▶  Play")
        self.btn_play_pause.setMinimumWidth(120)
        self.btn_play_pause.clicked.connect(self._on_play_pause)
        controls_layout.addWidget(self.btn_play_pause)

        controls_layout.addStretch()

        self.panel_layout.addLayout(controls_layout)

    def _setup_info_section(self):
        """Create the metadata grid below the previews."""
        info_layout = QHBoxLayout()
        info_layout.setSpacing(20)

        # Each info item is a small vertical block
        self.lbl_orig_fps = self._make_info_label("Original FPS", "—")
        self.lbl_enh_fps = self._make_info_label("Enhanced FPS", "—")
        self.lbl_preset = self._make_info_label("Preset Used", "—")
        self.lbl_format = self._make_info_label("Output Format", "—")

        info_layout.addStretch()
        info_layout.addWidget(self.lbl_orig_fps)
        info_layout.addWidget(self.lbl_enh_fps)
        info_layout.addWidget(self.lbl_preset)
        info_layout.addWidget(self.lbl_format)
        info_layout.addStretch()

        self.panel_layout.addLayout(info_layout)

    def _make_info_label(self, title: str, value: str) -> QLabel:
        """Create a two-line info label (title + value).

        Args:
            title: The label heading (e.g., "Original FPS").
            value: The default value text.

        Returns:
            A QLabel with the combined text.
        """
        lbl = QLabel(f"{title}\n{value}")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = lbl.font()
        font.setPointSize(12)
        lbl.setFont(font)
        lbl.setMinimumWidth(140)
        return lbl

    # ── Bottom Buttons ──────────────────────────────────────

    def _setup_bottom_buttons(self):
        """Create the navigation buttons."""
        self.btn_back_home = QPushButton("Back to Home")
        self.btn_back_home.setObjectName("SecondaryButton")
        self.btn_back_home.clicked.connect(self._on_navigate_home)

        self.btn_process_another = QPushButton("Process Another Video")
        self.btn_process_another.clicked.connect(self._on_navigate_home)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(20)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_back_home)
        btn_layout.addWidget(self.btn_process_another)
        btn_layout.addStretch()

        self.main_layout.addSpacing(10)
        self.main_layout.addLayout(btn_layout)

    # ── Playback Logic ──────────────────────────────────────

    def _on_play_pause(self):
        """Toggle between play and pause."""
        if self._is_playing:
            self._pause()
        else:
            self._play()

    def _play(self):
        """Start synchronized playback of both videos."""
        # Use the enhanced video's FPS for timer (it may be 2x the original)
        fps = self.player_enhanced.get_fps() or 30.0
        interval_ms = max(1, int(1000 / fps))

        self._playback_timer.start(interval_ms)
        self._is_playing = True
        self.btn_play_pause.setText("⏸  Pause")

    def _pause(self):
        """Pause playback."""
        self._playback_timer.stop()
        self._is_playing = False
        self.btn_play_pause.setText("▶  Play")

    def _on_restart(self):
        """Restart both videos from the beginning."""
        self._pause()
        self.player_original.seek_to_frame(0)
        self.player_enhanced.seek_to_frame(0)
        self._original_frame_accumulator = 0.0

    def _on_timer_tick(self):
        """Advance both videos by one frame based on their relative FPS."""
        # The timer ticks at the enhanced video's FPS. 
        # Always advance the enhanced video.
        self.player_enhanced.advance_frame()
        
        # Calculate how many frames the original video should advance per tick
        orig_fps = self.player_original.get_fps() or 30.0
        enh_fps = self.player_enhanced.get_fps() or 30.0
        
        # Avoid division by zero
        if enh_fps <= 0:
            enh_fps = 30.0
            
        ratio = orig_fps / enh_fps
        self._original_frame_accumulator += ratio
        
        # Advance original video if we have accumulated a full frame
        frames_to_advance = int(self._original_frame_accumulator)
        for _ in range(frames_to_advance):
            self.player_original.advance_frame()
        self._original_frame_accumulator -= frames_to_advance

        # Both will auto-loop via advance_frame, so playback continues indefinitely

    def _on_navigate_home(self):
        """Stop playback and navigate home."""
        self._pause()
        self.request_home.emit()

    # ── Public API ──────────────────────────────────────────

    def set_original_fps(self, fps: str):
        """Update the original FPS info label."""
        self.lbl_orig_fps.setText(f"Original FPS\n{fps}")

    def set_enhanced_fps(self, fps: str):
        """Update the enhanced FPS info label."""
        self.lbl_enh_fps.setText(f"Enhanced FPS\n{fps}")

    def set_preset(self, preset: str):
        """Update the preset info label."""
        self.lbl_preset.setText(f"Preset Used\n{preset}")

    def set_output_format(self, fmt: str):
        """Update the output format info label."""
        self.lbl_format.setText(f"Output Format\n{fmt}")

    def set_original_video(self, path: str):
        """Load the original video for playback."""
        if path:
            self.player_original.load_video(path)

    def set_enhanced_video(self, path: str):
        """Load the enhanced video for playback."""
        if path:
            self.player_enhanced.load_video(path)

    def start_playback(self):
        """Auto-start playback after videos are loaded."""
        self._play()

    def reset(self):
        """Stop playback and restore all fields to defaults."""
        self._pause()
        self._original_frame_accumulator = 0.0
        self.player_original.release()
        self.player_enhanced.release()
        self.lbl_orig_fps.setText("Original FPS\n—")
        self.lbl_enh_fps.setText("Enhanced FPS\n—")
        self.lbl_preset.setText("Preset Used\n—")
        self.lbl_format.setText("Output Format\n—")
