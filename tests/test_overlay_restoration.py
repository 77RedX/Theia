"""Tests for the OverlayRestoration component."""

import cv2
import numpy as np
import pytest

from video_engine.overlay_restoration import OverlayRestoration


@pytest.fixture
def overlay_restorer() -> OverlayRestoration:
    return OverlayRestoration()


def create_solid_frame(color_value: int, shape: tuple = (240, 320, 3)) -> np.ndarray:
    """Helper to create a BGR frame of a solid color."""
    return np.full(shape, color_value, dtype=np.uint8)


def test_identical_images_no_overlay(overlay_restorer: OverlayRestoration) -> None:
    """Test that identical smooth images produce an empty mask (no high contrast)."""
    # Create two identical dark gray frames
    frame1 = create_solid_frame(50)
    frame2 = create_solid_frame(50)
    
    mask = overlay_restorer.generate_mask(frame1, frame2)
    
    # Since it's a solid block of color, adaptive threshold won't find high contrast
    assert np.all(mask == 0)


def test_synthetic_subtitle(overlay_restorer: OverlayRestoration) -> None:
    """Test that a high-contrast static subtitle is detected on a moving background."""
    # Create a background that moves
    frame1 = create_solid_frame(50)
    frame2 = create_solid_frame(150)
    
    # Draw a synthetic subtitle (white text) in the exact same spot on both (disable antialiasing)
    cv2.putText(frame1, "HELLO WORLD", (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_4)
    cv2.putText(frame2, "HELLO WORLD", (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_4)
    
    mask = overlay_restorer.generate_mask(frame1, frame2)
    
    # The mask should have some 255 values where the text is
    assert np.any(mask == 255)
    
    # Check that the mask is completely zero in the top left where there is no text
    assert np.all(mask[0:100, 0:100] == 0)


def test_watermark(overlay_restorer: OverlayRestoration) -> None:
    """Test that a small logo/watermark is detected."""
    frame1 = create_solid_frame(50)
    frame2 = create_solid_frame(100)
    
    # Draw a white rectangle (watermark) in top right corner
    cv2.rectangle(frame1, (280, 10), (310, 40), (255, 255, 255), -1)
    cv2.rectangle(frame2, (280, 10), (310, 40), (255, 255, 255), -1)
    
    mask = overlay_restorer.generate_mask(frame1, frame2)
    
    # The mask should contain the watermark
    assert np.any(mask[10:40, 280:310] == 255)
    # Background should be zero
    assert np.all(mask[100:200, 50:150] == 0)


def test_restore_overlay_correctness(overlay_restorer: OverlayRestoration) -> None:
    """Test that pixels are correctly copied from original to generated using the mask."""
    # Original frame with a white subtitle
    original = create_solid_frame(0)
    cv2.putText(original, "SUBTITLE", (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    
    # AI generated frame without the subtitle, but the background color slightly changed
    generated = create_solid_frame(10)
    
    # Manually create a mask that covers the subtitle area
    mask = np.zeros((240, 320), dtype=np.uint8)
    mask[150:220, 40:200] = 255
    
    restored = overlay_restorer.restore_overlay(original, generated, mask)
    
    # The non-masked area should remain equal to the generated frame
    assert np.array_equal(restored[0:100, 0:100], generated[0:100, 0:100])
    
    # The masked area should have inherited pixels from the original frame
    assert np.array_equal(restored[150:220, 40:200], original[150:220, 40:200])


def test_empty_mask(overlay_restorer: OverlayRestoration) -> None:
    """Test restore_overlay with an entirely empty mask (no changes)."""
    original = create_solid_frame(0)
    generated = create_solid_frame(10)
    empty_mask = np.zeros((240, 320), dtype=np.uint8)
    
    restored = overlay_restorer.restore_overlay(original, generated, empty_mask)
    
    # The entire image should remain exactly like 'generated'
    assert np.array_equal(restored, generated)


def test_full_mask(overlay_restorer: OverlayRestoration) -> None:
    """Test restore_overlay with a completely full mask (copies everything)."""
    original = create_solid_frame(0)
    generated = create_solid_frame(10)
    full_mask = np.full((240, 320), 255, dtype=np.uint8)
    
    restored = overlay_restorer.restore_overlay(original, generated, full_mask)
    
    # The entire image should remain exactly like 'original'
    assert np.array_equal(restored, original)


def test_restore_shape_mismatch(overlay_restorer: OverlayRestoration) -> None:
    """Test that mismatched original/generated frames raise ValueError."""
    original = create_solid_frame(0, shape=(100, 100, 3))
    generated = create_solid_frame(0, shape=(200, 200, 3))
    mask = np.zeros((100, 100), dtype=np.uint8)
    
    with pytest.raises(ValueError, match="same shape"):
        overlay_restorer.restore_overlay(original, generated, mask)
