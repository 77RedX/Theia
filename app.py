from PyQt6.QtWidgets import QMainWindow, QStackedWidget
from PyQt6.QtGui import QFont

from screens.home_screen import HomeScreen
from screens.processing_screen import ProcessingScreen
from screens.comparison_screen import ComparisonScreen


class TheiaApp(QMainWindow):
    """Main application window for Theia Video Enhancer."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Theia Video Enhancer")
        self.resize(1200, 700)
        self.setMinimumSize(900, 600)

        self._apply_global_stylesheet()
        self.init_ui()

    def _apply_global_stylesheet(self):
        """Apply a premium dark theme across the entire application."""
        self.setStyleSheet("""
            /* ── Base ── */
            QMainWindow {
                background-color: #0f0f0f;
            }
            QWidget {
                background-color: transparent;
                font-family: "Segoe UI", "Arial", sans-serif;
            }

            /* ── Typography ── */
            QLabel {
                color: #e0e0e0;
                background: transparent;
            }
            QLabel#Title {
                color: #ffffff;
                font-size: 28px;
                font-weight: bold;
            }
            QLabel#Subtitle {
                color: #888888;
                font-size: 15px;
            }
            QLabel#SectionTitle {
                color: #cccccc;
                font-size: 14px;
                font-weight: bold;
            }
            QLabel#Muted {
                color: #666666;
                font-size: 12px;
            }
            QLabel#Accent {
                color: #6c63ff;
            }

            /* ── Cards ── */
            QFrame#CardPanel {
                background-color: #1a1a2e;
                border: 1px solid #2a2a4a;
                border-radius: 16px;
            }

            /* ── Primary Buttons ── */
            QPushButton {
                background-color: #6c63ff;
                color: #ffffff;
                border: none;
                border-radius: 10px;
                padding: 14px 32px;
                font-size: 14px;
                font-weight: bold;
                min-width: 160px;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #7b73ff;
            }
            QPushButton:pressed {
                background-color: #5a52e0;
            }

            /* ── Secondary / Outline Buttons ── */
            QPushButton#SecondaryButton {
                background-color: transparent;
                color: #6c63ff;
                border: 2px solid #6c63ff;
            }
            QPushButton#SecondaryButton:hover {
                background-color: rgba(108, 99, 255, 0.1);
            }
            QPushButton#SecondaryButton:pressed {
                background-color: rgba(108, 99, 255, 0.2);
            }

            /* ── Danger Buttons ── */
            QPushButton#DangerButton {
                background-color: transparent;
                color: #ff6b6b;
                border: 2px solid #ff6b6b;
            }
            QPushButton#DangerButton:hover {
                background-color: rgba(255, 107, 107, 0.1);
            }

            /* ── Progress Bar ── */
            QProgressBar {
                border: none;
                border-radius: 8px;
                background-color: #1a1a2e;
                min-height: 16px;
                max-height: 16px;
                text-align: center;
                color: transparent;
            }
            QProgressBar::chunk {
                border-radius: 8px;
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6c63ff, stop:1 #3f8efc
                );
            }

            /* ── Log / Terminal ── */
            QTextEdit {
                background-color: #0a0a14;
                color: #4ade80;
                border: 1px solid #2a2a4a;
                border-radius: 10px;
                padding: 12px;
                font-family: "Cascadia Code", "Consolas", monospace;
                font-size: 13px;
                selection-background-color: #6c63ff;
            }

            /* ── Scrollbars ── */
            QScrollBar:vertical {
                background: #0a0a14;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #333;
                border-radius: 4px;
                min-height: 30px;
            }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }
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
