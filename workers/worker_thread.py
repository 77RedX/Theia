"""Background worker thread for video processing."""

import traceback
from pathlib import Path
from PyQt6.QtCore import QThread, pyqtSignal


class VideoProcessingWorker(QThread):
    """Runs enhance_video() on a background thread to keep the UI responsive.

    Signals:
        progress_updated(int, int): Emitted with (current_frame, total_frames).
        log_message(str): Emitted with a log line for the processing log.
        processing_finished(bool, str): Emitted with (success, error_message).
    """

    progress_updated = pyqtSignal(int, int)
    log_message = pyqtSignal(str)
    processing_finished = pyqtSignal(bool, str)

    def __init__(self, input_path: str, output_path: str, preset: str, detect_scene_cuts: bool, protect_static_overlays: bool, parent=None):
        super().__init__(parent)
        self.input_path = input_path
        self.output_path = output_path
        self.preset = preset
        self.detect_scene_cuts = detect_scene_cuts
        self.protect_static_overlays = protect_static_overlays
        self._cancelled = False

    def cancel(self):
        """Request cancellation of the processing (thread-safe)."""
        self._cancelled = True

    @property
    def is_cancelled(self) -> bool:
        """Check if cancellation has been requested."""
        return self._cancelled

    def run(self):
        """Execute the video processing pipeline in the background thread."""
        try:
            from video_engine import enhance_video, TheiaConfig

            # Build the progress callback that emits signals
            def progress_callback(current_frame, total_frames):
                if self._cancelled:
                    raise InterruptedError("Processing cancelled by user.")

                self.progress_updated.emit(current_frame, total_frames)

                if current_frame % 25 == 0:
                    self.log_message.emit(
                        f"Processed frame {current_frame} of {total_frames}..."
                    )

            config = TheiaConfig(
                preset=self.preset,
                detect_scene_cuts=self.detect_scene_cuts,
                protect_static_overlays=self.protect_static_overlays,
                progress_callback=progress_callback,
            )

            self.log_message.emit("Initializing video engine...")

            enhance_video(
                input_video=self.input_path,
                output_video=self.output_path,
                config=config,
            )

            if self._cancelled:
                self.processing_finished.emit(False, "Processing cancelled by user.")
            else:
                self.processing_finished.emit(True, "")

        except InterruptedError:
            self.log_message.emit("Pipeline stopped due to user cancellation.")
            self.processing_finished.emit(False, "Processing cancelled by user.")
        except Exception as e:
            tb = traceback.format_exc()
            self.log_message.emit(f"ERROR: {e}")
            self.processing_finished.emit(False, str(e))
        finally:
            # Ensure QThread loop terminates cleanly
            self.quit()
