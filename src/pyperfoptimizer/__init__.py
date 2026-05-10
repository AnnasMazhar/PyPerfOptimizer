"""
PyPerfOptimizer - A comprehensive Python package for unified performance profiling, 
visualization, and optimization.

This package provides tools for:
- CPU profiling 
- Memory profiling 
- Line-by-line code profiling
- Performance visualization
- Code optimization recommendations
"""

__version__ = "0.2.0"

# Import key components for convenient access
from pyperfoptimizer.optimizer import CodeAnalyzer, Recommendations
from pyperfoptimizer.profiler import (
    CPUProfiler,
    LineProfiler,
    MemoryProfiler,
    ProfileManager,
)
from pyperfoptimizer.utils.context_managers import (
    cpu_profiler,
    line_profiler,
    memory_profiler,
)
from pyperfoptimizer.utils.decorators import profile_cpu, profile_line, profile_memory
from pyperfoptimizer.visualizer import (
    CPUVisualizer,
    Dashboard,
    MemoryVisualizer,
    TimelineVisualizer,
)

# Define what's exposed via `from pyperfoptimizer import *`
__all__ = [
    'CPUProfiler', 
    'MemoryProfiler', 
    'LineProfiler',
    'ProfileManager',
    'profile_cpu',
    'profile_memory',
    'profile_line',
    'cpu_profiler',
    'memory_profiler',
    'line_profiler',
    'CPUVisualizer',
    'MemoryVisualizer',
    'TimelineVisualizer',
    'Dashboard',
    'CodeAnalyzer',
    'Recommendations'
]
