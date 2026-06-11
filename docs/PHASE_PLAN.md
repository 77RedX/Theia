# Theia Video Engine Roadmap

## Phase 1 — Video Metadata Extraction

Goal:

Input video

↓

Load successfully

↓

Read metadata

Deliverables:

- Logger setup
- VideoReader class
- Load video
- FPS extraction
- Resolution extraction
- Frame count extraction
- Unit tests

Completion Criteria:

- [x] Video loads successfully
- [x] FPS retrieved
- [x] Resolution retrieved
- [x] Frame count retrieved
- [x] Tests passing

---

## Phase 2 — Frame Extraction

Goal:

Video

↓

Frames

Deliverables:

- Frame extraction
- Output frame storage
- Frame iterator

Completion Criteria:

- [ ] Frames extracted correctly
- [ ] Frame count matches source
- [ ] Tests passing

---

## Phase 3 — Video Reconstruction

Goal:

Frames

↓

Video

Deliverables:

- VideoWriter
- Frame writing
- Output video generation

Completion Criteria:

- [ ] Output video generated
- [ ] FPS preserved
- [ ] Resolution preserved

---

## Phase 4 — FFmpeg Integration

Goal:

Video

↓

Audio extraction

↓

Video reconstruction

↓

Audio merge

Deliverables:

- Audio extraction
- Audio merge
- FFmpeg utilities

Completion Criteria:

- [ ] Audio extracted
- [ ] Audio merged
- [ ] Output video playable

---

## Phase 5 — Processing Pipeline

Goal:

Frame processing workflow

Deliverables:

- Frame pipeline
- Frame streaming
- Temporary storage management

Completion Criteria:

- [ ] Pipeline functional
- [ ] Handles videos correctly

---

## Phase 6 — ONNX Integration

Goal:

Model inference

Deliverables:

- ONNX Runtime integration
- Inference wrapper

Completion Criteria:

- [ ] ONNX model loads
- [ ] Frame inference works

---

## Phase 7 — Full Video Inference

Goal:

Video enhancement

Deliverables:

- Predict video function
- End-to-end processing

Completion Criteria:

- [ ] FPS increased
- [ ] Output video generated

---

## Phase 8 — Optimization

Deliverables:

- Streaming architecture
- Reduced memory usage
- Performance improvements

Completion Criteria:

- [ ] Long videos supported
- [ ] Stable memory usage

---

## Phase 9 — Public API

Deliverables:

predict_video()

Completion Criteria:

- [ ] UI team can call API directly

---

## Phase 10 — Final Validation

Deliverables:

- Benchmark report
- Compatibility report

Completion Criteria:

- [ ] 480p tested
- [ ] 720p tested
- [ ] 1080p tested
- [ ] Short videos tested
- [ ] Long videos tested
