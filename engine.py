"""
Theia Video Enhancer — engine.py
──────────────────────────────────────────────────────────────────────────────
INTEGRATION STUB for Person 3 (Video Processing Engine Lead)
──────────────────────────────────────────────────────────────────────────────

This file is the bridge between the GUI (Person 4) and the processing
engine (Person 3). Right now it contains a stub that logs a warning.

Person 3: replace `predict_video()` below with your real implementation.
The GUI will call it exactly as shown — you own this function's body.

Contract:
  Input args  → input_path, output_path, fps, quality, progress_cb
  progress_cb → callable(pct: int, msg: str)  — call it often!
  Returns     → None (output file written to output_path)
  On error    → raise any Exception with a human-readable message

──────────────────────────────────────────────────────────────────────────────
"""

from typing import Callable
import logging

log = logging.getLogger(__name__)


def predict_video(
    input_path:  str,
    output_path: str,
    fps:         str,
    quality:     str,
    progress_cb: Callable[[int, str], None] | None = None,
) -> None:
    """
    Enhance a video by interpolating frames to increase FPS.

    Parameters
    ----------
    input_path   : Path to the source video file.
    output_path  : Path where the enhanced video should be written.
    fps          : FPS conversion label, e.g. "30 → 60 fps".
    quality      : One of "Fast", "Balanced", "High Quality".
    progress_cb  : Optional callback(percent: int, message: str).
                   Call this periodically so the GUI can update the bar.
                   Raise InterruptedError to respect cancellation:
                       if cancelled: raise InterruptedError("Cancelled")

    Returns
    -------
    None. The enhanced video must be written to `output_path`.

    Raises
    ------
    FileNotFoundError  : If input_path does not exist.
    RuntimeError       : If the model fails to initialise or inference fails.
    InterruptedError   : If the user cancels and the engine detects it.
    MemoryError        : If the system runs out of RAM during processing.

    Example (Person 3's real implementation)
    -----------------------------------------
    def predict_video(input_path, output_path, fps, quality, progress_cb=None):
        model = load_model(quality_map[quality])
        frames = extract_frames(input_path)
        audio  = extract_audio(input_path)

        for i, triplet in enumerate(make_triplets(frames)):
            pct = int(i / len(frames) * 100)
            if progress_cb:
                progress_cb(pct, f"Processing frame {i}")

            mid_frame = model.infer(triplet)
            write_frame(mid_frame)

        reconstruct_video(frames, output_path)
        attach_audio(audio, output_path)
    """

    # ── STUB — Remove this block when Person 3 delivers the engine ────────
    log.warning(
        "predict_video() called but no engine is integrated yet. "
        "See engine.py for the integration contract."
    )
    if progress_cb:
        progress_cb(0, "[STUB] Engine not yet integrated — using simulation mode.")

    raise NotImplementedError(
        "The real processing engine has not been integrated yet.\n"
        "The GUI is running in simulation mode (see ProcessingWorker.simulate_processing)."
    )
    # ── END STUB ──────────────────────────────────────────────────────────


# ── Quality → model config mapping (fill in when model is ready) ──────────
QUALITY_CONFIG = {
    "Fast":         {"model": "theia_fast.onnx",    "batch_size": 8,  "half_precision": True},
    "Balanced":     {"model": "theia_balanced.onnx", "batch_size": 4,  "half_precision": True},
    "High Quality": {"model": "theia_hq.onnx",       "batch_size": 2,  "half_precision": False},
}

# ── FPS conversion factors ────────────────────────────────────────────────
FPS_MULTIPLIERS = {
    "24 → 48 fps": 2,
    "30 → 60 fps": 2,
    "60 → 120 fps": 2,
}
