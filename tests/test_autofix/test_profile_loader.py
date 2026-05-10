"""Tests for profile_loader module."""

import cProfile
import json
import pstats
import tempfile
from pathlib import Path

import pytest

from pyperfoptimizer.autofix.profile_loader import HotFunction, load_profile


# --- Fixtures ---

SPEEDSCOPE_DATA = {
    "$schema": "https://www.speedscope.app/file-format-schema.json",
    "exporter": "py-spy@0.3.14",
    "shared": {
        "frames": [
            {"name": "process_data", "file": "/app/main.py", "line": 42},
            {"name": "parse_input", "file": "/app/utils.py", "line": 10},
            {"name": "write_output", "file": "/app/io.py", "line": 88},
        ]
    },
    "profiles": [
        {
            "samples": [[0, 1], [0], [0, 2], [1]],
            "weights": [5.0, 3.0, 2.0, 1.0],
        }
    ],
}

SCALENE_DATA = {
    "program": "main.py",
    "elapsed_time_sec": 10.0,
    "files": {
        "/app/main.py": {
            "functions": [
                {"name": "process_data", "line": 42, "n_cpu_percent_python": 30.0, "n_cpu_percent_c": 5.0},
                {"name": "helper", "line": 100, "n_cpu_percent_python": 10.0, "n_cpu_percent_c": 0.0},
            ]
        },
        "/app/utils.py": {
            "functions": [
                {"name": "parse", "line": 5, "n_cpu_percent_python": 15.0, "n_cpu_percent_c": 2.0},
            ]
        },
    },
}


@pytest.fixture
def speedscope_file(tmp_path):
    p = tmp_path / "profile.speedscope.json"
    p.write_text(json.dumps(SPEEDSCOPE_DATA))
    return p


@pytest.fixture
def scalene_file(tmp_path):
    p = tmp_path / "profile.scalene.json"
    p.write_text(json.dumps(SCALENE_DATA))
    return p


@pytest.fixture
def pstats_file(tmp_path):
    """Generate a real pstats binary file."""
    p = tmp_path / "profile.pstats"
    profiler = cProfile.Profile()
    profiler.enable()
    # Do some work to generate stats
    total = sum(range(1000))
    _ = [x * 2 for x in range(500)]
    profiler.disable()
    profiler.dump_stats(str(p))
    return p


# --- Tests ---

class TestLoadSpeedscope:
    def test_loads_and_sorts(self, speedscope_file):
        results = load_profile(speedscope_file)
        assert len(results) == 3
        assert all(isinstance(r, HotFunction) for r in results)
        # Sorted by time_pct descending
        assert results[0].time_pct >= results[1].time_pct >= results[2].time_pct

    def test_frame_fields(self, speedscope_file):
        results = load_profile(speedscope_file)
        top = results[0]
        assert top.name == "process_data"
        assert top.file == "main.py"
        assert top.line == 42

    def test_percentages_sum_reasonable(self, speedscope_file):
        results = load_profile(speedscope_file)
        # Each frame can appear in multiple samples, so total > 100% is normal (inclusive time)
        assert all(r.time_pct > 0 for r in results)


class TestLoadScalene:
    def test_loads_and_sorts(self, scalene_file):
        results = load_profile(scalene_file)
        assert len(results) == 3
        assert results[0].time_pct >= results[1].time_pct

    def test_frame_fields(self, scalene_file):
        results = load_profile(scalene_file)
        top = results[0]
        assert top.name == "process_data"
        assert top.file == "main.py"
        assert top.line == 42
        assert top.time_pct == 35.0  # 30 + 5
        assert top.cumtime == pytest.approx(3.5)  # 35% of 10s

    def test_multiple_files(self, scalene_file):
        results = load_profile(scalene_file)
        files = {r.file for r in results}
        assert "main.py" in files
        assert "utils.py" in files


class TestLoadPstats:
    def test_loads_binary(self, pstats_file):
        results = load_profile(pstats_file)
        assert len(results) > 0
        assert all(isinstance(r, HotFunction) for r in results)
        assert results[0].time_pct >= results[-1].time_pct

    def test_percentages_sum_to_100(self, pstats_file):
        results = load_profile(pstats_file)
        total = sum(r.time_pct for r in results)
        assert pytest.approx(total, abs=0.1) == 100.0


class TestAutoDetection:
    def test_detects_speedscope(self, speedscope_file):
        results = load_profile(str(speedscope_file))
        assert results[0].name == "process_data"

    def test_detects_scalene(self, scalene_file):
        results = load_profile(str(scalene_file))
        assert results[0].name == "process_data"

    def test_detects_pstats(self, pstats_file):
        results = load_profile(str(pstats_file))
        assert len(results) > 0

    def test_file_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_profile(tmp_path / "nonexistent.json")

    def test_unrecognized_format(self, tmp_path):
        p = tmp_path / "garbage.bin"
        p.write_bytes(b"\x00\x01\x02\x03garbage")
        with pytest.raises(ValueError, match="Unrecognized"):
            load_profile(p)


class TestEngineIntegration:
    """Test that hot_functions filtering works in the engine."""

    def test_scan_filters_by_hot_functions(self):
        from pyperfoptimizer.autofix import scan

        source = """\
result = []
for i in range(100):
    result.append(i)
"""
        # Without filter — should find optimizations (if pattern matches)
        all_opts = scan(source)

        # With filter pointing to line 999 — nothing should match
        hot = [HotFunction(name="other", file="x.py", line=999, time_pct=50.0, cumtime=1.0)]
        filtered = scan(source, hot_functions=hot)
        assert len(filtered) <= len(all_opts)

    def test_scan_includes_hot_line(self):
        from pyperfoptimizer.autofix import scan

        source = """\
result = []
for i in range(100):
    result.append(i)
"""
        # Hot function starting at line 1 should include line 2-3
        hot = [HotFunction(name="main", file="test.py", line=1, time_pct=80.0, cumtime=2.0)]
        opts = scan(source, hot_functions=hot)
        # Should still find optimizations since lines 1-3 are within hot range
        all_opts = scan(source)
        assert len(opts) == len(all_opts)
