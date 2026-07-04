from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QRadioButton, QButtonGroup, QComboBox
)
from PyQt6.QtCore import Qt, pyqtSignal

class SettingsScreen(QWidget):
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
        self.title_label = QLabel("Settings")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = self.title_label.font()
        title_font.setPointSize(24)
        title_font.setBold(True)
        self.title_label.setFont(title_font)

        self.subtitle_label = QLabel("Configure video enhancement options.")
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
        self.panel_layout.setSpacing(25)

        self._setup_preset_section()
        self._setup_fps_section()
        self._setup_format_section()

        # Center the panel horizontally
        self.panel_container_layout = QHBoxLayout()
        self.panel_container_layout.addStretch()
        self.panel_container_layout.addWidget(self.panel_frame)
        self.panel_container_layout.addStretch()

        self.main_layout.addLayout(self.panel_container_layout)

    def _setup_preset_section(self):
        lbl_preset = QLabel("Quality Preset")
        lbl_font = lbl_preset.font()
        lbl_font.setBold(True)
        lbl_preset.setFont(lbl_font)
        
        self.preset_group = QButtonGroup(self)
        
        self.rb_fast = QRadioButton("Fast")
        self.rb_balanced = QRadioButton("Balanced")
        self.rb_quality = QRadioButton("Quality")
        
        self.rb_balanced.setChecked(True)
        
        self.preset_group.addButton(self.rb_fast)
        self.preset_group.addButton(self.rb_balanced)
        self.preset_group.addButton(self.rb_quality)
        
        preset_layout = QHBoxLayout()
        preset_layout.addWidget(self.rb_fast)
        preset_layout.addWidget(self.rb_balanced)
        preset_layout.addWidget(self.rb_quality)
        preset_layout.addStretch()

        self.panel_layout.addWidget(lbl_preset)
        self.panel_layout.addLayout(preset_layout)

    def _setup_fps_section(self):
        lbl_fps = QLabel("Output FPS")
        lbl_font = lbl_fps.font()
        lbl_font.setBold(True)
        lbl_fps.setFont(lbl_font)
        
        self.fps_group = QButtonGroup(self)
        
        self.rb_fps_48 = QRadioButton("24 → 48 FPS")
        self.rb_fps_60 = QRadioButton("30 → 60 FPS")
        self.rb_fps_120 = QRadioButton("60 → 120 FPS")
        
        self.rb_fps_60.setChecked(True)
        
        self.fps_group.addButton(self.rb_fps_48)
        self.fps_group.addButton(self.rb_fps_60)
        self.fps_group.addButton(self.rb_fps_120)
        
        fps_layout = QHBoxLayout()
        fps_layout.addWidget(self.rb_fps_48)
        fps_layout.addWidget(self.rb_fps_60)
        fps_layout.addWidget(self.rb_fps_120)
        fps_layout.addStretch()

        self.panel_layout.addWidget(lbl_fps)
        self.panel_layout.addLayout(fps_layout)

    def _setup_format_section(self):
        lbl_format = QLabel("Output Format")
        lbl_font = lbl_format.font()
        lbl_font.setBold(True)
        lbl_format.setFont(lbl_font)
        
        self.cb_format = QComboBox()
        self.cb_format.addItems(["MP4", "MKV"])
        
        format_layout = QHBoxLayout()
        format_layout.addWidget(self.cb_format)
        format_layout.addStretch()

        self.panel_layout.addWidget(lbl_format)
        self.panel_layout.addLayout(format_layout)

    def _setup_bottom_buttons(self):
        self.btn_back = QPushButton("Back")
        self.btn_back.clicked.connect(self.request_home.emit)
        self.btn_save = QPushButton("Save Settings")
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_back)
        btn_layout.addWidget(self.btn_save)
        btn_layout.addStretch()

        self.main_layout.addSpacing(20)
        self.main_layout.addLayout(btn_layout)

    def get_selected_preset(self) -> str:
        """
        Returns the selected quality preset as a lowercase string.
        
        Returns:
            str: 'fast', 'balanced', or 'quality'
        """
        if self.rb_fast.isChecked():
            return "fast"
        elif self.rb_quality.isChecked():
            return "quality"
        return "balanced"

    def get_selected_fps(self) -> int:
        """
        Returns the selected target FPS as an integer.
        
        Returns:
            int: 48, 60, or 120
        """
        if self.rb_fps_48.isChecked():
            return 48
        elif self.rb_fps_120.isChecked():
            return 120
        return 60

    def get_output_format(self) -> str:
        """
        Returns the selected output format as a lowercase string.
        
        Returns:
            str: 'mp4' or 'mkv'
        """
        return self.cb_format.currentText().lower()
