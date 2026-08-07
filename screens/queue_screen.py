"""Batch Queue Workspace Screen for Theia Desktop Application."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QProgressBar, QTableWidget, QTableWidgetItem, QHeaderView, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from widgets.components import (
    BaseCard, PrimaryButton, SecondaryButton, DangerButton, TitleLabel, 
    SubtitleLabel, SectionHeader, StatusBadge, MetadataItem
)
from styles.theme_manager import ThemeManager


class QueueScreen(QWidget):
    """Batch Queue management workspace."""

    request_home = pyqtSignal()
    request_command_center = pyqtSignal()
    item_removed = pyqtSignal(int)
    clear_queue_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._scale = 1.0
        self.init_ui()

    def si(self, v: int) -> int:
        return max(1, int(v * self._scale))

    def init_ui(self):
        """Build Batch Queue workspace layout."""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(self.si(30), self.si(24), self.si(30), self.si(24))
        self.main_layout.setSpacing(self.si(20))

        # ── Header ──
        header_layout = QHBoxLayout()
        h_title_layout = QVBoxLayout()
        h_title_layout.setSpacing(self.si(4))
        h_title_layout.addWidget(TitleLabel("Batch Queue Manager", self._scale))
        h_title_layout.addWidget(SubtitleLabel("Monitor active task progress and orchestrate queued rendering jobs.", self._scale))
        header_layout.addLayout(h_title_layout)

        header_layout.addStretch()

        self.btn_goto_cmd = PrimaryButton("Go to Command Center ➔", self._scale)
        self.btn_goto_cmd.clicked.connect(self.request_command_center.emit)
        header_layout.addWidget(self.btn_goto_cmd)

        self.main_layout.addLayout(header_layout)

        # ── Active Running Task Header Card ──
        self._setup_active_task_card()

        # ── Pending Queue Table Panel ──
        self._setup_queue_table_panel()

    def _setup_active_task_card(self):
        """Build top card displaying currently executing task."""
        self.active_card = BaseCard(self._scale)
        layout = QVBoxLayout(self.active_card)
        layout.setContentsMargins(self.si(20), self.si(16), self.si(20), self.si(16))
        layout.setSpacing(self.si(12))

        # Card Title Row
        title_row = QHBoxLayout()
        title_row.addWidget(SectionHeader("ACTIVE PROCESSING TASK", self._scale))
        title_row.addStretch()
        self.active_status_badge = StatusBadge("IDLE", StatusBadge.STATE_MUTED, self._scale)
        title_row.addWidget(self.active_status_badge)
        layout.addLayout(title_row)

        # Task Details Row
        details_row = QHBoxLayout()
        details_row.setSpacing(self.si(16))

        self.lbl_active_filename = TitleLabel("No task currently processing", self._scale)
        self.lbl_active_filename.setStyleSheet(f"font-size: {self.si(15)}px; font-weight: 600; color: {ThemeManager.TEXT_PRIMARY}; border: none; background: transparent;")

        self.active_model_pill = MetadataItem("Model Preset", "—", self._scale)
        self.active_eta_pill = MetadataItem("ETA", "—", self._scale)
        self.active_frame_pill = MetadataItem("Frames", "—", self._scale)

        details_row.addWidget(self.lbl_active_filename, stretch=2)
        details_row.addWidget(self.active_model_pill)
        details_row.addWidget(self.active_eta_pill)
        details_row.addWidget(self.active_frame_pill)

        layout.addLayout(details_row)

        # Small Progress Bar
        self.active_progress_bar = QProgressBar()
        self.active_progress_bar.setRange(0, 100)
        self.active_progress_bar.setValue(0)
        self.active_progress_bar.setTextVisible(False)
        self.active_progress_bar.setFixedHeight(self.si(8))
        self.active_progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {ThemeManager.BG_BASE};
                border-radius: {self.si(4)}px;
                border: 1px solid {ThemeManager.BORDER};
            }}
            QProgressBar::chunk {{
                background-color: {ThemeManager.PRIMARY};
                border-radius: {self.si(4)}px;
            }}
        """)
        layout.addWidget(self.active_progress_bar)

        self.main_layout.addWidget(self.active_card)

    def _setup_queue_table_panel(self):
        """Build pending queue table panel."""
        panel_card = BaseCard(self._scale)
        layout = QVBoxLayout(panel_card)
        layout.setContentsMargins(self.si(20), self.si(16), self.si(20), self.si(16))
        layout.setSpacing(self.si(12))

        header_row = QHBoxLayout()
        header_row.addWidget(SectionHeader("PENDING QUEUE JOBS", self._scale))
        header_row.addStretch()

        self.btn_clear_queue = SecondaryButton("Clear Queue", self._scale)
        self.btn_clear_queue.clicked.connect(self.clear_queue_requested.emit)
        header_row.addWidget(self.btn_clear_queue)

        layout.addLayout(header_row)

        self.queue_table = QTableWidget(0, 5)
        self.queue_table.setHorizontalHeaderLabels(["#", "Input File", "Model Preset", "Scene Cuts", "Action"])
        self.queue_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.queue_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.queue_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.queue_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.queue_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.queue_table.verticalHeader().setVisible(False)
        self.queue_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.queue_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.queue_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {ThemeManager.BG_PANEL};
                border: 1px solid {ThemeManager.BORDER};
                border-radius: {self.si(8)}px;
                color: {ThemeManager.TEXT_SECONDARY};
                gridline-color: {ThemeManager.BORDER_SUBTLE};
            }}
            QHeaderView::section {{
                background-color: {ThemeManager.BG_SURFACE};
                color: {ThemeManager.TEXT_MUTED};
                font-weight: 600;
                font-size: {self.si(11)}px;
                padding: {self.si(6)}px;
                border: none;
                border-bottom: 1px solid {ThemeManager.BORDER};
            }}
            QTableWidget::item {{
                padding: {self.si(6)}px;
                border-bottom: 1px solid {ThemeManager.BORDER_SUBTLE};
            }}
        """)

        layout.addWidget(self.queue_table, stretch=1)
        self.main_layout.addWidget(panel_card, stretch=1)

    # ── API Updates ────────────────────────────────────────────

    def update_active_task(self, filename: str, preset: str, percent: int = 0, eta: str = "—", frames: str = "—", is_running: bool = True):
        """Update the active task header card."""
        if is_running:
            self.lbl_active_filename.setText(filename)
            self.active_model_pill.set_value(preset.capitalize())
            self.active_eta_pill.set_value(eta)
            self.active_frame_pill.set_value(frames)
            self.active_progress_bar.setValue(percent)
            self.active_status_badge.set_state("PROCESSING", StatusBadge.STATE_INFO)
        else:
            self.lbl_active_filename.setText("No task currently processing")
            self.active_model_pill.set_value("—")
            self.active_eta_pill.set_value("—")
            self.active_frame_pill.set_value("—")
            self.active_progress_bar.setValue(0)
            self.active_status_badge.set_state("IDLE", StatusBadge.STATE_MUTED)

    def set_queue_items(self, queue_items: list[dict]):
        """Populate the pending queue table."""
        self.queue_table.setRowCount(0)
        for idx, item in enumerate(queue_items):
            self.queue_table.insertRow(idx)
            
            # Position #
            pos_item = QTableWidgetItem(f"{idx + 1}")
            pos_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.queue_table.setItem(idx, 0, pos_item)

            # Input filename
            filename = item.get("input_path", "")
            if filename:
                from pathlib import Path
                filename = Path(filename).name
            self.queue_table.setItem(idx, 1, QTableWidgetItem(filename))

            # Model preset
            preset = item.get("preset", "fast").capitalize()
            self.queue_table.setItem(idx, 2, QTableWidgetItem(f"{preset} Model"))

            # Scene cuts
            scene_cuts = "Enabled" if item.get("detect_scene_cuts", True) else "Disabled"
            self.queue_table.setItem(idx, 3, QTableWidgetItem(scene_cuts))

            # Action button
            btn_remove = DangerButton("Remove", self._scale)
            btn_remove.setFixedSize(self.si(70), self.si(26))
            btn_remove.clicked.connect(lambda _, row=idx: self.item_removed.emit(row))
            self.queue_table.setCellWidget(idx, 4, btn_remove)

    def apply_scale(self, s: float):
        self._scale = s
