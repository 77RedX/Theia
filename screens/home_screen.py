"""Home Screen (Project Dashboard & Enhancement Inspector) for Theia Desktop Application."""

import os
from pathlib import Path
import cv2

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QFileDialog, QMessageBox, 
    QComboBox, QCheckBox, QSizePolicy, QTableWidget, QTableWidgetItem, QHeaderView, QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSignal, QUrl, QSize
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QImage, QPixmap, QColor, QCursor, QMouseEvent

from widgets.components import (
    BaseCard, PrimaryButton, SecondaryButton, TitleLabel, SubtitleLabel, 
    SectionHeader, StatusBadge, MetadataItem
)
from styles.theme_manager import ThemeManager


class MediaDropZone(QFrame):
    """Interactive drag-and-drop media zone supporting visual feedback, click-to-select, and thumbnail preview."""

    file_dropped = pyqtSignal(str)

    def __init__(self, scale: float = 1.0, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.scale = scale
        self.input_file = None

        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumHeight(int(220 * scale))
        self._set_default_style()

        self._init_ui()

    def si(self, v: int) -> int:
        return max(1, int(v * self.scale))

    def _set_default_style(self):
        r = self.si(12)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {ThemeManager.BG_PANEL};
                border: 2px dashed {ThemeManager.BORDER};
                border-radius: {r}px;
            }}
            QFrame:hover {{
                border: 2px dashed {ThemeManager.PRIMARY};
                background-color: {ThemeManager.BG_PANEL_HOVER};
            }}
        """)

    def _set_drag_active_style(self):
        r = self.si(12)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {ThemeManager.BG_PANEL_ACTIVE};
                border: 2px dashed {ThemeManager.PRIMARY_HOVER};
                border-radius: {r}px;
            }}
        """)

    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.setContentsMargins(self.si(20), self.si(20), self.si(20), self.si(20))
        self.main_layout.setSpacing(self.si(12))

        # Default Empty State Elements
        self.empty_container = QWidget()
        empty_layout = QVBoxLayout(self.empty_container)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.setSpacing(self.si(8))

        self.lbl_icon = QLabel("[ CLICK OR DROP MEDIA ]")
        self.lbl_icon.setStyleSheet(f"""
            font-size: {self.si(11)}px;
            font-weight: 700;
            color: {ThemeManager.PRIMARY};
            background-color: {ThemeManager.BG_SURFACE};
            border: 1px solid {ThemeManager.BORDER};
            border-radius: {self.si(6)}px;
            padding: {self.si(6)}px {self.si(16)}px;
            letter-spacing: 1px;
        """)
        self.lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_text = TitleLabel("Click or Drop Video to Begin Enhancement", self.scale)
        self.lbl_text.setStyleSheet(f"font-size: {self.si(16)}px; background: transparent; border: none;")
        self.lbl_text.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_sub = SubtitleLabel("Supports MP4, MKV, AVI, MOV up to 4K resolution", self.scale)
        self.lbl_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)

        empty_layout.addWidget(self.lbl_icon, alignment=Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(self.lbl_text)
        empty_layout.addWidget(self.lbl_sub)

        # Loaded Media Preview Elements
        self.preview_container = QWidget()
        preview_layout = QVBoxLayout(self.preview_container)
        preview_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_layout.setSpacing(self.si(10))

        self.lbl_thumbnail = QLabel()
        self.lbl_thumbnail.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_thumbnail.setStyleSheet(f"border-radius: {self.si(8)}px; border: 1px solid {ThemeManager.BORDER};")

        self.btn_replace = SecondaryButton("Replace Video...", self.scale)
        self.btn_replace.clicked.connect(self._on_replace_clicked)

        preview_layout.addWidget(self.lbl_thumbnail)
        preview_layout.addWidget(self.btn_replace, alignment=Qt.AlignmentFlag.AlignCenter)

        self.preview_container.hide()

        self.main_layout.addWidget(self.empty_container)
        self.main_layout.addWidget(self.preview_container)

    def set_thumbnail(self, path: str):
        """Extract and render a thumbnail from the video file."""
        self.input_file = path
        cap = cv2.VideoCapture(path)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb.shape
                qimg = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888).copy()
                pixmap = QPixmap.fromImage(qimg)
                
                target_w = max(200, self.width() - self.si(80))
                target_h = max(140, self.height() - self.si(80))
                
                scaled = pixmap.scaled(
                    target_w, target_h,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.lbl_thumbnail.setPixmap(scaled)
                self.empty_container.hide()
                self.preview_container.show()
        cap.release()

    def clear(self):
        self.input_file = None
        self.preview_container.hide()
        self.empty_container.show()

    def mousePressEvent(self, event: QMouseEvent):
        """Handle click anywhere on the drop zone to open file dialog."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._on_replace_clicked()
            event.accept()
        else:
            super().mousePressEvent(event)

    def _on_replace_clicked(self):
        parent_screen = self.parent()
        while parent_screen and not isinstance(parent_screen, HomeScreen):
            parent_screen = parent_screen.parent()
        if parent_screen and hasattr(parent_screen, 'select_video'):
            parent_screen.select_video()

    # ── Drag & Drop Event Overrides ──

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls and urls[0].isLocalFile():
                ext = Path(urls[0].toLocalFile()).suffix.lower()
                if ext in ['.mp4', '.mkv', '.avi', '.mov']:
                    self._set_drag_active_style()
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dragLeaveEvent(self, event):
        self._set_default_style()
        event.accept()

    def dropEvent(self, event: QDropEvent):
        self._set_default_style()
        urls = event.mimeData().urls()
        if urls and urls[0].isLocalFile():
            file_path = urls[0].toLocalFile()
            self.file_dropped.emit(file_path)
            event.acceptProposedAction()


class HomeScreen(QWidget):
    """Project Dashboard & Enhancement Inspector Master Screen."""

    # Emits (preset_string, detect_scene_cuts, protect_static_overlays)
    request_processing = pyqtSignal(str, bool, bool)
    # Emits (original_path, output_path)
    render_selected = pyqtSignal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.input_path = None
        self.detected_fps = None
        self.detected_format = None
        self.detected_resolution = "—"
        self.detected_duration = "—"
        self.detected_frame_count = 0
        self.detected_size_mb = "—"
        self._scale = 1.0

        self.recent_renders_data = [] # List of tuples: (original_path, output_path)

        self.init_ui()

    def si(self, v: int) -> int:
        return max(1, int(v * self._scale))

    def init_ui(self):
        """Build responsive split-pane dashboard layout."""
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(self.si(20), self.si(20), self.si(20), self.si(20))
        self.main_layout.setSpacing(self.si(20))

        self._setup_dashboard_pane()
        self._setup_inspector_pane()

    # ── Left Pane: Project Dashboard ──────────────────────────

    def _setup_dashboard_pane(self):
        dashboard_layout = QVBoxLayout()
        dashboard_layout.setSpacing(self.si(16))

        # Header
        header_layout = QVBoxLayout()
        header_layout.setSpacing(self.si(4))
        title = TitleLabel("Project Dashboard", self._scale)
        subtitle = SubtitleLabel("Select or drag a video file to run neural enhancement.", self._scale)
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        dashboard_layout.addLayout(header_layout)

        # Drop Zone
        self.drop_zone = MediaDropZone(self._scale, self)
        self.drop_zone.file_dropped.connect(self._on_file_dropped)
        dashboard_layout.addWidget(self.drop_zone, stretch=2)

        # Recent Renders Section
        recent_header_layout = QHBoxLayout()
        recent_label = SectionHeader("Recent Session Renders (Double-click to Review)", self._scale)
        recent_header_layout.addWidget(recent_label)
        recent_header_layout.addStretch()
        dashboard_layout.addLayout(recent_header_layout)

        self.recent_table = QTableWidget(0, 4)
        self.recent_table.setHorizontalHeaderLabels(["Filename", "Model", "Duration", "Status"])
        self.recent_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.recent_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.recent_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.recent_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.recent_table.verticalHeader().setVisible(False)
        self.recent_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.recent_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.recent_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {ThemeManager.BG_PANEL};
                border: 1px solid {ThemeManager.BORDER};
                border-radius: {self.si(8)}px;
                color: {ThemeManager.TEXT_PRIMARY};
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
            QTableWidget::item:hover {{
                background-color: {ThemeManager.BG_PANEL_HOVER};
            }}
            QTableWidget::item:selected {{
                background-color: {ThemeManager.BG_PANEL_ACTIVE};
                color: #FFFFFF;
            }}
        """)

        self.recent_table.cellDoubleClicked.connect(self._on_recent_render_clicked)
        self.recent_table.cellClicked.connect(self._on_recent_render_clicked)

        dashboard_layout.addWidget(self.recent_table, stretch=1)
        self.main_layout.addLayout(dashboard_layout, stretch=3)

    def add_recent_render(self, original_path: str, output_path: str, model: str, duration: str = "Done", status: str = "Completed"):
        """Dynamically add a completed render entry to recent session history."""
        self.recent_renders_data.insert(0, (original_path, output_path))

        self.recent_table.insertRow(0)

        filename = Path(output_path).name if output_path else "enhanced_render.mp4"
        self.recent_table.setItem(0, 0, QTableWidgetItem(filename))
        self.recent_table.setItem(0, 1, QTableWidgetItem(f"{model.capitalize()} Model"))
        self.recent_table.setItem(0, 2, QTableWidgetItem(duration))
        self.recent_table.setItem(0, 3, QTableWidgetItem(status))

    def _on_recent_render_clicked(self, row: int, col: int):
        """Handle click on recent render item."""
        if 0 <= row < len(self.recent_renders_data):
            orig_path, out_path = self.recent_renders_data[row]
            self.render_selected.emit(orig_path, out_path)

    # ── Right Pane: Enhancement Inspector ────────────────────

    def _setup_inspector_pane(self):
        """Build the right sidebar inspector."""
        self.inspector_card = BaseCard(self._scale)
        self.inspector_card.setMinimumWidth(self.si(320))
        self.inspector_card.setMaximumWidth(self.si(420))

        inspector_layout = QVBoxLayout(self.inspector_card)
        inspector_layout.setContentsMargins(self.si(18), self.si(18), self.si(18), self.si(18))
        inspector_layout.setSpacing(self.si(18))

        # 1. System Readiness
        sys_layout = QVBoxLayout()
        sys_layout.setSpacing(self.si(8))
        sys_layout.addWidget(SectionHeader("System Readiness", self._scale))

        gpu_status_layout = QHBoxLayout()
        self.gpu_badge = StatusBadge("GPU ACCELERATED", StatusBadge.STATE_SUCCESS, self._scale)
        gpu_status_layout.addWidget(self.gpu_badge)
        gpu_status_layout.addStretch()

        self.lbl_vram = SubtitleLabel("GPU: DirectML / CUDA Accelerated", self._scale)

        sys_layout.addLayout(gpu_status_layout)
        sys_layout.addWidget(self.lbl_vram)
        inspector_layout.addLayout(sys_layout)

        # Divider
        inspector_layout.addWidget(self._create_divider())

        # 2. File Metadata Specifications Grid
        meta_layout = QVBoxLayout()
        meta_layout.setSpacing(self.si(10))
        meta_layout.addWidget(SectionHeader("Input Video Specifications", self._scale))

        self.btn_select = SecondaryButton("Select Video File...", self._scale)
        self.btn_select.clicked.connect(self.select_video)
        meta_layout.addWidget(self.btn_select)

        self.lbl_filename = SubtitleLabel("No video loaded", self._scale)
        self.lbl_filename.setWordWrap(True)
        meta_layout.addWidget(self.lbl_filename)

        # Metadata Specs Grid (2x2)
        specs_grid = QGridLayout()
        specs_grid.setSpacing(self.si(8))

        self.meta_res = MetadataItem("Resolution", "—", self._scale)
        self.meta_fps = MetadataItem("Source FPS", "—", self._scale)
        self.meta_format = MetadataItem("Format", "—", self._scale)
        self.meta_size = MetadataItem("File Size", "—", self._scale)

        specs_grid.addWidget(self.meta_res, 0, 0)
        specs_grid.addWidget(self.meta_fps, 0, 1)
        specs_grid.addWidget(self.meta_format, 1, 0)
        specs_grid.addWidget(self.meta_size, 1, 1)

        meta_layout.addLayout(specs_grid)
        inspector_layout.addLayout(meta_layout)

        # Divider
        inspector_layout.addWidget(self._create_divider())

        # 3. AI Enhancement Options
        ai_layout = QVBoxLayout()
        ai_layout.setSpacing(self.si(12))
        ai_layout.addWidget(SectionHeader("Enhancement Settings", self._scale))

        self.model_combo = QComboBox()
        self.model_combo.setMinimumHeight(self.si(36))
        
        # Populate models dynamically from ModelRegistry
        try:
            from video_engine import ModelRegistry
            available = ModelRegistry().available_models()
            for model in available:
                self.model_combo.addItem(f"{model.capitalize()} Model", userData=model)
                if model == "fast":
                    self.model_combo.setCurrentText("Fast Model")
        except Exception:
            self.model_combo.addItem("Fast Model", userData="fast")
            self.model_combo.addItem("Balanced Model", userData="balanced")
            self.model_combo.addItem("Quality Model", userData="quality")

        ai_layout.addWidget(self.model_combo)

        self.cb_scene_cuts = QCheckBox("Detect & Skip Scene Cuts")
        self.cb_scene_cuts.setChecked(True)
        self.cb_protect_overlays = QCheckBox("Protect Static UI/HUD Overlays")
        self.cb_protect_overlays.setChecked(False)

        ai_layout.addWidget(self.cb_scene_cuts)
        ai_layout.addWidget(self.cb_protect_overlays)
        inspector_layout.addLayout(ai_layout)

        inspector_layout.addStretch()

        # 4. Main Call-To-Action Button
        self.btn_process = PrimaryButton("Enhance Video", self._scale)
        self.btn_process.setEnabled(False)
        self.btn_process.clicked.connect(self._on_start_processing)
        inspector_layout.addWidget(self.btn_process)

        self.main_layout.addWidget(self.inspector_card, stretch=1)

    def _create_divider(self) -> QFrame:
        div = QFrame()
        div.setFrameShape(QFrame.Shape.HLine)
        div.setStyleSheet(f"background-color: {ThemeManager.BORDER};")
        return div

    # ── Actions & Metadata Extraction ─────────────────────────

    def _on_file_dropped(self, file_path: str):
        self._load_video_metadata(file_path)

    def select_video(self):
        """Open native file dialog and read video metadata."""
        file_filter = "Video Files (*.mp4 *.mkv *.avi *.mov)"
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Video File", "", file_filter
        )
        if file_path:
            self._load_video_metadata(file_path)

    def _load_video_metadata(self, file_path: str):
        """Extract resolution, duration, frame rate, format, and size."""
        self.input_path = file_path
        path = Path(file_path)

        self.lbl_filename.setText(path.name)
        self.detected_format = path.suffix.lstrip(".").lower()
        self.meta_format.set_value(self.detected_format.upper())

        # File Size
        try:
            size_mb = os.path.getsize(file_path) / (1024 * 1024)
            self.detected_size_mb = f"{size_mb:.1f} MB"
            self.meta_size.set_value(self.detected_size_mb)
        except Exception:
            self.meta_size.set_value("—")

        # Thumbnail
        self.drop_zone.set_thumbnail(file_path)

        # OpenCV Video Analysis
        try:
            cap = cv2.VideoCapture(file_path)
            if cap.isOpened():
                fps = cap.get(cv2.CAP_PROP_FPS)
                w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

                self.detected_fps = round(fps, 2) if fps > 0 else 30.0
                self.detected_resolution = f"{w}x{h}"
                self.detected_frame_count = total_frames

                self.meta_res.set_value(self.detected_resolution)
                self.meta_fps.set_value(f"{self.detected_fps} FPS")

                if fps > 0 and total_frames > 0:
                    dur_sec = total_frames / fps
                    m, s = divmod(int(dur_sec), 60)
                    self.detected_duration = f"{m:02d}:{s:02d}"
            cap.release()
        except Exception:
            self.meta_fps.set_value("Unknown")
            self.meta_res.set_value("Unknown")

        # Enable CTA
        self.btn_process.setEnabled(True)

    def _on_start_processing(self):
        """Validate input selection and emit processing request signal."""
        if not self.input_path:
            QMessageBox.warning(
                self, "No Video Loaded",
                "Please select or drop a video file before enhancing."
            )
            return

        selected_model = self.model_combo.currentData() or "fast"
        detect_scene_cuts = self.cb_scene_cuts.isChecked()
        protect_static_overlays = self.cb_protect_overlays.isChecked()
        self.request_processing.emit(selected_model, detect_scene_cuts, protect_static_overlays)

    def reset(self):
        """Reset screen state."""
        self.input_path = None
        self.drop_zone.clear()
        self.lbl_filename.setText("No video loaded")
        self.meta_res.set_value("—")
        self.meta_fps.set_value("—")
        self.meta_format.set_value("—")
        self.meta_size.set_value("—")
        self.btn_process.setEnabled(False)

    def apply_scale(self, s: float):
        """Update scale factor."""
        self._scale = s
