"""Application Controller for the Theia Video Enhancer."""

import time
from pathlib import Path
from PyQt6.QtWidgets import QMessageBox, QFileDialog

from workers.worker_thread import VideoProcessingWorker


class ApplicationController:
    """Coordinates the application workflow between screens and the engine.

    Owns all business logic. Screens remain passive (display + emit signals).
    MainWindow only manages the QStackedWidget page switching.
    """

    def __init__(self, main_window):
        self.main_window = main_window
        self._worker = None
        self._start_time = None
        self._input_path = None
        self._output_path = None
        self._output_ext = None
        self._connect_signals()

    def _connect_signals(self):
        """Connect screen signals to controller methods."""
        self.main_window.home_screen.request_processing.connect(
            self.start_processing
        )
        self.main_window.comparison_screen.request_home.connect(
            self._show_home
        )
        self.main_window.processing_screen.cancel_requested.connect(
            self._on_cancel_requested
        )

    def _show_home(self):
        """Navigate to the Home Screen."""
        self.main_window.show_home()

    def start_processing(self):
        """Launch the processing pipeline on a background worker thread.

        1. Read input path and auto-detected metadata from HomeScreen.
        2. Prompt the user for an output save location.
        3. Navigate to the ProcessingScreen.
        4. Spawn a worker thread to run the engine.
        5. Worker signals drive all further UI updates and transitions.
        """
        home = self.main_window.home_screen
        input_path = home.input_path

        if not input_path:
            return

        # ── Derive output format from the input file's extension ──
        input_ext = Path(input_path).suffix.lstrip(".").lower()
        output_ext = input_ext if input_ext in ("mp4", "mkv") else "mp4"

        # ── Prompt user for output save location ──
        output_path, _ = QFileDialog.getSaveFileName(
            self.main_window,
            "Save Enhanced Video",
            f"enhanced_video.{output_ext}",
            f"Video Files (*.{output_ext})"
        )

        if not output_path:
            return

        # Store paths for use in completion handler
        self._input_path = input_path
        self._output_path = output_path
        self._output_ext = output_ext

        # ── Navigate to ProcessingScreen ──
        self.main_window.show_processing()
        ps = self.main_window.processing_screen

        ps.set_status("Starting engine...")
        ps.set_eta("Calculating...")

        # ── Record start time for ETA calculation ──
        self._start_time = time.monotonic()

        # ── Create and start the worker thread ──
        self._worker = VideoProcessingWorker(input_path, output_path)
        self._worker.progress_updated.connect(self._on_progress_updated)
        self._worker.log_message.connect(self._on_log_message)
        self._worker.processing_finished.connect(self._on_processing_finished)
        self._worker.start()

    # ── Worker signal handlers ──────────────────────────────

    def _on_progress_updated(self, current_frame: int, total_frames: int):
        """Update the processing screen with progress and calculated ETA."""
        ps = self.main_window.processing_screen

        # Update frame counter
        ps.set_frame(current_frame, total_frames)

        # Update progress bar
        if total_frames > 0:
            percent = min(100, int((current_frame / total_frames) * 100))
            ps.set_progress(percent)

            # ── ETA calculation ──
            elapsed = time.monotonic() - self._start_time
            fraction_done = current_frame / total_frames

            if fraction_done > 0.01 and elapsed > 1.0:
                # Estimate remaining time from elapsed and fraction completed
                estimated_total = elapsed / fraction_done
                remaining = max(0, estimated_total - elapsed)

                # Format as human-readable string
                ps.set_eta(self._format_eta(remaining))
                ps.set_status("Processing frames...")
            else:
                ps.set_eta("Calculating...")
                ps.set_status("Starting engine...")

    def _on_log_message(self, message: str):
        """Append a log message to the processing screen."""
        self.main_window.processing_screen.append_log(message)

    def _on_processing_finished(self, success: bool, error_message: str):
        """Handle processing completion — navigate to results or show error."""
        ps = self.main_window.processing_screen

        if success:
            ps.set_status("Completed")
            ps.set_eta("Done")
            ps.set_progress(100)
            ps.append_log("Processing completed successfully!")

            # ── Populate ComparisonScreen ──
            cs = self.main_window.comparison_screen
            cs.set_original_video(self._input_path)
            cs.set_enhanced_video(self._output_path)
            cs.set_preset("Fast")
            cs.set_output_format(self._output_ext.upper())

            home = self.main_window.home_screen
            if home.detected_fps is not None:
                cs.set_original_fps(str(home.detected_fps))
                cs.set_enhanced_fps(str(round(home.detected_fps * 2, 2)))

            self.main_window.show_comparison()

            # Auto-start side-by-side video playback
            cs.start_playback()
        else:
            if "cancelled" in error_message.lower():
                ps.set_status("Cancelled")
                ps.set_eta("—")
                ps.append_log("Processing was cancelled by user.")
                QMessageBox.information(
                    self.main_window,
                    "Cancelled",
                    "Processing was cancelled."
                )
                self.main_window.show_home()
            else:
                ps.set_status("Failed")
                ps.set_eta("—")
                ps.append_log(f"ERROR: {error_message}")
                QMessageBox.critical(
                    self.main_window,
                    "Processing Error",
                    f"An error occurred:\n{error_message}"
                )

        # Cleanup worker reference
        self._worker = None

    def _on_cancel_requested(self):
        """Cancel the running worker thread."""
        if self._worker is not None and self._worker.isRunning():
            self._worker.cancel()
            self.main_window.processing_screen.set_status("Cancelling...")
            self.main_window.processing_screen.append_log(
                "Cancellation requested, waiting for current frame..."
            )

    # ── Helpers ─────────────────────────────────────────────

    @staticmethod
    def _format_eta(seconds: float) -> str:
        """Format seconds into a human-readable ETA string.

        Args:
            seconds: Remaining seconds.

        Returns:
            Formatted string like '2m 15s', '45s', or '1h 3m'.
        """
        seconds = int(seconds)
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            m, s = divmod(seconds, 60)
            return f"{m}m {s}s"
        else:
            h, remainder = divmod(seconds, 3600)
            m, s = divmod(remainder, 60)
            return f"{h}h {m}m"
