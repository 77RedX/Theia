"""
Theia Video Enhancer — Processing Screen
Shows real-time progress, ETA, and logs while video is enhanced.
Uses a QThread worker so the UI never freezes.
When Person 3's engine is ready, swap the simulate_processing()
method body for the real predict_video() call.
"""

import os
import time
import random
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QProgressBar, QTextEdit, QMessageBox, QSizePolicy
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QTime
from PyQt6.QtGui import QFont

from theme import COLORS
from widgets import TitleLabel, CaptionLabel, Card, AppHeader, make_separator


# ── Background worker ─────────────────────────────────────────────────────
class ProcessingWorker(QThread):
    """
    Runs in a background thread so the UI stays responsive.

    ── INTEGRATION POINT (Person 3) ──────────────────────────────────────
    Replace `simulate_processing()` with a call to:

        from engine import predict_video
        predict_video(
            input_path  = self.input_path,
            output_path = self.output_path,
            fps         = self.fps_label,
            quality     = self.quality,
            progress_cb = self.report_progress,   # call with (pct: int, msg: str)
        )
    ──────────────────────────────────────────────────────────────────────
    """
    progress    = pyqtSignal(int, str)   # (percent, log_message)
    finished    = pyqtSignal(str)        # output_path
    error       = pyqtSignal(str)        # error_message

    def __init__(self, input_path, output_path, quality, fps_label):
        super().__init__()
        self.input_path  = input_path
        self.output_path = output_path
        self.quality     = quality
        self.fps_label   = fps_label
        self._cancelled  = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        try:
            self.simulate_processing()
        except Exception as e:
            self.error.emit(str(e))

    # ── Simulation (remove when real engine is integrated) ───────────────
    def simulate_processing(self):
        """Fake processing pipeline that mimics what the real engine will do."""
        stages = [
            (5,  "Initialising model..."),
            (10, "Loading model weights..."),
            (15, "Reading video metadata..."),
            (20, "Extracting audio stream..."),
            (25, "Splitting video into frames..."),
        ]

        # Initial stages
        for pct, msg in stages:
            if self._cancelled:
                return
            self.progress.emit(pct, msg)
            time.sleep(0.4)

        # Simulate per-frame processing
        src_fps = int(self.fps_label.split("→")[0].strip().replace(" fps",""))
        # Fake total frames based on "5 second clip at source fps"
        fake_total = src_fps * 5
        speed_map  = {"Fast": 0.03, "Balanced": 0.07, "High Quality": 0.14}
        delay      = speed_map.get(self.quality, 0.06)

        log_intervals = [
            "Generating interpolated frame {f}...",
            "Computing optical flow for frame {f}...",
            "Refining motion vectors at frame {f}...",
            "Applying temporal smoothing at frame {f}...",
        ]

        for i in range(1, fake_total + 1):
            if self._cancelled:
                self.progress.emit(0, "Processing cancelled.")
                return
            pct = 25 + int((i / fake_total) * 65)
            msg = random.choice(log_intervals).format(f=i)
            self.progress.emit(pct, msg)
            time.sleep(delay)

        # Final stages
        final_stages = [
            (92, "Merging frames into video..."),
            (95, "Re-attaching audio track..."),
            (98, "Encoding final output..."),
            (100,"Enhancement complete!"),
        ]
        for pct, msg in final_stages:
            if self._cancelled:
                return
            self.progress.emit(pct, msg)
            time.sleep(0.5)

        self.finished.emit(self.output_path)

    # ── Real engine hook (uncomment when Person 3 delivers) ──────────────
    # def real_processing(self):
    #     from engine import predict_video
    #     def report_progress(pct, msg):
    #         if self._cancelled:
    #             raise InterruptedError("Cancelled by user")
    #         self.progress.emit(pct, msg)
    #
    #     predict_video(
    #         input_path  = self.input_path,
    #         output_path = self.output_path,
    #         fps         = self.fps_label,
    #         quality     = self.quality,
    #         progress_cb = report_progress,
    #     )
    #     self.finished.emit(self.output_path)


