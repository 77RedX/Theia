"""Tests for the SceneDetector component."""

import numpy as np
import pytest

from video_engine.scene_detection import SceneDetector


def create_solid_frame(color_value: int) -> np.ndarray:
    """Helper to create a 320x240 BGR frame of a solid color."""
    return np.full((240, 320, 3), color_value, dtype=np.uint8)


def test_invalid_threshold() -> None:
    """Test that invalid thresholds raise ValueError during initialization."""
    with pytest.raises(ValueError, match="Invalid threshold"):
        SceneDetector(threshold=0.0)
        
    with pytest.raises(ValueError, match="Invalid threshold"):
        SceneDetector(threshold=-15.0)


def test_identical_frames() -> None:
    """Test that identical frames yield zero difference and no scene cut."""
    detector = SceneDetector(threshold=35.0)
    frame = create_solid_frame(100)
    
    score = detector.compute_difference(frame, frame)
    assert score == 0.0
    
    is_cut = detector.is_scene_cut(frame, frame)
    assert is_cut is False


def test_slightly_different_frames() -> None:
    """Test that frames with small differences do not trigger a cut."""
    detector = SceneDetector(threshold=35.0)
    
    # 100 vs 120 gives an absolute difference of 20
    frame1 = create_solid_frame(100)
    frame2 = create_solid_frame(120)
    
    score = detector.compute_difference(frame1, frame2)
    # The difference in grayscale between a solid 100 BGR and 120 BGR is 20
    assert 19.0 <= score <= 21.0
    
    is_cut = detector.is_scene_cut(frame1, frame2)
    assert is_cut is False


def test_completely_different_frames() -> None:
    """Test that frames with large differences trigger a scene cut."""
    detector = SceneDetector(threshold=35.0)
    
    frame1 = create_solid_frame(0)    # Black
    frame2 = create_solid_frame(255)  # White
    
    score = detector.compute_difference(frame1, frame2)
    assert score == 255.0
    
    is_cut = detector.is_scene_cut(frame1, frame2)
    assert is_cut is True


def test_threshold_sensitivity() -> None:
    """Test that the same frames trigger cuts differently based on threshold."""
    frame1 = create_solid_frame(100)
    frame2 = create_solid_frame(140)  # Diff is ~40
    
    # Detector with high threshold -> no cut
    high_detector = SceneDetector(threshold=50.0)
    assert high_detector.is_scene_cut(frame1, frame2) is False
    
    # Detector with low threshold -> cut
    low_detector = SceneDetector(threshold=20.0)
    assert low_detector.is_scene_cut(frame1, frame2) is True
