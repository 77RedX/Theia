# Theia Video Enhancer - Progress Journal

## Overview
This journal tracks the development of the **Theia Video Enhancer**, an AI-powered desktop application for video frame interpolation. The application is built using Python and PyQt6, focusing on a clean, modular object-oriented architecture.

## 2026-07-04

### 1. Project Initialization & Architecture Setup
**Objective**: Establish a scalable and maintainable foundation for the application.
- **Action**: Created a modular directory structure (`assets/`, `screens/`, `services/`, `styles/`, `widgets/`) to separate UI components from business logic and assets.
- **Implementation**: 
  - Set up `main.py` as the application entry point to cleanly handle the `QApplication` lifecycle.
  - Implemented `app.py` as the `QMainWindow`, utilizing a `QStackedWidget` as the central widget. This architectural choice allows for seamless navigation between different screens (Home, Settings, Processing, Comparison) within a single window, ensuring a smooth, modern user experience without the clutter of multiple dialogs.

### 2. Home Screen Implementation
**Objective**: Build a welcoming and intuitive landing page for users to start the enhancement process.
- **Action**: Developed the `HomeScreen` UI inside `screens/home_screen.py`.
- **Implementation**: 
  - Built a responsive UI using a combination of `QVBoxLayout` and `QHBoxLayout`, avoiding rigid absolute positioning so the app gracefully handles window resizing.
  - Designed a modern "Card" layout using a styled `QFrame` to group the main interaction elements clearly.
  - **Video Selection**: Integrated a native `QFileDialog` tied to the "Upload Video" button. Added file filters to restrict selection to supported video formats (`.mp4`, `.mkv`, `.avi`, `.mov`). Utilized `pathlib.Path` to extract and display only the selected filename to the user for a cleaner UI, while securely storing the full absolute path in memory for future backend processing.

### 3. Settings Screen Implementation
**Objective**: Provide users with fine-grained control over the AI frame interpolation parameters.
- **Action**: Developed the `SettingsScreen` UI inside `screens/settings_screen.py`.
- **Implementation**: 
  - Matched the design language of the Home screen (consistent margins, spacing, and card styles) to maintain visual continuity across the application.
  - **Configuration Options**:
    - *Quality Preset*: Utilized grouped `QRadioButton`s for Fast, Balanced (default), and Quality presets.
    - *Output FPS*: Implemented an exclusive `QButtonGroup` allowing the user to select target framerates (24→48, 30→60, 60→120).
    - *Output Format*: Added a `QComboBox` to offer output container selection (MP4 vs MKV).
  - **Encapsulation & Data Flow**: Designed clear, documented public accessor methods (`get_selected_preset()`, `get_selected_fps()`, `get_output_format()`). This ensures that when the backend engine eventually runs, it can safely and reliably query the user's configurations without needing to interact directly with the UI widgets.

### 4. Navigation Architecture
**Objective**: Enable seamless transitions between UI screens without tight coupling.
- **Action**: Implemented signal/slot-based navigation between `HomeScreen` and `SettingsScreen`.
- **Implementation**: 
  - To preserve modularity, individual screens do not import or hold references to the main window. Instead, they define native `pyqtSignal` events (e.g., `request_settings`, `request_home`).
  - When navigation buttons are clicked, the screens simply emit these signals.
  - The `TheiaApp` (MainWindow) acts as the central controller. It connects to these signals and handles the actual navigation by switching the `QStackedWidget`'s active index (`setCurrentWidget()`). This architecture strictly adheres to the Single Responsibility Principle and avoids circular dependencies.

### 5. Processing Screen Implementation
**Objective**: Build a real-time feedback UI for the user during long-running video enhancements.
- **Action**: Developed the `ProcessingScreen` UI inside `screens/processing_screen.py`.
- **Implementation**: 
  - Maintained visual consistency with the card-based layout using `QFrame`.
  - Added a `QProgressBar` and dynamic labels to track processing completion percentage, current frame over total frames, ETA, and current status.
  - Implemented a read-only `QTextEdit` component to stream timestamped logs to the user directly from the future processing engine.
  - Created a robust set of public methods (`set_progress`, `set_frame`, `set_status`, `set_eta`, `append_log`, `reset`). This acts as an API boundary: the engine can update the screen simply by calling these methods without needing to understand the underlying UI hierarchy or logic.

