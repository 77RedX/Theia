# Theia Video Enhancer

Theia Video Enhancer is an AI-powered desktop application that performs local video frame interpolation to increase frame rates (e.g., 30 FPS → 60 FPS) while preserving visual quality.

## Features
- End-to-end video processing pipeline
- Frame extraction and reconstruction
- Abstract AI Inference Engine integration
- ONNX Runtime backend for accelerated processing
- Fallback-safe audio extraction and merging

## Getting Started

### Prerequisites
- Python 3.10+
- FFmpeg (Must be installed and available in system PATH for audio operations)

### Installation
1. Clone the repository
2. Install standard dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Install inference-specific dependencies:
   ```bash
   pip install -r requirements-inference.txt
   ```

### Running Tests
To verify your environment is correctly set up, run the test suite:
```bash
pytest tests/ -v
```

## Architecture
This project is built around a frozen frame-pair processing architecture, cleanly decoupling the video I/O from the deep learning models. 
For a detailed view of the technical specifications, refer to `docs/PROJECT_OVERVIEW.md` and `docs/IMPLEMENTATION_JOURNAL.md`.

## License
Refer to `LICENSE` for distribution rights.
