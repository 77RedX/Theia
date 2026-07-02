"""Tests for ONNXInferenceEngine."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from video_engine.inference.onnx_engine import ONNXInferenceEngine


def test_missing_model() -> None:
    """Test that engine raises FileNotFoundError if model doesn't exist."""
    with pytest.raises(FileNotFoundError, match="ONNX model not found"):
        ONNXInferenceEngine("non_existent_model.onnx")


@patch("video_engine.inference.onnx_engine.Path.exists", return_value=True)
def test_lazy_loading(mock_exists: MagicMock) -> None:
    """Test that model does not load during initialization."""
    engine = ONNXInferenceEngine("dummy.onnx")
    
    assert not engine.is_loaded
    assert engine.input_name == ""
    assert engine.model_spec is None


@patch("video_engine.inference.onnx_engine.Path.exists", return_value=True)
@patch("video_engine.inference.onnx_engine.ort.get_available_providers")
@patch("video_engine.inference.onnx_engine.ort.InferenceSession")
def test_successful_loading_and_metadata_extraction(
    mock_session_cls: MagicMock,
    mock_providers: MagicMock,
    mock_exists: MagicMock,
) -> None:
    """Test loading the model and extracting metadata."""
    # Setup mocks
    mock_providers.return_value = ["CUDAExecutionProvider", "CPUExecutionProvider"]
    
    mock_session = MagicMock()
    mock_input = MagicMock()
    mock_input.name = "frames"
    mock_input.shape = ["batch_size", 6, 256, 448]
    
    mock_output = MagicMock()
    mock_output.name = "middle_frame"
    mock_output.shape = ["batch_size", 3, 256, 448]
    
    mock_session.get_inputs.return_value = [mock_input]
    mock_session.get_outputs.return_value = [mock_output]
    mock_session_cls.return_value = mock_session
    
    # Initialize engine
    engine = ONNXInferenceEngine("dummy.onnx")
    assert not engine.is_loaded
    
    # Load model
    engine.load_model()
    
    assert engine.is_loaded
    assert engine.input_name == "frames"
    assert engine.output_name == "middle_frame"
    assert engine.input_shape == ("batch_size", 6, 256, 448)
    assert engine.output_shape == ("batch_size", 3, 256, 448)
    
    # Verify ModelSpec configuration object was populated correctly
    spec = engine.model_spec
    assert spec is not None
    assert spec.channels == 6
    assert spec.input_height == 256
    assert spec.input_width == 448
    
    # Verify providers
    mock_session_cls.assert_called_once_with(
        "dummy.onnx", 
        providers=["CUDAExecutionProvider", "CPUExecutionProvider"]
    )


@patch("video_engine.inference.onnx_engine.Path.exists", return_value=True)
@patch("video_engine.inference.onnx_engine.ort.get_available_providers")
@patch("video_engine.inference.onnx_engine.ort.InferenceSession")
def test_cpu_fallback(
    mock_session_cls: MagicMock,
    mock_providers: MagicMock,
    mock_exists: MagicMock,
) -> None:
    """Test that CPU is used if CUDA is unavailable."""
    # CUDA not available
    mock_providers.return_value = ["CPUExecutionProvider"]
    
    mock_session = MagicMock()
    mock_input = MagicMock()
    mock_input.shape = ["batch_size", 6, 256, 448]
    mock_output = MagicMock()
    mock_output.shape = ["batch_size", 3, 256, 448]
    mock_session.get_inputs.return_value = [mock_input]
    mock_session.get_outputs.return_value = [mock_output]
    mock_session_cls.return_value = mock_session
    
    engine = ONNXInferenceEngine("dummy.onnx")
    engine.load_model()
    
    # Should only pass CPU provider
    mock_session_cls.assert_called_once_with(
        "dummy.onnx", 
        providers=["CPUExecutionProvider"]
    )


def test_inference_before_load() -> None:
    """Test that infer raises RuntimeError if model is not loaded."""
    with patch("video_engine.inference.onnx_engine.Path.exists", return_value=True):
        engine = ONNXInferenceEngine("dummy.onnx")
        left = np.zeros((1080, 1920, 3), dtype=np.uint8)
        right = np.zeros((1080, 1920, 3), dtype=np.uint8)
        
        with pytest.raises(RuntimeError, match="Model is not loaded."):
            engine.infer(left, right)


@patch("video_engine.inference.onnx_engine.Path.exists", return_value=True)
@patch("video_engine.inference.onnx_engine.ort.get_available_providers")
@patch("video_engine.inference.onnx_engine.ort.InferenceSession")
def test_successful_inference_and_shape_restoration(
    mock_session_cls: MagicMock,
    mock_providers: MagicMock,
    mock_exists: MagicMock,
) -> None:
    """Test full inference pipeline with mocked onnxruntime."""
    mock_providers.return_value = ["CPUExecutionProvider"]
    
    mock_session = MagicMock()
    mock_input = MagicMock()
    mock_input.name = "frames"
    mock_input.shape = ["batch_size", 6, 256, 448]
    
    mock_output = MagicMock()
    mock_output.name = "middle_frame"
    mock_output.shape = ["batch_size", 3, 256, 448]
    
    mock_session.get_inputs.return_value = [mock_input]
    mock_session.get_outputs.return_value = [mock_output]
    
    # Mock run to return a dummy output tensor
    dummy_out = np.zeros((1, 3, 256, 448), dtype=np.float32)
    mock_session.run.return_value = [dummy_out]
    
    mock_session_cls.return_value = mock_session
    
    engine = ONNXInferenceEngine("dummy.onnx")
    engine.load_model()
    
    left = np.zeros((1080, 1920, 3), dtype=np.uint8)
    right = np.zeros((1080, 1920, 3), dtype=np.uint8)
    
    with patch.object(engine, "_preprocess_frames", wraps=engine._preprocess_frames) as mock_pre:
        with patch.object(engine, "_postprocess_frame", wraps=engine._postprocess_frame) as mock_post:
            result = engine.infer(left, right)
            
            # Verify preprocessing was called
            mock_pre.assert_called_once()
            # Verify postprocessing was called
            mock_post.assert_called_once()
            
            # Verify the output frame shape matches the original input frames (1080, 1920, 3)
            assert result.shape == (1080, 1920, 3)
            assert result.dtype == np.uint8
            
            # Verify session.run was called with the right input dictionary
            mock_session.run.assert_called_once()
            args, kwargs = mock_session.run.call_args
            assert args[0] == ["middle_frame"]
            assert "frames" in args[1]
            # Input tensor should be shaped (1, 6, 256, 448)
            assert args[1]["frames"].shape == (1, 6, 256, 448)


@pytest.mark.skipif(not Path("models/basic/basic_model.onnx").exists(),
                    reason="basic_model.onnx not found")
def test_real_model_inference() -> None:
    """Test inference with the real ONNX model (no mocks)."""
    model_path = Path("models/basic/basic_model.onnx")
    
    engine = ONNXInferenceEngine(model_path)
    engine.load_model()
    
    assert engine.is_loaded
    
    # Create arbitrary 720p dummy frames
    height, width = 720, 1280
    left = np.zeros((height, width, 3), dtype=np.uint8)
    right = np.full((height, width, 3), 255, dtype=np.uint8)
    
    # Run real inference
    middle = engine.infer(left, right)
    
    # Verify outputs
    assert middle.dtype == np.uint8
    assert middle.shape == (height, width, 3)
