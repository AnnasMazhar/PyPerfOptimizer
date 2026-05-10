"""Auto-optimization pipeline for PyPerfOptimizer."""

from .engine import fix, fix_file, scan, scan_file
from .patterns.base import Match, Optimization, Pattern
from .profile_loader import HotFunction, load_profile
from .verify import BenchmarkResult, verify

__all__ = [
    "scan",
    "scan_file",
    "fix",
    "fix_file",
    "verify",
    "load_profile",
    "HotFunction",
    "Match",
    "Optimization",
    "Pattern",
    "BenchmarkResult",
]
