# Theia Video Enhancer - Portfolio Summary

## Project Overview
Theia is a modern, AI-powered video enhancement desktop application built with Python and PyQt6. It leverages deep learning models via ONNX Runtime to perform advanced video processing tasks such as frame interpolation, wrapped in a sleek, responsive, and hardware-accelerated environment.

## What Has Been Accomplished So Far

### 1. Application Architecture & UI
*   **Modern Desktop Interface:** Designed and developed a responsive desktop application using **PyQt6** featuring a custom, scalable dark theme with premium typography.
*   **Dynamic UI Scaling:** Implemented an intelligent scaling system that dynamically adjusts all UI metrics and stylesheets based on window size, ensuring a consistent experience across different resolutions.
*   **Modular Screen Design:** Architected the UI using a `QStackedWidget` to seamlessly manage distinct views including Home, Processing, Comparison, and Settings screens.

### 2. Core Video Processing Pipeline
*   **End-to-End Orchestration:** Built a robust `ProcessingPipeline` that handles frame extraction, AI inference, and video reconstruction seamlessly.
*   **Hardware-Accelerated Inference:** Integrated **ONNX Runtime** (`onnxruntime-directml`) to execute machine learning models efficiently using DirectML for hardware acceleration.
*   **Audio Management:** Developed an `AudioManager` to extract audio from the source video and multiplex it back into the enhanced video output without quality loss.

### 3. Advanced AI & Computer Vision Features
*   **Scene Cut Detection:** Implemented an intelligent scene detector that calculates frame differences and automatically skips AI interpolation across hard cuts, preventing visual artifacting ("morphing" between entirely different scenes).
*   **Static Overlay Restoration:** Engineered a system to detect and protect static UI elements (like subtitles, watermarks, or game HUDs) by generating pixel masks and restoring them post-inference, ensuring text and static elements remain crisp and unwarped.
*   **Diagnostic & Debug Systems:** Built a `DebugCollector` to capture intermediate frame states, scene scores, and masks for granular testing and performance tuning.

### 4. Deployment & Packaging
*   **Standalone Windows Executable:** Successfully bundled the entire Python environment, PyQt6 UI, and ONNX Runtime into a single, highly-portable `Theia.exe` using **PyInstaller**.
*   **Custom Branding:** Integrated custom high-resolution icons (`.ico` and `.jpg`) for both the application window and the Windows Explorer executable file.
*   **Professional Windows Installer:** Engineered a complete Windows setup script using **Inno Setup**, creating a compressed, single-file installer (`Theia_Installer.exe`) that automatically deploys the app, extracts bundled AI models, and creates Start Menu and Desktop shortcuts for end-users.
