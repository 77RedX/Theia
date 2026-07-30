"""Scene detection infrastructure for the video engine."""

import cv2
import numpy as np


class SceneDetector:
    """Detects scene cuts between adjacent video frames using deterministic pixel differences."""

    def __init__(self, threshold: float = 35.0) -> None:
        """Initialize the SceneDetector.
        
        Args:
            threshold: The normalized mean pixel intensity difference threshold.
                Differences exceeding this threshold are classified as scene cuts.
                
        Raises:
            ValueError: If threshold is less than or equal to 0.
        """
        if threshold <= 0:
            raise ValueError(f"Invalid threshold: {threshold}. Must be > 0.")
        self.threshold = threshold

    def compute_difference(self, left: np.ndarray, right: np.ndarray) -> float:
        """Compute the normalized pixel difference score between two frames.
        
        The baseline algorithm converts the frames to grayscale, computes the absolute
        difference, and returns the mean pixel intensity of the difference.
        
        Args:
            left: The first frame in BGR format.
            right: The second frame in BGR format.
            
        Returns:
            A float representing the mean difference score.
        """
        # Convert BGR to Grayscale
        gray_left = cv2.cvtColor(left, cv2.COLOR_BGR2GRAY)
        gray_right = cv2.cvtColor(right, cv2.COLOR_BGR2GRAY)
        
        # Compute absolute difference
        diff = cv2.absdiff(gray_left, gray_right)
        
        # Calculate mean pixel intensity
        score = float(np.mean(diff))
        
        return score

    def is_scene_cut(self, left: np.ndarray, right: np.ndarray) -> bool:
        """Determine if a scene cut occurred between the two frames.
        
        Args:
            left: The first frame in BGR format.
            right: The second frame in BGR format.
            
        Returns:
            True if the computed difference exceeds the threshold, False otherwise.
        """
        diff_score = self.compute_difference(left, right)
        return diff_score > self.threshold
