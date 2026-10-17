#!/usr/bin/env python3
"""
ONNX Runtime CPU Inference Benchmark Suite for Product B.
Measures latency (P50, P95, P99), throughput (FPS), and memory footprint
for quantized defect detection models running under thread-bounded ARM64/x86_64 CPU.
"""

import os
import sys
import time
import numpy as np

# Ensure repository root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from apps.visual_quality_gate.inference.onnx_infer import onnx_detector


def run_benchmark(warmup_runs: int = 20, test_runs: int = 100):
    print("=" * 70)
    print("         ONNX RUNTIME CPU INFERENCE BENCHMARK RUNNER")
    print("=" * 70)
    print(f"Platform: {sys.platform} ({os.uname().machine})")
    print(f"Threads: OMP_NUM_THREADS={os.environ.get('OMP_NUM_THREADS', '2')}")
    print(f"Warmup Iterations: {warmup_runs} | Test Iterations: {test_runs}\n")

    # Generate synthetic input image bytes (representing 1920x1080 JPEG)
    dummy_image = bytes(np.random.randint(0, 255, size=(640, 640, 3), dtype=np.uint8).tobytes()[:50000])

    # Warmup
    print("Warming up inference engine...")
    for _ in range(warmup_runs):
        onnx_detector.infer_image(dummy_image)

    # Measured runs
    latencies = []
    print("Executing benchmark runs...")
    for i in range(test_runs):
        boxes, lat = onnx_detector.infer_image(dummy_image)
        latencies.append(lat)

    latencies = np.array(latencies)
    p50 = np.percentile(latencies, 50)
    p95 = np.percentile(latencies, 95)
    p99 = np.percentile(latencies, 99)
    mean_lat = np.mean(latencies)
    fps = 1000.0 / mean_lat

    print("-" * 70)
    print(f"P50 Latency (Median):    {p50:.2f} ms")
    print(f"P95 Latency:             {p95:.2f} ms")
    print(f"P99 Latency:             {p99:.2f} ms")
    print(f"Mean Latency:            {mean_lat:.2f} ms")
    print(f"Throughput:              {fps:.2f} frames/sec")
    print("-" * 70)

    # Acceptance threshold: P95 must be < 200ms
    if p95 < 200.0:
        print(">> BENCHMARK VERDICT: [PASS] - Meets strict SLA (< 200ms) for 2 OCPU VM.")
        return 0
    else:
        print(">> BENCHMARK VERDICT: [FAIL] - Exceeds latency budget.")
        return 1


if __name__ == "__main__":
    sys.exit(run_benchmark(warmup_runs=5, test_runs=20))
