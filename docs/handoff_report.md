# Theia Video Engine - Handoff Report (Person 3)

**From:** Person 3 (Video Processing Engine)  
**To:** Person 4 (Desktop Application) & Person 5 (Deployment & QA)  
**Status:** Phases 1 through 7D Completed 

## Overview
The core video processing engine has been successfully implemented, tested, and frozen. We have a robust, pair-based frame processing pipeline that performs AI frame interpolation using ONNX Runtime. The engine successfully preserves video metadata (FPS, resolution), seamlessly handles audio extraction/merging via FFmpeg, and scales output duration and framerates dynamically based on the active model's configuration.

The engine is now ready for GUI integration (Person 4) and Deployment/QA validation (Person 5).

---

## For Person 4: Desktop Application (GUI Team)

Your primary interaction with the Video Engine will be through our frozen Public API. You do not need to instantiate any internal pipeline components, readers, or writers. 

### Canonical API
All integrations should use `enhance_video` and `TheiaConfig` from the `video_engine` package.

```python
from video_engine import enhance_video, TheiaConfig

# 1. Define configuration
config = TheiaConfig(
    preset="fast" # Supported presets: "fast" (basic model), "balanced" (plus), "quality" (pro)
)

# 2. Define a progress callback for the UI
def update_progress(current_frame, total_frames):
    percentage = (current_frame / total_frames) * 100
    print(f"Processing: {percentage:.1f}%")

# 3. Run the engine
enhance_video(
    input_path="input.mp4",
    output_path="output.mp4",
    config=config,
    progress_callback=update_progress
)
```

### Key Integration Points
* **Progress Callback:** Use the `progress_callback` to drive progress bars in the UI. It will pass the current frame count and the total expected frames.
* **Presets:** The engine dynamically resolves the preset (`fast`, `balanced`, `quality`) to the appropriate underlying model directory (`models/basic`, `models/plus`, `models/pro`) using the `ModelRegistry`. If a requested model is not installed, it will raise a clear exception.
* **Error Handling:** Ensure your UI gracefully catches exceptions raised by `enhance_video` (e.g. missing files, missing FFmpeg, unsupported video formats).

---

## For Person 5: Deployment & QA 

The Video Engine is isolated from the heavy training ecosystem (e.g. PyTorch), ensuring a lean deployment profile.

### System Dependencies
* **FFmpeg:** The engine relies on the system's `ffmpeg` and `ffprobe` binaries for audio extraction and merging. **The installer must ensure FFmpeg is bundled or available in the system PATH.**
* **Python Packages:** See `requirements-inference.txt` for production dependencies. It only requires `onnxruntime`, `opencv-python`, and standard libraries. Do *not* include training libraries in the production bundle.

### Model Deployment Architecture
Models are dynamically discovered by the `ModelRegistry`. They must follow a strict folder convention to be detected:

```text
models/
  └── basic/
      ├── model.onnx         # The compiled inference graph
      ├── model_info.json    # Metadata and interpolation factor (e.g. 2x FPS)
      └── README.md          # Deployment specs
```

* **Contract:** The pipeline relies on `model_info.json` to know the correct `fps_multiplier` (which scales output duration/framerate) and preprocessing formats. 
* **Scaling:** To deploy the "Plus" or "Pro" tiers later, simply drop the valid model package into `models/plus/` or `models/pro/` respectively. The engine will automatically detect them without needing any code updates.

### Validation Details
* End-to-end integration tests are passing.
* We successfully process single-frame videos without crashing.
* Missing-audio fallbacks gracefully revert to silent video outputs.
* Output FPS scaling is linked to the `fps_multiplier` in the model metadata, preventing detached audio or doubled playback length.

---

## Future Roadmap (Phase 8+)
While the core engine is robust, the following optimizations are deferred to Phase 8 and should be kept in mind:
* **Memory & Threading:** The current streaming architecture operates synchronously. Future updates will introduce threading to support longer videos and better memory utilization.
* **Directory Initializer:** Streamlining ONNX inference to load natively from standard model directories, though `ModelRegistry` handles this abstraction nicely right now. 
