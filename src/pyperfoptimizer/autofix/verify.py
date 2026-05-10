"""Benchmark verification for optimizations."""

import textwrap
import time
from dataclasses import dataclass


@dataclass
class BenchmarkResult:
    original_time: float
    optimized_time: float
    speedup: float
    passed: bool  # >10% improvement


def verify(original_source: str, optimized_source: str, n: int = 1000) -> BenchmarkResult:
    """Benchmark original vs optimized code and report speedup."""
    original_ns = {}
    optimized_ns = {}

    # Compile both
    orig_code = compile(textwrap.dedent(original_source), "<original>", "exec")
    opt_code = compile(textwrap.dedent(optimized_source), "<optimized>", "exec")

    # Warmup
    exec(orig_code, original_ns)
    exec(opt_code, optimized_ns)

    # Time original
    start = time.perf_counter()
    for _ in range(n):
        ns = {}
        exec(orig_code, ns)
    original_time = time.perf_counter() - start

    # Time optimized
    start = time.perf_counter()
    for _ in range(n):
        ns = {}
        exec(opt_code, ns)
    optimized_time = time.perf_counter() - start

    speedup = original_time / optimized_time if optimized_time > 0 else 1.0
    passed = speedup > 1.10

    return BenchmarkResult(
        original_time=original_time,
        optimized_time=optimized_time,
        speedup=speedup,
        passed=passed,
    )
