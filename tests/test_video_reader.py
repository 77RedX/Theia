"""Tests for the Phase 1 video metadata reader."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from video_engine import VideoReader


@pytest.fixture
def sample_video_path() -> Path:
    """Return the shared Phase 1 sample video path."""

    return Path(__file__).resolve().parents[1] / "assets" / "sample_videos" / "sample_video.avi"


@pytest.fixture
def loaded_reader(sample_video_path: Path) -> VideoReader:
    """Return a loaded reader and ensure its resources are released."""

    reader = VideoReader(sample_video_path)
    if not reader.load_video():
        pytest.fail(f"Failed to load sample video: {sample_video_path}")

    try:
        yield reader
    finally:
        reader.close()


def test_sample_video_exists(sample_video_path: Path) -> None:
    """The repository should include a real sample video for Phase 1 tests."""

    assert sample_video_path.exists()


def test_video_reader_loads_sample_video(sample_video_path: Path) -> None:
    """The reader should open the sample video successfully."""

    reader = VideoReader(sample_video_path)

    try:
        assert reader.load_video() is True
        assert reader.is_loaded is True
    finally:
        reader.close()


def test_video_reader_rejects_missing_file() -> None:
    """The reader should fail fast when the input file does not exist."""

    reader = VideoReader(Path(__file__).resolve().parent / "assets" / "sample_videos" / "missing_video.avi")

    with pytest.raises(FileNotFoundError, match="Video file not found"):
        reader.load_video()


def test_video_reader_reports_not_loaded_before_load(sample_video_path: Path) -> None:
    """Metadata access should fail before the video has been loaded."""

    reader = VideoReader(sample_video_path)

    with pytest.raises(RuntimeError, match="Video is not loaded"):
        reader.get_fps()

    with pytest.raises(RuntimeError, match="Video is not loaded"):
        reader.get_resolution()

    with pytest.raises(RuntimeError, match="Video is not loaded"):
        reader.get_frame_count()


def test_video_reader_returns_positive_fps(loaded_reader: VideoReader) -> None:
    """The reader should report a positive FPS value."""

    assert loaded_reader.get_fps() > 0


def test_video_reader_returns_positive_resolution(loaded_reader: VideoReader) -> None:
    """The reader should report a valid frame size."""

    width, height = loaded_reader.get_resolution()

    assert width > 0
    assert height > 0


def test_video_reader_returns_positive_frame_count(loaded_reader: VideoReader) -> None:
    """The reader should report a positive frame count."""

    assert loaded_reader.get_frame_count() > 0