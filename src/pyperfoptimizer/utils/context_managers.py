"""
Context manager utilities for PyPerfOptimizer.

This module provides context managers for easy profiling of code blocks.
"""

import contextlib
import time
import os
from typing import Dict, List, Optional, Any, Union, TextIO, Generator
import inspect

# Import profilers
from pyperfoptimizer.profiler.cpu_profiler import CPUProfiler
from pyperfoptimizer.profiler.memory_profiler import MemoryProfiler
from pyperfoptimizer.profiler.line_profiler import LineProfiler
from pyperfoptimizer.profiler.profile_manager import ProfileManager

@contextlib.contextmanager
def cpu_profiler(
    sort_by: str = 'cumulative',
    print_stats: bool = True,
    top_n: Optional[int] = 10,
    output: Optional[TextIO] = None,
    save_path: Optional[str] = None
) -> Generator[CPUProfiler, None, None]:
    """
    Context manager for CPU profiling a block of code.
    
    Args:
        sort_by: Sorting criteria for results (cumulative, time, calls, etc.)
        print_stats: Whether to print profiling statistics
        top_n: Number of top functions to display
        output: Output stream (defaults to sys.stdout)
        save_path: Path to save the profiling statistics to
        
    Yields:
        The CPU profiler instance
    """
    # Create a CPU profiler
    profiler = CPUProfiler(sort_by=sort_by)
    
    # Start profiling
    profiler.start()
    
    try:
        # Yield the profiler to the caller
        yield profiler
    finally:
        # Stop profiling
        profiler.stop()
        
        # Print statistics if requested
        if print_stats:
            print("\n--- CPU profiling results ---", file=output)
            profiler.print_stats(top_n=top_n, output=output)
            
        # Save statistics if requested
        if save_path:
            profiler.save_stats(save_path)
            if print_stats:
                print(f"Profiling statistics saved to {save_path}", file=output)

@contextlib.contextmanager
def memory_profiler(
    interval: float = 0.1,
    print_stats: bool = True,
    include_children: bool = True,
    output: Optional[TextIO] = None,
    save_path: Optional[str] = None
) -> Generator[MemoryProfiler, None, None]:
    """
    Context manager for memory profiling a block of code.
    
    Args:
        interval: Sampling interval in seconds
        print_stats: Whether to print profiling statistics
        include_children: Whether to include child processes
        output: Output stream (defaults to sys.stdout)
        save_path: Path to save the profiling statistics to
        
    Yields:
        The memory profiler instance
    """
    try:
        # Create a memory profiler
        profiler = MemoryProfiler(
            interval=interval,
            include_children=include_children
        )
        
        # Start profiling
        profiler.start()
        
        try:
            # Yield the profiler to the caller
            yield profiler
        finally:
            # Stop profiling
            profiler.stop()
            
            # Print statistics if requested
            if print_stats:
                print("\n--- Memory profiling results ---", file=output)
                profiler.print_stats(output=output)
                
            # Save statistics if requested
            if save_path:
                profiler.save_stats(save_path)
                if print_stats:
                    print(f"Memory profiling statistics saved to {save_path}", file=output)
    except ImportError as e:
        print(f"Memory profiling error: {e}", file=output)
        # Create a dummy context manager
        @contextlib.contextmanager
        def dummy_context():
            yield None
            
        with dummy_context() as dummy:
            yield dummy

@contextlib.contextmanager
def line_profiler(
    func_to_profile: Optional[callable] = None,
    print_stats: bool = True,
    stripzeros: bool = False,
    output: Optional[TextIO] = None,
    save_path: Optional[str] = None
) -> Generator[LineProfiler, None, None]:
    """
    Context manager for line-by-line profiling a block of code.
    
    Args:
        func_to_profile: Function to profile (optional)
        print_stats: Whether to print profiling statistics
        stripzeros: Whether to exclude lines with zero hits
        output: Output stream (defaults to sys.stdout)
        save_path: Path to save the profiling statistics to
        
    Yields:
        The line profiler instance
    """
    try:
        # Create a line profiler
        profiler = LineProfiler()
        
        # Add the function to profile if provided
        if func_to_profile:
            profiler.add_function(func_to_profile)
            
        # Start profiling
        profiler.enable()
        
        try:
            # Yield the profiler to the caller
            yield profiler
        finally:
            # Stop profiling
            profiler.disable()
            
            # Print statistics if requested
            if print_stats:
                print("\n--- Line profiling results ---", file=output)
                profiler.print_stats(output=output, stripzeros=stripzeros)
                
            # Save statistics if requested
            if save_path:
                profiler.save_stats(save_path)
                if print_stats:
                    print(f"Line profiling statistics saved to {save_path}", file=output)
    except ImportError as e:
        print(f"Line profiling error: {e}", file=output)
        # Create a dummy context manager
        @contextlib.contextmanager
        def dummy_context():
            yield None
            
        with dummy_context() as dummy:
            yield dummy

@contextlib.contextmanager
def profile_context(
    print_stats: bool = True,
    output: Optional[TextIO] = None,
    save_dir: Optional[str] = None,
    prefix: Optional[str] = None
) -> Generator[ProfileManager, None, None]:
    """
    Context manager for comprehensive profiling of a block of code.
    
    Args:
        print_stats: Whether to print profiling statistics
        output: Output stream (defaults to sys.stdout)
        save_dir: Directory to save the profiling statistics to
        prefix: Prefix for the saved files
        
    Yields:
        The profile manager instance
    """
    try:
        # Create a profile manager with all profilers enabled
        profile_manager = ProfileManager(
            enable_cpu=True,
            enable_memory=True,
            enable_line=True
        )
        
        # Start profiling
        profile_manager.start()
        
        try:
            # Yield the profile manager to the caller
            yield profile_manager
        finally:
            # Stop profiling
            profile_manager.stop()
            
            # Print statistics if requested
            if print_stats:
                print("\n--- Combined profiling results ---", file=output)
                profile_manager.print_stats(output=output)
                
                # Print recommendations
                recommendations = profile_manager.get_recommendations()
                if recommendations:
                    print("\n--- Optimization Recommendations ---", file=output)
                    for category, items in recommendations.items():
                        if items:
                            print(f"\n{category.upper()}:", file=output)
                            for item in items:
                                print(f"  - {item}", file=output)
                
            # Save statistics if requested
            if save_dir:
                os.makedirs(save_dir, exist_ok=True)
                prefix_value = prefix or "profile"
                filenames = profile_manager.save_stats(save_dir, prefix_value)
                
                if print_stats:
                    print(f"\nProfiling statistics saved to:", file=output)
                    for name, filename in filenames.items():
                        print(f"  {name}: {filename}", file=output)
    except Exception as e:
        print(f"Profiling error: {e}", file=output)
        # Create a dummy context manager
        @contextlib.contextmanager
        def dummy_context():
            yield None
            
        with dummy_context() as dummy:
            yield dummy
