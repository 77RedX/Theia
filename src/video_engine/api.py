"""Public API for Theia Video Enhancer."""

from pathlib import Path

from .config import TheiaConfig
from .inference.onnx_engine import ONNXInferenceEngine
from .model_registry import ModelRegistry
from .processing_pipeline import ProcessingPipeline
from .scene_detection import SceneDetector
from .overlay_restoration import OverlayRestoration
from .debug import DebugCollector


def enhance_video(
    input_video: str | Path,
    output_video: str | Path,
    config: TheiaConfig | None = None,
) -> None:
    """Enhance a video using the Theia AI engine.
    
    This is the main entry point for the application. It handles model discovery,
    backend initialization, and processing pipeline orchestration.
    
    Args:
        input_video: Path to the input video.
        output_video: Path to save the processed video.
        config: Optional configuration object. If None, default settings are used.
    """
    if config is None:
        config = TheiaConfig()

    # 1. Discover the model based on the requested preset
    registry = ModelRegistry()
    model_info = registry.get_model(config.preset)

    # 2. Instantiate and load the inference engine (currently ONNX only)
    engine = ONNXInferenceEngine(model_info.onnx_path)
    engine.load_model()
    
    # Log which execution provider is active
    from .logger import logger
    provider = engine.active_provider
    if "Tensorrt" in provider:
        logger.info("Using GPU acceleration via TensorRT (%s)", provider)
    elif "CUDA" in provider:
        logger.info("Using GPU acceleration via CUDA (%s)", provider)
    elif "Dml" in provider:
        logger.info("Using GPU acceleration via DirectML (%s)", provider)
    else:
        logger.warning(
            "Running on CPU (%s). Install onnxruntime-gpu for GPU acceleration.",
            provider,
        )

    # 3. Instantiate optional components
    scene_detector = SceneDetector(threshold=config.scene_cut_threshold)
    overlay_restoration = OverlayRestoration()
    
    debug_collector = None
    if config.debug_mode:
        debug_collector = DebugCollector(config.debug_output_dir)

    # 4. Instantiate and run the processing pipeline
    pipeline = ProcessingPipeline(
        inference_engine=engine,
        config=config,
        fps_multiplier=model_info.interpolation_factor,
        scene_detector=scene_detector,
        overlay_restoration=overlay_restoration,
        debug_collector=debug_collector
    )
    pipeline.process_video(input_video, output_video)
