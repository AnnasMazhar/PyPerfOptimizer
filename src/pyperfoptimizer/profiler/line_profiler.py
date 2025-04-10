"""
Line-by-line profiling functionality for PyPerfOptimizer.

This module integrates with the line_profiler package to provide detailed
line-by-line execution timing for Python code.
"""

import os
import io
import importlib.util
import tempfile
import inspect
import traceback
from typing import Callable, Dict, List, Optional, Any, Union, TextIO
from datetime import datetime

# Check if line_profiler is installed
try:
    import line_profiler
    _HAS_LINE_PROFILER = True
except ImportError:
    _HAS_LINE_PROFILER = False

class LineProfiler:
    """
    A class for line-by-line profiling of Python code.
    
    This class provides methods to profile functions at the line level,
    showing the time spent on each line of code.
    """
    
    def __init__(self):
        """Initialize the line profiler."""
        if not _HAS_LINE_PROFILER:
            raise ImportError(
                "The line_profiler package is required for line-by-line profiling. "
                "Install it using pip: pip install line_profiler"
            )
            
        self.line_profiler = line_profiler.LineProfiler()
        self.results = None
        
    def add_function(self, func: Callable) -> None:
        """
        Add a function to be profiled.
        
        Args:
            func: The function to profile
        """
        self.line_profiler.add_function(func)
        
    def enable(self) -> None:
        """Enable the line profiler."""
        self.line_profiler.enable()
        
    def disable(self) -> None:
        """Disable the line profiler."""
        self.line_profiler.disable()
        
    def profile_func(self, func: Callable, *args, **kwargs) -> Any:
        """
        Profile a function line by line.
        
        Args:
            func: The function to profile
            *args: Arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function
            
        Returns:
            The return value of the profiled function
        """
        # Wrap the function with the line profiler
        wrapped = self.line_profiler(func)
        
        # Call the wrapped function
        result = wrapped(*args, **kwargs)
        
        # Store the profiling results
        self.results = self.line_profiler.get_stats()
        
        return result
        
    def get_stats(self) -> Dict:
        """
        Get line profiling statistics.
        
        Returns:
            Dictionary containing line profiling statistics
        """
        if not self.results:
            return {}
            
        stats = {}
        stats['timestamp'] = datetime.now().isoformat()
        stats['functions'] = []
        
        # The structure of self.results can vary depending on the line_profiler version
        # We need to handle different possible types
        
        try:
            # Process the statistics for each profiled function
            # Handle the case where results is a dictionary with code_map attribute
            if hasattr(self.results, 'code_map'):
                code_map = self.results.code_map
                for (filename, function_name), lines_data in code_map.items():
                    # Extract line number (first line of the function)
                    line_number = min(lines_data.keys()) if lines_data else 0
                    
                    # Calculate total time for this function
                    total_time = sum(time for _, time in lines_data.values()) / 1e6  # Convert to seconds
                    
                    # Get the source code for each line
                    lines = {}
                    try:
                        if os.path.exists(filename):
                            with open(filename, 'r') as f:
                                all_lines = f.readlines()
                                
                            for line_idx, (hits_count, time) in lines_data.items():
                                line_content = all_lines[line_idx - 1].rstrip() if 0 < line_idx <= len(all_lines) else ""
                                lines[line_idx] = {
                                    'hits': hits_count,
                                    'time': time / 1e6,  # Convert to seconds
                                    'time_per_hit': time / hits_count / 1e6 if hits_count > 0 else 0,
                                    'percentage': (time / sum(time for _, time in lines_data.values()) * 100) 
                                                  if sum(time for _, time in lines_data.values()) > 0 else 0,
                                    'line_content': line_content
                                }
                    except Exception as e:
                        lines['error'] = str(e)
                        
                    function_stats = {
                        'filename': filename,
                        'line_number': line_number,
                        'function_name': function_name,
                        'total_time': total_time,
                        'lines': lines
                    }
                    
                    stats['functions'].append(function_stats)
            
            # Handle the case where results is a dictionary with items() method
            elif hasattr(self.results, 'items'):
                for (filename, line_number, function_name), timings in self.results.items():
                    # Get the total time spent in this function
                    total_time = sum(timings) / 1e6  # Convert to seconds
                    
                    # Get the number of hits for each line
                    hits = self.line_profiler.code_map.get((filename, function_name), {})
                    
                    # Get the source code for each line
                    lines = {}
                    try:
                        if os.path.exists(filename):
                            with open(filename, 'r') as f:
                                all_lines = f.readlines()
                                
                            for line_idx, (hits_count, time) in hits.items():
                                line_content = all_lines[line_idx - 1].rstrip() if 0 < line_idx <= len(all_lines) else ""
                                lines[line_idx] = {
                                    'hits': hits_count,
                                    'time': time / 1e6,  # Convert to seconds
                                    'time_per_hit': time / hits_count / 1e6 if hits_count > 0 else 0,
                                    'percentage': (time / sum(timings) * 100) if sum(timings) > 0 else 0,
                                    'line_content': line_content
                                }
                    except Exception as e:
                        lines['error'] = str(e)
                        
                    function_stats = {
                        'filename': filename,
                        'line_number': line_number,
                        'function_name': function_name,
                        'total_time': total_time,
                        'lines': lines
                    }
                    
                    stats['functions'].append(function_stats)
            
            # If we can't handle the results structure, create a simple stub result
            else:
                stats['functions'].append({
                    'filename': 'unknown',
                    'line_number': 0,
                    'function_name': 'unknown',
                    'total_time': 0,
                    'lines': {'error': 'Unsupported line_profiler results format'}
                })
        
        except Exception as e:
            # If anything goes wrong, add error information
            stats['error'] = str(e)
            stats['functions'].append({
                'filename': 'unknown',
                'line_number': 0,
                'function_name': 'unknown',
                'total_time': 0,
                'lines': {'error': f'Error processing results: {str(e)}'}
            })
            
        return stats
        
    def print_stats(self, output: Optional[TextIO] = None, stripzeros: bool = False) -> None:
        """
        Print line profiling statistics.
        
        Args:
            output: Output stream (defaults to sys.stdout)
            stripzeros: Whether to exclude lines with zero hits
        """
        if not self.results:
            print("No line profiling results available. Run a profile first.", file=output)
            return
            
        # Get a string buffer if output is not specified
        stream = output if output else io.StringIO()
        
        # Print the statistics
        self.line_profiler.print_stats(stream=stream, stripzeros=stripzeros)
        
        # If no output was specified, get the buffer contents and print it
        if not output:
            s = stream.getvalue()
            print(s)
            
    def save_stats(self, filename: str) -> None:
        """
        Save line profiling statistics to a file.
        
        Args:
            filename: File to save the statistics to
        """
        if not self.results:
            return
            
        # Ensure the directory exists
        os.makedirs(os.path.dirname(filename) if os.path.dirname(filename) else '.', exist_ok=True)
        
        # Try to pickle the stats
        try:
            import pickle
            with open(filename, 'wb') as f:
                pickle.dump(self.get_stats(), f)
        except Exception:
            # Fall back to a text file if pickling fails
            with open(filename, 'w') as f:
                self.print_stats(output=f)
                
    def load_stats(self, filename: str) -> None:
        """
        Load line profiling statistics from a file.
        
        Args:
            filename: File to load the statistics from
        """
        try:
            import pickle
            with open(filename, 'rb') as f:
                stats = pickle.load(f)
                
            # Recreate the LineProfiler with loaded stats
            self.results = stats
        except Exception as e:
            raise ValueError(f"Failed to load line profiling stats: {str(e)}")
            
    def clear(self) -> None:
        """Clear profiling results and reset the profiler."""
        self.line_profiler = line_profiler.LineProfiler()
        self.results = None
        
    def get_hotspots(self, n: int = 5) -> List[Dict]:
        """
        Get the top N hotspots (lines with highest execution time).
        
        Args:
            n: Number of hotspots to return
            
        Returns:
            List of dictionaries containing hotspot information
        """
        if not self.results:
            return []
            
        stats = self.get_stats()
        hotspots = []
        
        for func in stats.get('functions', []):
            filename = func['filename']
            function_name = func['function_name']
            
            for line_num, line_info in func.get('lines', {}).items():
                if isinstance(line_num, int):  # Skip any error entries
                    hotspots.append({
                        'filename': filename,
                        'function': function_name,
                        'line': line_num,
                        'content': line_info.get('line_content', ''),
                        'time': line_info.get('time', 0),
                        'hits': line_info.get('hits', 0),
                        'time_per_hit': line_info.get('time_per_hit', 0),
                        'percentage': line_info.get('percentage', 0)
                    })
        
        # Sort by time in descending order
        hotspots.sort(key=lambda x: x['time'], reverse=True)
        
        return hotspots[:n]
