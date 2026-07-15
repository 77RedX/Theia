"""Tests for the debug module."""

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import cv2
import numpy as np
import pytest

from video_engine.debug import DebugCollector
from video_engine.config import TheiaConfig
from video_engine.processing_pipeline import ProcessingPipeline
from video_engine.inference.base import InferenceEngine
from video_engine.scene_detection import SceneDetector
from video_engine.overlay_restoration import OverlayRestoration
from video_engine.video_writer import VideoWriter


@pytest.fixture
def dummy_video(tmp_path: Path) -> Path:
    """Create a short dummy MP4 file for testing."""
    path = tmp_path / "dummy.mp4"
    with VideoWriter(path, 30.0, (320, 240)) as writer:
        for i in range(4):
            # Create a scrolling gradient to ensure frames are different
            frame = np.zeros((240, 320, 3), dtype=np.uint8)
            frame[:, :] = (i * 20, i * 30, i * 40)
            writer.write_frame(frame)
    return path


def test_debug_collector_creates_directories(tmp_path: Path) -> None:
    """Test that DebugCollector creates the correct output directory structure."""
    debug_dir = tmp_path / "debug_output"
    collector = DebugCollector(debug_dir)
    
    # Check root dir created
    assert debug_dir.exists()
    assert debug_dir.is_dir()
    
    # Check pair dir created implicitly
    pair_dir = collector._get_pair_dir(5)
    assert pair_dir.exists()
    assert pair_dir.name == "pair_000005"


def test_debug_collector_save_frame(tmp_path: Path) -> None:
    """Test saving a frame."""
    collector = DebugCollector(tmp_path)
    frame = np.full((10, 10, 3), 128, dtype=np.uint8)
    
    with patch("video_engine.debug.cv2.imwrite") as mock_imwrite:
        collector.save_frame("left", frame, 42)
        
        expected_path = str(tmp_path / "pair_000042" / "left.png")
        mock_imwrite.assert_called_once()
        assert mock_imwrite.call_args[0][0] == expected_path


def test_debug_collector_save_scene_score(tmp_path: Path) -> None:
    """Test saving scene score."""
    collector = DebugCollector(tmp_path)
    collector.save_scene_score(45.12344, 1)
    
    expected_path = tmp_path / "pair_000001" / "scene_score.txt"
    assert expected_path.exists()
    assert expected_path.read_text(encoding="utf-8") == "45.1234"


def test_debug_collector_save_metadata(tmp_path: Path) -> None:
    """Test saving metadata."""
    collector = DebugCollector(tmp_path)
    meta = {"preset": "fast", "some_value": 42}
    collector.save_metadata(meta, 7)
    
    expected_path = tmp_path / "pair_000007" / "metadata.json"
    assert expected_path.exists()
    
    saved_meta = json.loads(expected_path.read_text(encoding="utf-8"))
    assert saved_meta["preset"] == "fast"
    assert saved_meta["some_value"] == 42
    assert "processing_timestamp" in saved_meta


@patch("video_engine.audio_manager.AudioManager.has_audio", return_value=False)
def test_pipeline_debug_disabled_overhead(mock_has: MagicMock, dummy_video: Path, tmp_path: Path) -> None:
    """Test that disabled debug mode bypasses all debug operations."""
    output_path = tmp_path / "out_debug_disabled.mp4"
    
    mock_engine = MagicMock(spec=InferenceEngine)
    mock_engine.infer.return_value = np.full((240, 320, 3), 128, dtype=np.uint8)
    
    mock_debug = MagicMock(spec=DebugCollector)
    
    config = TheiaConfig(debug_mode=False)
    
    pipeline = ProcessingPipeline(
        inference_engine=mock_engine,
        config=config,
        fps_multiplier=2,
        debug_collector=mock_debug
    )
    
    pipeline.process_video(dummy_video, output_path)
    
    # Should not be called
    mock_debug.save_frame.assert_not_called()
    mock_debug.save_scene_score.assert_not_called()
    mock_debug.save_metadata.assert_not_called()


@patch("video_engine.audio_manager.AudioManager.has_audio", return_value=False)
def test_pipeline_debug_enabled_export(mock_has: MagicMock, dummy_video: Path, tmp_path: Path) -> None:
    """Test that enabled debug mode successfully triggers exports for a frame pair."""
    output_path = tmp_path / "out_debug_enabled.mp4"
    
    mock_engine = MagicMock(spec=InferenceEngine)
    mock_engine.infer.return_value = np.full((240, 320, 3), 128, dtype=np.uint8)
    
    mock_scene = MagicMock(spec=SceneDetector)
    mock_scene.compute_difference.return_value = 10.0
    mock_scene.is_scene_cut.return_value = False
    
    mock_overlay = MagicMock(spec=OverlayRestoration)
    mock_overlay.generate_mask.return_value = np.zeros((240, 320), dtype=np.uint8)
    mock_overlay.restore_overlay.return_value = np.full((240, 320, 3), 128, dtype=np.uint8)
    
    mock_debug = MagicMock(spec=DebugCollector)
    
    config = TheiaConfig(debug_mode=True, protect_static_overlays=True, detect_scene_cuts=True)
    
    pipeline = ProcessingPipeline(
        inference_engine=mock_engine,
        config=config,
        fps_multiplier=2,
        scene_detector=mock_scene,
        overlay_restoration=mock_overlay,
        debug_collector=mock_debug
    )
    
    pipeline.process_video(dummy_video, output_path)
    
    assert mock_debug.save_frame.call_count > 0
    assert mock_debug.save_mask.call_count > 0
    assert mock_debug.save_scene_score.call_count > 0
    assert mock_debug.save_metadata.call_count > 0
