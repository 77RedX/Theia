import time
import torch
import torch.nn as nn
from models.modules.encoder import ResNetSEEncoder
from models.modules.flow import MultiScaleFlow
from models.modules.alignment import FlowGuidedAlignment
from models.modules.transformer import DualScaleTransformer
from models.modules.decoder import HierarchicalDecoder

from models.pro_model import ProModel
from utils.loss_pro import ProLoss


# ============================================================
# Configuration
# ============================================================

BATCH_SIZE = 8
HEIGHT = 256
WIDTH = 256
NUM_WARMUP = 3
NUM_PROFILE_ITERS = 10
LEARNING_RATE = 1e-4


# ============================================================
# Environment Utilities
# ============================================================

def print_environment():
    print("=" * 60)
    print("THEIA PROFILER")
    print("=" * 60)

    print(f"PyTorch Version : {torch.__version__}")
    print(f"CUDA Available  : {torch.cuda.is_available()}")

    if torch.cuda.is_available():
        print(f"CUDA Version    : {torch.version.cuda}")
        print(f"GPU             : {torch.cuda.get_device_name(0)}")
        print(
            f"GPU Capability  : {torch.cuda.get_device_properties(0).major}."
            f"{torch.cuda.get_device_properties(0).minor}"
        )

    print("=" * 60)


# ============================================================
# Model Utilities
# ============================================================

def count_parameters(model):
    total = sum(p.numel() for p in model.parameters())
    trainable = sum(
        p.numel() for p in model.parameters()
        if p.requires_grad
    )

    print("\nModel Statistics")
    print("-" * 60)
    print(f"Total Parameters      : {total:,}")
    print(f"Trainable Parameters  : {trainable:,}")
    print("-" * 60)

    return total


# ============================================================
# CUDA Timing Utility
# ============================================================

class CUDATimer:
    """
    High precision CUDA timer.
    Uses CUDA events instead of time.time().
    """

    def __init__(self):
        self.start_event = torch.cuda.Event(enable_timing=True)
        self.end_event = torch.cuda.Event(enable_timing=True)

    def start(self):
        self.start_event.record()

    def stop(self):
        self.end_event.record()
        torch.cuda.synchronize()
        return self.start_event.elapsed_time(self.end_event) / 1000.0


# ============================================================
# GPU Memory Utilities
# ============================================================

def reset_memory_stats():
    if torch.cuda.is_available():
        torch.cuda.reset_peak_memory_stats()


def memory_report():
    if not torch.cuda.is_available():
        return 0.0, 0.0, 0.0

    allocated = torch.cuda.memory_allocated() / 1024 ** 3
    reserved = torch.cuda.memory_reserved() / 1024 ** 3
    peak = torch.cuda.max_memory_allocated() / 1024 ** 3

    return allocated, reserved, peak


def print_memory():
    allocated, reserved, peak = memory_report()

    print("\nGPU Memory")
    print("-" * 60)
    print(f"Allocated : {allocated:.2f} GB")
    print(f"Reserved  : {reserved:.2f} GB")
    print(f"Peak      : {peak:.2f} GB")
    print("-" * 60)


# ============================================================
# Dummy Data
# ============================================================

def create_dummy_batch(device):
    img1 = torch.rand(
        BATCH_SIZE,
        3,
        HEIGHT,
        WIDTH,
        device=device
    )

    img2 = torch.rand(
        BATCH_SIZE,
        3,
        HEIGHT,
        WIDTH,
        device=device
    )

    img3 = torch.rand(
        BATCH_SIZE,
        3,
        HEIGHT,
        WIDTH,
        device=device
    )

    return img1, img2, img3


# ============================================================
# Warmup
# ============================================================

def warmup(model, criterion, optimizer, scaler, img1, img2, img3):
    print(f"\nRunning {NUM_WARMUP} warmup iterations...")

    model.train()

    for i in range(NUM_WARMUP):

        optimizer.zero_grad(set_to_none=True)

        with torch.amp.autocast("cuda"):

            preds = model(img1, img3)
            loss = criterion(preds, img2)

        scaler.scale(loss).backward()
        scaler.step(optimizer)
        scaler.update()

    torch.cuda.synchronize()

    reset_memory_stats()

    print("Warmup complete.\n")


# ============================================================
# Main
# ============================================================

def main():

    torch.autograd.set_detect_anomaly(False)

    device = torch.device(
        "cuda" if torch.cuda.is_available() else "cpu"
    )

    print_environment()

    model = ProModel().to(device)
    module_profiler = create_module_profiler(model)
    criterion = ProLoss().to(device)

    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=LEARNING_RATE
    )

    scaler = torch.amp.GradScaler("cuda")

    count_parameters(model)

    print("\nCreating dummy batch...")
    img1, img2, img3 = create_dummy_batch(device)

    warmup(
        model,
        criterion,
        optimizer,
        scaler,
        img1,
        img2,
        img3
    )

    print_memory()

    stats = benchmark(
        model,
        criterion,
        optimizer,
        scaler,
        module_profiler,
        img1,
        img2,
        img3,
    )

    print_stage_summary(stats)

    module_profiler.summary()

    final_report(
        stats,
        module_profiler,
    )

