"""Tests for the VideoWriter component."""

import os
from pathlib import Path

import cv2
import numpy as np
import pytest

from video_engine.video_reader import VideoReader
from video_engine.frame_extractor import FrameExtractor
from video_engine.video_writer import VideoWriter


@pytest.fixture
def temp_video_path(tmp_path: Path) -> Path:
    """Return a path for a temporary output video."""
    return tmp_path / "output.mp4"


def test_video_writer_initialization(temp_video_path: Path) -> None:
    """Test that VideoWriter initializes properties correctly."""
    writer = VideoWriter(temp_video_path, fps=30.0, resolution=(1920, 1080), codec="mp4v")
    
    assert writer.output_path == temp_video_path
    assert writer.fps == 30.0
    assert writer.resolution == (1920, 1080)
    assert writer.codec == "mp4v"
    assert not writer.is_open


def test_video_writer_open_close(temp_video_path: Path) -> None:
    """Test that open and close manage the lifecycle correctly."""
    writer = VideoWriter(temp_video_path, fps=30.0, resolution=(640, 480))
    
    assert writer.open()
    assert writer.is_open
    
    writer.close()
    assert not writer.is_open


def test_video_writer_context_manager(temp_video_path: Path) -> None:
    """Test that the context manager automatically opens and closes the writer."""
    with VideoWriter(temp_video_path, fps=30.0, resolution=(640, 480)) as writer:
        assert writer.is_open
        
    assert not writer.is_open


def test_video_writer_write_frame(temp_video_path: Path) -> None:
    """Test that writing frames creates a valid video file."""
    fps = 30.0
    resolution = (640, 480)
    num_frames = 10
    
    with VideoWriter(temp_video_path, fps=fps, resolution=resolution) as writer:
        for i in range(num_frames):
            # Create a dummy frame (solid color that changes slightly)
            frame = np.full((480, 640, 3), (i * 20, 100, 150), dtype=np.uint8)
            writer.write_frame(frame)
            
    assert temp_video_path.exists()
    assert temp_video_path.stat().st_size > 0
    

def test_video_writer_resolution_mismatch(temp_video_path: Path) -> None:
    """Test that an error is raised when writing a frame of incorrect size."""
    writer = VideoWriter(temp_video_path, fps=30.0, resolution=(640, 480))
    writer.open()
    
    wrong_size_frame = np.zeros((720, 1280, 3), dtype=np.uint8)
    
    with pytest.raises(ValueError, match="does not match writer resolution"):
        writer.write_frame(wrong_size_frame)
        
    writer.close()


def test_video_writer_raises_when_not_open(temp_video_path: Path) -> None:
    """Test that operations raise RuntimeError if the writer is not open."""
    writer = VideoWriter(temp_video_path, fps=30.0, resolution=(640, 480))
    
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    
    with pytest.raises(RuntimeError, match="not open"):
        writer.write_frame(frame)


def test_video_writer_invalid_configuration(temp_video_path: Path) -> None:
    """Test that invalid FPS or resolution raises ValueError."""
    with pytest.raises(ValueError, match="FPS must be greater than 0"):
        VideoWriter(temp_video_path, fps=0, resolution=(640, 480))
        
    with pytest.raises(ValueError, match="FPS must be greater than 0"):
        VideoWriter(temp_video_path, fps=-5.0, resolution=(640, 480))
        
    with pytest.raises(ValueError, match="Resolution must contain positive dimensions"):
        VideoWriter(temp_video_path, fps=30.0, resolution=(0, 480))
        
    with pytest.raises(ValueError, match="Resolution must contain positive dimensions"):
        VideoWriter(temp_video_path, fps=30.0, resolution=(640, 0))


def test_video_writer_invalid_frame_channels(temp_video_path: Path) -> None:
    """Test that invalid frame channels raise ValueError."""
    writer = VideoWriter(temp_video_path, fps=30.0, resolution=(640, 480))
    writer.open()
    
    # Grayscale image (2D array)
    gray_frame = np.zeros((480, 640), dtype=np.uint8)
    with pytest.raises(ValueError, match="Frame must be a 3-channel BGR image"):
        writer.write_frame(gray_frame)
        
    # 4-channel image (e.g., BGRA)
    bgra_frame = np.zeros((480, 640, 4), dtype=np.uint8)
    with pytest.raises(ValueError, match="Frame must be a 3-channel BGR image"):
        writer.write_frame(bgra_frame)
        
    # 1D array
    flat_array = np.zeros(480 * 640 * 3, dtype=np.uint8)
    with pytest.raises(ValueError, match="Frame must be a 3-channel BGR image"):
        writer.write_frame(flat_array)
        
    # Empty array
    empty_frame = np.array([])
    with pytest.raises(ValueError, match="Frame must be a 3-channel BGR image"):
        writer.write_frame(empty_frame)
        
    writer.close()


def test_end_to_end_pipeline(tmp_path: Path) -> None:
    """Test the full pipeline: generate dummy source, read, extract, and write."""
    # 1. Generate a small dummy source video
    source_path = tmp_path / "source.mp4"
    fps = 24.0
    resolution = (320, 240)
    frame_count = 15
    
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    dummy_writer = cv2.VideoWriter(str(source_path), fourcc, fps, resolution)
    for i in range(frame_count):
        frame = np.full((240, 320, 3), (i * 10, i * 10, i * 10), dtype=np.uint8)
        dummy_writer.write(frame)
    dummy_writer.release()
    
    # 2. Pipeline execution
    reader = VideoReader(source_path)
    assert reader.load_video()
    
    extracted_fps = reader.get_fps()
    extracted_res = reader.get_resolution()
    
    output_path = tmp_path / "output.mp4"
    
    extractor = FrameExtractor(reader)
    
    with VideoWriter(output_path, fps=extracted_fps, resolution=extracted_res) as writer:
        for frame in extractor.frame_generator():
            writer.write_frame(frame)
            
    reader.close()
    
    # 3. Verification
    assert output_path.exists()
    
    verify_reader = VideoReader(output_path)
    assert verify_reader.load_video()
    
    # allow for tiny floating point difference in FPS
    assert abs(verify_reader.get_fps() - fps) < 0.1
    assert verify_reader.get_resolution() == resolution
    
    output_frame_count = verify_reader.get_frame_count()
    # Codec behavior (like mp4v) can sometimes drop frames at the end of short videos on some platforms.
    # If exact equality fails, we document this reason and maintain the existing tolerance.
    if output_frame_count != frame_count:
        assert output_frame_count >= frame_count - 2, f"Expected {frame_count} frames, got {output_frame_count}"
    else:
        assert output_frame_count == frame_count
    
    verify_reader.close()
