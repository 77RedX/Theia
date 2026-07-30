# Engineering Decisions

## Python Version

Python 3.12.4

Reason:

Maximum compatibility with OpenCV, ONNX Runtime and PyTorch.

---

## Branch Strategy

Main branch:

main

Feature branch:

feature/video-engine

No direct commits to main.

---

## Testing Framework

pytest

---

## Logging Framework

Python logging module

---

## Initial Dependencies

* opencv-python
* pytest

Future Dependencies

* numpy
* onnxruntime
* torch
* ffmpeg-python (optional)

---

## Current Architecture

Phase 1

VideoReader

Only metadata extraction.

No frame extraction yet.

No AI integration yet.
