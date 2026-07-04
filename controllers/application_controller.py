from PyQt6.QtWidgets import QMessageBox, QFileDialog
from video_engine import enhance_video, TheiaConfig

class ApplicationController:
    """
    Main application controller.
    Owns the application workflow and coordinates communication between screens.
    """
    def __init__(self, main_window):
        self.main_window = main_window
        self.connect_signals()

    def connect_signals(self):
        """Connect UI signals to controller methods."""
        self.main_window.home_screen.request_settings.connect(self.show_settings)
        self.main_window.home_screen.request_processing.connect(self.start_processing)
        self.main_window.settings_screen.request_home.connect(self.show_home)
        self.main_window.comparison_screen.request_home.connect(self.show_home)

    def show_home(self):
        """Transition to Home Screen."""
        self.main_window.show_home()

    def show_settings(self):
        """Transition to Settings Screen."""
        self.main_window.show_settings()

    def start_processing(self):
        """Transition to Processing Screen and prepare for processing."""
        # 1. Read input video path
        input_path = self.main_window.home_screen.input_path
        if not input_path:
            return

        # 2. Read selected preset
        preset = self.main_window.settings_screen.get_selected_preset().lower()
        if preset != "fast":
            QMessageBox.information(
                self.main_window, 
                "Preset Unavailable", 
                "Only the 'Fast' preset is currently available in this version."
            )
            return

        # 3. Prompt for output path
        output_format = self.main_window.settings_screen.get_output_format().lower()
        default_ext = output_format if output_format else "mp4"
        
        output_path, _ = QFileDialog.getSaveFileName(
            self.main_window,
            "Save Enhanced Video",
            f"enhanced_video.{default_ext}",
            f"Video Files (*.{default_ext})"
        )

        if not output_path:
            return

        # 4. Navigate to ProcessingScreen and reset
        self.main_window.show_processing()
        processing_screen = self.main_window.processing_screen
        
        # 5. Set status and append log
        processing_screen.set_status("Starting engine...")
        processing_screen.append_log("Initializing video engine...")

        # 6. Create progress callback
        def progress_callback(current_frame, total_frames):
            processing_screen.set_frame(current_frame, total_frames)
            if total_frames > 0:
                percent = int((current_frame / total_frames) * 100)
                processing_screen.set_progress(percent)
            
            if current_frame % 25 == 0:
                processing_screen.append_log(f"Processed frame {current_frame} of {total_frames}...")

        # 7. Create config with the callback
        config = TheiaConfig(preset="fast", progress_callback=progress_callback)

        # 8 & 10. Call enhance_video and catch exceptions
        try:
            enhance_video(
                input_video=input_path,
                output_video=output_path,
                config=config
            )
            
            # 9. When processing completes
            processing_screen.set_status("Completed")
            
            self.main_window.show_comparison()
            comparison_screen = self.main_window.comparison_screen
            comparison_screen.set_original_video(input_path)
            comparison_screen.set_enhanced_video(output_path)
            comparison_screen.set_preset("Fast")
            comparison_screen.set_output_format(output_format.upper())
            
        except Exception as e:
            QMessageBox.critical(self.main_window, "Processing Error", f"An error occurred: {str(e)}")
            processing_screen.append_log(f"ERROR: {str(e)}")
            processing_screen.set_status("Failed")
