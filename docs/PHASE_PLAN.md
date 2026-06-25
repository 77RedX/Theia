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

- [x] Frames extracted correctly
- [x] Frame count matches source
- [x] Tests passing

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

- [x] Output video generated
- [x] FPS preserved
- [x] Resolution preserved

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

- [x] Audio extracted
- [x] Audio merged
- [x] Output video playable

---

## Phase 5 — Processing Pipeline

Goal:

Frame processing workflow

Deliverables:

- ProcessingPipeline
- Pair-based orchestration
- _process_pair()
- Pass-through processing
- Last frame handling
- Audio preservation integration
- Pipeline tests

Completion Criteria:

- [x] ProcessingPipeline implemented
- [x] Pair iteration functional
- [x] Last frame preserved
- [x] Audio preserved
- [x] End-to-end test passes

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
