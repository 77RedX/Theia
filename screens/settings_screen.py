"""Settings Workspace Screen for Theia Desktop Application."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QRadioButton, QButtonGroup, QComboBox, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal

from widgets.components import (
    BaseCard, PrimaryButton, SecondaryButton, TitleLabel, 
    SubtitleLabel, SectionHeader
)
from styles.theme_manager import ThemeManager


class SettingsScreen(QWidget):
    """Configuration and application settings workspace."""

    request_home = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._scale = 1.0
        self.init_ui()

    def si(self, v: int) -> int:
        return max(1, int(v * self._scale))

    def init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(self.si(30), self.si(24), self.si(30), self.si(24))
        self.main_layout.setSpacing(self.si(20))

        # Header
        header_layout = QVBoxLayout()
        header_layout.setSpacing(self.si(4))
        header_layout.addWidget(TitleLabel("Settings & Preferences", self._scale))
        header_layout.addWidget(SubtitleLabel("Configure video enhancement options, hardware acceleration, and output target defaults.", self._scale))
        self.main_layout.addLayout(header_layout)

        # Settings Card Panel
        self.card_panel = BaseCard(self._scale)
        panel_layout = QVBoxLayout(self.card_panel)
        panel_layout.setContentsMargins(self.si(24), self.si(24), self.si(24), self.si(24))
        panel_layout.setSpacing(self.si(20))

        # 1. Quality Preset Section
        panel_layout.addWidget(SectionHeader("Default Quality Preset", self._scale))
        
        self.preset_group = QButtonGroup(self)
        self.rb_fast = QRadioButton("Fast (Low latency)")
        self.rb_balanced = QRadioButton("Balanced (Recommended)")
        self.rb_quality = QRadioButton("Quality (High fidelity)")
        self.rb_balanced.setChecked(True)

        self.preset_group.addButton(self.rb_fast)
        self.preset_group.addButton(self.rb_balanced)
        self.preset_group.addButton(self.rb_quality)

        preset_layout = QHBoxLayout()
        preset_layout.setSpacing(self.si(20))
        preset_layout.addWidget(self.rb_fast)
        preset_layout.addWidget(self.rb_balanced)
        preset_layout.addWidget(self.rb_quality)
        preset_layout.addStretch()

        panel_layout.addLayout(preset_layout)
        panel_layout.addWidget(self._create_divider())

        # 2. Hardware Acceleration Section
        panel_layout.addWidget(SectionHeader("Hardware Acceleration Backend", self._scale))

        self.hw_group = QButtonGroup(self)
        self.rb_gpu = QRadioButton("GPU Acceleration (DirectML / CUDA) - Recommended")
        self.rb_cpu = QRadioButton("CPU Mode (Software Processing)")
        self.rb_gpu.setChecked(True)

        self.hw_group.addButton(self.rb_gpu)
        self.hw_group.addButton(self.rb_cpu)

        hw_layout = QHBoxLayout()
        hw_layout.setSpacing(self.si(20))
        hw_layout.addWidget(self.rb_gpu)
        hw_layout.addWidget(self.rb_cpu)
        hw_layout.addStretch()

        panel_layout.addLayout(hw_layout)
        panel_layout.addWidget(self._create_divider())

        # 3. Default Export Format Section
        panel_layout.addWidget(SectionHeader("Default Export Format", self._scale))

        self.cb_format = QComboBox()
        self.cb_format.addItems(["MP4", "MKV"])
        self.cb_format.setFixedSize(self.si(140), self.si(34))

        format_layout = QHBoxLayout()
        format_layout.addWidget(self.cb_format)
        format_layout.addStretch()

        panel_layout.addLayout(format_layout)

        self.main_layout.addWidget(self.card_panel)

        # Footer Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(self.si(16))
        btn_layout.addStretch()

        self.btn_back = SecondaryButton("Back to Dashboard", self._scale)
        self.btn_back.clicked.connect(self.request_home.emit)
        self.btn_save = PrimaryButton("Save Settings", self._scale)
        self.btn_save.clicked.connect(self.request_home.emit)

        btn_layout.addWidget(self.btn_back)
        btn_layout.addWidget(self.btn_save)

        self.main_layout.addLayout(btn_layout)
        self.main_layout.addStretch()

    def _create_divider(self) -> QFrame:
        div = QFrame()
        div.setFrameShape(QFrame.Shape.HLine)
        div.setStyleSheet(f"background-color: {ThemeManager.BORDER};")
        return div

    def get_selected_preset(self) -> str:
        if self.rb_fast.isChecked():
            return "fast"
        elif self.rb_quality.isChecked():
            return "quality"
        return "balanced"

    def is_gpu_enabled(self) -> bool:
        return self.rb_gpu.isChecked()

    def get_output_format(self) -> str:
        return self.cb_format.currentText().lower()

    def apply_scale(self, s: float):
        self._scale = s
