"""Diagnostics framework for the video engine."""

import json
import time
from pathlib import Path
from typing import Any

import cv2
import numpy as np


class DebugCollector:
    """Collects and exports diagnostics data from the processing pipeline."""

    def __init__(self, output_dir: Path | str) -> None:
        """Initialize the debug collector.
        
        Args:
            output_dir: The root directory for all debug outputs.
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _get_pair_dir(self, pair_idx: int) -> Path:
        """Get or create the directory for a specific frame pair."""
        pair_dir = self.output_dir / f"pair_{pair_idx:06d}"
        pair_dir.mkdir(parents=True, exist_ok=True)
        return pair_dir

    def save_frame(self, name: str, frame: np.ndarray, pair_idx: int) -> None:
        """Save a BGR frame as a PNG.
        
        Args:
            name: Name of the frame (e.g., 'left', 'generated').
            frame: The frame array.
            pair_idx: The current frame pair index.
        """
        path = self._get_pair_dir(pair_idx) / f"{name}.png"
        cv2.imwrite(str(path), frame)

    def save_mask(self, name: str, mask: np.ndarray, pair_idx: int) -> None:
        """Save a binary mask as a PNG.
        
        Args:
            name: Name of the mask (e.g., 'overlay_mask').
            mask: The binary mask array.
            pair_idx: The current frame pair index.
        """
        path = self._get_pair_dir(pair_idx) / f"{name}.png"
        cv2.imwrite(str(path), mask)

    def save_scene_score(self, score: float, pair_idx: int) -> None:
        """Save the scene detection difference score.
        
        Args:
            score: The computed scene cut score.
            pair_idx: The current frame pair index.
        """
        path = self._get_pair_dir(pair_idx) / "scene_score.txt"
        path.write_text(f"{score:.4f}", encoding="utf-8")

    def save_metadata(self, metadata: dict[str, Any], pair_idx: int) -> None:
        """Save pipeline metadata for this frame pair as JSON.
        
        Args:
            metadata: Dictionary containing metadata.
            pair_idx: The current frame pair index.
        """
        path = self._get_pair_dir(pair_idx) / "metadata.json"
        
        # Inject timestamp automatically
        metadata_copy = dict(metadata)
        metadata_copy["processing_timestamp"] = time.time()
        
        path.write_text(json.dumps(metadata_copy, indent=4), encoding="utf-8")