### 6. Comparison Screen Implementation
**Objective**: Provide users with a side-by-side comparison of their original and enhanced videos, along with export options.
- **Action**: Developed the `ComparisonScreen` UI inside `screens/comparison_screen.py`.
- **Implementation**: 
  - Continued using the established card-based `QFrame` design language with fully responsive layouts.
  - Built a split-view comparison section featuring two equal-sized `QFrame` panels designated for the original and enhanced video previews.
  - Implemented an information dashboard displaying the original FPS, target FPS, chosen preset, and format container.
  - Created a robust suite of setter methods (`set_original_fps`, `set_enhanced_fps`, `set_preset`, `set_output_format`, `set_original_video`, `set_enhanced_video`, and `reset`). This enables the backend to safely pass the processing results to the UI without touching the internal Qt widgets directly.
  - Utilized `pathlib.Path` to extract clear, readable filenames from absolute paths for the video preview placeholders.

### 7. MVC Refactoring (Application Controller)
**Objective**: Decouple the UI completely from the application logic to ensure a strict MVC architecture.
- **Action**: Extracted navigation wiring from `app.py` into a new `ApplicationController` inside `controllers/application_controller.py`.
- **Implementation**: 
  - Connected `HomeScreen`'s "Start Processing" button to emit a signal, but *only* if the user has actually selected a video. If no video is selected, a native `QMessageBox` intercepts and alerts the user, preventing an invalid state transition.
  - Linked `SettingsScreen`'s "Save Settings" button to navigate back to Home. The settings are preserved seamlessly in memory without touching the disk or database.
  - Wired `ComparisonScreen`'s "Back to Home" and "Process Another Video" buttons to safely return the user to the starting page, preserving their application-wide settings.
  - Bound the `ProcessingScreen`'s "Cancel" button to temporarily display an informative `QMessageBox` instead of killing the process, as the backend cancellation pipeline is not yet implemented.
  - Crucially, whenever the flow enters the `ProcessingScreen`, the central controller first calls `reset()` to guarantee the user always sees a clean, default slate (0% progress, wiped logs) instead of stale data from a previous run.

### 8. Backend Engine Integration
**Objective**: Connect the frozen video processing backend (provided by Person 3) to the Application Controller.
- **Action**: Modified `application_controller.py` to import and execute `enhance_video` from the `video_engine` module.
- **Implementation**: 
  - Strictly respected the backend black-box API boundary (`enhance_video` and `TheiaConfig`), avoiding any internal classes (FFmpeg, OpenCV, ONNX) in the controller logic.
  - Implemented the "Start Processing" pipeline:
    1. Reads the user's video path and chosen preset.
    2. Enforces the "Fast" preset limitation, throwing a `QMessageBox` if an unavailable preset is chosen.
    3. Prompts the user to define a save location using `QFileDialog`, defaulting to their chosen output format.
    4. Routes the UI to the `ProcessingScreen` and invokes `enhance_video`.
  - Constructed a dynamic `progress_callback` that maps the engine's real-time progress (current frame / total frames) directly to the UI's progress bar and live log stream (updating every 25 frames to prevent flooding).
  - Ensured graceful transitions upon completion: the app navigates to the `ComparisonScreen` and correctly populates the final dashboard metrics.
  - Wrapped the entire engine invocation in a try-except block, guaranteeing that any engine failure results in a safe UI alert and log dump, rather than a hard application crash.

