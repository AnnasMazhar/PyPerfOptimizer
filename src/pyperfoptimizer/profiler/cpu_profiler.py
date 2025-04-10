"""
CPU profiling functionality for PyPerfOptimizer.

This module uses cProfile to collect function call statistics and provides
an easy-to-use interface for CPU profiling Python code.
"""

import cProfile
import pstats
import io
import time
import functools
import os
from typing import Callable, Dict, List, Optional, Any, Union, TextIO
from datetime import datetime

class CPUProfiler:
    """
    A class for CPU profiling Python code.
    
    This class provides methods to profile functions or code blocks and
    analyze the results to identify performance bottlenecks.
    """
    
    def __init__(self, 
                 sort_by: str = 'cumulative',
                 strip_dirs: bool = False,
                 include_builtins: bool = False):
        """
        Initialize the CPU profiler.
        
        Args:
            sort_by: Sorting criteria for results. Options include 'cumulative',
                    'time', 'calls', etc. Defaults to 'cumulative'.
            strip_dirs: Whether to strip directory paths from file names.
            include_builtins: Whether to include built-in functions in results.
        """
        self.sort_by = sort_by
        self.strip_dirs = strip_dirs
        self.include_builtins = include_builtins
        self.profiler = cProfile.Profile()
        self.results = None
        self.start_time = None
        self.end_time = None
        
    def start(self) -> None:
        """Start CPU profiling."""
        self.start_time = time.time()
        self.profiler.enable()
        
    def stop(self) -> None:
        """Stop CPU profiling and store results."""
        self.profiler.disable()
        self.end_time = time.time()
        # Store results as pstats object
        s = io.StringIO()
        ps = pstats.Stats(self.profiler, stream=s).sort_stats(self.sort_by)
        if self.strip_dirs:
            ps.strip_dirs()
        self.results = ps
        
    def profile_func(self, func: Callable, *args, **kwargs) -> Any:
        """
        Profile a function execution.
        
        Args:
            func: The function to profile
            *args: Arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function
            
        Returns:
            The return value of the profiled function
        """
        self.start()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            self.stop()
            
    def get_stats(self) -> Dict:
        """
        Get profiling statistics.
        
        Returns:
            A dictionary containing profiling statistics
        """
        if not self.results:
            return {}
            
        stats = {}
        # Total execution time
        stats['total_time'] = self.end_time - self.start_time if self.start_time and self.end_time else 0
        
        # Get function statistics
        s = io.StringIO()
        self.results.stream = s
        self.results.print_stats()
        
        # Parse the stats output into structured data
        stats_str = s.getvalue()
        stats['raw_output'] = stats_str
        
        # Extract function-level data
        functions = []
        for line in stats_str.split('\n'):
            if line and not line.startswith('ncalls') and not line.startswith('   '):
                parts = line.strip().split()
                if len(parts) >= 6:  # Make sure there are enough columns
                    try:
                        func_data = {
                            'ncalls': parts[0],
                            'tottime': float(parts[1]),
                            'percall': float(parts[2]),
                            'cumtime': float(parts[3]),
                            'percall_cumtime': float(parts[4]),
                            'function': ' '.join(parts[5:])
                        }
                        functions.append(func_data)
                    except (ValueError, IndexError):
                        continue
        
        stats['functions'] = functions
        
        # Add date and time information
        stats['timestamp'] = datetime.now().isoformat()
        
        return stats
            
    def print_stats(self, 
                   top_n: Optional[int] = 10, 
                   output: Optional[TextIO] = None) -> None:
        """
        Print profiling statistics.
        
        Args:
            top_n: Number of top functions to display
            output: Output stream (defaults to sys.stdout)
        """
        if not self.results:
            print("No profiling results available. Run a profile first.", file=output)
            return
            
        self.results.stream = output  # Can be None, in which case sys.stdout is used
        if top_n:
            self.results.print_stats(top_n)
        else:
            self.results.print_stats()
            
    def save_stats(self, filename: str) -> None:
        """
        Save profiling statistics to a file.
        
        Args:
            filename: File to save the statistics to
        """
        if not self.results:
            return
            
        # Ensure the directory exists
        os.makedirs(os.path.dirname(filename) if os.path.dirname(filename) else '.', exist_ok=True)
        
        # Save stats to file
        self.results.dump_stats(filename)
        
    def load_stats(self, filename: str) -> None:
        """
        Load profiling statistics from a file.
        
        Args:
            filename: File to load the statistics from
        """
        stats = pstats.Stats(filename)
        stats.sort_stats(self.sort_by)
        if self.strip_dirs:
            stats.strip_dirs()
        self.results = stats
        
    def get_top_functions(self, n: int = 10) -> List[Dict]:
        """
        Get the top N functions by cumulative time.
        
        Args:
            n: Number of top functions to return
            
        Returns:
            List of dictionaries containing function information
        """
        stats = self.get_stats()
        if not stats or 'functions' not in stats:
            return []
            
        # Sort by cumulative time and return top n
        sorted_funcs = sorted(stats['functions'], 
                              key=lambda x: x['cumtime'], 
                              reverse=True)
        return sorted_funcs[:n]
        
    def clear(self) -> None:
        """Clear profiling results and reset profiler."""
        self.profiler = cProfile.Profile()
        self.results = None
        self.start_time = None
        self.end_time = None
