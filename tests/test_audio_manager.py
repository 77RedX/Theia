"""Tests for the AudioManager component."""

import os
import shutil
import subprocess
from collections.abc import Iterator
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from video_engine.audio_manager import AudioManager, AudioProcessingError


@pytest.fixture
def manager() -> Iterator[AudioManager]:
    """Return a fresh AudioManager instance with mocked system dependencies."""
    with patch("shutil.which", return_value="dummy/path"):
        yield AudioManager()


@pytest.fixture
def mock_video_path(tmp_path: Path) -> Path:
    """Return a dummy video path."""
    p = tmp_path / "dummy.mp4"
    p.write_text("dummy")
    return p


@pytest.fixture
def mock_audio_path(tmp_path: Path) -> Path:
    """Return a dummy audio path."""
    p = tmp_path / "dummy.m4a"
    p.write_text("dummy")
    return p


@patch("shutil.which")
def test_verify_ffmpeg_available_raises(mock_which: MagicMock) -> None:
    """Test that missing dependencies raise errors."""
    manager = AudioManager()
    mock_which.side_effect = lambda x: None if x == "ffmpeg" else "path/to/ffprobe"
    with pytest.raises(RuntimeError, match="ffmpeg not found"):
        manager._verify_ffmpeg_available()

    mock_which.side_effect = lambda x: "path/to/ffmpeg" if x == "ffmpeg" else None
    with pytest.raises(RuntimeError, match="ffprobe not found"):
        manager._verify_ffmpeg_available()


@patch("subprocess.run")
def test_has_audio_true(mock_run: MagicMock, manager: AudioManager, mock_video_path: Path) -> None:
    """Test has_audio returns True when an audio stream is found."""
    mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout="stream info")
    
    assert manager.has_audio(mock_video_path) is True
    mock_run.assert_called_once()
    assert "ffprobe" in mock_run.call_args[0][0]


@patch("subprocess.run")
def test_has_audio_false(mock_run: MagicMock, manager: AudioManager, mock_video_path: Path) -> None:
    """Test has_audio returns False when no audio stream is found."""
    mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout="")
    
    assert manager.has_audio(mock_video_path) is False


@patch("subprocess.run")
def test_has_audio_error(mock_run: MagicMock, manager: AudioManager, mock_video_path: Path) -> None:
    """Test has_audio raises AudioProcessingError on ffprobe failure."""
    mock_run.side_effect = subprocess.CalledProcessError(1, "ffprobe", stderr="error")
    
    with pytest.raises(AudioProcessingError, match="ffprobe failed"):
        manager.has_audio(mock_video_path)


@patch("subprocess.run")
def test_extract_audio_success(mock_run: MagicMock, manager: AudioManager, mock_video_path: Path) -> None:
    """Test extract_audio successfully calls ffmpeg and returns a path."""
    with patch.object(manager, "has_audio", return_value=True):
        mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")
        
        result_path = manager.extract_audio(mock_video_path)
        
        assert result_path is not None
        assert result_path.exists()
        assert result_path in manager._tracked_files
        
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "ffmpeg" in args
        assert "-vn" in args


def test_extract_audio_no_audio(manager: AudioManager, mock_video_path: Path) -> None:
    """Test extract_audio returns None if no audio stream exists."""
    with patch.object(manager, "has_audio", return_value=False):
        assert manager.extract_audio(mock_video_path) is None


@patch("subprocess.run")
def test_extract_audio_failure_cleans_up(mock_run: MagicMock, manager: AudioManager, mock_video_path: Path) -> None:
    """Test extract_audio cleans up temp file if ffmpeg fails."""
    with patch.object(manager, "has_audio", return_value=True):
        mock_run.side_effect = subprocess.CalledProcessError(1, "ffmpeg", stderr="error")
        
        with pytest.raises(AudioProcessingError, match="ffmpeg extraction failed"):
            manager.extract_audio(mock_video_path)
            
        assert len(manager._tracked_files) == 0


@patch("subprocess.run")
def test_extract_audio_timeout(mock_run: MagicMock, manager: AudioManager, mock_video_path: Path) -> None:
    """Test extract_audio handles timeout correctly."""
    with patch.object(manager, "has_audio", return_value=True):
        mock_run.side_effect = subprocess.TimeoutExpired("ffmpeg", 300)
        
        with pytest.raises(AudioProcessingError, match="ffmpeg extraction timed out"):
            manager.extract_audio(mock_video_path)
            
        assert len(manager._tracked_files) == 0


