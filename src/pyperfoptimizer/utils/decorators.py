"""
Decorator utilities for PyPerfOptimizer.

This module provides decorators for easy profiling of functions.
"""

import functools
import time
import os
from typing import Callable, Dict, List, Optional, Any, Union, TextIO
import inspect

# Import profilers
from pyperfoptimizer.profiler.cpu_profiler import CPUProfiler
from pyperfoptimizer.profiler.memory_profiler import MemoryProfiler
from pyperfoptimizer.profiler.line_profiler import LineProfiler
from pyperfoptimizer.profiler.profile_manager import ProfileManager

def profile_cpu(
    sort_by: str = 'cumulative',
    print_stats: bool = True,
    top_n: Optional[int] = 10,
    output: Optional[TextIO] = None,
    save_path: Optional[str] = None
) -> Callable:
    """
    Decorator for CPU profiling a function.
    
    Args:
        sort_by: Sorting criteria for results (cumulative, time, calls, etc.)
        print_stats: Whether to print profiling statistics
        top_n: Number of top functions to display
        output: Output stream (defaults to sys.stdout)
        save_path: Path to save the profiling statistics to
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Create a CPU profiler
            profiler = CPUProfiler(sort_by=sort_by)
            
            # Profile the function
            try:
                result = profiler.profile_func(func, *args, **kwargs)
            finally:
                # Print statistics if requested
                if print_stats:
                    print(f"\n--- CPU profiling results for {func.__name__} ---", file=output)
                    profiler.print_stats(top_n=top_n, output=output)
                    
                # Save statistics if requested
                if save_path:
                    profiler.save_stats(save_path)
                    if print_stats:
                        print(f"Profiling statistics saved to {save_path}", file=output)
                    
            return result
        
        return wrapper
    
    return decorator

def profile_memory(
    interval: float = 0.1,
    print_stats: bool = True,
    include_children: bool = True,
    output: Optional[TextIO] = None,
    save_path: Optional[str] = None
) -> Callable:
    """
    Decorator for memory profiling a function.
    
    Args:
        interval: Sampling interval in seconds
        print_stats: Whether to print profiling statistics
        include_children: Whether to include child processes
        output: Output stream (defaults to sys.stdout)
        save_path: Path to save the profiling statistics to
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # Create a memory profiler
                profiler = MemoryProfiler(
                    interval=interval,
                    include_children=include_children
                )
                
                # Profile the function
                result = profiler.profile_func(func, *args, **kwargs)
                
                # Print statistics if requested
                if print_stats:
                    print(f"\n--- Memory profiling results for {func.__name__} ---", file=output)
                    profiler.print_stats(output=output)
                    
                # Save statistics if requested
                if save_path:
                    profiler.save_stats(save_path)
                    if print_stats:
                        print(f"Memory profiling statistics saved to {save_path}", file=output)
                
                return result
            except ImportError as e:
                print(f"Memory profiling error: {e}", file=output)
                # Fall back to running the function without profiling
                return func(*args, **kwargs)
        
        return wrapper
    
    return decorator

def profile_line(
    print_stats: bool = True,
    stripzeros: bool = False,
    output: Optional[TextIO] = None,
    save_path: Optional[str] = None
) -> Callable:
    """
    Decorator for line-by-line profiling a function.
    
    Args:
        print_stats: Whether to print profiling statistics
        stripzeros: Whether to exclude lines with zero hits
        output: Output stream (defaults to sys.stdout)
        save_path: Path to save the profiling statistics to
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # Create a line profiler
                profiler = LineProfiler()
                
                # Profile the function
                result = profiler.profile_func(func, *args, **kwargs)
                
                # Print statistics if requested
                if print_stats:
                    print(f"\n--- Line profiling results for {func.__name__} ---", file=output)
                    profiler.print_stats(output=output, stripzeros=stripzeros)
                    
                # Save statistics if requested
                if save_path:
                    profiler.save_stats(save_path)
                    if print_stats:
                        print(f"Line profiling statistics saved to {save_path}", file=output)
                
                return result
            except ImportError as e:
                print(f"Line profiling error: {e}", file=output)
                # Fall back to running the function without profiling
                return func(*args, **kwargs)
        
        return wrapper
    
    return decorator

def profile_all(
    print_stats: bool = True,
    output: Optional[TextIO] = None,
    save_dir: Optional[str] = None,
    prefix: Optional[str] = None
) -> Callable:
    """
    Decorator for profiling a function with all available profilers.
    
    Args:
        print_stats: Whether to print profiling statistics
        output: Output stream (defaults to sys.stdout)
        save_dir: Directory to save the profiling statistics to
        prefix: Prefix for the saved files
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # Create a profile manager with all profilers enabled
                profile_manager = ProfileManager(
                    enable_cpu=True,
                    enable_memory=True,
                    enable_line=True
                )
                
                # Profile the function
                result = profile_manager.profile_func(func, *args, **kwargs)
                
                # Print statistics if requested
                if print_stats:
                    print(f"\n--- Combined profiling results for {func.__name__} ---", file=output)
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
                    prefix_value = prefix or func.__name__
                    filenames = profile_manager.save_stats(save_dir, prefix_value)
                    
                    if print_stats:
                        print(f"\nProfiling statistics saved to:", file=output)
                        for name, filename in filenames.items():
                            print(f"  {name}: {filename}", file=output)
                
                return result
            except Exception as e:
                print(f"Profiling error: {e}", file=output)
                # Fall back to running the function without profiling
                return func(*args, **kwargs)
        
        return wrapper
    
    return decorator
