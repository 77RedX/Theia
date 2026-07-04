"""Tests for the public API."""

from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from video_engine.api import enhance_video
from video_engine.config import TheiaConfig


@patch("video_engine.api.ModelRegistry")
@patch("video_engine.api.ONNXInferenceEngine")
@patch("video_engine.api.ProcessingPipeline")
def test_enhance_video_default_config(
    mock_pipeline_cls: MagicMock,
    mock_engine_cls: MagicMock,
    mock_registry_cls: MagicMock,
) -> None:
    """Test enhance_video uses default configuration when none is provided."""
    mock_registry = mock_registry_cls.return_value
    mock_engine = mock_engine_cls.return_value
    mock_pipeline = mock_pipeline_cls.return_value
    
    # Mock registry returning a dummy model info
    mock_model_info = MagicMock()
    mock_model_info.onnx_path = Path("dummy.onnx")
    mock_model_info.interpolation_factor = 2
    mock_registry.get_model.return_value = mock_model_info

    enhance_video("in.mp4", "out.mp4")

    # Verify registry invoked with default preset 'fast'
    mock_registry.get_model.assert_called_once_with("fast")
    
    # Verify engine instantiated with the onnx path and loaded
    mock_engine_cls.assert_called_once_with(Path("dummy.onnx"))
    mock_engine.load_model.assert_called_once()
    
    # Verify pipeline instantiated with engine and a default config
    mock_pipeline_cls.assert_called_once()
    kwargs = mock_pipeline_cls.call_args.kwargs
    assert kwargs["inference_engine"] == mock_engine
    assert isinstance(kwargs["config"], TheiaConfig)
    assert kwargs["fps_multiplier"] == 2
    
    # Verify process_video called
    mock_pipeline.process_video.assert_called_once_with("in.mp4", "out.mp4")


@patch("video_engine.api.ModelRegistry")
@patch("video_engine.api.ONNXInferenceEngine")
@patch("video_engine.api.ProcessingPipeline")
def test_enhance_video_custom_config(
    mock_pipeline_cls: MagicMock,
    mock_engine_cls: MagicMock,
    mock_registry_cls: MagicMock,
) -> None:
    """Test enhance_video respects custom configuration."""
    mock_registry = mock_registry_cls.return_value
    
    mock_model_info = MagicMock()
    mock_model_info.onnx_path = Path("custom.onnx")
    mock_model_info.interpolation_factor = 3
    mock_registry.get_model.return_value = mock_model_info

    # We use a preset we know is valid, but theoretically ModelRegistry validates this.
    # To test custom config flow, we just pass the config.
    # We'll use 'fast' to not trigger validation errors inside config itself, 
    # but let's change keep_audio to ensure the config object is passed along.
    custom_config = TheiaConfig(preset="fast", keep_audio=False)
    
    enhance_video("custom_in.mp4", "custom_out.mp4", config=custom_config)
    
    mock_registry.get_model.assert_called_once_with("fast")
    
    # Verify the pipeline received our exact custom config instance and multiplier
    kwargs = mock_pipeline_cls.call_args.kwargs
    assert kwargs["config"] is custom_config
    assert kwargs["fps_multiplier"] == 3


@patch("video_engine.api.ModelRegistry")
def test_enhance_video_invalid_preset_propagates(mock_registry_cls: MagicMock) -> None:
    """Test that invalid presets (caught by config or registry) propagate cleanly."""
    
    # Since TheiaConfig now raises ValueError on bad presets, it will fail before
    # even reaching ModelRegistry if we pass it explicitly.
    with pytest.raises(ValueError, match="Invalid preset"):
        TheiaConfig(preset="invalid_preset")
        
    # If a preset bypassed config validation but failed in registry (e.g. missing folder),
    # let's test that propagation.
    mock_registry = mock_registry_cls.return_value
    mock_registry.get_model.side_effect = RuntimeError("Model directory not found")
    
    valid_config = TheiaConfig(preset="fast")
    with pytest.raises(RuntimeError, match="Model directory not found"):
        enhance_video("in.mp4", "out.mp4", config=valid_config)
