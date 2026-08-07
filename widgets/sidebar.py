"""Sidebar navigation for Theia Desktop Application."""

from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from widgets.components import BaseButton, SectionHeader
from styles.theme_manager import ThemeManager

class SidebarButton(BaseButton):
    """A sleek navigation button with an active indicator pill and professional icon badge."""

    def __init__(self, text: str, scale: float = 1.0, parent=None):
        super().__init__(f"  ▪  {text}", scale, parent)
        self.setCheckable(True)
        self.btn_text = text
        self._apply_style()

    def _apply_style(self):
        h = self.si(40)
        self.setFixedHeight(h)
        
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {ThemeManager.TEXT_MUTED};
                border: none;
                border-radius: {self.si(6)}px;
                padding: {self.si(8)}px {self.si(16)}px;
                text-align: left;
                font-size: {self.si(13)}px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {ThemeManager.BG_PANEL_HOVER};
                color: {ThemeManager.TEXT_PRIMARY};
            }}
            QPushButton:checked {{
                background-color: {ThemeManager.BG_PANEL_ACTIVE};
                color: #FFFFFF;
                font-weight: 600;
                border-left: {self.si(3)}px solid {ThemeManager.PRIMARY};
            }}
        """)


class Sidebar(QFrame):
    """Main vertical left navigation sidebar."""

    navigation_requested = pyqtSignal(str)

    def __init__(self, scale: float = 1.0, parent=None):
        super().__init__(parent)
        self.scale = scale
        self.setObjectName("Sidebar")
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        self.setMinimumWidth(max(1, int(220 * scale)))

        self.setStyleSheet(f"""
            QFrame#Sidebar {{
                background-color: {ThemeManager.BG_SURFACE};
                border-right: 1px solid {ThemeManager.BORDER};
            }}
        """)

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(self.si(12), self.si(16), self.si(12), self.si(16))
        layout.setSpacing(self.si(6))

        # Main Workspace Group Header
        lbl_workspace = SectionHeader("WORKSPACE", self.scale)
        lbl_workspace.setStyleSheet(f"color: {ThemeManager.TEXT_MUTED}; font-size: {self.si(10)}px; font-weight: 700; padding: {self.si(4)}px {self.si(8)}px;")
        layout.addWidget(lbl_workspace)
        layout.addSpacing(self.si(2))

        # Navigation Buttons
        self.btn_dashboard = SidebarButton("Project Dashboard", self.scale)
        self.btn_command_center = SidebarButton("Command Center", self.scale)
        self.btn_queue = SidebarButton("Batch Queue", self.scale)
        self.btn_models = SidebarButton("AI Models", self.scale)

        # Settings Group Header
        lbl_system = SectionHeader("SYSTEM", self.scale)
        lbl_system.setStyleSheet(f"color: {ThemeManager.TEXT_MUTED}; font-size: {self.si(10)}px; font-weight: 700; padding: {self.si(4)}px {self.si(8)}px;")

        self.btn_settings = SidebarButton("Settings", self.scale)

        # Set Dashboard as active by default
        self.btn_dashboard.setChecked(True)

        # Connect signals
        self.btn_dashboard.clicked.connect(lambda: self._on_nav_clicked("dashboard", self.btn_dashboard))
        self.btn_command_center.clicked.connect(lambda: self._on_nav_clicked("command_center", self.btn_command_center))
        self.btn_queue.clicked.connect(lambda: self._on_nav_clicked("queue", self.btn_queue))
        self.btn_models.clicked.connect(lambda: self._on_nav_clicked("models", self.btn_models))
        self.btn_settings.clicked.connect(lambda: self._on_nav_clicked("settings", self.btn_settings))

        self.nav_buttons = [
            self.btn_dashboard, 
            self.btn_command_center, 
            self.btn_queue, 
            self.btn_models, 
            self.btn_settings
        ]

        layout.addWidget(self.btn_dashboard)
        layout.addWidget(self.btn_command_center)
        layout.addWidget(self.btn_queue)
        layout.addWidget(self.btn_models)

        layout.addStretch()

        layout.addWidget(lbl_system)
        layout.addSpacing(self.si(2))
        layout.addWidget(self.btn_settings)

    def si(self, val: int) -> int:
        return max(1, int(val * self.scale))

    def _on_nav_clicked(self, destination: str, clicked_btn: SidebarButton):
        """Handle exclusive selection and emit navigation signal."""
        for btn in self.nav_buttons:
            btn.setChecked(btn == clicked_btn)
        self.navigation_requested.emit(destination)

    def set_active(self, destination: str):
        """Programmatically set the active button."""
        target_btn = None
        if destination == "dashboard":
            target_btn = self.btn_dashboard
        elif destination == "command_center":
            target_btn = self.btn_command_center
        elif destination == "queue":
            target_btn = self.btn_queue
        elif destination == "models":
            target_btn = self.btn_models
        elif destination == "settings":
            target_btn = self.btn_settings

        if target_btn:
            for btn in self.nav_buttons:
                btn.setChecked(btn == target_btn)