@patch("subprocess.run")
def test_merge_audio_success(mock_run: MagicMock, manager: AudioManager, mock_video_path: Path, mock_audio_path: Path, tmp_path: Path) -> None:
    """Test merge_audio successfully calls ffmpeg."""
    mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")
    output_path = tmp_path / "output.mp4"
    output_path.write_text("dummy")  # Mock output file creation
    
    assert manager.merge_audio(mock_video_path, mock_audio_path, output_path) is True
    
    mock_run.assert_called_once()
    args = mock_run.call_args[0][0]
    assert "ffmpeg" in args
    assert "-c:v" in args
    assert "copy" in args


@patch("subprocess.run")
def test_merge_audio_failure(mock_run: MagicMock, manager: AudioManager, mock_video_path: Path, mock_audio_path: Path, tmp_path: Path) -> None:
    """Test merge_audio handles ffmpeg failure."""
    mock_run.side_effect = subprocess.CalledProcessError(1, "ffmpeg", stderr="error")
    output_path = tmp_path / "output.mp4"
    
    with pytest.raises(AudioProcessingError, match="ffmpeg merge failed"):
        manager.merge_audio(mock_video_path, mock_audio_path, output_path)


@patch("subprocess.run")
def test_merge_audio_timeout(mock_run: MagicMock, manager: AudioManager, mock_video_path: Path, mock_audio_path: Path, tmp_path: Path) -> None:
    """Test merge_audio handles timeout correctly."""
    mock_run.side_effect = subprocess.TimeoutExpired("ffmpeg", 300)
    output_path = tmp_path / "output.mp4"
    
    with pytest.raises(AudioProcessingError, match="ffmpeg merge timed out"):
        manager.merge_audio(mock_video_path, mock_audio_path, output_path)


@patch("subprocess.run")
def test_merge_audio_missing_output(mock_run: MagicMock, manager: AudioManager, mock_video_path: Path, mock_audio_path: Path, tmp_path: Path) -> None:
    """Test merge_audio raises error if ffmpeg succeeds but output is missing."""
    mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")
    output_path = tmp_path / "output.mp4"
    
    with pytest.raises(AudioProcessingError, match="output file not found"):
        manager.merge_audio(mock_video_path, mock_audio_path, output_path)


def test_has_audio_missing_file(manager: AudioManager, tmp_path: Path) -> None:
    """Test has_audio handles missing file."""
    with pytest.raises(FileNotFoundError, match="Video file not found"):
        manager.has_audio(tmp_path / "missing.mp4")


def test_merge_audio_missing_file(manager: AudioManager, mock_video_path: Path, mock_audio_path: Path, tmp_path: Path) -> None:
    """Test merge_audio handles missing files."""
    missing_path = tmp_path / "missing.mp4"
    output_path = tmp_path / "output.mp4"
    
    with pytest.raises(FileNotFoundError, match="Video file not found"):
        manager.merge_audio(missing_path, mock_audio_path, output_path)
        
    with pytest.raises(FileNotFoundError, match="Audio file not found"):
        manager.merge_audio(mock_video_path, missing_path, output_path)


def test_cleanup_removes_files(manager: AudioManager, tmp_path: Path) -> None:
    """Test cleanup removes tracked files."""
    dummy_file = tmp_path / "temp.m4a"
    dummy_file.write_text("data")
    
    manager._tracked_files.append(dummy_file)
    manager.cleanup()
    
    assert not dummy_file.exists()
    assert len(manager._tracked_files) == 0


def test_context_manager_cleanup(tmp_path: Path) -> None:
    """Test context manager cleans up files on exit."""
    dummy_file = tmp_path / "temp.m4a"
    dummy_file.write_text("data")
    
    with patch("shutil.which", return_value="dummy/path"):
        with AudioManager() as manager:
            manager._tracked_files.append(dummy_file)
        
    assert not dummy_file.exists()


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")
def test_integration_no_audio(tmp_path: Path) -> None:
    """Integration test: extract_audio on a video with no audio."""
    import cv2
    import numpy as np
    
    # Create a dummy video with no audio
    source_path = tmp_path / "source.mp4"
    fps = 24.0
    resolution = (320, 240)
    frame_count = 5
    
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    dummy_writer = cv2.VideoWriter(str(source_path), fourcc, fps, resolution)
    for _ in range(frame_count):
        frame = np.zeros((240, 320, 3), dtype=np.uint8)
        dummy_writer.write(frame)
    dummy_writer.release()
    
    with AudioManager() as manager:
        assert manager.has_audio(source_path) is False
        assert manager.extract_audio(source_path) is None