# ── Processing Screen ─────────────────────────────────────────────────────
class ProcessingScreen(QWidget):
    """
    Screen 3: Processing
    Emits `finished` with output path when done.
    Emits `cancelled` to abort and return to settings.
    """
    finished  = pyqtSignal(str)   # output_path
    cancelled = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._worker    = None
        self._start_time = None
        self._timer     = QTimer(self)
        self._timer.timeout.connect(self._update_eta)
        self._build_ui()

    # ── UI construction ────────────────────────────────────────────────────
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.header = AppHeader("Processing")
        root.addWidget(self.header)

        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(60, 44, 60, 44)
        body_layout.setSpacing(20)

        # ── Title ──
        title = TitleLabel("Enhancing Your Video", size=26)
        sub   = CaptionLabel("Please wait while Theia processes your footage. Do not close the application.", 13)
        body_layout.addWidget(title)
        body_layout.addSpacing(4)
        body_layout.addWidget(sub)
        body_layout.addWidget(make_separator())
        body_layout.addSpacing(8)

        # ── Animated spinner label ──
        self.status_lbl = QLabel("Initialising...")
        self.status_lbl.setFont(QFont("Segoe UI", 15, QFont.Weight.DemiBold))
        self.status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_lbl.setStyleSheet(f"color: {COLORS['accent_light']}; background: transparent;")
        body_layout.addWidget(self.status_lbl)

        # ── Progress bar ──
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(14)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        body_layout.addWidget(self.progress_bar)

        # ── Percent + ETA row ──
        pct_row = QHBoxLayout()
        self.pct_lbl = QLabel("0%")
        self.pct_lbl.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        self.pct_lbl.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")

        self.eta_lbl = QLabel("Calculating ETA...")
        self.eta_lbl.setFont(QFont("Segoe UI", 12))
        self.eta_lbl.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent;")

        pct_row.addWidget(self.pct_lbl)
        pct_row.addStretch()
        pct_row.addWidget(self.eta_lbl)
        body_layout.addLayout(pct_row)

        body_layout.addSpacing(8)

        # ── Stats row ──
        stats_card = Card()
        stats_layout = QHBoxLayout(stats_card)
        stats_layout.setContentsMargins(24, 16, 24, 16)

        self.quality_stat  = _Stat("Quality",  "—")
        self.fps_stat      = _Stat("Target FPS","—")
        self.elapsed_stat  = _Stat("Elapsed",  "0s")

        for s in [self.quality_stat, self.fps_stat, self.elapsed_stat]:
            stats_layout.addWidget(s)
            if s is not self.elapsed_stat:
                div = QLabel("|")
                div.setStyleSheet(f"color: {COLORS['bg_border']}; background:transparent; font-size:20px;")
                div.setAlignment(Qt.AlignmentFlag.AlignCenter)
                stats_layout.addWidget(div)

        body_layout.addWidget(stats_card)
        body_layout.addSpacing(8)

        # ── Logs ──
        log_header = QLabel("PROCESSING LOG")
        log_header.setStyleSheet(f"""
            color: {COLORS['text_secondary']};
            font-size: 10px;
            font-weight: 800;
            letter-spacing: 2px;
            background: transparent;
        """)
        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setFixedHeight(160)

        body_layout.addWidget(log_header)
        body_layout.addWidget(self.log_box)

        body_layout.addStretch()

        # ── Cancel button ──
        self.cancel_btn = QPushButton("✕  Cancel Processing")
        self.cancel_btn.setFixedHeight(44)
        self.cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {COLORS['error']};
                border: 1.5px solid {COLORS['error']};
                border-radius: 8px;
                font-size: 14px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {COLORS['error']}22;
            }}
        """)
        self.cancel_btn.clicked.connect(self._on_cancel)
        body_layout.addWidget(self.cancel_btn)

        root.addWidget(body)

    # ── Public: start processing ──────────────────────────────────────────
    def start_processing(self, input_path, output_path, quality, fps_label):
        """Called by main window to kick off processing."""
        self._start_time = time.time()
        self._last_pct   = 0

        # Update stat labels
        self.quality_stat.set_value(quality)
        self.fps_stat.set_value(fps_label)
        self.pct_lbl.setText("0%")
        self.eta_lbl.setText("Calculating ETA...")
        self.progress_bar.setValue(0)
        self.log_box.clear()
        self.status_lbl.setText("Starting...")
        self.cancel_btn.setEnabled(True)

        self._append_log(f"Input:   {os.path.basename(input_path)}")
        self._append_log(f"Output:  {os.path.basename(output_path)}")
        self._append_log(f"Quality: {quality}   FPS: {fps_label}")
        self._append_log("─" * 44)

        # Start ETA timer
        self._timer.start(1000)

        # Launch worker thread
        self._worker = ProcessingWorker(input_path, output_path, quality, fps_label)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    # ── Slots ─────────────────────────────────────────────────────────────
    def _on_progress(self, pct, msg):
        self._last_pct = pct
        self.progress_bar.setValue(pct)
        self.pct_lbl.setText(f"{pct}%")
        self.status_lbl.setText(msg)
        self._append_log(msg)

    def _update_eta(self):
        if self._start_time is None:
            return
        elapsed = int(time.time() - self._start_time)
        self.elapsed_stat.set_value(self._fmt_secs(elapsed))

        pct = self._last_pct
        if pct > 5:
            total_est = elapsed / (pct / 100)
            remaining = max(0, int(total_est - elapsed))
            self.eta_lbl.setText(f"ETA: {self._fmt_secs(remaining)}")

    def _on_cancel(self):
        reply = QMessageBox.question(
            self, "Cancel Processing",
            "Are you sure you want to cancel?\nAll progress will be lost.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            if self._worker:
                self._worker.cancel()
                self._worker.wait()
            self._timer.stop()
            self.cancelled.emit()

    def _on_finished(self, output_path):
        self._timer.stop()
        self.cancel_btn.setEnabled(False)
        self.status_lbl.setText("✓ Enhancement complete!")
        self.status_lbl.setStyleSheet(f"color: {COLORS['success']}; background: transparent; font-size: 15px; font-weight: 700;")
        self._append_log("─" * 44)
        self._append_log("✓ Processing complete.")
        self.finished.emit(output_path)

    def _on_error(self, msg):
        self._timer.stop()
        self.cancel_btn.setEnabled(False)
        QMessageBox.critical(
            self, "Processing Failed",
            f"An error occurred during processing:\n\n{msg}\n\n"
            "Please check the log for details."
        )
        self._append_log(f"[ERROR] {msg}")
        self.cancelled.emit()

    # ── Helpers ───────────────────────────────────────────────────────────
    def _append_log(self, text):
        ts = QTime.currentTime().toString("hh:mm:ss")
        self.log_box.append(f"[{ts}]  {text}")
        # Auto-scroll to bottom
        sb = self.log_box.verticalScrollBar()
        sb.setValue(sb.maximum())

    @staticmethod
    def _fmt_secs(seconds):
        if seconds < 60:
            return f"{seconds}s"
        m, s = divmod(seconds, 60)
        return f"{m}m {s}s"


# ── Internal stat widget ───────────────────────────────────────────────────
class _Stat(QWidget):
    def __init__(self, label, value):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(3)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._val_lbl = QLabel(value)
        self._val_lbl.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        self._val_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._val_lbl.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")

        lbl = QLabel(label.upper())
        lbl.setFont(QFont("Segoe UI", 9))
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent; letter-spacing: 1.5px;")

        layout.addWidget(self._val_lbl)
        layout.addWidget(lbl)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

    def set_value(self, v):
        self._val_lbl.setText(v)
