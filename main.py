"""
Theia Video Enhancer — main.py
Entry point. Wires all screens together via QStackedWidget.

Navigation flow:
    HomeScreen  →  SettingsScreen  →  ProcessingScreen  →  ResultsScreen
         ↑               ↑                   ↑
         └───────────────┴───────────────────┘  (back / new video)

Integration with Person 3:
    When predict_video() is ready, edit screens/processing_screen.py
    and uncomment the `real_processing()` method, then call it in `run()`.
    No changes needed here in main.py.
"""

import sys
import os
from datetime import datetime

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QStackedWidget,
    QVBoxLayout, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QPalette, QColor

from theme import APP_STYLESHEET, COLORS
from screens import HomeScreen, SettingsScreen, ProcessingScreen, ResultsScreen


# ── Page indices for QStackedWidget ───────────────────────────────────────
PAGE_HOME       = 0
PAGE_SETTINGS   = 1
PAGE_PROCESSING = 2
PAGE_RESULTS    = 3


class TheiaApp(QMainWindow):
    """
    Main application window.
    Holds a QStackedWidget and coordinates data passing between screens.
    """

    def __init__(self):
        super().__init__()
        self._video_path  = None
        self._output_path = None
        self._quality     = "Balanced"
        self._fps_label   = "30 → 60 fps"

        self._setup_window()
        self._setup_screens()
        self._connect_signals()

    # ── Window setup ──────────────────────────────────────────────────────
    def _setup_window(self):
        self.setWindowTitle("Theia Video Enhancer")
        self.resize(860, 700)
        self.setMinimumSize(760, 580)

        # Centre on screen
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width()  - self.width())  // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

        self.setStyleSheet(APP_STYLESHEET)

    # ── Screen setup ──────────────────────────────────────────────────────
    def _setup_screens(self):
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.home_screen       = HomeScreen()
        self.settings_screen   = SettingsScreen()
        self.processing_screen = ProcessingScreen()
        self.results_screen    = ResultsScreen()

        self.stack.addWidget(self.home_screen)        # PAGE_HOME
        self.stack.addWidget(self.settings_screen)    # PAGE_SETTINGS
        self.stack.addWidget(self.processing_screen)  # PAGE_PROCESSING
        self.stack.addWidget(self.results_screen)     # PAGE_RESULTS

        self.stack.setCurrentIndex(PAGE_HOME)

    # ── Signal wiring ─────────────────────────────────────────────────────
    def _connect_signals(self):
        # Home → Settings
        self.home_screen.proceed.connect(self._on_video_selected)

        # Settings → Processing  (or back to Home)
        self.settings_screen.proceed.connect(self._on_settings_confirmed)
        self.settings_screen.back.connect(lambda: self._go_to(PAGE_HOME))

        # Processing → Results  (or back to Settings on cancel)
        self.processing_screen.finished.connect(self._on_processing_done)
        self.processing_screen.cancelled.connect(lambda: self._go_to(PAGE_SETTINGS))

        # Results → Home (new video)
        self.results_screen.new_video.connect(self._on_new_video)
        self.results_screen.export_done.connect(self._on_exported)

    # ── Navigation helpers ────────────────────────────────────────────────
    def _go_to(self, page_index):
        self.stack.setCurrentIndex(page_index)

    # ── Signal handlers ───────────────────────────────────────────────────
    def _on_video_selected(self, path):
        """Home → Settings: store selected video path and advance."""
        self._video_path = path
        self._go_to(PAGE_SETTINGS)

    def _on_settings_confirmed(self, quality, fps_label):
        """Settings → Processing: build output path, start worker."""
        self._quality   = quality
        self._fps_label = fps_label

        # Ensure outputs folder exists
        out_dir = os.path.join(os.path.dirname(__file__), "outputs")
        os.makedirs(out_dir, exist_ok=True)

        # Build unique output filename
        basename  = os.path.splitext(os.path.basename(self._video_path))[0]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_name  = f"{basename}_theia_{timestamp}.mp4"
        self._output_path = os.path.join(out_dir, out_name)

        self._go_to(PAGE_PROCESSING)

        # Kick off processing
        self.processing_screen.start_processing(
            input_path  = self._video_path,
            output_path = self._output_path,
            quality     = self._quality,
            fps_label   = self._fps_label,
        )

    def _on_processing_done(self, output_path):
        """Processing → Results: pass all info to results screen."""
        self._output_path = output_path
        self.results_screen.set_result(
            input_path  = self._video_path,
            output_path = self._output_path,
            quality     = self._quality,
            fps_label   = self._fps_label,
        )
        self._go_to(PAGE_RESULTS)

    def _on_new_video(self):
        """Results → Home: reset state for a fresh session."""
        self._video_path  = None
        self._output_path = None
        # Reset home screen to initial state
        self.home_screen.selected_video = None
        self.home_screen.file_card.hide()
        self.home_screen.drop_zone.show()
        self.home_screen.browse_btn.setText("  ⬆  Browse for Video")
        self.home_screen.continue_btn.setEnabled(False)
        self._go_to(PAGE_HOME)

    def _on_exported(self, save_path):
        """Just log the export; user is already notified by dialog."""
        print(f"[Theia] Exported to: {save_path}")

    # ── Graceful close ────────────────────────────────────────────────────
    def closeEvent(self, event):
        """Warn if processing is still running."""
        if (self.stack.currentIndex() == PAGE_PROCESSING and
                self.processing_screen._worker and
                self.processing_screen._worker.isRunning()):
            reply = QMessageBox.question(
                self, "Processing in Progress",
                "A video is currently being processed.\n\n"
                "Closing now will cancel it. Continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.processing_screen._worker.cancel()
                self.processing_screen._worker.wait()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


# ── Entry point ────────────────────────────────────────────────────────────
def main():
    # High-DPI support
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("Theia Video Enhancer")
    app.setApplicationVersion("0.1.0")
    app.setOrganizationName("Theia")

    # Force dark palette at OS level
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window,          QColor(COLORS["bg_deep"]))
    palette.setColor(QPalette.ColorRole.WindowText,      QColor(COLORS["text_primary"]))
    palette.setColor(QPalette.ColorRole.Base,            QColor(COLORS["bg_surface"]))
    palette.setColor(QPalette.ColorRole.AlternateBase,   QColor(COLORS["bg_raised"]))
    palette.setColor(QPalette.ColorRole.Text,            QColor(COLORS["text_primary"]))
    palette.setColor(QPalette.ColorRole.Button,          QColor(COLORS["bg_raised"]))
    palette.setColor(QPalette.ColorRole.ButtonText,      QColor(COLORS["text_primary"]))
    palette.setColor(QPalette.ColorRole.Highlight,       QColor(COLORS["accent"]))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#FFFFFF"))
    app.setPalette(palette)

    window = TheiaApp()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
