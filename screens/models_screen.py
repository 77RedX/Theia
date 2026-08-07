"""Model Manager Workspace Screen for Theia Desktop Application."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QGridLayout, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from widgets.components import (
    BaseCard, PrimaryButton, SecondaryButton, TitleLabel, 
    SubtitleLabel, SectionHeader, StatusBadge, MetadataItem
)
from styles.theme_manager import ThemeManager


class ModelCard(BaseCard):
    """Card representing an ONNX inference model checkpoint."""

    def __init__(self, name: str, desc: str, channels: str, input_res: str, status: str, scale: float = 1.0, parent=None):
        super().__init__(scale, parent)
        self.scale = scale

        layout = QVBoxLayout(self)
        layout.setContentsMargins(max(1, int(18 * scale)), max(1, int(18 * scale)), max(1, int(18 * scale)), max(1, int(18 * scale)))
        layout.setSpacing(max(1, int(12 * scale)))

        # Header Row
        h_row = QHBoxLayout()
        lbl_title = TitleLabel(name, scale)
        lbl_title.setStyleSheet(f"font-size: {max(1, int(16 * scale))}px; font-weight: 700; color: {ThemeManager.TEXT_PRIMARY}; border: none; background: transparent;")
        
        badge = StatusBadge(status, StatusBadge.STATE_SUCCESS if status == "READY" else StatusBadge.STATE_INFO, scale)
        
        h_row.addWidget(lbl_title)
        h_row.addStretch()
        h_row.addWidget(badge)

        layout.addLayout(h_row)

        # Description
        lbl_desc = SubtitleLabel(desc, scale)
        layout.addWidget(lbl_desc)

        # Tech specs grid
        grid = QGridLayout()
        grid.setSpacing(max(1, int(8 * scale)))

        grid.addWidget(MetadataItem("Input Channels", channels, scale), 0, 0)
        grid.addWidget(MetadataItem("Native Resolution", input_res, scale), 0, 1)

        layout.addLayout(grid)


class ModelManagerScreen(QWidget):
    """AI Model Checkpoints & Execution Provider Manager."""

    request_home = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._scale = 1.0
        self.init_ui()

    def si(self, v: int) -> int:
        return max(1, int(v * self._scale))

    def init_ui(self):
        """Build Model Manager layout."""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(self.si(30), self.si(24), self.si(30), self.si(24))
        self.main_layout.setSpacing(self.si(20))

        # Header
        header_layout = QVBoxLayout()
        header_layout.setSpacing(self.si(4))
        header_layout.addWidget(TitleLabel("AI Neural Models", self._scale))
        header_layout.addWidget(SubtitleLabel("Inspect ONNX model architectures and hardware acceleration backends.", self._scale))
        self.main_layout.addLayout(header_layout)

        # Execution Provider Status Panel
        provider_card = BaseCard(self._scale)
        p_layout = QHBoxLayout(provider_card)
        p_layout.setContentsMargins(self.si(20), self.si(14), self.si(20), self.si(14))

        p_info_layout = QVBoxLayout()
        p_info_layout.setSpacing(self.si(2))
        p_info_layout.addWidget(SectionHeader("ACTIVE HARDWARE BACKEND", self._scale))
        
        # Query ONNX Runtime provider
        provider_name = "DirectML / CUDA Execution Provider (GPU Accelerated)"
        try:
            import onnxruntime as ort
            providers = ort.get_available_providers()
            if "CUDAExecutionProvider" in providers:
                provider_name = "NVIDIA CUDA Execution Provider (GPU Accelerated)"
            elif "DmlExecutionProvider" in providers:
                provider_name = "DirectML Execution Provider (GPU Accelerated)"
            else:
                provider_name = "CPU Execution Provider (Fallback)"
        except Exception:
            pass

        lbl_provider = SubtitleLabel(provider_name, self._scale)
        lbl_provider.setStyleSheet(f"font-size: {self.si(14)}px; font-weight: 600; color: {ThemeManager.SUCCESS}; border: none; background: transparent;")
        p_info_layout.addWidget(lbl_provider)

        p_layout.addLayout(p_info_layout)
        p_layout.addStretch()

        self.main_layout.addWidget(provider_card)

        # Model Cards Grid
        models_header = SectionHeader("REGISTERED MODEL CHECKPOINTS", self._scale)
        self.main_layout.addWidget(models_header)

        models_layout = QHBoxLayout()
        models_layout.setSpacing(self.si(16))

        card_fast = ModelCard("Fast Model", "Low-latency frame interpolation optimized for real-time preview.", "6 (2x RGB)", "256 x 448", "READY", self._scale)
        card_balanced = ModelCard("Balanced Model", "Standard quality model balancing speed and clarity.", "6 (2x RGB)", "256 x 448", "READY", self._scale)
        card_quality = ModelCard("Quality Model", "Deep residual model with maximum optical flow fidelity.", "6 (2x RGB)", "256 x 448", "READY", self._scale)

        models_layout.addWidget(card_fast)
        models_layout.addWidget(card_balanced)
        models_layout.addWidget(card_quality)

        self.main_layout.addLayout(models_layout)
        self.main_layout.addStretch()

    def apply_scale(self, s: float):
        self._scale = s
