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

## Phase 3 - Video Reconstruction

### Goal

Reconstruct a valid output video from a sequence of streamed frames, preserving the original frames per second (FPS) and resolution, without applying any modifications or AI processing yet.

### What Was Done

1. Implemented the `VideoWriter` class.
   - Initialized with strict constraints for FPS and resolution.
   - Encapsulated the `cv2.VideoWriter` lifecycle completely within the class, following the ownership pattern established in Phase 1.
   - Added validation to ensure initialized dimensions are strictly positive.

2. Added frame channel and dimension validation.
   - Implemented checks inside `write_frame` to guarantee incoming frames are 3-channel BGR images and match the initialized resolution perfectly.
   - This prevents silent dropped frames by OpenCV and prepares the data format for future ONNX integration.

3. Managed resource safety.
   - Provided `open()`, `close()`, and a context manager (`__enter__`, `__exit__`) to guarantee that output files are gracefully finalized and not left corrupted.

4. Implemented testing.
   - Wrote unit tests for property initialization, resolution mismatch errors, and uninitialized access exceptions.
   - Built an end-to-end integration test that generates dummy frames, passes them through the `VideoWriter`, and then re-reads the output with `VideoReader` to verify the frame count and metadata survived perfectly.

### Why These Changes Were Made

Phase 3 was the critical bridge to ensure we could actually assemble a finished product from isolated frames. By keeping the `VideoWriter` decoupled from the `FrameExtractor`, we made it trivial to insert processing steps between them in the future. The strict validation logic was introduced early because debugging OpenCV's silent failures during video generation is notoriously difficult; failing fast with explicit `ValueError`s saves massive headaches down the line.

### Validation

- Ran `pytest` against the newly added `test_video_writer.py`.
- Verified that both unit tests and the full pipeline integration test pass with high reliability.

### Scope Boundaries

The following items were intentionally left out of scope:
- Frame modifications or watermarks
- AI processing or interpolation
- Audio handling (deferred to Phase 4)
- Optimization

## Phase 4 - Audio Preservation

### Goal

Ensure the final enhanced video retains its original sound by extracting audio from the source before processing, and merging it back into the reconstructed video using system FFmpeg.

### What Was Done

1. Implemented the `AudioManager` class.
   - Created a standalone manager that handles file paths directly rather than meddling with the in-memory frame stream.
   - Utilized Python's `subprocess` module to securely call the system's `ffmpeg` and `ffprobe` binaries.
   - Added `has_audio` to dynamically check if the source file contains audio tracks.
   - Implemented `extract_audio` to pull the track into a temporary AAC file (`.m4a`).
   - Implemented `merge_audio` to combine the new video frames with the extracted audio seamlessly without quality-destroying re-encoding.

2. Designed an autonomous cleanup strategy.
   - Used Python's `tempfile` module to securely create temporary audio files.
   - Tracked all generated files internally and hooked a `cleanup()` routine into the class's context manager and destructor to guarantee disk cleanliness.

3. Improved reliability and fail-safes.
   - Added a `FFMPEG_TIMEOUT` to protect against hanging subprocesses.
   - Built automatic cleanup triggers if extraction fails mid-way.
   - Verified the actual existence of output files after the merge command reports success.
   - Added a lazy dependency check (`_verify_ffmpeg_available()`) to raise clear errors if FFmpeg isn't installed.

4. Verified with mocked integration tests.
   - Mocked `shutil.which` and `subprocess.run` to thoroughly test behavior, timeouts, and extraction logic without forcing heavy FFmpeg calls or requiring the binary to be present for the test suite to succeed.
   - Wrote an integration test that creates a dummy video using OpenCV to test the "no audio" fallback.

### Why These Changes Were Made

