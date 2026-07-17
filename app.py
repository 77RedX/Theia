import math

from PyQt6.QtWidgets import QMainWindow, QStackedWidget
from PyQt6.QtGui import QFont, QResizeEvent

from screens.home_screen import HomeScreen
from screens.processing_screen import ProcessingScreen
from screens.comparison_screen import ComparisonScreen


class TheiaApp(QMainWindow):
    """Main application window for Theia Video Enhancer."""

    # Baseline resolution the UI was designed for
    _BASE_W, _BASE_H = 1200, 700

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Theia Video Enhancer")
        self.resize(self._BASE_W, self._BASE_H)
        self.setMinimumSize(900, 600)

        self._current_scale = 1.0
        self._apply_global_stylesheet(1.0)
        self.init_ui()

    # ── Scaling ─────────────────────────────────────────────

    def _scale_factor(self) -> float:
        """Compute scale factor from the current window size relative to baseline."""
        w = self.width()
        h = self.height()
        diag = math.sqrt(w * w + h * h)
        base_diag = math.sqrt(self._BASE_W ** 2 + self._BASE_H ** 2)
        return max(0.85, diag / base_diag)

    def resizeEvent(self, event: QResizeEvent):
        """Recalculate scale and reapply stylesheet + screen layouts on resize."""
        super().resizeEvent(event)
        new_scale = self._scale_factor()
        # Only re-apply if scale changed meaningfully (avoids thrashing)
        if abs(new_scale - self._current_scale) > 0.02:
            self._current_scale = new_scale
            self._apply_global_stylesheet(new_scale)
            # Notify screens so they can rescale their own metrics
            for screen in (self.home_screen, self.processing_screen, self.comparison_screen):
                if hasattr(screen, 'apply_scale'):
                    screen.apply_scale(new_scale)

    # ── Stylesheet ──────────────────────────────────────────

    def _apply_global_stylesheet(self, s: float):
        """Apply a premium dark theme, with every metric scaled by *s*."""
        # Helper to round-scale an int
        def si(v):
            return int(v * s)

        self.setStyleSheet(f"""
            /* ── Base ── */
            QMainWindow {{
                background-color: #0b0b12;
            }}
            QWidget {{
                background-color: transparent;
                font-family: "Segoe UI Variable", "Segoe UI", "Inter", "Roboto", sans-serif;
            }}

            /* ── Typography ── */
            QLabel {{
                color: #e2e8f0;
                background: transparent;
                font-size: {si(14)}px;
            }}
            QLabel#Title {{
                color: #ffffff;
                font-size: {si(36)}px;
                font-weight: 800;
            }}
            QLabel#Subtitle {{
                color: #94a3b8;
                font-size: {si(16)}px;
                font-weight: 500;
            }}
            QLabel#SectionTitle {{
                color: #cbd5e1;
                font-size: {si(15)}px;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            QLabel#Muted {{
                color: #64748b;
                font-size: {si(13)}px;
                font-weight: 500;
            }}
            QLabel#Accent {{
                color: #a78bfa;
                font-size: {si(16)}px;
                font-weight: 700;
            }}

            /* ── Cards ── */
            QFrame#CardPanel {{
                background-color: #151522;
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: {si(20)}px;
            }}

            /* ── Primary Buttons ── */
            QPushButton {{
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #8b5cf6, stop:1 #6366f1);
                color: #ffffff;
                border: none;
                border-radius: {si(12)}px;
                padding: {si(14)}px {si(32)}px;
                font-size: {si(15)}px;
                font-weight: 700;
                min-width: {si(160)}px;
            }}
            QPushButton:hover {{
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #a78bfa, stop:1 #818cf8);
            }}
            QPushButton:pressed {{
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #7c3aed, stop:1 #4f46e5);
            }}
            QPushButton:disabled {{
                background-color: #334155;
                color: #94a3b8;
            }}

            /* ── Secondary / Outline Buttons ── */
            QPushButton#SecondaryButton {{
                background-color: rgba(139, 92, 246, 0.1);
                color: #a78bfa;
                border: 1px solid rgba(139, 92, 246, 0.3);
            }}
            QPushButton#SecondaryButton:hover {{
                background-color: rgba(139, 92, 246, 0.2);
                border: 1px solid rgba(139, 92, 246, 0.5);
            }}
            QPushButton#SecondaryButton:pressed {{
                background-color: rgba(139, 92, 246, 0.3);
            }}

            /* ── Danger Buttons ── */
            QPushButton#DangerButton {{
                background-color: rgba(239, 68, 68, 0.1);
                color: #fca5a5;
                border: 1px solid rgba(239, 68, 68, 0.3);
            }}
            QPushButton#DangerButton:hover {{
                background-color: rgba(239, 68, 68, 0.2);
                border: 1px solid rgba(239, 68, 68, 0.5);
            }}

            /* ── Progress Bar ── */
            QProgressBar {{
                border: none;
                border-radius: {si(10)}px;
                background-color: #1e1e2d;
                min-height: {si(20)}px;
                max-height: {si(20)}px;
                text-align: center;
                color: transparent;
            }}
            QProgressBar::chunk {{
                border-radius: {si(10)}px;
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ec4899, stop:0.5 #8b5cf6, stop:1 #3b82f6
                );
            }}

            /* ── Combo Box ── */
            QComboBox {{
                background-color: #1e1e2d;
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: {si(8)}px;
                padding: {si(8)}px {si(16)}px;
                color: #e2e8f0;
                font-size: {si(14)}px;
                font-weight: 500;
                min-width: {si(150)}px;
            }}
            QComboBox:hover {{
                border: 1px solid rgba(139, 92, 246, 0.5);
            }}
            QComboBox::drop-down {{
                border: none;
                width: {si(30)}px;
                subcontrol-position: right center;
                subcontrol-origin: padding;
            }}
            QComboBox::down-arrow {{
                image: url(assets/dropdown_arrow.svg);
                width: {si(12)}px;
                height: {si(12)}px;
            }}
            QComboBox QAbstractItemView {{
                background-color: #151522;
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: {si(8)}px;
                color: #e2e8f0;
                selection-background-color: #8b5cf6;
                selection-color: #ffffff;
                outline: none;
                padding: {si(4)}px;
                font-size: {si(14)}px;
            }}

            /* ── CheckBox ── */
            QCheckBox {{
                color: #cbd5e1;
                font-size: {si(14)}px;
                spacing: {si(10)}px;
            }}
            QCheckBox::indicator {{
                width: {si(20)}px;
                height: {si(20)}px;
                border-radius: {si(6)}px;
                border: 1px solid rgba(255, 255, 255, 0.2);
                background-color: #151522;
            }}
            QCheckBox::indicator:hover {{
                border: 1px solid #8b5cf6;
            }}
            QCheckBox::indicator:checked {{
                background-color: #8b5cf6;
                border: 1px solid #8b5cf6;
            }}

            /* ── Log / Terminal ── */
            QTextEdit {{
                background-color: #0d0d16;
                color: #10b981;
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: {si(12)}px;
                padding: {si(16)}px;
                font-family: "Cascadia Code", "Consolas", "Fira Code", monospace;
                font-size: {si(14)}px;
                selection-background-color: rgba(139, 92, 246, 0.4);
            }}

            /* ── Scrollbars ── */
            QScrollBar:vertical {{
                background: #0b0b12;
                width: {si(10)}px;
                border-radius: {si(5)}px;
            }}
            QScrollBar::handle:vertical {{
                background: #334155;
                border-radius: {si(5)}px;
                min-height: {si(40)}px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: #475569;
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)

    def init_ui(self):
        """Initialize the central stacked widget and all screens."""
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        # Instantiate screens
        self.home_screen = HomeScreen()
        self.processing_screen = ProcessingScreen()
        self.comparison_screen = ComparisonScreen()

        # Add screens to stacked widget
        self.stacked_widget.addWidget(self.home_screen)
        self.stacked_widget.addWidget(self.processing_screen)
        self.stacked_widget.addWidget(self.comparison_screen)

    def show_home(self):
        """Switch to the Home Screen."""
        self.stacked_widget.setCurrentWidget(self.home_screen)

    def show_processing(self):
        """Switch to the Processing Screen."""
        self.processing_screen.reset()
        self.stacked_widget.setCurrentWidget(self.processing_screen)

    def show_comparison(self):
        """Switch to the Comparison Screen."""
        self.stacked_widget.setCurrentWidget(self.comparison_screen)
