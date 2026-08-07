"""Batch Queue Screen for the Theia Video Enhancer."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QFrame
)
from PyQt6.QtCore import Qt

from widgets.components import BaseCard, PrimaryButton, SecondaryButton, TitleLabel, SubtitleLabel, SectionHeader
from styles.theme_manager import ThemeManager

class BatchQueueScreen(QWidget):
    """UI for managing a queue of videos to process."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._scale = 1.0
        self.init_ui()

    def init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(40, 40, 40, 40)
        self.main_layout.setSpacing(24)

        # ── Header ──
        header_layout = QHBoxLayout()
        title_layout = QVBoxLayout()
        title_layout.addWidget(TitleLabel("Batch Queue", self._scale))
        title_layout.addWidget(SubtitleLabel("Queue multiple videos for overnight processing.", self._scale))
        
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        
        self.btn_add = PrimaryButton("+ Add to Queue", self._scale)
        self.btn_clear = SecondaryButton("Clear Completed", self._scale)
        header_layout.addWidget(self.btn_clear)
        header_layout.addWidget(self.btn_add)
        
        self.main_layout.addLayout(header_layout)

        # ── Queue Table ──
        self.table_card = BaseCard(self._scale)
        card_layout = QVBoxLayout(self.table_card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Filename", "Model", "Duration", "Status", "Action"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {ThemeManager.BG_PANEL};
                border: none;
                border-radius: {int(8 * self._scale)}px;
                color: {ThemeManager.TEXT_PRIMARY};
                gridline-color: {ThemeManager.BORDER};
            }}
            QHeaderView::section {{
                background-color: {ThemeManager.BG_BASE};
                color: {ThemeManager.TEXT_MUTED};
                padding: 12px;
                border: none;
                border-bottom: 1px solid {ThemeManager.BORDER};
                border-right: 1px solid {ThemeManager.BORDER};
                font-weight: bold;
            }}
            QTableWidget::item {{
                padding: 12px;
                border-bottom: 1px solid {ThemeManager.BORDER};
            }}
        """)
        
        # Add mock data
        self._add_mock_row("interview_cam1.mp4", "Quality", "15:24", "Queued")
        self._add_mock_row("broll_city.mkv", "Fast", "02:10", "Processing (45%)")
        self._add_mock_row("wedding_dance.mp4", "Quality", "05:40", "Done")
        
        card_layout.addWidget(self.table)
        self.main_layout.addWidget(self.table_card, stretch=1)
        
        # ── Footer ──
        footer_layout = QHBoxLayout()
        self.lbl_eta = SubtitleLabel("Total Queue ETA: ~45 mins", self._scale)
        footer_layout.addWidget(self.lbl_eta)
        footer_layout.addStretch()
        
        self.btn_start = PrimaryButton("Start Queue", self._scale)
        footer_layout.addWidget(self.btn_start)
        
        self.main_layout.addLayout(footer_layout)
        
    def _add_mock_row(self, filename: str, model: str, duration: str, status: str):
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(filename))
        self.table.setItem(row, 1, QTableWidgetItem(model))
        self.table.setItem(row, 2, QTableWidgetItem(duration))
        
        item_status = QTableWidgetItem(status)
        if status == "Done":
            item_status.setForeground(Qt.GlobalColor.green)
        elif "Processing" in status:
            item_status.setForeground(Qt.GlobalColor.cyan)
        else:
            item_status.setForeground(Qt.GlobalColor.gray)
            
        self.table.setItem(row, 3, item_status)
        self.table.setItem(row, 4, QTableWidgetItem("Remove"))

    def apply_scale(self, s: float):
        self._scale = s
