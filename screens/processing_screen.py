"""Processing Screen (AI Command Center) for Theia Desktop Application."""

import time
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QProgressBar, QTextEdit, QSizePolicy, QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QTextCursor

from widgets.components import (
    BaseCard, PrimaryButton, SecondaryButton, DangerButton, TitleLabel, 
    SubtitleLabel, SectionHeader, StatusBadge, PipelineBadge, MetadataItem
)
from styles.theme_manager import ThemeManager


class ProcessingScreen(QWidget):
    """Real-time processing workspace and telemetry command center."""

    cancel_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._scale = 1.0
        self._start_time = 0
        self._last_progress = 0
        self._current_frame = 0
        self._total_frames = 0
        self.init_ui()

    def si(self, v: int) -> int:
        return max(1, int(v * self._scale))

    def init_ui(self):
        """Build the Command Center layout."""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(self.si(30), self.si(24), self.si(30), self.si(24))
        self.main_layout.setSpacing(self.si(20))

        # ── Header ──
        header_layout = QVBoxLayout()
        header_layout.setSpacing(self.si(4))
        header_layout.addWidget(TitleLabel("AI Command Center", self._scale))
        header_layout.addWidget(SubtitleLabel("Processing frames through deep neural enhancement model...", self._scale))
        self.main_layout.addLayout(header_layout)

        # ── Pipeline Visualization Stepper Banner ──
        self._setup_pipeline_banner()

        # ── Telemetry & Engine Terminal Content ──
        content_layout = QHBoxLayout()
        content_layout.setSpacing(self.si(20))

        self._setup_telemetry_panel(content_layout)
        self._setup_terminal_panel(content_layout)

        self.main_layout.addLayout(content_layout, stretch=1)

        # ── Footer Controls ──
        footer_layout = QHBoxLayout()
        footer_layout.addStretch()

        self.btn_cancel = DangerButton("Cancel Processing", self._scale)
        self.btn_cancel.clicked.connect(self._on_cancel)
        footer_layout.addWidget(self.btn_cancel)

        self.main_layout.addLayout(footer_layout)

    # ── Pipeline Stepper Banner ──

    def _setup_pipeline_banner(self):
        """Build horizontal stage visualization banner."""
        self.pipeline_card = BaseCard(self._scale)
        self.pipeline_card.setMaximumHeight(self.si(70))

        layout = QHBoxLayout(self.pipeline_card)
        layout.setContentsMargins(self.si(20), 0, self.si(20), 0)
        layout.setSpacing(self.si(16))

        self.stage_decoding = PipelineBadge("1. Decoding", PipelineBadge.STATE_ACTIVE, self._scale)
        self.stage_inference = PipelineBadge("2. AI Inference", PipelineBadge.STATE_PENDING, self._scale)
        self.stage_encoding = PipelineBadge("3. Encoding", PipelineBadge.STATE_PENDING, self._scale)

        arrow1 = QLabel("›")
        arrow1.setStyleSheet(f"color: {ThemeManager.TEXT_MUTED}; font-size: {self.si(16)}px; font-weight: bold;")
        arrow2 = QLabel("›")
        arrow2.setStyleSheet(f"color: {ThemeManager.TEXT_MUTED}; font-size: {self.si(16)}px; font-weight: bold;")

        layout.addStretch()
        layout.addWidget(self.stage_decoding)
        layout.addWidget(arrow1)
        layout.addWidget(self.stage_inference)
        layout.addWidget(arrow2)
        layout.addWidget(self.stage_encoding)
        layout.addStretch()

        self.main_layout.addWidget(self.pipeline_card)

    # ── Telemetry & Progress Panel ──

    def _setup_telemetry_panel(self, parent_layout: QHBoxLayout):
        """Hardware and progress metrics panel."""
        self.telemetry_card = BaseCard(self._scale)
        self.telemetry_card.setMinimumWidth(self.si(340))
        self.telemetry_card.setMaximumWidth(self.si(420))

        layout = QVBoxLayout(self.telemetry_card)
        layout.setContentsMargins(self.si(20), self.si(20), self.si(20), self.si(20))
        layout.setSpacing(self.si(16))

        layout.addWidget(SectionHeader("Live Telemetry & Metrics", self._scale))

        # Status Badge Row
        status_row = QHBoxLayout()
        self.status_badge = StatusBadge("INITIALIZING", StatusBadge.STATE_INFO, self._scale)
        status_row.addWidget(self.status_badge)
        status_row.addStretch()
        layout.addLayout(status_row)

        # Specs Metrics Grid (2x2)
        metrics_grid = QGridLayout()
        metrics_grid.setSpacing(self.si(8))

        self.meta_frame = MetadataItem("Frame Counter", "0 / 0", self._scale)
        self.meta_eta = MetadataItem("Estimated Time", "Calculating...", self._scale)
        self.meta_fps = MetadataItem("Engine Speed", "— FPS", self._scale)
        self.meta_stage = MetadataItem("Active Stage", "Decoding", self._scale)

        metrics_grid.addWidget(self.meta_frame, 0, 0)
        metrics_grid.addWidget(self.meta_eta, 0, 1)
        metrics_grid.addWidget(self.meta_fps, 1, 0)
        metrics_grid.addWidget(self.meta_stage, 1, 1)

        layout.addLayout(metrics_grid)

        layout.addStretch()

        # Hero Percentage Readout
        self.lbl_percent = TitleLabel("0%", self._scale)
        self.lbl_percent.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.lbl_percent.setStyleSheet(f"font-size: {self.si(32)}px; font-weight: 800; color: {ThemeManager.PRIMARY}; border: none; background: transparent;")
        layout.addWidget(self.lbl_percent)

        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setMinimumHeight(self.si(14))
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {ThemeManager.BG_BASE};
                border-radius: {self.si(7)}px;
                border: 1px solid {ThemeManager.BORDER};
            }}
            QProgressBar::chunk {{
                background-color: {ThemeManager.PRIMARY};
                border-radius: {self.si(7)}px;
            }}
        """)
        layout.addWidget(self.progress_bar)

        parent_layout.addWidget(self.telemetry_card)

    # ── Terminal Log Viewer Panel ──

    def _setup_terminal_panel(self, parent_layout: QHBoxLayout):
        """Engine system log terminal."""
        self.terminal_card = BaseCard(self._scale)

        layout = QVBoxLayout(self.terminal_card)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Terminal Header Bar
        header = QFrame()
        header.setStyleSheet(f"""
            QFrame {{
                background-color: {ThemeManager.BG_SURFACE};
                border-bottom: 1px solid {ThemeManager.BORDER};
                border-top-left-radius: {self.si(10)}px;
                border-top-right-radius: {self.si(10)}px;
            }}
        """)
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(self.si(16), self.si(10), self.si(16), self.si(10))

        h_title = SectionHeader("Engine Command Terminal", self._scale)
        self.btn_clear_log = SecondaryButton("Clear Log", self._scale)
        self.btn_clear_log.setMinimumWidth(self.si(80))
        self.btn_clear_log.setFixedHeight(self.si(28))
        self.btn_clear_log.clicked.connect(self.log_text_edit_clear)

        h_layout.addWidget(h_title)
        h_layout.addStretch()
        h_layout.addWidget(self.btn_clear_log)

        layout.addWidget(header)

        # Log Output Box
        self.log_text_edit = QTextEdit()
        self.log_text_edit.setReadOnly(True)
        self.log_text_edit.setStyleSheet(f"""
            QTextEdit {{
                background-color: {ThemeManager.BG_PANEL};
                color: {ThemeManager.TEXT_SECONDARY};
                font-family: {ThemeManager.FONT_MONO};
                font-size: {self.si(12)}px;
                border: none;
                padding: {self.si(12)}px;
            }}
        """)
        layout.addWidget(self.log_text_edit)

        parent_layout.addWidget(self.terminal_card, stretch=1)

    def log_text_edit_clear(self):
        self.log_text_edit.clear()

    # ── Public API Methods (Controller Interactivity) ──────────

    def reset(self):
        """Reset workspace state for a new processing run."""
        self.progress_bar.setValue(0)
        self.lbl_percent.setText("0%")
        self.log_text_edit.clear()
        self.btn_cancel.setEnabled(True)
        self.btn_cancel.setText("Cancel Processing")

        self.set_status("Preparing...")
        self.set_eta("Calculating...")
        self.set_frame(0, 0)
        self._start_time = time.time()
        self._last_progress = 0

        self._update_pipeline_stage("Decoding")
        self.append_log("System ready. Initializing video processing pipeline...")

    def set_progress(self, percent: int):
        """Update progress bar and hero percentage readout."""
        self.progress_bar.setValue(percent)
        self.lbl_percent.setText(f"{percent}%")

    def set_eta(self, eta_text: str):
        """Update estimated time metric pill."""
        self.meta_eta.set_value(eta_text)

    def set_frame(self, current: int, total: int):
        """Update frame counter and calculate FPS."""
        self._current_frame = current
        self._total_frames = total
        self.meta_frame.set_value(f"{current} / {total}")

        if current > 0 and self._start_time > 0:
            elapsed = time.time() - self._start_time
            if elapsed > 0.5:
                fps = current / elapsed
                self.meta_fps.set_value(f"{fps:.1f} FPS")

    def set_status(self, text: str):
        """Update status badge, button state, and active pipeline stage."""
        t = text.lower()
        if "cancelling" in t:
            self.status_badge.set_state("CANCELLING", StatusBadge.STATE_WARNING)
            self.btn_cancel.setText("Cancelling...")
            self.btn_cancel.setEnabled(False)
        elif "cancel" in t:
            self.status_badge.set_state("CANCELLED", StatusBadge.STATE_WARNING)
            self.btn_cancel.setText("Cancel Processing")
            self.btn_cancel.setEnabled(True)
            self._update_pipeline_stage("Cancelled")
        elif "complete" in t or "done" in t:
            self.status_badge.set_state("COMPLETED", StatusBadge.STATE_SUCCESS)
            self._update_pipeline_stage("Completed")
            self.btn_cancel.setText("Cancel Processing")
            self.btn_cancel.setEnabled(True)
        elif "fail" in t or "error" in t:
            self.status_badge.set_state("FAILED", StatusBadge.STATE_DANGER)
            self.btn_cancel.setText("Cancel Processing")
            self.btn_cancel.setEnabled(True)
        else:
            self.status_badge.set_state(text.upper(), StatusBadge.STATE_INFO)
            self.btn_cancel.setText("Cancel Processing")
            self.btn_cancel.setEnabled(True)

        if "decod" in t or "extract" in t:
            self._update_pipeline_stage("Decoding")
        elif "infer" in t or "process" in t or "enhanc" in t or "generat" in t:
            self._update_pipeline_stage("AI Inference")
        elif "encod" in t or "mux" in t or "sav" in t:
            self._update_pipeline_stage("Encoding")

    def append_log(self, message: str):
        """Add timestamped entry to terminal log viewer."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted = f'<span style="color:{ThemeManager.TEXT_MUTED};">[{timestamp}]</span> {message}'
        self.log_text_edit.append(formatted)

        # Auto-scroll to bottom
        scrollbar = self.log_text_edit.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    # ── Internal Stage Update Helpers ──────────────────────────

    def _update_pipeline_stage(self, active_stage: str):
        """Update stage stepper badges."""
        self.meta_stage.set_value(active_stage)

        if active_stage == "Decoding":
            self.stage_decoding.set_stage_state(PipelineBadge.STATE_ACTIVE)
            self.stage_inference.set_stage_state(PipelineBadge.STATE_PENDING)
            self.stage_encoding.set_stage_state(PipelineBadge.STATE_PENDING)
        elif active_stage == "AI Inference":
            self.stage_decoding.set_stage_state(PipelineBadge.STATE_COMPLETED)
            self.stage_inference.set_stage_state(PipelineBadge.STATE_ACTIVE)
            self.stage_encoding.set_stage_state(PipelineBadge.STATE_PENDING)
        elif active_stage == "Encoding":
            self.stage_decoding.set_stage_state(PipelineBadge.STATE_COMPLETED)
            self.stage_inference.set_stage_state(PipelineBadge.STATE_COMPLETED)
            self.stage_encoding.set_stage_state(PipelineBadge.STATE_ACTIVE)
        elif active_stage == "Completed":
            self.stage_decoding.set_stage_state(PipelineBadge.STATE_COMPLETED)
            self.stage_inference.set_stage_state(PipelineBadge.STATE_COMPLETED)
            self.stage_encoding.set_stage_state(PipelineBadge.STATE_COMPLETED)
        elif active_stage == "Cancelled":
            self.stage_decoding.set_stage_state(PipelineBadge.STATE_PENDING)
            self.stage_inference.set_stage_state(PipelineBadge.STATE_PENDING)
            self.stage_encoding.set_stage_state(PipelineBadge.STATE_PENDING)

    def _on_cancel(self):
        """Emit cancellation signal and update button feedback."""
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.setText("Cancelling...")
        self.set_status("Cancelling...")
        self.cancel_requested.emit()

    def apply_scale(self, s: float):
        self._scale = s
