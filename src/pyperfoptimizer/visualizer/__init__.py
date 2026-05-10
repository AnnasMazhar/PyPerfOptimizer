"""
Visualizer module for PyPerfOptimizer.

This module provides tools for visualizing profiling results, including
CPU time, memory usage, and line-by-line execution timelines.
"""

from pyperfoptimizer.visualizer.cpu_visualizer import CPUVisualizer
from pyperfoptimizer.visualizer.dashboard import Dashboard
from pyperfoptimizer.visualizer.memory_visualizer import MemoryVisualizer
from pyperfoptimizer.visualizer.timeline_visualizer import TimelineVisualizer

__all__ = ['CPUVisualizer', 'MemoryVisualizer', 'TimelineVisualizer', 'Dashboard']
