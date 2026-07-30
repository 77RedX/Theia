"""Phase 5 processing pipeline orchestration."""

import os
import shutil
import tempfile
from collections.abc import Callable
from pathlib import Path

import numpy as np

from .audio_manager import AudioManager, AudioProcessingError
from .frame_extractor import FrameExtractor
from .logger import logger
from .video_reader import VideoReader
from .video_writer import VideoWriter
from .inference.base import InferenceEngine
from .config import TheiaConfig
from .scene_detection import SceneDetector
from .overlay_restoration import OverlayRestoration
from .debug import DebugCollector


class ProcessingPipeline:
    """Orchestrates the end-to-end video processing flow."""

    def __init__(
        self,
        inference_engine: InferenceEngine | None = None,
        config: TheiaConfig | None = None,
        fps_multiplier: int = 1,
        scene_detector: SceneDetector | None = None,
        overlay_restoration: OverlayRestoration | None = None,
        debug_collector: DebugCollector | None = None,
    ) -> None:
        """Initialize the processing pipeline.
        
        Args:
            inference_engine: Optional inference engine for frame interpolation.
                If None, the pipeline will act as a pass-through.
            config: Optional central configuration object. Defaults to basic TheiaConfig.
            fps_multiplier: Expected output FPS multiplier derived from the model.
        """
        self.inference_engine = inference_engine
        self.config = config or TheiaConfig()
        self.fps_multiplier = fps_multiplier
        self.scene_detector = scene_detector
        self.overlay_restoration = overlay_restoration
        self.debug_collector = debug_collector

    def _process_pair(self, left: np.ndarray, right: np.ndarray, pair_idx: int) -> list[np.ndarray]:
        """Process a frame pair.
        
        Args:
            left: The first frame in the pair.
            right: The second frame in the pair.
            pair_idx: The current frame pair index.
            
        Returns:
            A list containing the left frame and, if an inference engine is present,
            the generated middle frame.
        """
        is_cut = False
        scene_score = 0.0
        
        if self.scene_detector is not None and self.config.detect_scene_cuts:
            if self.config.debug_mode and self.debug_collector is not None:
                scene_score = self.scene_detector.compute_difference(left, right)
            
            if self.scene_detector.is_scene_cut(left, right):
                logger.info("Scene cut detected, skipping inference")
                is_cut = True

        mask = None
        middle = None
        restored = None
        
        if not is_cut:
            if self.inference_engine is None:
                return [left]
                
            # Optional: Generate overlay mask before inference
            if self.overlay_restoration is not None and self.config.protect_static_overlays:
                mask = self.overlay_restoration.generate_mask(left, right)
                
            middle = self.inference_engine.infer(left, right)
            
            # Optional: Restore overlay pixels on the generated frame
            if self.overlay_restoration is not None and mask is not None:
                restored = self.overlay_restoration.restore_overlay(left, middle, mask)
                middle = restored

        # Diagnostic Export (zero-overhead if disabled)
        if self.config.debug_mode and self.debug_collector is not None:
            self.debug_collector.save_frame("left", left, pair_idx)
            self.debug_collector.save_frame("right", right, pair_idx)
            
            if self.scene_detector is not None:
                self.debug_collector.save_scene_score(scene_score, pair_idx)
                
            if mask is not None:
                self.debug_collector.save_mask("overlay_mask", mask, pair_idx)
                
            if middle is not None:
                self.debug_collector.save_frame("generated", middle, pair_idx)
                
            if restored is not None:
                self.debug_collector.save_frame("restored", restored, pair_idx)
                
            metadata = {
                "pair_index": pair_idx,
                "scene_detected": is_cut,
                "scene_score": scene_score,
                "overlay_enabled": self.config.protect_static_overlays,
                "model_preset": self.config.preset,
                "original_resolution": [int(left.shape[1]), int(left.shape[0])]
            }
            self.debug_collector.save_metadata(metadata, pair_idx)

        if is_cut or self.inference_engine is None:
            return [left]

        return [left, middle]

    def process_video(
        self,
        input_video: str | Path,
        output_video: str | Path,
        progress_callback: Callable[[int, int], None] | None = None
    ) -> None:
        """Process the video end-to-end.
        
        Args:
            input_video: Path to the input video.
            output_video: Path to save the final video.
            progress_callback: Optional callback receiving (current_frame, total_frames).
            
        Raises:
            FileNotFoundError: If the input video does not exist.
        """
        input_video = Path(input_video)
        output_video = Path(output_video)

        if not input_video.exists():
            raise FileNotFoundError(f"Input video not found: {input_video}")

        # Ensure output directory exists
        output_video.parent.mkdir(parents=True, exist_ok=True)

        logger.info("Starting processing pipeline for %s", input_video)

        # Resolve progress callback (favor method argument for backward compatibility)
        resolved_progress_callback = progress_callback or self.config.progress_callback

        with AudioManager() as audio_manager:
            # Check for audio streams
            has_audio = False
            audio_path = None
            if self.config.keep_audio:
                try:
                    has_audio = audio_manager.has_audio(input_video)
                    if has_audio:
                        audio_path = audio_manager.extract_audio(input_video)
                except (RuntimeError, AudioProcessingError) as e:
                    logger.warning("Audio extraction failed or dependencies missing: %s. Proceeding without audio.", e)
                    has_audio = False

            # Create a temporary video path to write frames into before merging audio
            temp_video_fd, temp_video_str = tempfile.mkstemp(suffix=".mp4")
            os.close(temp_video_fd)
            temp_video_path = Path(temp_video_str)

            try:
                # 1. Video Reader
                reader = VideoReader(input_video)
                reader.load_video()
                try:
                    fps = reader.get_fps()
                    resolution = reader.get_resolution()
                    
                    output_fps = fps * self.fps_multiplier if self.inference_engine else fps

                    # 2. Frame Extractor
                    extractor = FrameExtractor(reader)

                    # 3. Video Writer
                    with VideoWriter(temp_video_path, output_fps, resolution) as writer:
                        total_frames = reader.get_frame_count()
                        
                        if total_frames == 1:
                            # Handle single-frame video specially
                            single_frame = next(extractor.frame_generator(), None)
                            if single_frame is not None:
                                writer.write_frame(single_frame)
                                if resolved_progress_callback:
                                    resolved_progress_callback(1, 1)
                        else:
                            last_frame = None
                            # Track input frames consumed (not output frames written)
                            # to keep progress 0–100% even when interpolation multiplies output
                            input_frames_done = 1  # First 'left' frame is consumed on first pair read

                            # Iterate over frame pairs
                            for left, right in extractor.frame_pair_generator():
                                # Process the pair
                                processed_frames = self._process_pair(left, right, input_frames_done)
                                
                                # Write returned frames
                                for frame in processed_frames:
                                    writer.write_frame(frame)
                                    
                                last_frame = right
                                input_frames_done += 1  # Each pair advances one input frame
                                if resolved_progress_callback:
                                    resolved_progress_callback(input_frames_done, total_frames)

                            # Pipeline owns appending the final frame
                            if last_frame is not None:
                                writer.write_frame(last_frame)
                                if resolved_progress_callback:
                                    resolved_progress_callback(total_frames, total_frames)
                finally:
                    reader.close()

                # 4. Finalize Output
                if has_audio and audio_path is not None:
                    try:
                        audio_manager.merge_audio(temp_video_path, audio_path, output_video)
                        logger.info("Audio merged successfully into %s", output_video)
                    except AudioProcessingError as e:
                        logger.error("Failed to merge audio: %s. Falling back to video-only.", e)
                        shutil.move(str(temp_video_path), str(output_video))
                else:
                    # No audio to merge, compress the temp video to the final destination
                    try:
                        audio_manager.compress_video(temp_video_path, output_video)
                        logger.info("Video compressed successfully into %s", output_video)
                    except Exception as e:
                        logger.error("Failed to compress video: %s. Falling back to uncompressed video.", e)
                        shutil.move(str(temp_video_path), str(output_video))
                    
            finally:
                # Clean up the temporary video file if it still exists
                if temp_video_path.exists():
                    try:
                        temp_video_path.unlink()
                    except Exception as e:
                        logger.warning("Failed to delete temp video file %s: %s", temp_video_path, e)
