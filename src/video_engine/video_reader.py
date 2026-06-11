"""Video metadata reader for Phase 1 of Theia Video Enhancer."""

from __future__ import annotations

from pathlib import Path

import cv2

from .logger import logger


class VideoReader:
    """Load a video file and expose basic metadata.

    The reader only handles video loading and metadata extraction in Phase 1.
    Frame extraction, AI processing, and reconstruction are intentionally out
    of scope.
    """

    def __init__(self, video_path: str | Path) -> None:
        """Initialize the reader with a video path."""

        self.video_path = Path(video_path)
        self._capture: cv2.VideoCapture | None = None

    @property
    def is_loaded(self) -> bool:
        """Return whether a video capture is currently open."""

        return self._capture is not None

    def load_video(self) -> bool:
        """Open the video file and return ``True`` when loading succeeds."""

        self.close()

        if not self.video_path.exists():
            raise FileNotFoundError(f"Video file not found: {self.video_path}")

        capture = cv2.VideoCapture(str(self.video_path))
        if not capture.isOpened():
            logger.error("Failed to load video: %s", self.video_path)
            capture.release()
            return False

        self._capture = capture
        logger.info("Loaded video: %s", self.video_path)
        return True

    def get_fps(self) -> float:
        """Return the video's frames per second."""

        self._ensure_loaded()
        assert self._capture is not None
        fps = float(self._capture.get(cv2.CAP_PROP_FPS))
        return fps

    def get_resolution(self) -> tuple[int, int]:
        """Return the video's width and height in pixels."""

        self._ensure_loaded()
        assert self._capture is not None
        width = int(self._capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self._capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        return width, height

    def get_frame_count(self) -> int:
        """Return the total number of frames in the loaded video."""

        self._ensure_loaded()
        assert self._capture is not None
        frame_count = int(self._capture.get(cv2.CAP_PROP_FRAME_COUNT))
        return frame_count

    def close(self) -> None:
        """Release the underlying video capture, if it is open."""

        if self._capture is not None:
            try:
                self._capture.release()
            except Exception:
                pass
            self._capture = None

    def __del__(self) -> None:
        """Safely release video resources during object cleanup."""

        try:
            self.close()
        except Exception:
            pass

    def _ensure_loaded(self) -> None:
        """Raise an error when metadata is requested before loading."""

        if self._capture is None:
            raise RuntimeError("Video is not loaded. Call load_video() first.")