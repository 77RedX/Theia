"""Application Controller for the Theia Video Enhancer Desktop Suite."""

import time
from pathlib import Path
from PyQt6.QtWidgets import QMessageBox, QFileDialog
from PyQt6.QtCore import QStandardPaths

from workers.worker_thread import VideoProcessingWorker
from widgets.components import StatusBadge


class ApplicationController:
    """Coordinates application flow between views, task queue, and the underlying video engine.

    Owns operational business logic and batch queue state. Workspace screens remain passive.
    MainWindow handles window management and QStackedWidget page switching.
    """

    def __init__(self, main_window):
        self.main_window = main_window
        self._worker = None
        self._active_workers = [] # Keep references to prevent premature QThread destruction
        self._start_time = None
        self._input_path = None
        self._output_path = None
        self._output_ext = None
        self._preset = "basic"

        # Batch Queue State
        self._task_queue = [] # List of dicts representing pending jobs

        self._connect_signals()

    def _connect_signals(self):
        """Connect view signals to controller handler methods."""
        # Home Screen requests
        self.main_window.home_screen.request_processing.connect(
            self.start_processing
        )

        # Recent Renders selection request
        self.main_window.home_screen.render_selected.connect(
            self._on_recent_render_selected
        )

        # Comparison Screen requests
        self.main_window.comparison_screen.request_home.connect(
            self._show_home
        )

        # Settings Screen requests
        self.main_window.settings_screen.request_home.connect(
            self._show_home
        )

        # Processing Screen requests
        self.main_window.processing_screen.cancel_requested.connect(
            self._on_cancel_requested
        )

        # Queue Screen requests
        self.main_window.queue_screen.request_command_center.connect(
            self._show_processing
        )
        self.main_window.queue_screen.item_removed.connect(
            self._on_queue_item_removed
        )
        self.main_window.queue_screen.clear_queue_requested.connect(
            self._on_clear_queue
        )

        # Title bar status badge click navigation
        self.main_window.title_bar.status_badge_clicked.connect(
            self._show_processing
        )

        # Sidebar navigation requests
        self.main_window.sidebar.navigation_requested.connect(
            self._on_navigation_requested
        )

    def _on_navigation_requested(self, destination: str):
        """Handle sidebar navigation requests."""
        if destination == "dashboard":
            self.main_window.show_home()
        elif destination == "command_center":
            self.main_window.show_processing()
        elif destination == "queue":
            self.main_window.show_queue()
        elif destination == "models":
            self.main_window.show_models()
        elif destination == "settings":
            self.main_window.show_settings()

    def _show_home(self):
        """Navigate to Project Dashboard."""
        self.main_window.show_home()

    def _show_processing(self):
        """Navigate to AI Command Center workspace."""
        self.main_window.show_processing()

    def _on_recent_render_selected(self, original_path: str, output_path: str):
        """Handle click/double-click on recent renders item."""
        orig_p = Path(original_path) if original_path else None
        out_p = Path(output_path) if output_path else None

        missing = None
        if not out_p or not out_p.exists():
            missing = output_path
        elif not orig_p or not orig_p.exists():
            missing = original_path

        if missing:
            QMessageBox.warning(
                self.main_window,
                "Video File Not Found",
                f"The requested render video file could not be found at location:\n\n{missing}"
            )
            return

        # Load video pair into review workspace
        cs = self.main_window.comparison_screen
        cs.load_videos(original_path, output_path)
        self.main_window.show_comparison()
        cs.toggle_playback()

    def start_processing(self, preset: str, detect_scene_cuts: bool, protect_static_overlays: bool):
        """Launch or queue video enhancement workflow."""
        home = self.main_window.home_screen
        input_path = home.input_path

        if not input_path:
            return

        # Derive output format from input file extension
        input_ext = Path(input_path).suffix.lstrip(".").lower()
        output_ext = input_ext if input_ext in ("mp4", "mkv") else "mp4"

        # Prompt user for output save file path
        default_dir = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.MoviesLocation)
        default_path = str(Path(default_dir) / f"enhanced_{Path(input_path).stem}.{output_ext}")

        output_path, _ = QFileDialog.getSaveFileName(
            self.main_window,
            "Save Enhanced Video",
            default_path,
            f"Video Files (*.{output_ext})"
        )

        if not output_path:
            return

        task_item = {
            "input_path": input_path,
            "output_path": output_path,
            "output_ext": output_ext,
            "preset": preset,
            "detect_scene_cuts": detect_scene_cuts,
            "protect_static_overlays": protect_static_overlays
        }

        # If a task is already actively processing on worker thread, queue it automatically!
        if self._worker is not None and self._worker.isRunning():
            self._task_queue.append(task_item)
            self._update_queue_ui()
            
            QMessageBox.information(
                self.main_window,
                "Task Queued",
                f"A processing task is currently active.\n'{Path(input_path).name}' has been added to the Batch Queue (Position {len(self._task_queue)})."
            )
            self.main_window.show_queue()
            return

        # No active worker, run task immediately!
        self._run_task(task_item)

    def _run_task(self, task_item: dict):
        """Execute task on background worker thread."""
        self._input_path = task_item["input_path"]
        self._output_path = task_item["output_path"]
        self._output_ext = task_item["output_ext"]
        self._preset = task_item["preset"]

        # Clean up completed workers from registry
        self._active_workers = [w for w in self._active_workers if w.isRunning()]
        if self._worker is not None:
            if self._worker.isRunning():
                self._worker.quit()
                self._worker.wait(3000)
            self._active_workers.append(self._worker)
            self._worker = None

        # Reset and navigate to Processing Command Center
        self.main_window.processing_screen.reset()
        self.main_window.show_processing()

        ps = self.main_window.processing_screen
        ps.set_status("Starting engine...")
        ps.set_eta("Calculating...")

        self.main_window.title_bar.update_status("PROCESSING", StatusBadge.STATE_INFO)
        self.main_window.queue_screen.update_active_task(
            Path(self._input_path).name, self._preset, 0, "Calculating...", "0 / 0", True
        )

        self._start_time = time.monotonic()

        # Instantiate worker thread
        self._worker = VideoProcessingWorker(
            self._input_path,
            self._output_path,
            self._preset,
            task_item["detect_scene_cuts"],
            task_item["protect_static_overlays"]
        )
        self._worker.progress_updated.connect(self._on_progress_updated)
        self._worker.log_message.connect(self._on_log_message)
        self._worker.processing_finished.connect(self._on_processing_finished)
        self._worker.start()

    # ── Queue Operations ──────────────────────────────────────

    def _update_queue_ui(self):
        """Update QueueScreen with pending items."""
        self.main_window.queue_screen.set_queue_items(self._task_queue)

    def _on_queue_item_removed(self, index: int):
        """Remove a pending item from the queue."""
        if 0 <= index < len(self._task_queue):
            removed = self._task_queue.pop(index)
            self._update_queue_ui()
            self.main_window.status_bar.showMessage(f"Removed '{Path(removed['input_path']).name}' from Batch Queue.", 3000)

    def _on_clear_queue(self):
        """Clear all pending queue items."""
        self._task_queue.clear()
        self._update_queue_ui()
        self.main_window.status_bar.showMessage("Batch Queue cleared.", 3000)

    # ── Worker Signal Event Handlers ──────────────────────────

    def _on_progress_updated(self, current_frame: int, total_frames: int):
        """Update processing progress and ETA calculation."""
        ps = self.main_window.processing_screen
        ps.set_frame(current_frame, total_frames)

        percent = 0
        eta_str = "Calculating..."
        frame_str = f"{current_frame} / {total_frames}"

        if total_frames > 0:
            percent = min(100, int((current_frame / total_frames) * 100))
            ps.set_progress(percent)

            elapsed = time.monotonic() - self._start_time
            fraction_done = current_frame / total_frames

            if fraction_done > 0.01 and elapsed > 1.0:
                estimated_total = elapsed / fraction_done
                remaining = max(0, estimated_total - elapsed)
                eta_str = self._format_eta(remaining)

                ps.set_eta(eta_str)
                ps.set_status("Processing frames...")
            else:
                ps.set_eta("Calculating...")
                ps.set_status("Starting engine...")

        # Keep QueueScreen active card in sync
        self.main_window.queue_screen.update_active_task(
            Path(self._input_path).name if self._input_path else "Processing",
            self._preset, percent, eta_str, frame_str, True
        )

    def _on_log_message(self, message: str):
        """Append log message to terminal and update status bar."""
        self.main_window.processing_screen.append_log(message)
        self.main_window.status_bar.showMessage(message, 3000)

    def _on_processing_finished(self, success: bool, error_message: str):
        """Handle processing completion and automatic queue advancement."""
        ps = self.main_window.processing_screen
        
        # Safely handle worker thread lifecycle to prevent QThread destruction crashes
        worker = self._worker
        if worker is not None:
            if worker.isRunning():
                worker.quit()
                worker.wait(3000)
            self._active_workers.append(worker)
            self._worker = None

        self._active_workers = [w for w in self._active_workers if w.isRunning()]

        if success:
            ps.set_status("Completed")
            ps.set_eta("Done")
            ps.set_progress(100)
            ps.append_log("Processing completed successfully!")

            completed_input = self._input_path
            completed_output = self._output_path

            # Add to Recent Renders history on HomeScreen
            elapsed = time.monotonic() - (self._start_time or time.monotonic())
            self.main_window.home_screen.add_recent_render(
                completed_input, completed_output, self._preset, self._format_eta(elapsed), "Completed"
            )

            # Check if more tasks are waiting in the queue
            if len(self._task_queue) > 0:
                self.main_window.status_bar.showMessage("Completed task. Starting next queued job...", 4000)
                next_task = self._task_queue.pop(0)
                self._update_queue_ui()
                self._run_task(next_task)
                return

            # No remaining queue tasks
            self.main_window.title_bar.update_status("COMPLETED", StatusBadge.STATE_SUCCESS)
            self.main_window.queue_screen.update_active_task("", "", 0, "—", "—", False)

            # Populate comparison workspace
            cs = self.main_window.comparison_screen
            cs.load_videos(completed_input, completed_output)
            self.main_window.show_comparison()
            cs.toggle_playback()
        else:
            self.main_window.queue_screen.update_active_task("", "", 0, "—", "—", False)
            if "cancelled" in error_message.lower():
                ps.set_status("Cancelled")
                ps.set_eta("—")
                ps.set_progress(0)
                ps.set_frame(0, 0)
                ps.append_log("Processing was cancelled by user.")
                self.main_window.title_bar.update_status("CANCELLED", StatusBadge.STATE_WARNING)
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
                self.main_window.title_bar.update_status("ERROR", StatusBadge.STATE_DANGER)
                QMessageBox.critical(
                    self.main_window,
                    "Processing Error",
                    f"An error occurred:\n{error_message}"
                )

    def _on_cancel_requested(self):
        """Cancel active worker thread execution."""
        if self._worker is not None and self._worker.isRunning():
            self._worker.cancel()
            self.main_window.processing_screen.set_status("Cancelling...")
            self.main_window.title_bar.update_status("CANCELLING...", StatusBadge.STATE_WARNING)
            self.main_window.processing_screen.append_log(
                "Cancellation requested, waiting for pipeline thread to finish..."
            )

    # ── Helpers ───────────────────────────────────────────────

    @staticmethod
    def _format_eta(seconds: float) -> str:
        """Format seconds into human-readable ETA representation."""
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
