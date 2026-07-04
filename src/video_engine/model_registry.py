"""Model Registry for managing deployed AI models."""

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ModelInfo:
    """Represents a deployed model configuration."""
    preset: str
    model_name: str
    version: str
    backend: str
    interpolation_factor: int
    onnx_path: Path
    metadata_path: Path


class ModelRegistry:
    """Discovers and validates deployed inference models."""

    # Frozen preset mapping
    PRESET_MAPPING = {
        "fast": "basic",
        "balanced": "plus",
        "quality": "pro"
    }

    def __init__(self, models_dir: str | Path = "models") -> None:
        """Initialize the model registry.
        
        Args:
            models_dir: The root directory containing deployed model packages.
        """
        self._models_dir = Path(models_dir)

    def _validate_model_dir(self, preset: str, folder_name: str) -> ModelInfo:
        """Validate a single model directory and return its information."""
        model_path = self._models_dir / folder_name
        
        if not model_path.exists() or not model_path.is_dir():
            raise RuntimeError(f"Preset '{preset}' is unavailable. Model directory not found: {model_path}")

        # Check for README.md
        readme_path = model_path / "README.md"
        if not readme_path.exists():
            raise RuntimeError(f"Missing README.md in {model_path}")

        # Check for model_info.json
        metadata_path = model_path / "model_info.json"
        if not metadata_path.exists():
            raise RuntimeError(f"Missing model_info.json in {model_path}")

        # Check for exactly one .onnx file
        onnx_files = list(model_path.glob("*.onnx"))
        if not onnx_files:
            raise RuntimeError(f"Missing .onnx file in {model_path}")
        if len(onnx_files) > 1:
            raise RuntimeError(f"Multiple .onnx files found in {model_path}. Only one is allowed.")
        
        onnx_path = onnx_files[0]

        # Parse model_info.json
        try:
            with open(metadata_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Invalid JSON in {metadata_path}: {e}")

        model_name = data.get("model_name", "Unknown")
        version = data.get("version", "Unknown")
        backend = data.get("backend", "Unknown")
        interpolation_factor = data.get("interpolation_factor", 1)

        return ModelInfo(
            preset=preset,
            model_name=model_name,
            version=version,
            backend=backend,
            interpolation_factor=interpolation_factor,
            onnx_path=onnx_path,
            metadata_path=metadata_path
        )

    def available_models(self) -> list[str]:
        """Return a list of available presets."""
        available = []
        for preset, folder in self.PRESET_MAPPING.items():
            model_dir = self._models_dir / folder
            if model_dir.exists() and model_dir.is_dir():
                try:
                    self._validate_model_dir(preset, folder)
                    available.append(preset)
                except RuntimeError:
                    # Invalid model directory, treat as unavailable
                    pass
        return available

    def get_model(self, preset: str) -> ModelInfo:
        """Get the model configuration for a specific preset.
        
        Args:
            preset: The desired preset (fast, balanced, quality).
            
        Returns:
            The parsed model information.
            
        Raises:
            RuntimeError: If preset is invalid or model is not properly deployed.
        """
        preset_lower = preset.lower()
        if preset_lower not in self.PRESET_MAPPING:
            raise RuntimeError(
                f"Unknown preset: '{preset}'. Valid presets are {list(self.PRESET_MAPPING.keys())}"
            )
            
        folder_name = self.PRESET_MAPPING[preset_lower]
        return self._validate_model_dir(preset_lower, folder_name)
