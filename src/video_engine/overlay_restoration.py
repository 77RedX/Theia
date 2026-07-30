"""Overlay restoration infrastructure for the video engine."""

import cv2
import numpy as np


class OverlayRestoration:
    """Detects and restores static overlays (e.g., watermarks, subtitles) independently of AI models."""

    def generate_mask(self, left: np.ndarray, right: np.ndarray) -> np.ndarray:
        """Generate a binary mask identifying persistent static overlays.
        
        Args:
            left: The first frame in BGR format.
            right: The second frame in BGR format.
            
        Returns:
            A binary uint8 mask of the same width and height, where 255 represents 
            an overlay candidate and 0 represents a normal region.
        """
        # Grayscale conversion
        gray_left = cv2.cvtColor(left, cv2.COLOR_BGR2GRAY)
        gray_right = cv2.cvtColor(right, cv2.COLOR_BGR2GRAY)
        
        # Absolute difference to find strictly static regions
        diff = cv2.absdiff(gray_left, gray_right)
        _, static_mask = cv2.threshold(diff, 5, 255, cv2.THRESH_BINARY_INV)
        
        # Adaptive threshold to isolate high contrast elements (text, logos)
        # Using THRESH_BINARY with C=-2 so that only pixels strictly brighter than local mean become 255.
        high_contrast = cv2.adaptiveThreshold(
            gray_left, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, -2
        )
        
        # High contrast filtering: only keep static regions that have high contrast
        mask = cv2.bitwise_and(static_mask, high_contrast)
        
        # Small morphological cleanup
        kernel = np.ones((3, 3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.dilate(mask, kernel, iterations=1)
        
        return mask

    def restore_overlay(self, original: np.ndarray, generated: np.ndarray, mask: np.ndarray) -> np.ndarray:
        """Restore overlay pixels from the original frame onto the generated frame.
        
        Args:
            original: The original unaltered frame (BGR).
            generated: The interpolated/AI-generated frame (BGR).
            mask: The binary mask where 255 indicates overlay pixels.
            
        Returns:
            A new frame with the overlay burned back in.
        """
        if original.shape != generated.shape:
            raise ValueError("Original and generated frames must have the same shape.")
            
        result = generated.copy()
        
        # Ensure mask is boolean for fast numpy indexing
        bool_mask = mask == 255
        
        result[bool_mask] = original[bool_mask]
        
        return result
