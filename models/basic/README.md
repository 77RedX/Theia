# BasicFlowInterp

## Purpose
This model provides baseline frame interpolation for the Theia Video Enhancer engine. It predicts a single intermediate frame ("middle_frame") between two consecutive input frames.

## Backend
- **Framework**: ONNX Runtime
- **Opset Version**: 17

## Input Specification
- **Name**: `frames`
- **Shape**: `[batch_size, 6, 256, 448]`
- **Format**: NCHW
- **Data Type**: `float32` (normalized to `[0.0, 1.0]`)
- **Color Space**: RGB

## Output Specification
- **Name**: `middle_frame`
- **Shape**: `[batch_size, 3, 256, 448]`
- **Format**: NCHW
- **Data Type**: `float32` (normalized to `[0.0, 1.0]`)
- **Color Space**: RGB

## Fixed Input Resolution
This ONNX graph enforces a strict **fixed input resolution** of `256` (height) by `448` (width). Providing tensors of any other spatial dimensions will result in a shape mismatch error during runtime execution.

## Responsibilities of the Inference Engine
Because the core `ProcessingPipeline` operates on raw, native-resolution OpenCV frames, the inference engine is solely responsible for bridging the gap between those frames and the strict constraints of this model. 

Specifically, the inference engine performs:
- **Resizing**: Downscaling incoming native frames exactly to `448x256`.
- **BGR→RGB Conversion**: Shifting OpenCV's default color channels to the RGB space expected by the model.
- **Normalization**: Converting `uint8` values to `float32` mapped between `[0.0, 1.0]`.
- **Inference**: Passing the formatted tensor into the ONNX session.
- **Denormalization**: Mapping `[0.0, 1.0]` floats back into clamped `[0, 255] uint8` values.
- **RGB→BGR Conversion**: Reverting channels to OpenCV's standard.
- **Resize back to original resolution**: Upscaling the `256x448` output frame back to the source video's original dimensions so it integrates seamlessly into the pipeline.
