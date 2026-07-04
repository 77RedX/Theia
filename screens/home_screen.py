"""Home Screen for the Theia Video Enhancer."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from pathlib import Path

import cv2


class HomeScreen(QWidget):
    """Landing page where the user selects a video to enhance."""

    request_processing = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.input_path = None
        self.detected_fps = None
        self.detected_format = None
        self.init_ui()

    def init_ui(self):
        """Build the Home Screen layout."""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(60, 50, 60, 30)
        self.main_layout.setSpacing(10)

        self._setup_header()
        self.main_layout.addSpacing(30)
        self._setup_main_panel()
        self.main_layout.addStretch()
        self._setup_footer()

    # ── Header ──────────────────────────────────────────────

    def _setup_header(self):
        """Create the title and subtitle labels."""
        self.title_label = QLabel("Theia Video Enhancer")
        self.title_label.setObjectName("Title")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.subtitle_label = QLabel("AI-Powered Video Frame Interpolation")
        self.subtitle_label.setObjectName("Subtitle")
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.main_layout.addWidget(self.title_label)
        self.main_layout.addWidget(self.subtitle_label)

    # ── Main Card ───────────────────────────────────────────

    def _setup_main_panel(self):
        """Create the central card with video selection and info."""
        self.panel_frame = QFrame()
        self.panel_frame.setObjectName("CardPanel")

        self.panel_layout = QVBoxLayout(self.panel_frame)
        self.panel_layout.setContentsMargins(50, 40, 50, 40)
        self.panel_layout.setSpacing(16)

        # ── Video info section ──
        self.lbl_section_title = QLabel("Selected Video")
        self.lbl_section_title.setObjectName("SectionTitle")
        self.lbl_section_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_filename = QLabel("No video selected")
        self.lbl_filename.setAlignment(Qt.AlignmentFlag.AlignCenter)
        filename_font = self.lbl_filename.font()
        filename_font.setPointSize(13)
        self.lbl_filename.setFont(filename_font)

        # ── Detected metadata row ──
        self.metadata_layout = QHBoxLayout()
        self.metadata_layout.setSpacing(40)

        self.lbl_fps_info = QLabel("FPS:  —")
        self.lbl_fps_info.setObjectName("Muted")
        self.lbl_fps_info.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_format_info = QLabel("Format:  —")
        self.lbl_format_info.setObjectName("Muted")
        self.lbl_format_info.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.metadata_layout.addStretch()
        self.metadata_layout.addWidget(self.lbl_fps_info)
        self.metadata_layout.addWidget(self.lbl_format_info)
        self.metadata_layout.addStretch()

        # ── Buttons ──
        self.btn_select = QPushButton("Select Video")
        self.btn_select.clicked.connect(self.select_video)

        self.btn_process = QPushButton("Start Processing")
        self.btn_process.clicked.connect(self._on_start_processing)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(20)
        button_layout.addStretch()
        button_layout.addWidget(self.btn_select)
        button_layout.addWidget(self.btn_process)
        button_layout.addStretch()

        # ── Assemble card ──
        self.panel_layout.addWidget(self.lbl_section_title)
        self.panel_layout.addWidget(self.lbl_filename)
        self.panel_layout.addLayout(self.metadata_layout)
        self.panel_layout.addSpacing(10)
        self.panel_layout.addLayout(button_layout)

        # Center the card horizontally with stretch
        container = QHBoxLayout()
        container.addStretch(1)
        container.addWidget(self.panel_frame, stretch=4)
        container.addStretch(1)

        self.main_layout.addLayout(container)

    # ── Footer ──────────────────────────────────────────────

    def _setup_footer(self):
        """Create the footer text."""
        self.footer_label = QLabel("Runs locally · No data leaves your machine")
        self.footer_label.setObjectName("Muted")
        self.footer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(self.footer_label)

    # ── Actions ─────────────────────────────────────────────

    def select_video(self):
        """Open a file dialog, detect FPS and format, and update the UI."""
        file_filter = "Video Files (*.mp4 *.mkv *.avi *.mov)"
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Video", "", file_filter
        )

        if not file_path:
            return

        self.input_path = file_path
        path = Path(file_path)

        # Update filename
        self.lbl_filename.setText(path.name)

        # Detect format from extension
        self.detected_format = path.suffix.lstrip(".").lower()
        self.lbl_format_info.setText(f"Format:  {self.detected_format.upper()}")

        # Detect FPS using OpenCV
        try:
            cap = cv2.VideoCapture(file_path)
            if cap.isOpened():
                fps = cap.get(cv2.CAP_PROP_FPS)
                self.detected_fps = round(fps, 2)
                self.lbl_fps_info.setText(f"FPS:  {self.detected_fps}")
            else:
                self.detected_fps = None
                self.lbl_fps_info.setText("FPS:  Unknown")
            cap.release()
        except Exception:
            self.detected_fps = None
            self.lbl_fps_info.setText("FPS:  Unknown")

    def _on_start_processing(self):
        """Validate selection and emit the processing signal."""
        if not self.input_path:
            QMessageBox.warning(
                self, "No Video Selected",
                "Please select a video file before starting."
            )
            return

        self.request_processing.emit()
