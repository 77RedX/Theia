"""Tests for inference preprocessing utilities."""

import numpy as np
import pytest

from video_engine.inference.preprocessing import (
    add_batch_dim,
    bgr_to_rgb,
    chw_to_hwc,
    denormalize,
    hwc_to_chw,
    normalize,
    remove_batch_dim,
    rgb_to_bgr,
)


def test_bgr_to_rgb() -> None:
    """Test BGR to RGB conversion."""
    # Create a 2x2 BGR image: Blue channel is 255, Green and Red are 0
    bgr = np.zeros((2, 2, 3), dtype=np.uint8)
    bgr[..., 0] = 255
    
    rgb = bgr_to_rgb(bgr)
    
    assert rgb.shape == (2, 2, 3)
    assert rgb.dtype == np.uint8
    # In RGB, the red channel (index 0) should be 0, blue channel (index 2) should be 255
    assert np.all(rgb[..., 0] == 0)
    assert np.all(rgb[..., 1] == 0)
    assert np.all(rgb[..., 2] == 255)


def test_rgb_to_bgr() -> None:
    """Test RGB to BGR conversion."""
    # Create a 2x2 RGB image: Red channel is 255, Green and Blue are 0
    rgb = np.zeros((2, 2, 3), dtype=np.uint8)
    rgb[..., 0] = 255
    
    bgr = rgb_to_bgr(rgb)
    
    assert bgr.shape == (2, 2, 3)
    assert bgr.dtype == np.uint8
    # In BGR, the blue channel (index 0) should be 0, red channel (index 2) should be 255
    assert np.all(bgr[..., 0] == 0)
    assert np.all(bgr[..., 1] == 0)
    assert np.all(bgr[..., 2] == 255)


def test_normalize() -> None:
    """Test image normalization to [0.0, 1.0]."""
    img = np.array([0, 127, 255], dtype=np.uint8)
    
    norm = normalize(img)
    
    assert norm.dtype == np.float32
    np.testing.assert_allclose(norm, [0.0, 127.0/255.0, 1.0], rtol=1e-5)


def test_denormalize() -> None:
    """Test image denormalization back to [0, 255] uint8."""
    norm = np.array([-0.1, 0.0, 0.5, 1.0, 1.1], dtype=np.float32)
    
    denorm = denormalize(norm)
    
    assert denorm.dtype == np.uint8
    np.testing.assert_array_equal(denorm, [0, 0, 128, 255, 255])


def test_hwc_to_chw() -> None:
    """Test transposing from HWC to CHW."""
    # Shape: (Height, Width, Channels) -> (2, 3, 4)
    hwc = np.zeros((2, 3, 4))
    
    chw = hwc_to_chw(hwc)
    
    assert chw.shape == (4, 2, 3)


def test_chw_to_hwc() -> None:
    """Test transposing from CHW to HWC."""
    # Shape: (Channels, Height, Width) -> (4, 2, 3)
    chw = np.zeros((4, 2, 3))
    
    hwc = chw_to_hwc(chw)
    
    assert hwc.shape == (2, 3, 4)


def test_add_batch_dim() -> None:
    """Test adding a batch dimension."""
    tensor = np.zeros((3, 224, 224))
    
    batched = add_batch_dim(tensor)
    
    assert batched.shape == (1, 3, 224, 224)


def test_remove_batch_dim() -> None:
    """Test removing a batch dimension."""
    batched = np.zeros((1, 3, 224, 224))
    
    unbatched = remove_batch_dim(batched)
    
    assert unbatched.shape == (3, 224, 224)


def test_remove_batch_dim_error_on_multiple_batches() -> None:
    """Test remove_batch_dim raises an error if batch size != 1."""
    batched = np.zeros((2, 3, 224, 224))
    
    with pytest.raises(ValueError):
        remove_batch_dim(batched)
