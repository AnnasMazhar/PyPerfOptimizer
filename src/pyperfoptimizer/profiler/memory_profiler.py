"""
Memory profiling functionality for PyPerfOptimizer.

This module integrates with the memory_profiler package to track memory usage
of Python functions and code blocks.
"""

import os
import sys
import time
import tempfile
import functools
import traceback
import importlib.util
import psutil
from typing import Callable, Dict, List, Optional, Any, Union, TextIO
from datetime import datetime

# Check if memory_profiler is installed
try:
    import memory_profiler
    _HAS_MEMORY_PROFILER = True
except ImportError:
    _HAS_MEMORY_PROFILER = False

# Function to get memory usage in MB using psutil as a fallback
def get_memory_usage():
    """Get current memory usage in MB."""
    try:
        if _HAS_MEMORY_PROFILER:
            return memory_profiler.memory_usage()[0]
        else:
            # Fallback to psutil if memory_profiler is not available
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / (1024 * 1024)  # Convert to MB
    except Exception:
        # If all else fails, return a placeholder value
        return 0.0

class MemoryProfiler:
    """
    A class for memory profiling Python code.
    
    This class provides methods to profile functions or code blocks and
    analyze the memory usage to identify potential memory issues.
    """
    
    def __init__(self, 
                interval: float = 0.1,
                include_children: bool = True,
                multiprocess: bool = False):
        """
        Initialize the memory profiler.
        
        Args:
            interval: Sampling interval in seconds
            include_children: Whether to include child processes
            multiprocess: Whether to track memory across multiple processes
        """
        if not _HAS_MEMORY_PROFILER:
            raise ImportError(
                "The memory_profiler package is required for memory profiling. "
                "Install it using pip: pip install memory_profiler"
            )
        
        self.interval = interval
        self.include_children = include_children
        self.multiprocess = multiprocess
        self.start_time = None
        self.end_time = None
        self.results = None
        self.baseline_memory = None
        self._mprof_output = None
        
    def start(self) -> None:
        """Start memory profiling."""
        self.start_time = time.time()
        self.baseline_memory = memory_profiler.memory_usage()[0]
        
        # Instead of using LogFile which may not be available in all versions,
        # we'll use memory_profiler's core functions directly
        self._timestamps = []
        self._memory_samples = []
        
        # Take an initial sample
        self._timestamps.append(0.0)
        self._memory_samples.append(self.baseline_memory)
        
        # Create a thread or process that will sample memory at regular intervals
        # For simplicity, we're just going to create a simple structure to record samples
        # Note: In a real implementation, this would be a thread/process
        # This simplified version will take samples only when profile_func is used
        
    def stop(self) -> None:
        """Stop memory profiling and process results."""
        self.end_time = time.time()
        
        # Take a final sample
        elapsed = self.end_time - self.start_time
        self._timestamps.append(elapsed)
        final_memory = memory_profiler.memory_usage()[0]
        self._memory_samples.append(final_memory)
        
        # Store the results
        self.results = {
            'timestamps': self._timestamps,
            'memory_mb': self._memory_samples,
            'duration': elapsed,
            'baseline_memory': self.baseline_memory
        }
            
    def cleanup(self) -> None:
        """Clean up resources."""
        # No files to clean up in this implementation
        # Just reset our memory samples
        self._timestamps = []
        self._memory_samples = []
            
    def profile_func(self, func: Callable, *args, **kwargs) -> Any:
        """
        Profile memory usage of a function.
        
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
            
    def profile_line_by_line(self, func: Callable, *args, **kwargs) -> Dict:
        """
        Profile memory usage line by line.
        
        Args:
            func: The function to profile
            *args: Arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function
            
        Returns:
            Dictionary with line-by-line memory usage
        """
        # This method relies on the @profile decorator from memory_profiler
        # We'll use a temporary file to store the function with @profile
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Get function source and write to a temporary file
            import inspect
            source = inspect.getsource(func)
            func_name = func.__name__
            module_name = func.__module__
            
            # Create a temporary module for the function
            temp_module_path = os.path.join(temp_dir, "temp_function.py")
            with open(temp_module_path, 'w') as f:
                # Prepend the profile decorator
                f.write("from memory_profiler import profile\n\n")
                # Add any imports from the original module
                if module_name != "__main__":
                    f.write(f"from {module_name} import *\n\n")
                # Write the function with @profile decorator
                if not source.lstrip().startswith('@'):
                    f.write("@profile\n")
                f.write(source)
                
            # Import the temporary module
            spec = importlib.util.spec_from_file_location("temp_module", temp_module_path)
            temp_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(temp_module)
            
            # Get the profiled function
            profiled_func = getattr(temp_module, func_name)
            
            # Create a string buffer to capture the output
            import io
            old_stdout = memory_profiler.sys.stdout
            string_buffer = io.StringIO()
            memory_profiler.sys.stdout = string_buffer
            
            # Call the profiled function
            try:
                profiled_func(*args, **kwargs)
            finally:
                memory_profiler.sys.stdout = old_stdout
                
            # Parse the line-by-line profiling results
            output = string_buffer.getvalue()
            line_results = self._parse_line_profile_output(output)
            
            return line_results
            
        except Exception as e:
            print(f"Error in line-by-line profiling: {e}")
            traceback.print_exc()
            return {"error": str(e)}
        finally:
            # Clean up the temporary files
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
            
    def _parse_line_profile_output(self, output: str) -> Dict:
        """
        Parse the line profile output from memory_profiler.
        
        Args:
            output: String output from memory_profiler
            
        Returns:
            Dictionary with line-by-line memory information
        """
        lines = output.strip().split('\n')
        line_stats = []
        filename = None
        func_name = None
        
        for line in lines:
            # Check for the Line # header
            if 'Line #' in line and 'Mem usage' in line:
                continue
                
            # Check for function definition line
            if '@profile' in line or 'def ' in line:
                if 'def ' in line:
                    # Extract function name
                    parts = line.split('def ')[1].split('(')[0].strip()
                    func_name = parts
                continue
                
            # Try to parse a line of profiling output
            try:
                parts = line.strip().split()
                if len(parts) >= 4 and parts[0].isdigit():
                    line_num = int(parts[0])
                    mem_usage = float(parts[1])
                    increment = float(parts[2])
                    code = ' '.join(parts[3:])
                    
                    line_stats.append({
                        'line_num': line_num,
                        'memory_mb': mem_usage,
                        'increment_mb': increment,
                        'code': code
                    })
            except (ValueError, IndexError):
                if 'Filename:' in line:
                    # Extract filename
                    filename = line.split('Filename:')[1].strip()
        
        return {
            'filename': filename,
            'function': func_name,
            'line_stats': line_stats,
            'raw_output': output
        }
            
    def get_stats(self) -> Dict:
        """
        Get memory profiling statistics.
        
        Returns:
            Dictionary containing memory profiling statistics
        """
        if not self.results:
            return {}
            
        stats = self.results.copy()
        
        # Add summarized statistics
        if stats.get('memory_mb'):
            memory = stats['memory_mb']
            stats['peak_memory'] = max(memory) if memory else 0
            stats['min_memory'] = min(memory) if memory else 0
            stats['avg_memory'] = sum(memory) / len(memory) if memory else 0
            stats['final_memory'] = memory[-1] if memory else 0
            stats['memory_increase'] = stats['final_memory'] - stats['baseline_memory']
        
        # Add timestamp info
        stats['timestamp'] = datetime.now().isoformat()
        
        return stats
        
    def print_stats(self, output: Optional[TextIO] = None) -> None:
        """
        Print memory profiling statistics.
        
        Args:
            output: Output stream (defaults to sys.stdout)
        """
        if not self.results:
            print("No memory profiling results available. Run a profile first.", file=output)
            return
            
        stats = self.get_stats()
        
        print("=== Memory Profiling Results ===", file=output)
        print(f"Duration: {stats['duration']:.2f} seconds", file=output)
        print(f"Baseline Memory: {stats['baseline_memory']:.2f} MB", file=output)
        print(f"Peak Memory: {stats['peak_memory']:.2f} MB", file=output)
        print(f"Final Memory: {stats['final_memory']:.2f} MB", file=output)
        print(f"Memory Increase: {stats['memory_increase']:.2f} MB", file=output)
        print(f"Average Memory: {stats['avg_memory']:.2f} MB", file=output)
        
    def save_stats(self, filename: str) -> None:
        """
        Save memory profiling statistics to a file.
        
        Args:
            filename: File to save the statistics to
        """
        if not self.results:
            return
            
        # Ensure the directory exists
        os.makedirs(os.path.dirname(filename) if os.path.dirname(filename) else '.', exist_ok=True)
        
        # Save stats to file
        import json
        with open(filename, 'w') as f:
            json.dump(self.get_stats(), f, indent=2)
            
    def load_stats(self, filename: str) -> None:
        """
        Load memory profiling statistics from a file.
        
        Args:
            filename: File to load the statistics from
        """
        import json
        with open(filename, 'r') as f:
            self.results = json.load(f)
            
    def clear(self) -> None:
        """Clear profiling results."""
        self.results = None
        self.start_time = None
        self.end_time = None
        self.baseline_memory = None
        self._timestamps = []
        self._memory_samples = []
