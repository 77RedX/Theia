from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from pathlib import Path

class HomeScreen(QWidget):
    request_settings = pyqtSignal()
    request_processing = pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.input_path = None
        self.init_ui()

    def init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(40, 40, 40, 40)
        self.main_layout.setSpacing(20)

        self._setup_header()
        self._setup_main_panel()
        
        # Pushes footer to the bottom
        self.main_layout.addStretch()
        self._setup_footer()

    def _setup_header(self):
        self.title_label = QLabel("Theia Video Enhancer")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = self.title_label.font()
        title_font.setPointSize(24)
        title_font.setBold(True)
        self.title_label.setFont(title_font)

        self.subtitle_label = QLabel("AI Powered Video Frame Interpolation")
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_font = self.subtitle_label.font()
        subtitle_font.setPointSize(14)
        self.subtitle_label.setFont(subtitle_font)

        self.main_layout.addWidget(self.title_label)
        self.main_layout.addWidget(self.subtitle_label)
        self.main_layout.addSpacing(30)

    def _setup_main_panel(self):
        self.panel_frame = QFrame()
        self.panel_frame.setObjectName("CardPanel")


        self.panel_layout = QVBoxLayout(self.panel_frame)
        self.panel_layout.setContentsMargins(40, 40, 40, 40)
        self.panel_layout.setSpacing(15)

        self.lbl_selected_video_title = QLabel("Selected Video")
        self.lbl_selected_video_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_font = self.lbl_selected_video_title.font()
        lbl_font.setBold(True)
        lbl_font.setPointSize(12)
        self.lbl_selected_video_title.setFont(lbl_font)

        self.lbl_selected_video_value = QLabel("No video selected")
        self.lbl_selected_video_value.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.btn_upload = QPushButton("Upload Video")
        self.btn_upload.clicked.connect(self.select_video)
        self.btn_settings = QPushButton("Settings")
        self.btn_settings.clicked.connect(self.request_settings.emit)
        self.btn_process = QPushButton("Start Processing")
        self.btn_process.clicked.connect(self._on_start_processing)

        # Center the buttons horizontally
        self.button_layout = QHBoxLayout()
        self.button_layout.addStretch()
        
        self.v_button_layout = QVBoxLayout()
        self.v_button_layout.setSpacing(10)
        self.v_button_layout.addWidget(self.btn_upload)
        self.v_button_layout.addWidget(self.btn_settings)
        self.v_button_layout.addWidget(self.btn_process)
        
        self.button_layout.addLayout(self.v_button_layout)
        self.button_layout.addStretch()

        self.panel_layout.addWidget(self.lbl_selected_video_title)
        self.panel_layout.addWidget(self.lbl_selected_video_value)
        self.panel_layout.addSpacing(20)
        self.panel_layout.addLayout(self.button_layout)

        # Center the panel in the main layout
        self.panel_container_layout = QHBoxLayout()
        self.panel_container_layout.addStretch()
        self.panel_container_layout.addWidget(self.panel_frame)
        self.panel_container_layout.addStretch()

        self.main_layout.addLayout(self.panel_container_layout)

    def _setup_footer(self):
        self.footer_label = QLabel("Runs locally using AI frame interpolation.")
        self.footer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer_font = self.footer_label.font()
        footer_font.setPointSize(10)
        self.footer_label.setFont(footer_font)

        self.main_layout.addWidget(self.footer_label)

    def select_video(self):
        """Open a file dialog to select a video and update the UI label."""
        file_filter = "Video Files (*.mp4 *.mkv *.avi *.mov)"
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Video",
            "",
            file_filter
        )
        
        if file_path:
            self.input_path = file_path
            filename = Path(file_path).name
            self.lbl_selected_video_value.setText(filename)

    def _on_start_processing(self):
        """Handle the Start Processing button click."""
        if not self.input_path:
            QMessageBox.warning(self, "Warning", "Please select a video before continuing.")
            return
        
        self.request_processing.emit()
