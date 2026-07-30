# Plus Model

This is the Plus Tier AI interpolation model. It provides higher quality interpolation using an advanced flow-based approach.

## Model Details
- **Architecture**: Flow-based Video Interpolation (Plus version)
- **Inputs**: 2 separate tensors `img1` and `img3`, each with shape `[batch, 3, height, width]`.
- **Output**: 1 tensor `output` with shape `[batch, 3, height, width]`.
- **Color Space**: RGB

## Usage Requirements
Requires the inference engine to feed inputs as two separate tensors rather than a single concatenated one.
