"""
Profile manager functionality for PyPerfOptimizer.

This module provides a unified interface to manage different types of profilers
(CPU, memory, line) and their results.
"""

import os
import json
import time
from typing import Callable, Dict, List, Optional, Any, Union, TextIO
from datetime import datetime

from pyperfoptimizer.profiler.cpu_profiler import CPUProfiler
from pyperfoptimizer.profiler.memory_profiler import MemoryProfiler
from pyperfoptimizer.profiler.line_profiler import LineProfiler

class ProfileManager:
    """
    A class for managing multiple profilers.
    
    This class provides a unified interface to work with different types of
    profilers (CPU, memory, line) simultaneously.
    """
    
    def __init__(self, 
                enable_cpu: bool = True,
                enable_memory: bool = True,
                enable_line: bool = True):
        """
        Initialize the profile manager.
        
        Args:
            enable_cpu: Whether to enable CPU profiling
            enable_memory: Whether to enable memory profiling
            enable_line: Whether to enable line-by-line profiling
        """
        self.profilers = {}
        self.enabled_profilers = []
        self.results = {}
        
        if enable_cpu:
            try:
                self.profilers['cpu'] = CPUProfiler()
                self.enabled_profilers.append('cpu')
            except ImportError:
                print("Warning: CPU profiler could not be initialized")
                
        if enable_memory:
            try:
                self.profilers['memory'] = MemoryProfiler()
                self.enabled_profilers.append('memory')
            except ImportError:
                print("Warning: Memory profiler could not be initialized")
                
        if enable_line:
            try:
                self.profilers['line'] = LineProfiler()
                self.enabled_profilers.append('line')
            except ImportError:
                print("Warning: Line profiler could not be initialized")
                
    def start(self) -> None:
        """Start all enabled profilers."""
        for name in self.enabled_profilers:
            profiler = self.profilers.get(name)
            if profiler:
                if name == 'cpu':
                    profiler.start()
                elif name == 'memory':
                    profiler.start()
                elif name == 'line':
                    profiler.enable()
                    
    def stop(self) -> None:
        """Stop all enabled profilers and collect results."""
        for name in self.enabled_profilers:
            profiler = self.profilers.get(name)
            if profiler:
                if name == 'cpu':
                    profiler.stop()
                    self.results['cpu'] = profiler.get_stats()
                elif name == 'memory':
                    profiler.stop()
                    self.results['memory'] = profiler.get_stats()
                elif name == 'line':
                    profiler.disable()
                    self.results['line'] = profiler.get_stats()
                    
    def profile_func(self, func: Callable, *args, **kwargs) -> Any:
        """
        Profile a function using all enabled profilers.
        
        Args:
            func: The function to profile
            *args: Arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function
            
        Returns:
            The return value of the profiled function
        """
        # Start all profilers
        self.start()
        
        # Special handling for line profiler (needs function registration)
        if 'line' in self.enabled_profilers and 'line' in self.profilers:
            self.profilers['line'].add_function(func)
            
        try:
            # Execute the function
            result = func(*args, **kwargs)
            return result
        finally:
            # Stop all profilers
            self.stop()
            
    def get_stats(self) -> Dict:
        """
        Get statistics from all profilers.
        
        Returns:
            Dictionary containing all profiling statistics
        """
        combined_stats = {
            'timestamp': datetime.now().isoformat(),
            'profilers': {}
        }
        
        for name, stats in self.results.items():
            combined_stats['profilers'][name] = stats
            
        return combined_stats
        
    def print_stats(self, output: Optional[TextIO] = None) -> None:
        """
        Print statistics from all profilers.
        
        Args:
            output: Output stream (defaults to sys.stdout)
        """
        print("=== PyPerfOptimizer Profile Results ===", file=output)
        print(f"Timestamp: {datetime.now().isoformat()}", file=output)
        print(file=output)
        
        # Print CPU stats if available
        if 'cpu' in self.results and self.results['cpu']:
            print("--- CPU Profiling Results ---", file=output)
            if 'cpu' in self.profilers:
                self.profilers['cpu'].print_stats(output=output)
            print(file=output)
            
        # Print memory stats if available
        if 'memory' in self.results and self.results['memory']:
            print("--- Memory Profiling Results ---", file=output)
            if 'memory' in self.profilers:
                self.profilers['memory'].print_stats(output=output)
            print(file=output)
            
        # Print line profiling stats if available
        if 'line' in self.results and self.results['line']:
            print("--- Line Profiling Results ---", file=output)
            if 'line' in self.profilers:
                self.profilers['line'].print_stats(output=output)
            print(file=output)
            
    def save_stats(self, directory: str, prefix: Optional[str] = None) -> Dict[str, str]:
        """
        Save statistics from all profilers to files.
        
        Args:
            directory: Directory to save the statistics to
            prefix: Prefix for the filenames
            
        Returns:
            Dictionary mapping profiler names to filenames
        """
        if not os.path.exists(directory):
            os.makedirs(directory)
            
        prefix = prefix or f"profile_{int(time.time())}"
        filenames = {}
        
        # Save combined stats
        combined_file = os.path.join(directory, f"{prefix}_combined.json")
        with open(combined_file, 'w') as f:
            json.dump(self.get_stats(), f, indent=2)
        filenames['combined'] = combined_file
        
        # Save individual profiler stats
        for name in self.enabled_profilers:
            profiler = self.profilers.get(name)
            if profiler and hasattr(profiler, 'save_stats'):
                if name == 'cpu':
                    filename = os.path.join(directory, f"{prefix}_cpu.prof")
                    profiler.save_stats(filename)
                    filenames['cpu'] = filename
                elif name == 'memory':
                    filename = os.path.join(directory, f"{prefix}_memory.json")
                    profiler.save_stats(filename)
                    filenames['memory'] = filename
                elif name == 'line':
                    filename = os.path.join(directory, f"{prefix}_line.lprof")
                    profiler.save_stats(filename)
                    filenames['line'] = filename
                    
        return filenames
        
    def load_stats(self, filenames: Dict[str, str]) -> None:
        """
        Load statistics for each profiler from files.
        
        Args:
            filenames: Dictionary mapping profiler names to filenames
        """
        for name, filename in filenames.items():
            if name == 'combined':
                try:
                    with open(filename, 'r') as f:
                        self.results = json.load(f).get('profilers', {})
                except (json.JSONDecodeError, IOError) as e:
                    print(f"Error loading combined stats: {str(e)}")
            elif name in self.profilers and hasattr(self.profilers[name], 'load_stats'):
                try:
                    self.profilers[name].load_stats(filename)
                    self.results[name] = self.profilers[name].get_stats()
                except Exception as e:
                    print(f"Error loading {name} stats: {str(e)}")
                    
    def clear(self) -> None:
        """Clear all profilers and their results."""
        self.results = {}
        for name, profiler in self.profilers.items():
            if hasattr(profiler, 'clear'):
                profiler.clear()
                
    def get_recommendations(self) -> Dict[str, List[str]]:
        """
        Generate basic recommendations based on profiling results.
        
        Returns:
            Dictionary with recommendations for each profiler type
        """
        recommendations = {}
        
        # CPU profiler recommendations
        if 'cpu' in self.results and self.results['cpu']:
            cpu_recommendations = []
            
            # Check top functions
            if 'cpu' in self.profilers:
                top_funcs = self.profilers['cpu'].get_top_functions(5)
                if top_funcs:
                    cpu_recommendations.append(
                        f"Focus optimization efforts on the top time-consuming function: "
                        f"{top_funcs[0].get('function', 'unknown')}"
                    )
                    
                    # Add specific recommendations based on function patterns
                    for func in top_funcs:
                        func_name = func.get('function', '')
                        if 'sort' in func_name.lower():
                            cpu_recommendations.append(
                                f"Consider using a more efficient sorting algorithm for {func_name}"
                            )
                        elif any(op in func_name.lower() for op in ['loop', 'iter', 'for', 'while']):
                            cpu_recommendations.append(
                                f"Check for inefficient loops in {func_name}"
                            )
                        elif any(term in func_name.lower() for term in ['read', 'write', 'load', 'save', 'file', 'io']):
                            cpu_recommendations.append(
                                f"I/O operations in {func_name} may be slowing down execution"
                            )
                            
            recommendations['cpu'] = cpu_recommendations
            
        # Memory profiler recommendations
        if 'memory' in self.results and self.results['memory']:
            memory_data = self.results['memory']
            memory_recommendations = []
            
            # Check for memory leaks
            if memory_data.get('memory_increase', 0) > 10:  # More than 10MB increase
                memory_recommendations.append(
                    f"Potential memory leak detected - memory increased by "
                    f"{memory_data.get('memory_increase', 0):.2f} MB"
                )
                
            # Check for high peak memory
            if memory_data.get('peak_memory', 0) > 1000:  # More than 1GB peak
                memory_recommendations.append(
                    f"High peak memory usage: {memory_data.get('peak_memory', 0):.2f} MB. "
                    "Consider batch processing or memory optimization."
                )
                
            recommendations['memory'] = memory_recommendations
            
        # Line profiler recommendations
        if 'line' in self.results and self.results['line']:
            line_recommendations = []
            
            # Find hotspots
            if 'line' in self.profilers:
                hotspots = self.profilers['line'].get_hotspots(3)
                for idx, hotspot in enumerate(hotspots):
                    line_recommendations.append(
                        f"Hotspot #{idx+1}: {hotspot.get('function', 'unknown')}, "
                        f"line {hotspot.get('line', 0)}: {hotspot.get('content', 'unknown')} "
                        f"({hotspot.get('percentage', 0):.1f}% of time, "
                        f"{hotspot.get('time', 0):.6f} seconds)"
                    )
                    
            recommendations['line'] = line_recommendations
            
        return recommendations
