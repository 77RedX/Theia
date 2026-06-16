"""Streaming frame extraction for Phase 2 of Theia Video Enhancer."""

from __future__ import annotations

from collections.abc import Iterator

import cv2
import numpy as np

from .video_reader import VideoReader


class FrameExtractor:
    """Stream frames and frame pairs from a loaded video reader."""

    def __init__(self, video_reader: VideoReader) -> None:
        """Store a loaded video reader for streaming frame access."""

        self._video_reader = video_reader
        self._video_reader._get_capture()

    def frame_generator(self) -> Iterator[np.ndarray]:
        """Yield frames one at a time from the start of the video."""

        capture = self._video_reader._get_capture()
        self._reset_to_start(capture)

        while True:
            success, frame = capture.read()
            if not success or frame is None:
                break
            yield frame

    def frame_pair_generator(self) -> Iterator[tuple[np.ndarray, np.ndarray]]:
        """Yield overlapping adjacent frame pairs from the start of the video."""

        capture = self._video_reader._get_capture()
        self._reset_to_start(capture)

        success, previous_frame = capture.read()
        if not success or previous_frame is None:
            return

        while True:
            success, current_frame = capture.read()
            if not success or current_frame is None:
                break
            yield previous_frame, current_frame
            previous_frame = current_frame

    def _reset_to_start(self, capture: cv2.VideoCapture) -> None:
        """Move the capture position back to the first frame."""

        if not capture.set(cv2.CAP_PROP_POS_FRAMES, 0):
            raise RuntimeError("Unable to reset video capture to frame 0.")