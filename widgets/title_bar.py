"""Custom Title Bar Header for Theia Desktop Application."""

from pathlib import Path
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QWidget
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QSize
from PyQt6.QtGui import QMouseEvent, QIcon, QCursor, QPixmap

from styles.theme_manager import ThemeManager
from widgets.components import StatusBadge

class TitleBarButton(QPushButton):
    """Custom title bar window control button (Minimize, Maximize, Close)."""
    
    def __init__(self, text: str, is_close: bool = False, scale: float = 1.0, parent=None):
        super().__init__(text, parent)
        self.scale = scale
        self.is_close = is_close
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._apply_style()

    def si(self, v: int) -> int:
        return max(1, int(v * self.scale))

    def _apply_style(self):
        w = self.si(42)
        h = self.si(32)
        self.setFixedSize(QSize(w, h))

        if self.is_close:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {ThemeManager.TEXT_SECONDARY};
                    border: none;
                    font-size: {self.si(12)}px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {ThemeManager.BTN_CLOSE_HOVER_BG};
                    color: #FFFFFF;
                }}
                QPushButton:pressed {{
                    background-color: #BE123C;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {ThemeManager.TEXT_SECONDARY};
                    border: none;
                    font-size: {self.si(12)}px;
                }}
                QPushButton:hover {{
                    background-color: {ThemeManager.BTN_HOVER_BG};
                    color: {ThemeManager.TEXT_PRIMARY};
                }}
                QPushButton:pressed {{
                    background-color: {ThemeManager.BG_PANEL_HOVER};
                }}
            """)


class CustomTitleBar(QFrame):
    """Integrated frameless header featuring branding logo pixmap, status badge, and window controls."""

    minimize_requested = pyqtSignal()
    maximize_requested = pyqtSignal()
    close_requested = pyqtSignal()
    status_badge_clicked = pyqtSignal()

    def __init__(self, target_window, scale: float = 1.0, parent=None):
        super().__init__(parent)
        self.target_window = target_window
        self.scale = scale
        self._drag_position = QPoint()

        self.setObjectName("CustomTitleBar")
        self.setFixedHeight(max(1, int(38 * scale)))
        
        self.setStyleSheet(f"""
            QFrame#CustomTitleBar {{
                background-color: {ThemeManager.TITLEBAR_BG};
                border-bottom: 1px solid {ThemeManager.BORDER};
            }}
        """)

        self._init_ui()

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(max(1, int(12 * self.scale)), 0, 0, 0)
        layout.setSpacing(max(1, int(10 * self.scale)))

        # Brand Icon / App Icon Pixmap
        self.lbl_logo = QLabel()
        icon_path = Path(__file__).parent.parent / "app_icon.ico"
        sz = max(1, int(20 * self.scale))
        if icon_path.exists():
            pix = QPixmap(str(icon_path)).scaled(
                sz, sz, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            )
            self.lbl_logo.setPixmap(pix)
        else:
            self.lbl_logo.setText("•")
            self.lbl_logo.setStyleSheet(f"color: {ThemeManager.PRIMARY}; font-size: {sz}px; font-weight: bold;")

        # App Title
        self.lbl_title = QLabel("THEIA")
        self.lbl_title.setStyleSheet(f"""
            color: {ThemeManager.TEXT_PRIMARY};
            font-size: {max(1, int(12 * self.scale))}px;
            font-weight: 800;
            letter-spacing: 1.5px;
            background: transparent;
            border: none;
        """)

        self.lbl_subtitle = QLabel("DESKTOP")
        self.lbl_subtitle.setStyleSheet(f"""
            color: {ThemeManager.TEXT_MUTED};
            font-size: {max(1, int(10 * self.scale))}px;
            font-weight: 600;
            letter-spacing: 1px;
            background: transparent;
            border: none;
        """)

        # Engine Status Badge
        self.status_badge = StatusBadge("READY", StatusBadge.STATE_SUCCESS, self.scale)
        self.status_badge.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.status_badge.setToolTip("Click to jump to AI Command Center workspace")

        # Window Controls
        self.btn_minimize = TitleBarButton("─", is_close=False, scale=self.scale)
        self.btn_maximize = TitleBarButton("□", is_close=False, scale=self.scale)
        self.btn_close = TitleBarButton("×", is_close=True, scale=self.scale)

        self.btn_minimize.clicked.connect(self._on_minimize)
        self.btn_maximize.clicked.connect(self._on_maximize)
        self.btn_close.clicked.connect(self._on_close)

        # Assembly
        layout.addWidget(self.lbl_logo)
        layout.addWidget(self.lbl_title)
        layout.addWidget(self.lbl_subtitle)
        layout.addSpacing(max(1, int(8 * self.scale)))
        layout.addWidget(self.status_badge)
        
        layout.addStretch()

        # Window Action Buttons layout
        ctrl_layout = QHBoxLayout()
        ctrl_layout.setContentsMargins(0, 0, 0, 0)
        ctrl_layout.setSpacing(0)
        ctrl_layout.addWidget(self.btn_minimize)
        ctrl_layout.addWidget(self.btn_maximize)
        ctrl_layout.addWidget(self.btn_close)

        layout.addLayout(ctrl_layout)

    # ── Status Updates ──

    def update_status(self, text: str, state: str = StatusBadge.STATE_SUCCESS):
        """Update the integrated title bar status badge."""
        self.status_badge.set_state(text, state)

    def update_maximize_icon(self, is_maximized: bool):
        """Update the maximize/restore icon."""
        self.btn_maximize.setText("❐" if is_maximized else "□")

    # ── Button Handlers ──

    def _on_minimize(self):
        if self.target_window:
            self.target_window.showMinimized()
        self.minimize_requested.emit()

    def _on_maximize(self):
        if self.target_window:
            if self.target_window.isMaximized():
                self.target_window.showNormal()
                self.update_maximize_icon(False)
            else:
                self.target_window.showMaximized()
                self.update_maximize_icon(True)
        self.maximize_requested.emit()

    def _on_close(self):
        if self.target_window:
            self.target_window.close()
        self.close_requested.emit()

    # ── Window Dragging & Status Badge Click Override ──

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            # Check if click was over status badge
            badge_rect = self.status_badge.geometry()
            if badge_rect.contains(event.pos()):
                self.status_badge_clicked.emit()
                event.accept()
                return

            self._drag_position = event.globalPosition().toPoint() - self.target_window.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() == Qt.MouseButton.LeftButton and self.target_window:
            if not self.target_window.isMaximized():
                self.target_window.move(event.globalPosition().toPoint() - self._drag_position)
                event.accept()

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._on_maximize()
            event.accept()
