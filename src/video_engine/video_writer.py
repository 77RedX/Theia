"""Video writer for Phase 3 of Theia Video Enhancer."""

from __future__ import annotations

from pathlib import Path
import types

import cv2
import numpy as np

from .logger import logger


class VideoWriter:
    """Writes streamed frames into an output video file, preserving source metadata.

    The writer is the sole owner of the cv2.VideoWriter lifecycle.
    """

    def __init__(self, output_path: str | Path, fps: float, resolution: tuple[int, int], codec: str = "mp4v") -> None:
        """Initialize the video writer with required metadata.

        Args:
            output_path: Path to the output video file.
            fps: Frames per second.
            resolution: (width, height) tuple.
            codec: FourCC codec string (e.g., "mp4v", "XVID").
        """
        if fps <= 0:
            raise ValueError("FPS must be greater than 0")
        width, height = resolution
        if width <= 0 or height <= 0:
            raise ValueError("Resolution must contain positive dimensions")
            
        self.output_path = Path(output_path)
        self.fps = fps
        self.resolution = resolution
        self.codec = codec
        self._writer: cv2.VideoWriter | None = None

    @property
    def is_open(self) -> bool:
        """Return whether the video writer is currently open."""
        return self._writer is not None

    def open(self) -> bool:
        """Initialize cv2.VideoWriter and return True if successful."""
        self.close()

        # Ensure parent directory exists
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        fourcc = cv2.VideoWriter_fourcc(*self.codec)
        writer = cv2.VideoWriter(str(self.output_path), fourcc, self.fps, self.resolution)
        
        if not writer.isOpened():
            logger.error("Failed to open video writer: %s", self.output_path)
            writer.release()
            return False

        self._writer = writer
        logger.info(
            "Opened video writer: %s (fps: %f, res: %s, codec: %s)", 
            self.output_path, self.fps, self.resolution, self.codec
        )
        return True

    def write_frame(self, frame: np.ndarray) -> None:
        """Write a single frame to the output video."""
        self._ensure_open()
        assert self._writer is not None
        
        # Verify frame is a color image
        if frame.ndim != 3 or frame.shape[2] != 3:
            raise ValueError("Frame must be a 3-channel BGR image")
            
        # Verify resolution
        h, w = frame.shape[:2]
        if (w, h) != self.resolution:
            raise ValueError(f"Frame resolution {(w, h)} does not match writer resolution {self.resolution}")
            
        self._writer.write(frame)

    def close(self) -> None:
        """Release the underlying cv2.VideoWriter instance."""
        if self._writer is not None:
            try:
                self._writer.release()
            except Exception:
                pass
            self._writer = None

    def __enter__(self) -> VideoWriter:
        """Context manager entry point."""
        if not self.is_open:
            if not self.open():
                raise RuntimeError(f"Failed to open video writer for {self.output_path}")
        return self

    def __exit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: types.TracebackType | None) -> None:
        """Context manager exit point to ensure safe cleanup."""
        self.close()

    def __del__(self) -> None:
        """Safely release video resources during object cleanup."""
        try:
            self.close()
        except Exception:
            pass
            
    def _ensure_open(self) -> None:
        """Raise an error when operations are attempted before opening."""
        if self._writer is None:
            raise RuntimeError("Video writer is not open. Call open() first.")
