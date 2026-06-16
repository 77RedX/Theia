# Theia Video Enhancer Implementation Journal

This journal is written as a project timeline for interview and recruiter review. It documents what was built, why each change was made, and how the work was kept scoped to the current phase.

## How This Journal Is Updated

After each phase is completed, add a new phase entry here in chronological order.

Each entry should capture:

- What the phase goal was
- What files changed
- Why those changes were needed
- What validation was performed
- What was intentionally left out of scope

## Phase 1 - Video Metadata Extraction

### Goal

Build the first stable slice of the video engine: load a video file successfully and extract basic metadata without starting any future pipeline work.

### What Was Done

1. Established the `src/video_engine/` package structure.
   - Added a package entry point so the video engine can be imported cleanly.
   - Kept the package focused on metadata handling only.

2. Added centralized logging.
   - Created a dedicated logger module to standardize messages from the video engine.
   - Used Python's built-in logging system to avoid unnecessary dependencies.

3. Implemented the `VideoReader` class.
   - Added video loading with `cv2.VideoCapture`.
   - Exposed metadata accessors for FPS, resolution, and frame count.
   - Added a loading-state guard so metadata cannot be requested before a successful load.

4. Hardened the reader for real-world use.
   - Added explicit file existence validation before opening a video.
   - Added safe cleanup through `close()` and `__del__()` so OpenCV resources are released reliably.
   - Added an `is_loaded` property to make state inspection explicit and readable.

5. Built tests around the actual behavior.
   - Verified that the sample video exists.
   - Verified that a valid sample video loads successfully.
   - Verified that FPS, resolution, and frame count are all positive.
   - Added failure-path tests for missing files and metadata access before loading.
   - Used fixtures to ensure `VideoCapture` objects are closed after each test.

6. Moved the sample asset to a more maintainable location.
   - Relocated the sample video from `tests/` to `assets/sample_videos/`.
   - Kept project assets separate from test code to make the repository structure cleaner and easier to grow.

7. Updated the phase checklist.
   - Marked the Phase 1 completion criteria as done in the roadmap.

### Why These Changes Were Made

The Phase 1 implementation was intentionally kept narrow so the project could prove one reliable capability before any later pipeline work started. The main goal was to create a clean base for future phases: a reader that opens real videos, reports trustworthy metadata, and fails clearly when input is invalid.

The extra robustness work was added because video code depends on external files and native resources. That means it needs clear error handling, explicit load-state tracking, and cleanup behavior that does not depend on users remembering to close objects manually.

The test changes were made to validate real behavior rather than only the happy path. That made the phase useful as a foundation for later engine work and reduced the risk of carrying hidden assumptions into Phase 2.

### Validation

- Ran the Phase 1 test suite with `pytest`.
- Confirmed all tests passed after the robustness updates.
- Checked the modified Python files for syntax and error issues.

### Scope Boundaries

The following items were intentionally not implemented in Phase 1:

- Frame extraction
- Video reconstruction
- FFmpeg integration
- ONNX Runtime
- AI inference
- Interpolation
- Any Phase 2+ functionality

## Phase 2 - Frame Extraction

### Goal

Build the second stable slice of the video engine: stream decoded frames from a loaded video reader without introducing reconstruction or inference logic.

### What Was Done

1. Extended the video engine with a dedicated frame extraction module.
   - Added `FrameExtractor` to keep frame streaming separate from metadata responsibilities.
   - Accepted a loaded `VideoReader` instance so capture ownership stayed centralized in Phase 1 code.

2. Added streaming frame generators.
   - Implemented `frame_generator()` to yield one frame at a time in order.
   - Implemented `frame_pair_generator()` to yield overlapping adjacent pairs for future interpolation work.
   - Reset the capture position before each generator run so repeated iteration starts from frame 0.

3. Kept the implementation memory-conscious.
   - Avoided loading the entire video into memory.
   - Kept the API generator-based so downstream pipeline stages can consume frames incrementally.

4. Strengthened the tests around streaming behavior.
   - Verified a loaded `VideoReader` is accepted and an unloaded one is rejected.
   - Verified frames and frame pairs are produced correctly.
   - Verified generated frame count matches the metadata frame count.
   - Verified generators restart cleanly from the beginning on repeated use.

5. Kept Phase 1 behavior intact.
   - Reused the existing `VideoReader` resource model.
   - Avoided any changes to metadata behavior that were not required for frame extraction support.

### Why These Changes Were Made

Phase 2 needed to establish the streaming foundation for later processing stages while still remaining simple enough to validate in isolation. The design focused on generators because future interpolation and pipeline work will need ordered access to frames and adjacent frame pairs without expensive full-video buffering.

The test updates were important because they prove the frame stream is genuinely sequential and restartable, which protects against cursor-position bugs and supports later reuse by downstream consumers.

### Validation

- Ran the Phase 1 and Phase 2 test suites together with `pytest`.
- Confirmed all tests passed after the cleanup pass.
- Checked the modified Python files for syntax and error issues.

### Scope Boundaries

The following items were intentionally not implemented in Phase 2:

- Frame saving
- FFmpeg integration
- ONNX Runtime
- AI inference
- Interpolation
- Reconstruction
- Audio handling
- Threading
- Optimization
- Video writing

## Phase 3 and Beyond

Add later phase entries here only after the corresponding phase is complete.
