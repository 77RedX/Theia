"""Preprocessing and postprocessing utilities for inference."""

import cv2
import numpy as np


def bgr_to_rgb(image: np.ndarray) -> np.ndarray:
    """Convert an image from BGR to RGB color space.
    
    Args:
        image: A numpy array representing a BGR image.
        
    Returns:
        The RGB equivalent image.
    """
    return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)


def rgb_to_bgr(image: np.ndarray) -> np.ndarray:
    """Convert an image from RGB to BGR color space.
    
    Args:
        image: A numpy array representing an RGB image.
        
    Returns:
        The BGR equivalent image.
    """
    return cv2.cvtColor(image, cv2.COLOR_RGB2BGR)


def normalize(image: np.ndarray) -> np.ndarray:
    """Normalize an image array to the range [0.0, 1.0].
    
    Args:
        image: A numpy array (usually uint8) to normalize.
        
    Returns:
        A float32 numpy array normalized to [0.0, 1.0].
    """
    return image.astype(np.float32) / 255.0


def denormalize(image: np.ndarray) -> np.ndarray:
    """Denormalize a [0.0, 1.0] float array back to [0, 255] uint8.
    
    Args:
        image: A float numpy array normalized to [0.0, 1.0].
        
    Returns:
        A uint8 numpy array with values clamped to [0, 255].
    """
    return np.clip(np.round(image * 255.0), 0, 255).astype(np.uint8)


def hwc_to_chw(image: np.ndarray) -> np.ndarray:
    """Transpose an image from (Height, Width, Channels) to (Channels, Height, Width).
    
    Args:
        image: A numpy array of shape (H, W, C).
        
    Returns:
        A numpy array of shape (C, H, W).
    """
    return np.transpose(image, (2, 0, 1))


def chw_to_hwc(image: np.ndarray) -> np.ndarray:
    """Transpose an image from (Channels, Height, Width) to (Height, Width, Channels).
    
    Args:
        image: A numpy array of shape (C, H, W).
        
    Returns:
        A numpy array of shape (H, W, C).
    """
    return np.transpose(image, (1, 2, 0))


def add_batch_dim(tensor: np.ndarray) -> np.ndarray:
    """Add a batch dimension to the tensor at axis 0.
    
    Args:
        tensor: A numpy array (e.g., shape C, H, W).
        
    Returns:
        A numpy array with an added batch dimension (e.g., shape 1, C, H, W).
    """
    return np.expand_dims(tensor, axis=0)


def remove_batch_dim(tensor: np.ndarray) -> np.ndarray:
    """Remove the batch dimension from the tensor at axis 0.
    
    Args:
        tensor: A numpy array with a batch dimension (e.g., shape 1, C, H, W).
        
    Returns:
        A numpy array with the batch dimension removed (e.g., shape C, H, W).
    """
    return np.squeeze(tensor, axis=0)