### 9. GUI Refactor — Auto-Detection, Settings Removal & Premium UI/UX Overhaul
**Objective**: Simplify the user flow by removing the manual Settings screen, auto-detecting video metadata on upload, and overhauling the entire UI to a premium dark theme.
- **Action**: Rewrote all four screen files and the global stylesheet. Deleted the `SettingsScreen` dependency.
- **Implementation**:
  - **Removed SettingsScreen entirely**: The user no longer manually configures FPS, preset, or output format. The `SettingsScreen` class, its import in `app.py`, and all related signal connections were stripped out. Only 3 screens remain in the `QStackedWidget`: Home → Processing → Comparison.
  - **Auto-detection on video upload**: When the user selects a video via `QFileDialog`, the `HomeScreen` now uses OpenCV (`cv2.VideoCapture`) to read the source FPS and extracts the file extension as the format. Both values are displayed in a metadata row below the filename and stored as `self.detected_fps` / `self.detected_format` for the controller to consume.
  - **Premium global dark theme**: Replaced the basic stylesheet in `app.py` with a comprehensive design system featuring:
    - Deep black background (`#0f0f0f`) with card surfaces (`#1a1a2e`)
    - Purple-to-blue accent gradient (`#6c63ff` → `#3f8efc`) on the progress bar
    - Named object styles (`#Title`, `#Subtitle`, `#SectionTitle`, `#Muted`, `#Accent`, `#CardPanel`, `#SecondaryButton`, `#DangerButton`) for consistent visual hierarchy
    - Generous button padding (`14px 32px`) and minimum widths (`160px`) to prevent compression at any window size
    - Custom scrollbar and terminal-style log theming
  - **Bug fixes**:
    - Removed the inline `setStyleSheet("background-color: white")` on the `QTextEdit` log in `processing_screen.py` that was overriding the dark theme with a jarring white background.
    - Removed conflicting inline card styles from all screens that clashed with the global `#CardPanel` rule.
  - **Controller updates**: `ApplicationController` now auto-derives the output format from the input file extension and populates the `ComparisonScreen` with both the original FPS and the doubled (enhanced) FPS.

### 10. Critical Bug Fixes — UI Freezing, ETA Timer & Cancel Button
**Objective**: Resolve the application becoming "Not Responding" during processing, fix the ETA timer permanently stuck on "Calculating...", and wire up the non-functional Cancel button.
- **Root cause analysis**:
  - **UI freezing**: `enhance_video()` was called directly on the main/GUI thread inside `ApplicationController.start_processing()`. This blocked the Qt event loop for the entire duration of processing (minutes), causing Windows to flag the window as "Not Responding". The `progress_callback` updated QLabel text, but because the event loop never ran, those updates only appeared sporadically.
  - **Stuck ETA**: No ETA calculation logic existed anywhere in the codebase. The label was initialized to `"Calculating..."` in `ProcessingScreen.reset()` and was never updated by the controller.
  - **Dead Cancel button**: `ProcessingScreen._on_cancel()` displayed a `QMessageBox.information("not implemented yet")` placeholder and performed no actual cancellation.
- **Implementation**:
  - **New `workers/worker_thread.py`**: Created a `VideoProcessingWorker(QThread)` class that runs `enhance_video()` on a background thread. The worker emits three signals: `progress_updated(int, int)`, `log_message(str)`, and `processing_finished(bool, str)`. The progress callback inside the worker checks a thread-safe `_cancelled` flag on every frame and raises `InterruptedError` to bail out cleanly.
  - **Controller rewrite (`application_controller.py`)**: Replaced the direct `enhance_video()` call with `VideoProcessingWorker.start()`. Connected all three worker signals to handler methods. Added `_on_progress_updated()` which records `time.monotonic()` at start and computes `remaining = (elapsed / fraction_done) - elapsed`, formatted as `"2m 15s"` or `"45s"` via `_format_eta()`. Added `_on_processing_finished()` to navigate to ComparisonScreen on success, show error dialog on failure, and return home on cancellation.
  - **Cancel wiring (`processing_screen.py`)**: Added a `cancel_requested = pyqtSignal()` to `ProcessingScreen`. Replaced the placeholder `_on_cancel()` with a `QMessageBox.question()` confirmation dialog that emits the signal on "Yes". The controller connects this signal to `_on_cancel_requested()`, which calls `worker.cancel()` and updates the status to "Cancelling...".

