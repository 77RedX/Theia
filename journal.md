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

---
**Status**: The core integration of the GUI and the Video Engine is complete.
