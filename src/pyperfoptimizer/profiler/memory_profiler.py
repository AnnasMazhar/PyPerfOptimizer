"""
Memory profiling functionality for PyPerfOptimizer.

This module integrates with the memory_profiler package to track memory usage
of Python functions and code blocks.
"""

import os
import time
import tempfile
import functools
import traceback
import importlib.util
from typing import Callable, Dict, List, Optional, Any, Union, TextIO
from datetime import datetime

# Check if memory_profiler is installed
try:
    import memory_profiler
    _HAS_MEMORY_PROFILER = True
except ImportError:
    _HAS_MEMORY_PROFILER = False

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
        
        # Start memory profiling with memory_profiler
        # For continuous monitoring, we'll use a temporary file
        fd, self._mprof_output = tempfile.mkstemp(suffix='.dat')
        os.close(fd)
        
        # Start mprof in a separate process
        try:
            # We're using memory_profiler's API directly rather than the command-line tool
            # This is more flexible and doesn't require subprocess
            self._memory_usage_monitor = memory_profiler.LogFile(
                self._mprof_output, 
                self.interval
            )
            self._memory_usage_monitor.start()
        except Exception as e:
            self.cleanup()
            raise RuntimeError(f"Failed to start memory profiling: {str(e)}")
            
    def stop(self) -> None:
        """Stop memory profiling and process results."""
        try:
            if hasattr(self, '_memory_usage_monitor') and self._memory_usage_monitor:
                self._memory_usage_monitor.stop()
                
            self.end_time = time.time()
            
            # Process the memory log file
            if self._mprof_output and os.path.exists(self._mprof_output):
                timestamps = []
                mem_usage = []
                
                with open(self._mprof_output, 'r') as f:
                    for line in f:
                        if line.startswith('CMDLINE'):
                            continue
                        try:
                            parts = line.strip().split()
                            if len(parts) >= 2:
                                ts = float(parts[0])
                                mem = float(parts[1])
                                timestamps.append(ts)
                                mem_usage.append(mem)
                        except (ValueError, IndexError):
                            continue
                
                self.results = {
                    'timestamps': timestamps,
                    'memory_mb': mem_usage,
                    'duration': self.end_time - self.start_time,
                    'baseline_memory': self.baseline_memory
                }
        finally:
            self.cleanup()
            
    def cleanup(self) -> None:
        """Clean up temporary files."""
        if self._mprof_output and os.path.exists(self._mprof_output):
            try:
                os.remove(self._mprof_output)
            except (OSError, IOError):
                pass
            self._mprof_output = None
            
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
        self._mprof_output = None
