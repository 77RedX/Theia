from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QProgressBar, QTextEdit, QMessageBox
)
from PyQt6.QtCore import Qt
from datetime import datetime

class ProcessingScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(40, 40, 40, 40)
        self.main_layout.setSpacing(20)

        self._setup_header()
        self._setup_main_panel()
        self._setup_bottom_buttons()
        
        self.main_layout.addStretch()

    def _setup_header(self):
        self.title_label = QLabel("Processing Video")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = self.title_label.font()
        title_font.setPointSize(24)
        title_font.setBold(True)
        self.title_label.setFont(title_font)

        self.subtitle_label = QLabel("Generating intermediate frames using AI.")
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_font = self.subtitle_label.font()
        subtitle_font.setPointSize(14)
        self.subtitle_label.setFont(subtitle_font)

        self.main_layout.addWidget(self.title_label)
        self.main_layout.addWidget(self.subtitle_label)
        self.main_layout.addSpacing(20)

    def _setup_main_panel(self):
        self.panel_frame = QFrame()
        self.panel_frame.setObjectName("CardPanel")


        self.panel_layout = QVBoxLayout(self.panel_frame)
        self.panel_layout.setContentsMargins(40, 40, 40, 40)
        self.panel_layout.setSpacing(20)

        self._setup_progress_section()
        self._setup_statistics_section()
        self._setup_log_section()

        # Center the panel horizontally
        self.panel_container_layout = QHBoxLayout()
        self.panel_container_layout.addStretch(1)
        self.panel_container_layout.addWidget(self.panel_frame, stretch=4)
        self.panel_container_layout.addStretch(1)

        self.main_layout.addLayout(self.panel_container_layout)

    def _setup_progress_section(self):
        self.progress_layout = QHBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        
        self.lbl_progress_percent = QLabel("0%")
        font = self.lbl_progress_percent.font()
        font.setBold(True)
        self.lbl_progress_percent.setFont(font)

        self.progress_layout.addWidget(self.progress_bar)
        self.progress_layout.addWidget(self.lbl_progress_percent)
        
        self.panel_layout.addLayout(self.progress_layout)

    def _setup_statistics_section(self):
        self.stats_layout = QVBoxLayout()
        self.stats_layout.setSpacing(10)

        self.lbl_current_frame = QLabel("Current Frame: 0 / 0")
        self.lbl_eta = QLabel("Estimated Time Remaining: Calculating...")
        self.lbl_status = QLabel("Current Status: Preparing...")

        for lbl in [self.lbl_current_frame, self.lbl_eta, self.lbl_status]:
            font = lbl.font()
            font.setPointSize(11)
            lbl.setFont(font)
            self.stats_layout.addWidget(lbl)

        self.panel_layout.addLayout(self.stats_layout)

    def _setup_log_section(self):
        self.log_text_edit = QTextEdit()
        self.log_text_edit.setReadOnly(True)
        self.log_text_edit.setText("Ready to start processing...")
        self.log_text_edit.setMinimumHeight(150)
        
        self.log_text_edit.setStyleSheet("background-color: white; border: 1px solid #aaa;")

        self.panel_layout.addWidget(self.log_text_edit)

    def _setup_bottom_buttons(self):
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self._on_cancel)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addStretch()

        self.main_layout.addSpacing(20)
        self.main_layout.addLayout(btn_layout)

    def set_progress(self, percent: int):
        """
        Updates the progress bar and the percentage label.
        
        Args:
            percent (int): The current progress from 0 to 100.
        """
        self.progress_bar.setValue(percent)
        self.lbl_progress_percent.setText(f"{percent}%")

    def set_frame(self, current: int, total: int):
        """
        Updates the current frame and total frames label.
        
        Args:
            current (int): The current frame being processed.
            total (int): The total number of frames.
        """
        self.lbl_current_frame.setText(f"Current Frame: {current} / {total}")

    def set_status(self, status: str):
        """
        Updates the current status label.
        
        Args:
            status (str): A short string describing what is happening.
        """
        self.lbl_status.setText(f"Current Status: {status}")

    def set_eta(self, text: str):
        """
        Updates the estimated time remaining label.
        
        Args:
            text (str): The ETA string to display.
        """
        self.lbl_eta.setText(f"Estimated Time Remaining: {text}")

    def append_log(self, message: str):
        """
        Appends a timestamped message to the processing log.
        
        Args:
            message (str): The log message to display.
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        self.log_text_edit.append(formatted_message)

    def reset(self):
        """
        Resets the screen to its initial state before processing.
        """
        self.set_progress(0)
        self.set_frame(0, 0)
        self.set_eta("Calculating...")
        self.set_status("Preparing...")
        self.log_text_edit.clear()
        self.log_text_edit.setText("Ready to start processing...")

    def _on_cancel(self):
        """Handle the Cancel button click."""
        QMessageBox.information(self, "Information", "Processing cancellation is not implemented yet.")
