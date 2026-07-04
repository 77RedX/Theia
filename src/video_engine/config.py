"""Configuration layer for the Theia video engine."""

from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class TheiaConfig:
    """Immutable configuration for the Theia video engine."""
    
    preset: str = "fast"
    backend: str = "onnx"
    keep_audio: bool = True
    output_format: str = "mp4"
    progress_callback: Callable[[int, int], None] | None = None
    
    def __post_init__(self) -> None:
        """Validate configuration values."""
        # Validate preset
        if self.preset.lower() not in {"fast", "balanced", "quality"}:
            raise ValueError(f"Invalid preset: '{self.preset}'. Must be one of 'fast', 'balanced', 'quality'.")
            
        # Validate backend
        if self.backend.lower() not in {"onnx"}:
            raise ValueError(f"Invalid backend: '{self.backend}'. Must be 'onnx'.")
            
        # Validate output format
        if self.output_format.lower() not in {"mp4", "mkv"}:
            raise ValueError(f"Invalid output format: '{self.output_format}'. Must be 'mp4' or 'mkv'.")
