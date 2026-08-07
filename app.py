"""Main application window for Theia Video Enhancer Desktop Suite."""

import math
from pathlib import Path
from PyQt6.QtWidgets import (
    QMainWindow, QStackedWidget, QStatusBar, QWidget, QVBoxLayout, QHBoxLayout, QLabel
)
from PyQt6.QtGui import QFont, QResizeEvent, QIcon
from PyQt6.QtCore import Qt, QSize

from styles.theme_manager import ThemeManager
from screens.home_screen import HomeScreen
from screens.processing_screen import ProcessingScreen
from screens.comparison_screen import ComparisonScreen
from screens.settings_screen import SettingsScreen
from screens.queue_screen import QueueScreen
from screens.models_screen import ModelManagerScreen
from widgets.sidebar import Sidebar
from widgets.title_bar import CustomTitleBar
from widgets.components import StatusBadge

class PlaceholderScreen(QWidget):
    """Placeholder view for features under active development."""
    def __init__(self, title: str):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl = QLabel(f"{title}\n\n(Work In Progress)")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet(f"font-size: 20px; color: {ThemeManager.TEXT_MUTED}; font-weight: bold;")
        layout.addWidget(lbl)


class TheiaApp(QMainWindow):
    """Main application shell for Theia Video Enhancer Desktop."""

    _BASE_W, _BASE_H = 1280, 760

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Theia Video Enhancer")
        self.resize(self._BASE_W, self._BASE_H)
        self.setMinimumSize(960, 640)

        # Set window icon from app_icon.ico
        icon_path = Path(__file__).parent / "app_icon.ico"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        # Frameless window configuration for modern custom title bar
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)

        self._current_scale = 1.0
        self._apply_global_stylesheet(1.0)
        self.init_ui()

    # ── Metric Scaling ────────────────────────────────────────

    def _scale_factor(self) -> float:
        """Compute relative UI scaling factor based on window dimensions."""
        w = self.width()
        h = self.height()
        diag = math.sqrt(w * w + h * h)
        base_diag = math.sqrt(self._BASE_W ** 2 + self._BASE_H ** 2)
        return max(0.85, diag / base_diag)

    def resizeEvent(self, event: QResizeEvent):
        """Recalculate scale metrics and propagate to screens on window resize."""
        super().resizeEvent(event)
        new_scale = self._scale_factor()
        if abs(new_scale - self._current_scale) > 0.02:
            self._current_scale = new_scale
            self._apply_global_stylesheet(new_scale)
            
            # Notify title bar and screens of metric changes
            if hasattr(self, 'title_bar'):
                self.title_bar.scale = new_scale
            if hasattr(self, 'sidebar'):
                self.sidebar.scale = new_scale

            for screen in (
                self.home_screen, self.processing_screen, self.comparison_screen, 
                self.settings_screen, self.queue_screen, self.models_screen
            ):
                if hasattr(screen, 'apply_scale'):
                    screen.apply_scale(new_scale)

    def _apply_global_stylesheet(self, s: float):
        """Apply dynamic QSS stylesheet generated from ThemeManager tokens."""
        self.setStyleSheet(ThemeManager.generate_stylesheet(s))

    # ── UI Construction ───────────────────────────────────────

    def init_ui(self):
        """Build the master frame layout: Title Bar -> Workspace Body (Sidebar + Stack) -> Status Bar."""
        
        # Central Main Widget Shell
        self.main_container = QWidget(self)
        self.setCentralWidget(self.main_container)

        self.root_layout = QVBoxLayout(self.main_container)
        self.root_layout.setContentsMargins(0, 0, 0, 0)
        self.root_layout.setSpacing(0)

        # 1. Custom Title Bar Header
        self.title_bar = CustomTitleBar(self, scale=self._current_scale)
        self.root_layout.addWidget(self.title_bar)

        # 2. Workspace Body Container
        self.workspace_body = QWidget()
        self.body_layout = QHBoxLayout(self.workspace_body)
        self.body_layout.setContentsMargins(0, 0, 0, 0)
        self.body_layout.setSpacing(0)

        # Sidebar Navigation
        self.sidebar = Sidebar(scale=self._current_scale)
        self.body_layout.addWidget(self.sidebar)

        # Central QStackedWidget View Matrix
        self.stacked_widget = QStackedWidget()
        self.body_layout.addWidget(self.stacked_widget, stretch=1)

        self.root_layout.addWidget(self.workspace_body, stretch=1)

        # Instantiate Passive Workspace Screens
        self.home_screen = HomeScreen()
        self.processing_screen = ProcessingScreen()
        self.comparison_screen = ComparisonScreen()
        self.settings_screen = SettingsScreen()
        self.queue_screen = QueueScreen()
        self.models_screen = ModelManagerScreen()
        self.placeholder_screen = PlaceholderScreen("Module Coming Soon")

        # Register Screens in Stack
        self.stacked_widget.addWidget(self.home_screen)          # Index 0
        self.stacked_widget.addWidget(self.processing_screen)    # Index 1
        self.stacked_widget.addWidget(self.comparison_screen)    # Index 2
        self.stacked_widget.addWidget(self.settings_screen)      # Index 3
        self.stacked_widget.addWidget(self.queue_screen)         # Index 4
        self.stacked_widget.addWidget(self.models_screen)        # Index 5
        self.stacked_widget.addWidget(self.placeholder_screen)   # Index 6

        # 3. Modern Status Bar Footer
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Engine Status: Ready")

    # ── Workspace Switching API ───────────────────────────────

    def show_home(self):
        """Switch view to Project Dashboard."""
        self.stacked_widget.setCurrentWidget(self.home_screen)
        self.sidebar.set_active("dashboard")

    def show_processing(self):
        """Switch view to Processing Command Center."""
        self.stacked_widget.setCurrentWidget(self.processing_screen)
        self.sidebar.set_active("command_center")

    def show_command_center(self):
        """Alias for show_processing."""
        self.show_processing()

    def show_comparison(self):
        """Switch view to Review & Comparison Workspace."""
        self.stacked_widget.setCurrentWidget(self.comparison_screen)

    def show_settings(self):
        """Switch view to Settings Panel."""
        self.stacked_widget.setCurrentWidget(self.settings_screen)
        self.sidebar.set_active("settings")

    def show_queue(self):
        """Switch view to Batch Queue workspace."""
        self.stacked_widget.setCurrentWidget(self.queue_screen)
        self.sidebar.set_active("queue")

    def show_models(self):
        """Switch view to Model Manager workspace."""
        self.stacked_widget.setCurrentWidget(self.models_screen)
        self.sidebar.set_active("models")

    def show_placeholder(self):
        """Switch view to generic placeholder."""
        self.stacked_widget.setCurrentWidget(self.placeholder_screen)