# ============================================================
# Module Forward Profiler
# ============================================================

class ModuleProfiler:
    """
    Profiles major model components using CUDA events.

    Modules are detected by TYPE rather than attribute name, making
    the profiler resilient to future architecture changes.

    Multiple calls to the same module type (e.g. encoder twice,
    alignment eight times) are accumulated automatically.
    """

    MODULE_TYPES = {
        "Encoder": ResNetSEEncoder,
        "Flow": MultiScaleFlow,
        "Alignment": FlowGuidedAlignment,
        "Transformer": DualScaleTransformer,
        "Decoder": HierarchicalDecoder,
    }

    def __init__(self):

        self.handles = []

        self.starts = {}

        self.total_time = {}

        self.call_count = {}

    # --------------------------------------------------------

    def reset(self):

        self.total_time.clear()
        self.call_count.clear()

    # --------------------------------------------------------

    def _pre_hook(self, name):

        def hook(module, inputs):

            event = torch.cuda.Event(enable_timing=True)

            event.record()

            self.starts[id(module)] = event

        return hook

    # --------------------------------------------------------

    def _post_hook(self, name):

        def hook(module, inputs, output):

            end = torch.cuda.Event(enable_timing=True)

            end.record()

            torch.cuda.synchronize()

            start = self.starts.pop(id(module))

            elapsed = start.elapsed_time(end) / 1000.0

            self.total_time[name] = (
                self.total_time.get(name, 0.0)
                + elapsed
            )

            self.call_count[name] = (
                self.call_count.get(name, 0)
                + 1
            )

        return hook

    # --------------------------------------------------------

    def attach(self, model):

        print("\nAttaching module profiler...\n")

        attached = 0

        for module in model.modules():

            for name, module_type in self.MODULE_TYPES.items():

                if isinstance(module, module_type):

                    pre = module.register_forward_pre_hook(
                        self._pre_hook(name)
                    )

                    post = module.register_forward_hook(
                        self._post_hook(name)
                    )

                    self.handles.extend([pre, post])

                    attached += 1

                    print(
                        f"✓ {name:<12}"
                        f"{module.__class__.__name__}"
                    )

        print(f"\nTotal instrumented modules : {attached}\n")

    # --------------------------------------------------------

    def remove(self):

        for h in self.handles:
            h.remove()

        self.handles.clear()

    # --------------------------------------------------------

    def summary(self):

        if not self.total_time:

            print("\nNo profiling data collected.\n")

            return

        total_forward = sum(self.total_time.values())

        print("\n")
        print("=" * 70)
        print("FORWARD MODULE BREAKDOWN")
        print("=" * 70)

        ranked = sorted(
            self.total_time.items(),
            key=lambda x: x[1],
            reverse=True
        )

        print(
            f"{'Module':<18}"
            f"{'Calls':>8}"
            f"{'Avg(s)':>12}"
            f"{'Total(s)':>12}"
            f"{'%':>10}"
        )

        print("-" * 70)

        for name, total in ranked:

            calls = self.call_count[name]

            avg = total / calls

            pct = total / total_forward * 100

            print(
                f"{name:<18}"
                f"{calls:>8}"
                f"{avg:>12.4f}"
                f"{total:>12.4f}"
                f"{pct:>9.2f}"
            )

        print("-" * 70)

        print(f"{'TOTAL':<18}{'':>8}{'':>12}{total_forward:>12.4f}")

        print("=" * 70)


# ============================================================
# Helper
# ============================================================

def create_module_profiler(model):

    profiler = ModuleProfiler()

    profiler.attach(model)

    return profiler

# ============================================================
# Training Benchmark
# ============================================================

