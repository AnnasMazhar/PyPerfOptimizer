"""Load profiling output from py-spy, cProfile, or Scalene and identify hot functions."""

import json
import os
import pstats
from dataclasses import dataclass
from pathlib import Path


@dataclass
class HotFunction:
    """A function identified as hot from profiling data."""
    name: str
    file: str
    line: int
    time_pct: float
    cumtime: float


def load_profile(path: str | Path) -> list[HotFunction]:
    """Load a profile from any supported format (auto-detected). Returns hot functions sorted by time_pct desc."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Profile not found: {path}")

    # Try JSON formats first
    try:
        with open(path) as f:
            data = json.load(f)
        if _is_speedscope(data):
            return _parse_speedscope(data)
        if _is_scalene(data):
            return _parse_scalene(data)
    except (json.JSONDecodeError, UnicodeDecodeError):
        pass

    # Try pstats binary
    try:
        return _parse_pstats(path)
    except Exception:
        pass

    raise ValueError(f"Unrecognized profile format: {path}")


def _is_speedscope(data: dict) -> bool:
    return "$schema" in data or data.get("exporter", "").startswith("py-spy") or "profiles" in data and "shared" in data


def _is_scalene(data: dict) -> bool:
    return "files" in data or "program" in data and "elapsed_time_sec" in data


def _parse_speedscope(data: dict) -> list[HotFunction]:
    """Parse py-spy speedscope JSON format."""
    shared = data.get("shared", {})
    frames = shared.get("frames", [])
    profiles = data.get("profiles", [])

    # Aggregate sample counts per frame
    frame_weights: dict[int, float] = {}
    total_weight = 0.0

    for profile in profiles:
        samples = profile.get("samples", [])
        weights = profile.get("weights", [1.0] * len(samples))
        for sample, weight in zip(samples, weights):
            for frame_idx in sample:
                frame_weights[frame_idx] = frame_weights.get(frame_idx, 0.0) + weight
                total_weight += weight

    if total_weight == 0:
        return []

    results = []
    for idx, weight in frame_weights.items():
        if idx >= len(frames):
            continue
        frame = frames[idx]
        name = frame.get("name", "")
        file = frame.get("file", "")
        line = frame.get("line", 0)
        time_pct = (weight / total_weight) * 100
        results.append(HotFunction(name=name, file=os.path.basename(file), line=line, time_pct=time_pct, cumtime=weight))

    results.sort(key=lambda h: h.time_pct, reverse=True)
    return results


def _parse_scalene(data: dict) -> list[HotFunction]:
    """Parse Scalene JSON output."""
    files_data = data.get("files", {})
    elapsed = data.get("elapsed_time_sec", 1.0) or 1.0

    results = []
    for filepath, file_info in files_data.items():
        functions = file_info.get("functions", [])
        for func in functions:
            name = func.get("name", "")
            line = func.get("line", 0)
            cpu_time = func.get("n_cpu_percent_python", 0) + func.get("n_cpu_percent_c", 0)
            results.append(HotFunction(
                name=name,
                file=os.path.basename(filepath),
                line=line,
                time_pct=cpu_time,
                cumtime=cpu_time * elapsed / 100,
            ))

    results.sort(key=lambda h: h.time_pct, reverse=True)
    return results


def _parse_pstats(path: Path) -> list[HotFunction]:
    """Parse cProfile pstats binary."""
    stats = pstats.Stats(str(path))
    total_tt = sum(v[2] for v in stats.stats.values()) or 1.0

    results = []
    for (filename, line, name), (cc, nc, tt, ct, callers) in stats.stats.items():
        time_pct = (tt / total_tt) * 100
        results.append(HotFunction(
            name=name,
            file=os.path.basename(filename),
            line=line,
            time_pct=time_pct,
            cumtime=ct,
        ))

    results.sort(key=lambda h: h.time_pct, reverse=True)
    return results
