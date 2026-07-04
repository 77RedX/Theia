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
