from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from pathlib import Path

class ComparisonScreen(QWidget):
    request_home = pyqtSignal()
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
        self.title_label = QLabel("Processing Complete")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = self.title_label.font()
        title_font.setPointSize(24)
        title_font.setBold(True)
        self.title_label.setFont(title_font)

        self.subtitle_label = QLabel("Your enhanced video is ready.")
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
        self.panel_layout.setContentsMargins(30, 30, 30, 30)
        self.panel_layout.setSpacing(20)

        self._setup_comparison_section()
        self._setup_info_section()

        # Center the panel horizontally
        self.panel_container_layout = QHBoxLayout()
        self.panel_container_layout.addStretch(1)
        self.panel_container_layout.addWidget(self.panel_frame, stretch=8)
        self.panel_container_layout.addStretch(1)

        self.main_layout.addLayout(self.panel_container_layout)

    def _setup_comparison_section(self):
        self.comparison_layout = QHBoxLayout()
        self.comparison_layout.setSpacing(20)

        # Left Panel (Original)
        self.left_panel = QVBoxLayout()
        self.lbl_left_title = QLabel("Original Video")
        self.lbl_left_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = self.lbl_left_title.font()
        font.setBold(True)
        self.lbl_left_title.setFont(font)
        
        self.frame_original = QFrame()
        self.frame_original.setStyleSheet("background-color: black; border-radius: 5px;")
        self.frame_original.setMinimumHeight(250)
        self.frame_original_layout = QVBoxLayout(self.frame_original)
        self.lbl_original_preview = QLabel("Original Video Preview")
        self.lbl_original_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_original_preview.setStyleSheet("color: white;")
        self.frame_original_layout.addWidget(self.lbl_original_preview)

        self.left_panel.addWidget(self.lbl_left_title)
        self.left_panel.addWidget(self.frame_original)

        # Right Panel (Enhanced)
        self.right_panel = QVBoxLayout()
        self.lbl_right_title = QLabel("Enhanced Video")
        self.lbl_right_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_right_title.setFont(font)

        self.frame_enhanced = QFrame()
        self.frame_enhanced.setStyleSheet("background-color: black; border-radius: 5px;")
        self.frame_enhanced.setMinimumHeight(250)
        self.frame_enhanced_layout = QVBoxLayout(self.frame_enhanced)
        self.lbl_enhanced_preview = QLabel("Enhanced Video Preview")
        self.lbl_enhanced_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_enhanced_preview.setStyleSheet("color: white;")
        self.frame_enhanced_layout.addWidget(self.lbl_enhanced_preview)

        self.right_panel.addWidget(self.lbl_right_title)
        self.right_panel.addWidget(self.frame_enhanced)

        self.comparison_layout.addLayout(self.left_panel)
        self.comparison_layout.addLayout(self.right_panel)

        self.panel_layout.addLayout(self.comparison_layout)

    def _setup_info_section(self):
        self.info_layout = QHBoxLayout()
        self.info_layout.setSpacing(40)
        
        # Left side info
        self.info_left = QVBoxLayout()
        self.lbl_orig_fps = QLabel("Original FPS:\n--")
        self.lbl_orig_fps.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_enh_fps = QLabel("Enhanced FPS:\n--")
        self.lbl_enh_fps.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_left.addWidget(self.lbl_orig_fps)
        self.info_left.addWidget(self.lbl_enh_fps)

        # Right side info
        self.info_right = QVBoxLayout()
        self.lbl_preset = QLabel("Preset Used:\n--")
        self.lbl_preset.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_format = QLabel("Output Format:\n--")
        self.lbl_format.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_right.addWidget(self.lbl_preset)
        self.info_right.addWidget(self.lbl_format)

        self.info_layout.addStretch()
        self.info_layout.addLayout(self.info_left)
        self.info_layout.addSpacing(40)
        self.info_layout.addLayout(self.info_right)
        self.info_layout.addStretch()

        self.panel_layout.addSpacing(20)
        self.panel_layout.addLayout(self.info_layout)

    def _setup_bottom_buttons(self):
        self.btn_back_home = QPushButton("Back to Home")
        self.btn_back_home.clicked.connect(self.request_home.emit)
        self.btn_process_another = QPushButton("Process Another Video")
        self.btn_process_another.clicked.connect(self.request_home.emit)
        self.btn_export = QPushButton("Export Video")
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_back_home)
        btn_layout.addWidget(self.btn_process_another)
        btn_layout.addWidget(self.btn_export)
        btn_layout.addStretch()

        self.main_layout.addSpacing(20)
        self.main_layout.addLayout(btn_layout)

    def set_original_fps(self, fps: str):
        """
        Updates the original FPS label.
        
        Args:
            fps (str): The original FPS.
        """
        self.lbl_orig_fps.setText(f"Original FPS:\n{fps}")

    def set_enhanced_fps(self, fps: str):
        """
        Updates the enhanced FPS label.
        
        Args:
            fps (str): The enhanced FPS.
        """
        self.lbl_enh_fps.setText(f"Enhanced FPS:\n{fps}")

    def set_preset(self, preset: str):
        """
        Updates the preset used label.
        
        Args:
            preset (str): The preset used (e.g. Fast, Balanced, Quality).
        """
        self.lbl_preset.setText(f"Preset Used:\n{preset}")

    def set_output_format(self, fmt: str):
        """
        Updates the output format label.
        
        Args:
            fmt (str): The output format used (e.g. MP4, MKV).
        """
        self.lbl_format.setText(f"Output Format:\n{fmt}")

    def set_original_video(self, path: str):
        """
        Displays the filename of the original video in the preview placeholder.
        
        Args:
            path (str): The path to the original video file.
        """
        if not path:
            return
        filename = Path(path).name
        self.lbl_original_preview.setText(filename)

    def set_enhanced_video(self, path: str):
        """
        Displays the filename of the enhanced video in the preview placeholder.
        
        Args:
            path (str): The path to the enhanced video file.
        """
        if not path:
            return
        filename = Path(path).name
        self.lbl_enhanced_preview.setText(filename)

    def reset(self):
        """
        Restores every field back to its default placeholder state.
        """
        self.lbl_orig_fps.setText("Original FPS:\n--")
        self.lbl_enh_fps.setText("Enhanced FPS:\n--")
        self.lbl_preset.setText("Preset Used:\n--")
        self.lbl_format.setText("Output Format:\n--")
        self.lbl_original_preview.setText("Original Video Preview")
        self.lbl_enhanced_preview.setText("Enhanced Video Preview")
