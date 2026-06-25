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


class ProcessingPipeline:
    """Orchestrates the end-to-end video processing flow."""

    @staticmethod
    def _process_pair(left: np.ndarray, right: np.ndarray) -> list[np.ndarray]:
        """Process a frame pair. Phase 5 pass-through behavior.
        
        Args:
            left: The first frame in the pair.
            right: The second frame in the pair.
            
        Returns:
            A list containing only the left frame.
        """
        return [left]

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

        with AudioManager() as audio_manager:
            # Check for audio streams
            has_audio = False
            audio_path = None
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

                    # 2. Frame Extractor
                    extractor = FrameExtractor(reader)

                    # 3. Video Writer
                    with VideoWriter(temp_video_path, fps, resolution) as writer:
                        total_frames = reader.get_frame_count()
                        
                        if total_frames == 1:
                            # Handle single-frame video specially
                            single_frame = next(extractor.frame_generator(), None)
                            if single_frame is not None:
                                writer.write_frame(single_frame)
                                if progress_callback:
                                    progress_callback(1, 1)
                        else:
                            last_frame = None
                            processed_count = 0

                            # Iterate over frame pairs
                            for left, right in extractor.frame_pair_generator():
                                # Process the pair
                                processed_frames = self._process_pair(left, right)
                                
                                # Write returned frames
                                for frame in processed_frames:
                                    writer.write_frame(frame)
                                    
                                last_frame = right
                                processed_count += len(processed_frames)
                                if progress_callback:
                                    progress_callback(processed_count, total_frames)

                            # Pipeline owns appending the final frame
                            if last_frame is not None:
                                writer.write_frame(last_frame)
                                processed_count += 1
                                if progress_callback:
                                    progress_callback(processed_count, total_frames)
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
                    # No audio to merge, just move the temp video to the final destination
                    logger.info("Moving video-only output to %s", output_video)
                    shutil.move(str(temp_video_path), str(output_video))
                    
            finally:
                # Clean up the temporary video file if it still exists
                if temp_video_path.exists():
                    try:
                        temp_video_path.unlink()
                    except Exception as e:
                        logger.warning("Failed to delete temp video file %s: %s", temp_video_path, e)
