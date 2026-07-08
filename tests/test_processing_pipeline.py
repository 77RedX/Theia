"""Tests for the ProcessingPipeline component."""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import cv2
import numpy as np
import pytest

from video_engine.audio_manager import AudioProcessingError
from video_engine.processing_pipeline import ProcessingPipeline
from video_engine.video_reader import VideoReader


@pytest.fixture
def pipeline() -> ProcessingPipeline:
    """Return a fresh ProcessingPipeline instance."""
    return ProcessingPipeline()


@pytest.fixture
def dummy_video(tmp_path: Path) -> Path:
    """Create a short dummy video for testing."""
    path = tmp_path / "dummy.mp4"
    fps = 30.0
    resolution = (320, 240)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(path), fourcc, fps, resolution)
    
    # Write 4 frames: black, red, green, blue
    frames = [
        np.zeros((240, 320, 3), dtype=np.uint8),
        np.full((240, 320, 3), (0, 0, 255), dtype=np.uint8),
        np.full((240, 320, 3), (0, 255, 0), dtype=np.uint8),
        np.full((240, 320, 3), (255, 0, 0), dtype=np.uint8),
    ]
    for frame in frames:
        writer.write(frame)
    writer.release()
    return path


@pytest.fixture
def dummy_single_frame_video(tmp_path: Path) -> Path:
    """Create a single-frame video for testing."""
    path = tmp_path / "dummy_single.mp4"
    fps = 30.0
    resolution = (320, 240)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(path), fourcc, fps, resolution)
    
    writer.write(np.zeros((240, 320, 3), dtype=np.uint8))
    writer.release()
    return path


def test_pipeline_initializes(pipeline: ProcessingPipeline) -> None:
    """Test that pipeline can be initialized."""
    assert pipeline is not None


