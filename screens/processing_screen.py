"""Processing Screen for the Theia Video Enhancer."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QProgressBar, QTextEdit, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from datetime import datetime


class ProcessingScreen(QWidget):
    """Displays real-time progress while the engine processes a video."""

    cancel_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        """Build the Processing Screen layout."""
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
        self.title_label = QLabel("Processing Video")
        self.title_label.setObjectName("Title")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.subtitle_label = QLabel("Generating intermediate frames using AI")
        self.subtitle_label.setObjectName("Subtitle")
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.main_layout.addWidget(self.title_label)
        self.main_layout.addWidget(self.subtitle_label)

    # ── Main Card ───────────────────────────────────────────

    def _setup_main_panel(self):
        """Create the card with progress, stats, and log."""
        self.panel_frame = QFrame()
        self.panel_frame.setObjectName("CardPanel")

        self.panel_layout = QVBoxLayout(self.panel_frame)
        self.panel_layout.setContentsMargins(40, 35, 40, 35)
        self.panel_layout.setSpacing(20)

        self._setup_progress_section()
        self._setup_statistics_section()
        self._setup_log_section()

        # Full-width card with side margins via stretch
        container = QHBoxLayout()
        container.addStretch(1)
        container.addWidget(self.panel_frame, stretch=6)
        container.addStretch(1)

        self.main_layout.addLayout(container)

    def _setup_progress_section(self):
        """Create the progress bar and percentage label."""
        progress_layout = QHBoxLayout()
        progress_layout.setSpacing(16)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)

        self.lbl_progress_percent = QLabel("0%")
        self.lbl_progress_percent.setObjectName("Accent")
        percent_font = self.lbl_progress_percent.font()
        percent_font.setPointSize(14)
        percent_font.setBold(True)
        self.lbl_progress_percent.setFont(percent_font)
        self.lbl_progress_percent.setMinimumWidth(50)

        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.lbl_progress_percent)

        self.panel_layout.addLayout(progress_layout)

    def _setup_statistics_section(self):
        """Create the frame count, ETA, and status labels."""
        stats_layout = QVBoxLayout()
        stats_layout.setSpacing(8)

        self.lbl_current_frame = QLabel("Current Frame:  0 / 0")
        self.lbl_eta = QLabel("Estimated Time Remaining:  Calculating...")
        self.lbl_status = QLabel("Current Status:  Preparing...")

        for lbl in [self.lbl_current_frame, self.lbl_eta, self.lbl_status]:
            font = lbl.font()
            font.setPointSize(12)
            lbl.setFont(font)
            stats_layout.addWidget(lbl)

        self.panel_layout.addLayout(stats_layout)

    def _setup_log_section(self):
        """Create the read-only processing log."""
        self.log_text_edit = QTextEdit()
        self.log_text_edit.setReadOnly(True)
        self.log_text_edit.setText("Ready to start processing...")
        self.log_text_edit.setMinimumHeight(160)
        # No inline setStyleSheet — uses global QTextEdit style from app.py

        self.panel_layout.addWidget(self.log_text_edit)

    # ── Bottom Buttons ──────────────────────────────────────

    def _setup_bottom_buttons(self):
        """Create the cancel button."""
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setObjectName("DangerButton")
        self.btn_cancel.clicked.connect(self._on_cancel)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addStretch()

        self.main_layout.addSpacing(10)
        self.main_layout.addLayout(btn_layout)

    # ── Public API ──────────────────────────────────────────

    def set_progress(self, percent: int):
        """Update the progress bar and percentage label.

        Args:
            percent: Progress value from 0 to 100.
        """
        self.progress_bar.setValue(percent)
        self.lbl_progress_percent.setText(f"{percent}%")

    def set_frame(self, current: int, total: int):
        """Update the current frame counter.

        Args:
            current: Current frame being processed.
            total: Total number of frames.
        """
        self.lbl_current_frame.setText(f"Current Frame:  {current} / {total}")

    def set_status(self, status: str):
        """Update the current status label.

        Args:
            status: Short description of the current operation.
        """
        self.lbl_status.setText(f"Current Status:  {status}")

    def set_eta(self, text: str):
        """Update the estimated time remaining label.

        Args:
            text: ETA string to display.
        """
        self.lbl_eta.setText(f"Estimated Time Remaining:  {text}")

    def append_log(self, message: str):
        """Append a timestamped message to the processing log.

        Args:
            message: Log message to display.
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text_edit.append(f"[{timestamp}] {message}")

    def reset(self):
        """Reset the screen to its initial state."""
        self.set_progress(0)
        self.set_frame(0, 0)
        self.set_eta("Calculating...")
        self.set_status("Preparing...")
        self.log_text_edit.clear()
        self.log_text_edit.setText("Ready to start processing...")

    def _on_cancel(self):
        """Handle the Cancel button click with a confirmation dialog."""
        reply = QMessageBox.question(
            self, "Cancel Processing",
            "Are you sure you want to cancel the current processing?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.cancel_requested.emit()
