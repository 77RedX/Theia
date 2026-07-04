from PyQt6.QtWidgets import QMainWindow, QStackedWidget

from screens.home_screen import HomeScreen
from screens.settings_screen import SettingsScreen
from screens.processing_screen import ProcessingScreen
from screens.comparison_screen import ComparisonScreen

class TheiaApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Theia Video Enhancer")
        self.resize(1200, 700)
        
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
            }
            QLabel {
                color: #e0e0e0;
            }
            QFrame#CardPanel {
                border: 1px solid #333;
                border-radius: 12px;
                background-color: #2a2a2a;
            }
            QPushButton {
                background-color: #007acc;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #0098ff;
            }
            QPushButton:pressed {
                background-color: #005c99;
            }
            QRadioButton {
                color: #e0e0e0;
                font-size: 14px;
            }
            QComboBox {
                background-color: #333333;
                color: white;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 5px;
            }
            QProgressBar {
                border: 1px solid #444;
                border-radius: 5px;
                text-align: center;
                background-color: #222;
                color: white;
            }
            QProgressBar::chunk {
                background-color: #007acc;
                border-radius: 5px;
            }
            QTextEdit {
                background-color: #1e1e1e;
                color: #00ff00;
                border: 1px solid #444;
                border-radius: 5px;
                font-family: Consolas, monospace;
            }
        """)
        
        self.init_ui()

    def init_ui(self):
        # Create the central stacked widget
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        # Instantiate screens
        self.home_screen = HomeScreen()
        self.settings_screen = SettingsScreen()
        self.processing_screen = ProcessingScreen()
        self.comparison_screen = ComparisonScreen()

        # Add screens to stacked widget
        self.stacked_widget.addWidget(self.home_screen)
        self.stacked_widget.addWidget(self.settings_screen)
        self.stacked_widget.addWidget(self.processing_screen)
        self.stacked_widget.addWidget(self.comparison_screen)

    def show_home(self):
        """Switch to the Home Screen."""
        self.stacked_widget.setCurrentWidget(self.home_screen)

    def show_settings(self):
        """Switch to the Settings Screen."""
        self.stacked_widget.setCurrentWidget(self.settings_screen)

    def show_processing(self):
        """Switch to the Processing Screen."""
        self.processing_screen.reset()
        self.stacked_widget.setCurrentWidget(self.processing_screen)

    def show_comparison(self):
        """Switch to the Comparison Screen."""
        self.stacked_widget.setCurrentWidget(self.comparison_screen)