def benchmark(
    model,
    criterion,
    optimizer,
    scaler,
    profiler,
    img1,
    img2,
    img3,
):
    print("=" * 70)
    print("RUNNING TRAINING BENCHMARK")
    print("=" * 70)

    model.train()

    profiler.reset()
    reset_memory_stats()

    stats = {
        "forward": [],
        "loss": [],
        "backward": [],
        "optimizer": [],
        "total": [],
    }

    for iteration in range(NUM_PROFILE_ITERS):

        optimizer.zero_grad(set_to_none=True)

        total_start = torch.cuda.Event(enable_timing=True)
        total_end = torch.cuda.Event(enable_timing=True)

        fwd_start = torch.cuda.Event(enable_timing=True)
        fwd_end = torch.cuda.Event(enable_timing=True)

        loss_start = torch.cuda.Event(enable_timing=True)
        loss_end = torch.cuda.Event(enable_timing=True)

        back_start = torch.cuda.Event(enable_timing=True)
        back_end = torch.cuda.Event(enable_timing=True)

        opt_start = torch.cuda.Event(enable_timing=True)
        opt_end = torch.cuda.Event(enable_timing=True)

        total_start.record()

        # ---------------- Forward ----------------

        fwd_start.record()

        with torch.amp.autocast("cuda"):

            preds = model(img1, img3)

        fwd_end.record()

        # ---------------- Loss ----------------

        loss_start.record()

        loss = criterion(preds, img2)

        loss_end.record()

        # ---------------- Backward ----------------

        back_start.record()

        scaler.scale(loss).backward()

        back_end.record()

        # ---------------- Optimizer ----------------

        opt_start.record()

        scaler.step(optimizer)
        scaler.update()

        opt_end.record()

        total_end.record()

        torch.cuda.synchronize()

        stats["forward"].append(
            fwd_start.elapsed_time(fwd_end) / 1000
        )

        stats["loss"].append(
            loss_start.elapsed_time(loss_end) / 1000
        )

        stats["backward"].append(
            back_start.elapsed_time(back_end) / 1000
        )

        stats["optimizer"].append(
            opt_start.elapsed_time(opt_end) / 1000
        )

        stats["total"].append(
            total_start.elapsed_time(total_end) / 1000
        )

        print(
            f"Iteration {iteration+1:02d}/{NUM_PROFILE_ITERS} "
            f"completed."
        )

    return stats

def print_stage_summary(stats):

    print()
    print("=" * 70)
    print("ITERATION BREAKDOWN")
    print("=" * 70)

    total = sum(stats["total"]) / len(stats["total"])

    for key in ["forward", "loss", "backward", "optimizer"]:

        avg = sum(stats[key]) / len(stats[key])

        pct = avg / total * 100

        print(
            f"{key.capitalize():<12}"
            f"{avg:>8.4f} s"
            f"   "
            f"{pct:>6.2f}%"
        )

    print("-" * 70)

    print(
        f"{'Total':<12}"
        f"{total:>8.4f} s"
    )

    print("=" * 70)

    allocated, reserved, peak = memory_report()

    print()
    print("GPU Memory")
    print("-" * 70)

    print(f"Peak Allocated : {peak:.2f} GB")
    print(f"Reserved       : {reserved:.2f} GB")

import csv
from datetime import datetime

# ============================================================
# Final Report
# ============================================================

TRAIN_SEQUENCES = 46181     # Change if dataset changes


def average(values):
    return sum(values) / len(values)


def estimate_training(stats):

    iter_time = average(stats["total"])

    samples_per_second = BATCH_SIZE / iter_time

    epoch_time = TRAIN_SEQUENCES * iter_time / BATCH_SIZE

    return iter_time, samples_per_second, epoch_time


def format_time(seconds):

    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60

    return f"{hours:d}h {minutes:02d}m {secs:04.1f}s"


def detect_bottlenecks(profiler):

    print()
    print("=" * 70)
    print("BOTTLENECK ANALYSIS")
    print("=" * 70)

    total = sum(profiler.total_time.values())

    ranked = sorted(
        profiler.total_time.items(),
        key=lambda x: x[1],
        reverse=True
    )

    for name, t in ranked:

        pct = t / total * 100

        if pct >= 25:
            level = "HIGH"
        elif pct >= 15:
            level = "MEDIUM"
        else:
            level = "LOW"

        print(
            f"{name:<18}"
            f"{pct:>6.2f}%"
            f"   {level}"
        )

    print("=" * 70)


def export_csv(stats, profiler):

    filename = (
        "profile_"
        + datetime.now().strftime("%Y%m%d_%H%M%S")
        + ".csv"
    )

    with open(filename, "w", newline="") as f:

        writer = csv.writer(f)

        writer.writerow(["Stage", "Average Seconds"])

        for key in stats:

            writer.writerow([key, average(stats[key])])

        writer.writerow([])

        writer.writerow(
            [
                "Module",
                "Calls",
                "Total Seconds",
            ]
        )

        for name in profiler.total_time:

            writer.writerow(
                [
                    name,
                    profiler.call_count[name],
                    profiler.total_time[name],
                ]
            )

    print(f"\nSaved profile to {filename}")


def final_report(stats, profiler):

    iter_time, throughput, epoch = estimate_training(stats)

    print()
    print("=" * 70)
    print("THEIA PROFILING REPORT")
    print("=" * 70)

    print(f"GPU                 : {torch.cuda.get_device_name(0)}")
    print(f"Batch Size          : {BATCH_SIZE}")
    print(f"Image Size          : {HEIGHT} x {WIDTH}")

    print()
    print(f"Average Iteration   : {iter_time:.4f} s")
    print(f"Throughput          : {throughput:.2f} samples/s")
    print(f"Estimated Epoch     : {format_time(epoch)}")

    allocated, reserved, peak = memory_report()

    print()
    print(f"Peak GPU Memory     : {peak:.2f} GB")
    print(f"Reserved Memory     : {reserved:.2f} GB")

    print("=" * 70)

    detect_bottlenecks(profiler)

    export_csv(stats, profiler)

if __name__ == "__main__":
    main()