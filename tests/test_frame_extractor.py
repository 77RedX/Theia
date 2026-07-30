"""Tests for Phase 2 frame extraction behavior."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from video_engine import FrameExtractor, VideoReader


@pytest.fixture
def sample_video_path() -> Path:
    """Return the shared sample video used by the video engine tests."""

    return Path(__file__).resolve().parents[1] / "assets" / "sample_videos" / "sample_video.avi"


@pytest.fixture
def loaded_reader(sample_video_path: Path) -> VideoReader:
    """Return a loaded video reader and close it after the test."""

    reader = VideoReader(sample_video_path)
    assert reader.load_video() is True

    try:
        yield reader
    finally:
        reader.close()


@pytest.fixture
def unloaded_reader(sample_video_path: Path) -> VideoReader:
    """Return a reader that has not been loaded."""

    return VideoReader(sample_video_path)


@pytest.fixture
def extractor(loaded_reader: VideoReader) -> FrameExtractor:
    """Return a frame extractor backed by a loaded reader."""

    return FrameExtractor(loaded_reader)


def test_loaded_video_reader_is_accepted(loaded_reader: VideoReader) -> None:
    """A loaded reader should be accepted by the frame extractor."""

    extractor = FrameExtractor(loaded_reader)

    assert isinstance(extractor, FrameExtractor)


def test_unloaded_video_reader_is_rejected(unloaded_reader: VideoReader) -> None:
    """An unloaded reader should be rejected immediately."""

    with pytest.raises(RuntimeError, match="Video is not loaded"):
        FrameExtractor(unloaded_reader)


def test_frame_generator_yields_frames(
    extractor: FrameExtractor,
    loaded_reader: VideoReader,
) -> None:
    """The frame generator should yield numpy frames."""

    frame_count = sum(1 for _ in extractor.frame_generator())

    assert frame_count == loaded_reader.get_frame_count()


def test_frame_pair_generator_yields_pairs(extractor: FrameExtractor) -> None:
    """The frame pair generator should yield adjacent frame pairs."""

    first_pair = next(extractor.frame_pair_generator())

    assert isinstance(first_pair, tuple)
    assert len(first_pair) == 2
    assert isinstance(first_pair[0], np.ndarray)
    assert isinstance(first_pair[1], np.ndarray)


def test_generated_frame_count_matches_metadata(loaded_reader: VideoReader) -> None:
    """The number of generated frames should match the video metadata."""

    extractor = FrameExtractor(loaded_reader)
    frame_count = sum(1 for _ in extractor.frame_generator())

    assert frame_count == loaded_reader.get_frame_count()


def test_generators_restart_from_beginning_correctly(loaded_reader: VideoReader) -> None:
    """Generators should restart from the first frame on each new iteration."""

    extractor = FrameExtractor(loaded_reader)

    frame_count_1 = sum(1 for _ in extractor.frame_generator())
    frame_count_2 = sum(1 for _ in extractor.frame_generator())

    assert frame_count_1 == frame_count_2

    pair_count_1 = sum(1 for _ in extractor.frame_pair_generator())
    pair_count_2 = sum(1 for _ in extractor.frame_pair_generator())

    assert pair_count_1 == pair_count_2