Audio processing is fundamentally different from frame processing. By handing off audio to FFmpeg via subprocesses, we avoided bloated Python wrappers and allowed the engine to use standard, highly optimized native tools. Normalizing the extracted audio to AAC ensures broad compatibility, while using the `copy` codec during the merge phase keeps the operation lightning-fast. The timeout and cleanup safeguards were added because leftover temporary files or hanging subprocesses are common, silent killers in media pipelines.

### Validation

- Mocked internal systems to execute the `test_audio_manager.py` suite.
- Confirmed handling of timeouts, bad configurations, and missing files all resulted in the correct `AudioProcessingError`.

### Scope Boundaries

The following items were intentionally left out of scope:
- Audio enhancement or noise reduction
- GUI integration
- The orchestration pipeline (deferred to Phase 5)
- ONNX/AI work

## Phase 5 - Processing Pipeline

### Goal

Build the core `ProcessingPipeline` to orchestrate the video processing lifecycle, uniting the reader, extractor, writer, and audio manager components together using a locked frame-pair architecture.

### What Was Done

1. Implemented the `ProcessingPipeline` class.
   - Designed a clean public API (`process_video`) that safely handles missing files and sets up the full video enhancement workflow.
   - Embedded a generic `progress_callback` to prepare for future GUI integration.

2. Enforced Locked Architecture Decisions.
   - Built a static `_process_pair` method explicitly consuming `left` and `right` frames and outputting `[left]` as the current pass-through behavior.
   - Iterated strictly using the canonical `frame_pair_generator()`.
   - Explicitly handled the pipeline-owned final frame append behavior (so that `[left]` outputs correctly yield the full original frame count).

3. Edge Case Handling and Reliability.
   - Added specific safeguards for single-frame videos, safely capturing the lone frame without crashing.
   - Hooked up `AudioManager` to safely extract and merge audio from the original video to an intermediate path, falling back automatically to video-only if an error or timeout occurs.

4. Validated with comprehensive tests.
   - Wrote unit tests confirming the progress callback triggers.
   - Mocked dependencies to rigorously test no-audio fallbacks.
   - Ran full end-to-end processing against real `.avi` files to guarantee metadata, FPS, and resolution preservation were strictly upheld.

### Why These Changes Were Made

Phase 5 ties the distinct systems into a single product flow without muddying the waters with deep learning logic. By establishing a rigid, pair-based processing loop now, adding complex AI interpolation models later will be as simple as substituting the pass-through `_process_pair` with the inference function. Making `_process_pair` a static method enforces its pure-function intent, keeping it free of hidden state. We also added the `progress_callback` signature early so the future desktop UI team can immediately bind to it without forcing us to redesign the main loop.

### Validation

- The full `pytest` suite passes with all 46 tests.
- Single-frame videos, missing-file conditions, and audio failures gracefully degrade instead of crashing the process.

### Scope Boundaries

The following items were intentionally left out of scope:
- AI inference and interpolation logic (deferred)
- ONNX Runtime and CUDA logic
- Threading and Optimization
- GUI actualization (only the callback signature was added)

## Phase 6 and Beyond

Add later phase entries here only after the corresponding phase is complete.

# Architecture Decisions (Frozen)

## Decision 1

Processing Unit

Frame Pairs

Locked

Pipeline iterates using:

for left, right in extractor.frame_pair_generator()

Reason:

Theia is fundamentally an interpolation engine.

Planned models:

* Residual U-Net
* Deep U-Net
* Flow + U-Net
* Flow + Transformer + U-Net

All consume frame pairs.

## Decision 2

FrameExtractor API

Keep:

frame_generator()

frame_pair_generator()

Locked

## Decision 3

Phase 5 Processing API

ProcessingPipeline

Private method:

_process_pair(left,right)

Phase 5:

return [left]

Phase 6:

return [left,middle]

Phase 7:

return [
left,
generated25,
generated50,
generated75
]

## Decision 4

PairProcessor abstraction

Deferred.

Not before Phase 7/8.

Reason:

No multiple backends currently exist.

## Decision 5

Last frame ownership

Pipeline owns appending the final frame.

Locked.
