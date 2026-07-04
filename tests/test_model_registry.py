"""Tests for the ModelRegistry."""

import json
from pathlib import Path

import pytest

from video_engine.model_registry import ModelRegistry


def create_mock_model_dir(base_path: Path, folder_name: str, 
                          has_readme: bool = True, 
                          has_json: bool = True, 
                          num_onnx: int = 1) -> Path:
    """Helper to create a mocked deployed model directory."""
    model_dir = base_path / folder_name
    model_dir.mkdir(parents=True, exist_ok=True)
    
    if has_readme:
        (model_dir / "README.md").write_text("# Dummy", encoding="utf-8")
        
    if has_json:
        info = {
            "model_name": f"Dummy_{folder_name}",
            "version": "1.0.0",
            "backend": "onnx",
            "interpolation_factor": 2,
            "input": {"name": "frames"}
        }
        with open(model_dir / "model_info.json", "w", encoding="utf-8") as f:
            json.dump(info, f)
            
    for i in range(num_onnx):
        (model_dir / f"model_{i}.onnx").touch()
        
    return model_dir


def test_registry_discovers_real_basic_model() -> None:
    """Test that the registry can discover the real basic model if deployed."""
    # This assumes the real models/basic exists as setup in Phase 6G
    real_models_path = Path("models")
    if not real_models_path.exists():
        pytest.skip("Real models directory not found.")
        
    registry = ModelRegistry(real_models_path)
    
    # It should discover at least 'fast' if 'models/basic' is properly deployed
    models = registry.available_models()
    assert "fast" in models
    
    # get_model should return correct dataclass
    model_info = registry.get_model("fast")
    assert model_info.preset == "fast"
    assert model_info.model_name == "BasicFlowInterp"
    assert model_info.interpolation_factor == 2
    assert model_info.onnx_path.exists()
    assert model_info.metadata_path.exists()


def test_available_models_only_returns_valid_presets(tmp_path: Path) -> None:
    """Test that available_models only lists presets that are fully deployed."""
    registry = ModelRegistry(tmp_path)
    
    # Initially empty
    assert registry.available_models() == []
    
    # Add a valid 'basic' model (maps to 'fast')
    create_mock_model_dir(tmp_path, "basic")
    assert registry.available_models() == ["fast"]
    
    # Add a broken 'plus' model (maps to 'balanced') - missing README
    create_mock_model_dir(tmp_path, "plus", has_readme=False)
    # Should still only return 'fast', gracefully ignoring the broken one in available_models()
    assert registry.available_models() == ["fast"]


def test_get_model_invalid_preset(tmp_path: Path) -> None:
    """Test requesting a preset that does not exist in the mapping."""
    registry = ModelRegistry(tmp_path)
    with pytest.raises(RuntimeError, match="Unknown preset"):
        registry.get_model("ultra_fast")


def test_get_model_absent_directory(tmp_path: Path) -> None:
    """Test requesting a preset whose directory does not exist."""
    registry = ModelRegistry(tmp_path)
    # directory 'plus' (for 'balanced') is absent
    with pytest.raises(RuntimeError, match="Preset 'balanced' is unavailable"):
        registry.get_model("balanced")


def test_missing_readme(tmp_path: Path) -> None:
    """Test validation fails when README.md is missing."""
    create_mock_model_dir(tmp_path, "basic", has_readme=False)
    registry = ModelRegistry(tmp_path)
    
    with pytest.raises(RuntimeError, match="Missing README.md"):
        registry.get_model("fast")


def test_missing_json(tmp_path: Path) -> None:
    """Test validation fails when model_info.json is missing."""
    create_mock_model_dir(tmp_path, "basic", has_json=False)
    registry = ModelRegistry(tmp_path)
    
    with pytest.raises(RuntimeError, match="Missing model_info.json"):
        registry.get_model("fast")


def test_missing_onnx(tmp_path: Path) -> None:
    """Test validation fails when no ONNX file exists."""
    create_mock_model_dir(tmp_path, "basic", num_onnx=0)
    registry = ModelRegistry(tmp_path)
    
    with pytest.raises(RuntimeError, match="Missing .onnx file"):
        registry.get_model("fast")


def test_duplicate_onnx(tmp_path: Path) -> None:
    """Test validation fails when multiple ONNX files exist."""
    create_mock_model_dir(tmp_path, "basic", num_onnx=2)
    registry = ModelRegistry(tmp_path)
    
    with pytest.raises(RuntimeError, match="Multiple .onnx files found"):
        registry.get_model("fast")
