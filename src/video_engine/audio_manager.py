"""Audio manager for Phase 4 of Theia Video Enhancer."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import types
from pathlib import Path

from .logger import logger

FFMPEG_TIMEOUT = 300

class AudioProcessingError(Exception):
    """Exception raised when FFmpeg encounters an error."""
    pass


class AudioManager:
    """Manages audio extraction and merging using system FFmpeg."""

    def __init__(self, temp_dir: str | Path | None = None) -> None:
        """Initialize the audio manager, optionally specifying a temporary directory.

        Args:
            temp_dir: Directory to store temporary audio files. If None, uses system default.
        
        Raises:
            RuntimeError: If ffmpeg or ffprobe are not found in the system PATH.
        """
        self.temp_dir = Path(temp_dir) if temp_dir else None
        self._tracked_files: list[Path] = []
        
    def _verify_ffmpeg_available(self) -> None:
        """Verify ffmpeg and ffprobe are available in the system PATH."""
        if not shutil.which("ffmpeg"):
            raise RuntimeError("ffmpeg not found in system PATH. FFmpeg is required for audio processing.")
        if not shutil.which("ffprobe"):
            raise RuntimeError("ffprobe not found in system PATH. FFprobe is required for audio processing.")
            
    def has_audio(self, video_path: str | Path) -> bool:
        """Check if the source video contains an audio stream using ffprobe."""
        self._verify_ffmpeg_available()
        video_path = Path(video_path)
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")
            
        command = [
            "ffprobe",
            "-i", str(video_path),
            "-show_streams",
            "-select_streams", "a",
            "-loglevel", "error"
        ]
        
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True, timeout=FFMPEG_TIMEOUT)
            # If ffprobe outputs any stream information, an audio stream exists.
            return bool(result.stdout.strip())
        except subprocess.CalledProcessError as e:
            logger.error("Failed to probe video for audio: %s", e.stderr)
            raise AudioProcessingError(f"ffprobe failed: {e.stderr}") from e
        except subprocess.TimeoutExpired as e:
            logger.error("Failed to probe video for audio: timed out")
            raise AudioProcessingError(f"ffprobe timed out after {FFMPEG_TIMEOUT}s") from e

    def extract_audio(self, video_path: str | Path) -> Path | None:
        """Extract audio from the video to a temporary file.

        Returns:
            The path to the temporary audio file, or None if no audio exists.
        """
        self._verify_ffmpeg_available()
        video_path = Path(video_path)
        if not self.has_audio(video_path):
            logger.info("No audio stream found in %s", video_path)
            return None
            
        # Create a temporary file for the extracted audio
        fd, temp_audio_path_str = tempfile.mkstemp(suffix=".m4a", dir=self.temp_dir)
        os.close(fd)
        temp_audio_path = Path(temp_audio_path_str)
        self._tracked_files.append(temp_audio_path)
        
        command = [
            "ffmpeg",
            "-y",  # Overwrite output without asking
            "-i", str(video_path),
            "-vn",  # Disable video
            "-c:a", "aac",  # Convert to AAC for broad compatibility
            "-q:a", "2",    # High quality
            "-loglevel", "error",
            str(temp_audio_path)
        ]
        
        logger.info("Extracting audio from %s to %s", video_path, temp_audio_path)
        try:
            subprocess.run(command, capture_output=True, text=True, check=True, timeout=FFMPEG_TIMEOUT)
            return temp_audio_path
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            if temp_audio_path.exists():
                try:
                    temp_audio_path.unlink()
                except Exception:
                    pass
            if temp_audio_path in self._tracked_files:
                self._tracked_files.remove(temp_audio_path)
                
            if isinstance(e, subprocess.TimeoutExpired):
                logger.error("Failed to extract audio: timed out")
                raise AudioProcessingError(f"ffmpeg extraction timed out after {FFMPEG_TIMEOUT}s") from e
            else:
                logger.error("Failed to extract audio: %s", e.stderr)
                raise AudioProcessingError(f"ffmpeg extraction failed: {e.stderr}") from e

    def merge_audio(self, video_path: str | Path, audio_path: str | Path, final_output_path: str | Path) -> bool:
        """Merge an audio file into a video file.

        Returns:
            True if successful.
        """
        self._verify_ffmpeg_available()
        video_path = Path(video_path)
        audio_path = Path(audio_path)
        final_output_path = Path(final_output_path)
        
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
            
        # Ensure parent directory exists
        final_output_path.parent.mkdir(parents=True, exist_ok=True)
        
        command = [
            "ffmpeg",
            "-y",
            "-i", str(video_path),
            "-i", str(audio_path),
            "-c:v", "copy",  # Copy video stream without re-encoding
            "-c:a", "copy",  # Copy audio stream without re-encoding
            "-loglevel", "error",
            str(final_output_path)
        ]
        
        logger.info("Merging audio %s into video %s -> %s", audio_path, video_path, final_output_path)
        try:
            subprocess.run(command, capture_output=True, text=True, check=True, timeout=FFMPEG_TIMEOUT)
            if not final_output_path.exists():
                raise AudioProcessingError("ffmpeg merge succeeded but output file not found")
            return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            if isinstance(e, subprocess.TimeoutExpired):
                logger.error("Failed to merge audio: timed out")
                raise AudioProcessingError(f"ffmpeg merge timed out after {FFMPEG_TIMEOUT}s") from e
            else:
                logger.error("Failed to merge audio: %s", e.stderr)
                raise AudioProcessingError(f"ffmpeg merge failed: {e.stderr}") from e

    def cleanup(self) -> None:
        """Delete any temporary audio files created by this instance."""
        for path in self._tracked_files:
            try:
                if path.exists():
                    path.unlink()
            except Exception as e:
                logger.warning("Failed to delete temporary audio file %s: %s", path, e)
        self._tracked_files.clear()

    def __enter__(self) -> AudioManager:
        """Context manager entry point."""
        return self

    def __exit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: types.TracebackType | None) -> None:
        """Context manager exit point to ensure cleanup of temporary files."""
        self.cleanup()
        
    def __del__(self) -> None:
        """Safely release resources during object cleanup."""
        self.cleanup()