### 11. Progress Counter Fix & Side-by-Side Video Playback
**Objective**: Fix the progress counter exceeding 100% (showing ~200%) and replace the static thumbnail on the ComparisonScreen with actual synchronized video playback.
- **Root cause analysis**:
  - **Progress >100%**: In `processing_pipeline.py`, the progress callback received `processed_count` which tracked *output* frames written (including interpolated middle frames). Since the 2× interpolation engine generates 2 output frames per input pair, `processed_count` reached approximately `2 × total_input_frames`, causing the percentage to climb to ~200% against the input `total_frames`.
  - **Static thumbnail**: The previous `ComparisonScreen` extracted a single frame from each video via OpenCV and displayed it as a `QPixmap`. No actual video playback was implemented.
- **Implementation**:
  - **Pipeline fix (`processing_pipeline.py`)**: Replaced `processed_count += len(processed_frames)` with a new `input_frames_done` counter that increments by 1 per pair iteration (tracking input frames consumed, not output frames written). Starts at 1 (the first "left" frame) and reaches exactly `total_frames` after all pairs are processed. The final callback explicitly reports `(total_frames, total_frames)` to guarantee 100%. Added a `min(100, ...)` safety cap in the controller.
  - **Video playback (`comparison_screen.py`)**: Created a new `VideoPlayerWidget(QFrame)` class that uses `cv2.VideoCapture` + `QTimer` for frame-by-frame video playback:
    - `load_video(path)` opens the video, reads FPS/frame count, and displays the first frame immediately.
    - `advance_frame()` reads the next frame, converts BGR→RGB→`QImage`→`QPixmap`, and scales it to fit the label. Auto-loops to the beginning when the video ends.
    - `seek_to_frame(idx)` enables restart functionality.
  - **Playback controls**: Added ▶ Play / ⏸ Pause toggle and ⏮ Restart buttons. A `QTimer` fires at the enhanced video's native FPS to drive both players simultaneously. Playback auto-starts when the comparison screen appears via `start_playback()` called from the controller.
  - **Navigation safety**: The `_on_navigate_home()` method pauses playback and releases video captures before navigating away, preventing resource leaks.

### 12. UI Scaling, Dropdown Fix, and GPU Acceleration
**Objective**: Ensure the UI scales perfectly in maximized mode, fix the broken combo box arrow, and resolve the issue where the AI engine was only running on the CPU.
- **Root cause analysis**:
  - **UI Scaling**: Hardcoded pixel values in `app.py`'s stylesheet and hardcoded stretch ratios in layout code prevented the UI from resizing gracefully when the window was maximized.
  - **Dropdown Arrow**: The `QComboBox` drop-down arrow was using CSS border hacks (`border-left`/`border-bottom`) which Qt's stylesheet engine does not render.
  - **GPU Processing**: The project depended on `onnxruntime` (which is CPU-only) instead of `onnxruntime-gpu`. The inference engine silently fell back to `CPUExecutionProvider`.
- **Implementation**:
  - **Dynamic Scaling System**: Rewrote `app.py` to calculate a scale factor (`window_diagonal / base_diagonal`) on every `resizeEvent`. Re-applied the stylesheet with all pixel metrics dynamically multiplied by this scale factor. Added `apply_scale()` to all screens to similarly scale margins, maximum widths, and spacing, ensuring a responsive design.
  - **Dropdown Fix**: Created a clean SVG chevron (`assets/dropdown_arrow.svg`) and updated the `QComboBox::down-arrow` rule to properly reference it using `image: url()`.
  - **GPU Support (`onnxruntime-directml`)**: Replaced `onnxruntime-gpu` (which failed to load due to missing CUDA 13.x DLLs globally on the system) with `onnxruntime-directml` in `requirements-inference.txt` and the virtual environment. DirectML leverages DirectX 12 to run hardware-accelerated machine learning on any modern GPU without requiring the massive NVIDIA CUDA Toolkit, making it plug-and-play for the end user.
  - **Provider Logic & Logging**: Updated `ONNXInferenceEngine` to explicitly prioritize `TensorrtExecutionProvider > CUDAExecutionProvider > DmlExecutionProvider > CPUExecutionProvider`. Added an `active_provider` property and updated `api.py` to log which backend is being utilized so the user has immediate feedback.

---
**Status**: The application features a dynamic, scalable premium dark theme, supports correct model selection, and correctly utilizes NVIDIA GPUs (via DirectML) for dramatically faster inference out-of-the-box.
