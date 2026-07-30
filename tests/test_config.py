"""Tests for the centralized configuration object."""

from collections.abc import Callable
import pytest

from video_engine.config import TheiaConfig
from video_engine.processing_pipeline import ProcessingPipeline


def test_default_configuration() -> None:
    """Test that default configuration is valid."""
    config = TheiaConfig()
    assert config.preset == "fast"
    assert config.backend == "onnx"
    assert config.keep_audio is True
    assert config.output_format == "mp4"
    assert config.detect_scene_cuts is True
    assert config.scene_cut_threshold == 35.0
    assert config.protect_static_overlays is False
    assert config.debug_mode is False
    assert config.debug_output_dir == "debug"
    assert config.progress_callback is None


def test_invalid_preset() -> None:
    """Test validation of invalid preset."""
    with pytest.raises(ValueError, match="Invalid preset: 'ultra'"):
        TheiaConfig(preset="ultra")


def test_invalid_backend() -> None:
    """Test validation of invalid backend."""
    with pytest.raises(ValueError, match="Invalid backend: 'torch'"):
        TheiaConfig(backend="torch")


def test_invalid_output_format() -> None:
    """Test that invalid output format raises ValueError."""
    with pytest.raises(ValueError, match="Invalid output format"):
        TheiaConfig(output_format="avi")


def test_invalid_scene_cut_threshold() -> None:
    """Test that invalid scene cut threshold raises ValueError."""
    with pytest.raises(ValueError, match="Invalid scene cut threshold"):
        TheiaConfig(scene_cut_threshold=0.0)
    with pytest.raises(ValueError, match="Invalid scene cut threshold"):
        TheiaConfig(scene_cut_threshold=-1.5)


def test_invalid_protect_static_overlays() -> None:
    """Test that invalid protect_static_overlays type raises TypeError."""
    with pytest.raises(TypeError, match="protect_static_overlays must be a boolean"):
        # We need to ignore type checking for the intentional bad assignment here
        TheiaConfig(protect_static_overlays="yes")  # type: ignore


def test_invalid_debug_mode() -> None:
    """Test that invalid debug_mode type raises TypeError."""
    with pytest.raises(TypeError, match="debug_mode must be a boolean"):
        TheiaConfig(debug_mode="yes")  # type: ignore


def test_invalid_debug_output_dir() -> None:
    """Test that invalid debug_output_dir type raises TypeError."""
    with pytest.raises(TypeError, match="debug_output_dir must be a string"):
        TheiaConfig(debug_output_dir=123)  # type: ignore


def test_frozen_dataclass_behavior() -> None:
    """Test that configuration is immutable after initialization."""
    config = TheiaConfig()
    
    # FrozenInstanceError (subclass of AttributeError) raised when frozen=True
    with pytest.raises(Exception):
        config.preset = "quality"  # type: ignore


def test_pipeline_accepts_configuration() -> None:
    """Test that ProcessingPipeline accepts the configuration object."""
    config = TheiaConfig(keep_audio=False)
    pipeline = ProcessingPipeline(config=config)
    assert pipeline.config.keep_audio is False
    assert pipeline.config.preset == "fast"
