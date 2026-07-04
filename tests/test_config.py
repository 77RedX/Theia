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
    """Test validation of invalid output format."""
    with pytest.raises(ValueError, match="Invalid output format: 'avi'"):
        TheiaConfig(output_format="avi")


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