def test_missing_input_file(pipeline: ProcessingPipeline, tmp_path: Path) -> None:
    """Test missing file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError, match="Input video not found"):
        pipeline.process_video(tmp_path / "missing.mp4", tmp_path / "out.mp4")


@patch("video_engine.audio_manager.AudioManager.has_audio")
@patch("video_engine.audio_manager.AudioManager.extract_audio")
@patch("video_engine.audio_manager.AudioManager.merge_audio")
def test_pass_through_and_last_frame(mock_merge: MagicMock, mock_extract: MagicMock, mock_has: MagicMock,
                                     pipeline: ProcessingPipeline, dummy_video: Path, tmp_path: Path) -> None:
    """Test that pass-through logic and last frame preservation work correctly."""
    mock_has.return_value = False  # No audio to simplify
    output_path = tmp_path / "out.mp4"
    
    pipeline.process_video(dummy_video, output_path)
    
    assert output_path.exists()
    
    # Read back and verify
    reader = VideoReader(output_path)
    reader.load_video()
    try:
        assert reader.get_frame_count() == 4  # 3 from pairs, 1 appended last frame
        assert reader.get_fps() == 30.0
        assert reader.get_resolution() == (320, 240)
        
        # Verify output duration matches input duration
        input_duration = 4 / 30.0
        output_duration = reader.get_frame_count() / reader.get_fps()
        assert abs(input_duration - output_duration) < 0.05
    finally:
        reader.close()


@patch("video_engine.audio_manager.AudioManager.has_audio")
@patch("video_engine.audio_manager.AudioManager.extract_audio")
@patch("video_engine.audio_manager.AudioManager.merge_audio")
def test_audio_preserved(mock_merge: MagicMock, mock_extract: MagicMock, mock_has: MagicMock,
                         pipeline: ProcessingPipeline, dummy_video: Path, tmp_path: Path) -> None:
    """Test audio is extracted and merged when present."""
    mock_has.return_value = True
    mock_extract.return_value = Path("dummy.m4a")
    
    # Make merge mock actually create the output file so moving logic doesn't fail
    def mock_merge_impl(temp_vid, audio, out_vid):
        import shutil
        shutil.move(str(temp_vid), str(out_vid))
    
    mock_merge.side_effect = mock_merge_impl
    output_path = tmp_path / "out_audio.mp4"
    
    pipeline.process_video(dummy_video, output_path)
    
    mock_has.assert_called_once()
    mock_extract.assert_called_once()
    mock_merge.assert_called_once()
    assert output_path.exists()


@patch("video_engine.audio_manager.AudioManager.has_audio")
@patch("video_engine.audio_manager.AudioManager.extract_audio")
@patch("video_engine.audio_manager.AudioManager.merge_audio")
def test_no_audio_fallback(mock_merge: MagicMock, mock_extract: MagicMock, mock_has: MagicMock,
                           pipeline: ProcessingPipeline, dummy_video: Path, tmp_path: Path) -> None:
    """Test pipeline still succeeds if audio processing fails midway."""
    mock_has.return_value = True
    mock_extract.return_value = Path("dummy.m4a")
    mock_merge.side_effect = AudioProcessingError("merge failed")
    
    output_path = tmp_path / "out_fallback.mp4"
    
    pipeline.process_video(dummy_video, output_path)
    
    # Should fall back to video-only
    assert output_path.exists()
    reader = VideoReader(output_path)
    reader.load_video()
    try:
        assert reader.get_frame_count() == 4
    finally:
        reader.close()


@pytest.mark.skipif(not os.path.exists("assets/sample_videos/sample_video.avi"), 
                    reason="sample_video.avi not found")
def test_end_to_end_integration(pipeline: ProcessingPipeline, tmp_path: Path) -> None:
    """End-to-end integration test on real sample video."""
    input_path = Path("assets/sample_videos/sample_video.avi")
    output_path = tmp_path / "e2e_out.mp4"
    
    with patch("shutil.which", return_value="dummy/path"):
        # We patch shutil.which to bypass missing ffmpeg check if any on dev environments,
        # but the test might fail if ffmpeg is actually missing and used. 
        # Actually, let's just let it run naturally without mocks to test true end-to-end.
        pass

    pipeline.process_video(input_path, output_path)
    
    assert output_path.exists()
    
    # Verify original properties
    orig_reader = VideoReader(input_path)
    orig_reader.load_video()
    try:
        orig_frames = orig_reader.get_frame_count()
        orig_fps = orig_reader.get_fps()
        orig_res = orig_reader.get_resolution()
    finally:
        orig_reader.close()
        
    out_reader = VideoReader(output_path)
    out_reader.load_video()
    try:
        assert out_reader.get_frame_count() == orig_frames
        assert out_reader.get_fps() == orig_fps
        assert out_reader.get_resolution() == orig_res
    finally:
        out_reader.close()


@patch("video_engine.audio_manager.AudioManager.has_audio", return_value=False)
def test_single_frame_video(mock_has: MagicMock, pipeline: ProcessingPipeline, 
                            dummy_single_frame_video: Path, tmp_path: Path) -> None:
    """Test pipeline correctly handles a video with only 1 frame."""
    output_path = tmp_path / "out_single.mp4"
    
    pipeline.process_video(dummy_single_frame_video, output_path)
    
    assert output_path.exists()
    
    reader = VideoReader(output_path)
    reader.load_video()
    try:
        assert reader.get_frame_count() == 1
    finally:
        reader.close()


@patch("video_engine.audio_manager.AudioManager.has_audio", return_value=False)
def test_progress_callback(mock_has: MagicMock, pipeline: ProcessingPipeline, 
                           dummy_video: Path, tmp_path: Path) -> None:
    """Test progress callback is invoked properly."""
    output_path = tmp_path / "out_progress.mp4"
    
    progress_updates = []
    
    def on_progress(current: int, total: int) -> None:
        progress_updates.append((current, total))
        
    pipeline.process_video(dummy_video, output_path, progress_callback=on_progress)
    
    assert output_path.exists()
    assert len(progress_updates) > 0
    # Final progress update should be (4, 4) since dummy video has 4 frames
    assert progress_updates[-1] == (4, 4)


from video_engine.inference.base import InferenceEngine

@patch("video_engine.audio_manager.AudioManager.has_audio", return_value=False)
def test_inference_integration_doubles_frames(mock_has: MagicMock, dummy_video: Path, tmp_path: Path) -> None:
    """Test that integration with inference engine doubles frames correctly."""
    output_path = tmp_path / "out_infer.mp4"
    
    mock_engine = MagicMock(spec=InferenceEngine)
    # The middle frame is just a dummy gray frame
    mock_engine.infer.return_value = np.full((240, 320, 3), 128, dtype=np.uint8)
    
    # The pipeline is instantiated with fps_multiplier=2
    pipeline = ProcessingPipeline(inference_engine=mock_engine, fps_multiplier=2)
    pipeline.process_video(dummy_video, output_path)
    
    assert output_path.exists()
    
    reader = VideoReader(output_path)
    reader.load_video()
    try:
        # Original is 4 frames.
        # Pairs: (F1, F2), (F2, F3), (F3, F4) => 3 pairs.
        # Each pair outputs 2 frames [left, middle]. Total 6 frames.
        # Pipeline appends the last frame (F4) at the end. Total 7 frames.
        assert reader.get_frame_count() == 7
    finally:
        reader.close()
    
    assert mock_engine.infer.call_count == 3


from video_engine.scene_detection import SceneDetector

@patch("video_engine.audio_manager.AudioManager.has_audio", return_value=False)
def test_scene_cut_skips_inference(mock_has: MagicMock, dummy_video: Path, tmp_path: Path) -> None:
    """Test that a detected scene cut skips inference and avoids interpolation."""
    output_path = tmp_path / "out_scene_cut.mp4"
    
    mock_engine = MagicMock(spec=InferenceEngine)
    mock_engine.infer.return_value = np.full((240, 320, 3), 128, dtype=np.uint8)
    
    # Create a SceneDetector mock that detects a cut on the 2nd pair (between red and green)
    mock_scene_detector = MagicMock(spec=SceneDetector)
    # The dummy video has frames: black, red, green, blue.
    # Pairs are:
    # 1. black -> red
    # 2. red -> green
    # 3. green -> blue
    # We will mock it so that the 2nd pair (red -> green) triggers a scene cut.
    mock_scene_detector.is_scene_cut.side_effect = [False, True, False]
    
    pipeline = ProcessingPipeline(
        inference_engine=mock_engine, 
        fps_multiplier=2,
        scene_detector=mock_scene_detector
    )
    
    pipeline.process_video(dummy_video, output_path)
    
    assert output_path.exists()
    
    reader = VideoReader(output_path)
    reader.load_video()
    try:
        # Original is 4 frames.
        # Pairs:
        # 1. False -> outputs 2 frames [left, middle]
        # 2. True -> outputs 1 frame [left]
        # 3. False -> outputs 2 frames [left, middle]
        # Last frame (blue) is appended: 1 frame
        # Total frames expected: 2 + 1 + 2 + 1 = 6 frames
        assert reader.get_frame_count() == 6
    finally:
        reader.close()
    
    # Inference should only have been called twice (for pairs 1 and 3)
    assert mock_engine.infer.call_count == 2
    
    # is_scene_cut should have been called 3 times (once per pair)
    assert mock_scene_detector.is_scene_cut.call_count == 3


from video_engine.inference.onnx_engine import ONNXInferenceEngine

@pytest.mark.skipif(not Path("models/basic/basic_model.onnx").exists(),
                    reason="basic_model.onnx not found")
@patch("video_engine.audio_manager.AudioManager.has_audio", return_value=False)
def test_real_model_pipeline_integration(mock_has: MagicMock, dummy_video: Path, tmp_path: Path) -> None:
    """End-to-end test using the real ONNX backend."""
    model_path = Path("models/basic/basic_model.onnx")
    
    # Init and load the real engine
    engine = ONNXInferenceEngine(model_path)
    engine.load_model()
    
    # Init pipeline with real engine and a multiplier of 2
    pipeline = ProcessingPipeline(inference_engine=engine, fps_multiplier=2)
    
    output_path = tmp_path / "out_real_infer.mp4"
    pipeline.process_video(dummy_video, output_path)
    
    assert output_path.exists()
    
    # Verify outputs
    orig_reader = VideoReader(dummy_video)
    orig_reader.load_video()
    try:
        orig_frames = orig_reader.get_frame_count()
        orig_fps = orig_reader.get_fps()
        orig_res = orig_reader.get_resolution()
    finally:
        orig_reader.close()
        
    out_reader = VideoReader(output_path)
    out_reader.load_video()
    try:
        # FPS should double
        assert out_reader.get_fps() == orig_fps * 2
        assert out_reader.get_resolution() == orig_res
        
        # Frame count equals 2*N - 1
        expected_frames = (2 * orig_frames) - 1
        assert out_reader.get_frame_count() == expected_frames
        
        # Verify duration matches
        input_duration = orig_frames / orig_fps
        output_duration = out_reader.get_frame_count() / out_reader.get_fps()
        assert abs(input_duration - output_duration) < 0.05
    finally:
        out_reader.close()


from video_engine.overlay_restoration import OverlayRestoration
from video_engine.config import TheiaConfig

@patch("video_engine.audio_manager.AudioManager.has_audio", return_value=False)
def test_overlay_restoration_called(mock_has: MagicMock, dummy_video: Path, tmp_path: Path) -> None:
    """Test that overlay restoration is correctly invoked when enabled."""
    output_path = tmp_path / "out_overlay.mp4"
    
    mock_engine = MagicMock(spec=InferenceEngine)
    mock_engine.infer.return_value = np.full((240, 320, 3), 128, dtype=np.uint8)
    
    mock_overlay = MagicMock(spec=OverlayRestoration)
    mock_overlay.generate_mask.return_value = np.zeros((240, 320), dtype=np.uint8)
    mock_overlay.restore_overlay.return_value = np.full((240, 320, 3), 128, dtype=np.uint8)
    
    config = TheiaConfig(protect_static_overlays=True, detect_scene_cuts=False)
    
    pipeline = ProcessingPipeline(
        inference_engine=mock_engine,
        config=config,
        fps_multiplier=2,
        overlay_restoration=mock_overlay
    )
    
    pipeline.process_video(dummy_video, output_path)
    
    assert output_path.exists()
    
    # 3 frame pairs, so it should be called 3 times
    assert mock_overlay.generate_mask.call_count == 3
    assert mock_overlay.restore_overlay.call_count == 3


@patch("video_engine.audio_manager.AudioManager.has_audio", return_value=False)
def test_overlay_restoration_disabled_bypasses(mock_has: MagicMock, dummy_video: Path, tmp_path: Path) -> None:
    """Test that disabled configuration bypasses overlay restoration entirely."""
    output_path = tmp_path / "out_overlay_disabled.mp4"
    
    mock_engine = MagicMock(spec=InferenceEngine)
    mock_engine.infer.return_value = np.full((240, 320, 3), 128, dtype=np.uint8)
    
    mock_overlay = MagicMock(spec=OverlayRestoration)
    
    config = TheiaConfig(protect_static_overlays=False)
    
    pipeline = ProcessingPipeline(
        inference_engine=mock_engine,
        config=config,
        fps_multiplier=2,
        overlay_restoration=mock_overlay
    )
    
    pipeline.process_video(dummy_video, output_path)
    
    assert mock_overlay.generate_mask.call_count == 0
    assert mock_overlay.restore_overlay.call_count == 0


@patch("video_engine.audio_manager.AudioManager.has_audio", return_value=False)
def test_scene_cuts_bypass_overlay_restoration(mock_has: MagicMock, dummy_video: Path, tmp_path: Path) -> None:
    """Test that scene cuts skip inference and overlay generation."""
    output_path = tmp_path / "out_overlay_scene_cut.mp4"
    
    mock_engine = MagicMock(spec=InferenceEngine)
    mock_engine.infer.return_value = np.full((240, 320, 3), 128, dtype=np.uint8)
    
    mock_scene_detector = MagicMock(spec=SceneDetector)
    # Detect a cut on every single frame pair
    mock_scene_detector.is_scene_cut.return_value = True
    
    mock_overlay = MagicMock(spec=OverlayRestoration)
    
    config = TheiaConfig(protect_static_overlays=True, detect_scene_cuts=True)
    
    pipeline = ProcessingPipeline(
        inference_engine=mock_engine,
        config=config,
        fps_multiplier=2,
        scene_detector=mock_scene_detector,
        overlay_restoration=mock_overlay
    )
    
    pipeline.process_video(dummy_video, output_path)
    
    # Inference should never be called
    assert mock_engine.infer.call_count == 0
    # Overlay should never be generated since inference was skipped
    assert mock_overlay.generate_mask.call_count == 0
    assert mock_overlay.restore_overlay.call_count == 0

