# ◈ Theia Video Enhancer — Desktop Application

> **Person 4 — Desktop Application Lead**
> Built with PyQt6. Fully functional UI with simulation mode.
> Plug in Person 3's engine when ready — zero GUI changes needed.

---

## Project Structure

```
Theia-Video-Enhancer/
├── main.py                     ← Entry point. Run this.
├── theme.py                    ← All colours, fonts, stylesheet
├── widgets.py                  ← Shared reusable UI components
├── engine.py                   ← Integration stub for Person 3
├── requirements.txt
│
├── screens/
│   ├── __init__.py
│   ├── home_screen.py          ← Screen 1: Upload video
│   ├── settings_screen.py      ← Screen 2: Quality + FPS settings
│   ├── processing_screen.py    ← Screen 3: Progress bar, logs, ETA
│   └── results_screen.py       ← Screen 4: Stats, compare, export
│
├── outputs/                    ← Processed videos land here
├── videos/                     ← (optional) source videos
└── models/                     ← (future) model weights go here
```

---

## Quick Start

### 1. Install Python 3.12+
https://www.python.org/downloads/

✅ Check "Add Python to PATH" during install.

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the app
```bash
python main.py
```

---

## Navigation Flow

```
HomeScreen
  Upload video (browse or drag-and-drop)
  ↓ Continue
SettingsScreen
  Choose quality: Fast / Balanced / High Quality
  Choose FPS: 24→48 / 30→60 / 60→120
  ↓ Start Enhancement
ProcessingScreen
  Real-time progress bar
  ETA countdown
  Live processing log
  Cancel button
  ↓ (auto-advance on completion)
ResultsScreen
  Before / After panels
  Stats: original FPS, enhanced FPS, quality, file size
  Export button (save anywhere)
  "Enhance Another Video" button
```

---

## Screens

### Home Screen
- Drag-and-drop zone for video files
- Browse button with file dialog
- Validates format (MP4, MKV, AVI, MOV, WEBM, FLV)
- Shows file name, size, and ✓ Ready badge once selected
- Error popup for unsupported formats

### Settings Screen
- Three quality preset cards (Fast ⚡ / Balanced ⚖ / High Quality ✦)
- Three FPS option cards with animated selection state
- Live settings summary before starting
- Back button returns to Home

### Processing Screen
- Animated progress bar with gradient fill
- Real-time percentage + ETA
- Elapsed timer
- Scrolling log window (timestamped)
- Cancel button with confirmation dialog
- Graceful close protection (warns if processing is active)
- Background QThread — UI never freezes

### Results Screen
- Success banner
- Stats grid: original FPS / enhanced FPS / quality / file size
- Before/After file panels
- Export dialog (save MP4 or MKV anywhere)
- "Enhance Another Video" resets to Home

---

## Error Handling

| Situation               | UI Response                              |
|-------------------------|------------------------------------------|
| Unsupported file format | QMessageBox.warning with format list     |
| File not found at start | QMessageBox.critical                     |
| Processing error        | QMessageBox.critical with log details    |
| User cancels            | Confirmation dialog, returns to Settings |
| Close during processing | Confirmation dialog, waits for thread    |
| Export path not found   | QMessageBox.critical                     |
| Low memory (future)     | QMessageBox.warning                      |

---

## Integration with Person 3 (Engine Lead)

When Person 3's `predict_video()` is ready:

1. Open `screens/processing_screen.py`
2. Find the `ProcessingWorker.run()` method
3. Replace `self.simulate_processing()` with `self.real_processing()`
4. Uncomment the `real_processing()` method (lines marked with `#`)
5. Update `engine.py` with the real implementation

**The GUI calls Person 3's function like this:**
```python
predict_video(
    input_path  = "/path/to/input.mp4",
    output_path = "/path/to/output.mp4",
    fps         = "30 → 60 fps",
    quality     = "Balanced",
    progress_cb = lambda pct, msg: ...,   # updates the progress bar
)
```

**Person 3 must:**
- Write the output file to `output_path`
- Call `progress_cb(pct, msg)` regularly (every frame ideally)
- Raise `InterruptedError` if `_cancelled` is True
- Raise `MemoryError` for RAM issues
- Raise `RuntimeError` for model failures

---

## Design System

**Palette:**
| Name           | Hex       | Use                        |
|----------------|-----------|----------------------------|
| bg_deep        | `#0A0A0F` | App background             |
| bg_surface     | `#111118` | Cards                      |
| bg_raised      | `#1A1A25` | Elevated elements          |
| accent         | `#7C3AED` | Primary actions (violet)   |
| accent_light   | `#9D5CF0` | Hover states               |
| text_primary   | `#F0EFF8` | Main text                  |
| text_secondary | `#8B8BA0` | Labels, captions           |
| success        | `#22C55E` | Completion, check marks    |
| error          | `#EF4444` | Errors, cancel             |

**Font:** Segoe UI (Windows) / SF Pro (Mac) / Helvetica Neue (Linux)
**Mono font:** Cascadia Code / Consolas (log window)

---

## Week Plan (Person 4)

- **Week 0** ✅ Understand the build scope
- **Week 1** ✅ Environment, project structure, basic window
- **Week 2** ✅ Home screen + file validation
- **Week 3** ✅ Settings screen + navigation
- **Week 4** ✅ Processing screen + background thread
- **Week 5** ✅ Results screen + export
- **Week 6** → Meet Person 3, integrate `predict_video()`
- **Week 7** → Final polish, error edge cases, testing

---

## Author
Person 4 — Desktop Application Lead, Theia Project
