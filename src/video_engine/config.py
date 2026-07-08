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
    detect_scene_cuts: bool = True
    scene_cut_threshold: float = 35.0
    protect_static_overlays: bool = False
    debug_mode: bool = False
    debug_output_dir: str = "debug"
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
            
        # Validate scene cut threshold
        if self.scene_cut_threshold <= 0:
            raise ValueError(f"Invalid scene cut threshold: {self.scene_cut_threshold}. Must be > 0.")
            
        # Validate protect_static_overlays type
        if not isinstance(self.protect_static_overlays, bool):
            raise TypeError(f"protect_static_overlays must be a boolean, got {type(self.protect_static_overlays)}")
            
        # Validate debug_mode type
        if not isinstance(self.debug_mode, bool):
            raise TypeError(f"debug_mode must be a boolean, got {type(self.debug_mode)}")
            
        # Validate debug_output_dir type
        if not isinstance(self.debug_output_dir, str):
            raise TypeError(f"debug_output_dir must be a string, got {type(self.debug_output_dir)}")
