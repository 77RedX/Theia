# Theia Video Enhancer

## Project Description

Theia Video Enhancer is a desktop application that performs AI-powered video frame interpolation to increase video frame rates while preserving visual quality.

Example:

24 FPS → 48 FPS

30 FPS → 60 FPS

60 FPS → 120 FPS

The application operates locally on user hardware and does not require cloud processing.

---

## Core Features

* Video input support
* Frame extraction
* AI frame interpolation
* FPS enhancement
* Before/after comparison
* Export enhanced videos
* Local execution

---

## Team Responsibilities

### Person 1

Model Research & Training

### Person 2

Dataset Engineering & Evaluation

### Person 3

Video Processing Engine

### Person 4

Desktop Application

### Person 5

Deployment & QA

---

## Person 3 Scope

Responsible for:

* Video loading
* Metadata extraction
* Frame extraction
* Scene detection (infrastructure)
* Frame processing pipeline
* Model inference integration
* Overlay Restoration
* Debug & Diagnostics Framework
* Audio handling
* Export pipeline

Not responsible for:

* Model training
* Dataset preparation
* UI implementation
* Installer creation

---

## Deployment Organization

Deep learning models are distributed in isolated deployment packages within the `models/` directory (e.g., `models/basic/`). 

Each model package must contain:
1. `model.onnx` (The static compiled computation graph)
2. `model_info.json` (A strict configuration contract for dimensions, color spaces, and preprocessing rules)
3. `README.md` (Deployment-focused documentation detailing input/output specs and engine responsibilities)

This layout natively supports future scaling to multiple model tiers (e.g. Plus, Pro) without modifying the core pipeline code.

### Model Discovery
New models can be easily added to the application simply by creating a new directory under `models/` (e.g. `models/<model_name>/`) containing:
- `model.onnx`
- `model_info.json`
- `README.md`

The newly implemented `ModelRegistry` automatically discovers and validates these deployments, making them instantly available to the `ProcessingPipeline` without requiring any internal code changes.

---

## Development Philosophy

1. Build incrementally.
2. Test every feature before adding new features.
3. Separate pipeline debugging from model debugging.
4. Prefer maintainability over premature optimization.
5. Every major feature must have tests.
6. Architecture decisions are frozen once validated.
7. Prefer future compatibility over premature abstraction.
8. Frame pairs are the canonical processing unit.

## Architecture Decisions

- **Decision 7**: TheiaConfig is the single source of runtime configuration. Scattered parameters have been aggregated into an immutable, frozen dataclass ensuring a safe boundary.

---

## Public API

The entire video engine is exposed via a single canonical API endpoint. Downstream clients (GUI, CLI, SDK) should **only** rely on this endpoint, rather than instantiating internal pipeline components directly.

Example usage:

```python
from video_engine import enhance_video, TheiaConfig

config = TheiaConfig(
    preset="fast"
)

enhance_video(
    "input.mp4",
    "output.mp4",
    config,
)
```