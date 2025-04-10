"""
Recommendations functionality for PyPerfOptimizer.

This module provides tools for generating optimization recommendations
based on profiling results and code analysis.
"""

import ast
import re
from typing import Dict, List, Set, Tuple, Optional, Any, Union, Callable
import inspect

class Recommendations:
    """
    A class for generating optimization recommendations.
    
    This class analyzes profiling results and code to provide specific
    recommendations for improving performance.
    """
    
    def __init__(self):
        """Initialize the recommendations generator."""
        self.recommendations = {
            'cpu': [],
            'memory': [],
            'algorithm': [],
            'code_structure': []
        }
        
    def reset(self) -> None:
        """Reset the recommendations."""
        self.__init__()
        
    def generate_from_cpu_profile(self, cpu_data: Dict) -> List[str]:
        """
        Generate recommendations based on CPU profiling data.
        
        Args:
            cpu_data: CPU profiling data from CPUProfiler.get_stats()
            
        Returns:
            List of CPU optimization recommendations
        """
        recommendations = []
        
        # Check if we have function data
        if not cpu_data or 'functions' not in cpu_data or not cpu_data['functions']:
            recommendations.append(
                "No CPU profiling data available. Run a CPU profile to get recommendations."
            )
            self.recommendations['cpu'] = recommendations
            return recommendations
            
        # Analyze hotspots
        hotspots = cpu_data['functions'][:5]  # Top 5 functions
        
        if hotspots:
            recommendations.append(
                f"Focus optimization efforts on top time-consuming function: {hotspots[0].get('function', 'unknown')}"
            )
            
        # Check for recursive functions
        for func in cpu_data.get('functions', []):
            if '/' in str(func.get('ncalls', '')):
                recommendations.append(
                    f"Function {func.get('function', 'unknown')} is recursive. "
                    "Consider an iterative approach or memoization if it recalculates the same values."
                )
                
        # Check overall execution time
        total_time = cpu_data.get('total_time', 0)
        if total_time > 1.0:
            recommendations.append(
                f"Total execution time ({total_time:.2f}s) is high. "
                "Consider parallelizing or optimizing the most expensive operations."
            )
            
        # Function-specific recommendations
        for func in hotspots:
            func_name = func.get('function', '')
            
            # Check for sorting operations
            if any(sort_op in func_name.lower() for sort_op in ['sort', 'order']):
                recommendations.append(
                    f"Function {func_name} may involve sorting. "
                    "Use appropriate sorting algorithm and consider the sorted() key parameter."
                )
                
            # Check for I/O operations
            if any(io_op in func_name.lower() for io_op in ['read', 'write', 'load', 'save', 'file', 'open']):
                recommendations.append(
                    f"Function {func_name} may involve I/O operations. "
                    "Consider buffering, asynchronous I/O, or batching operations."
                )
                
            # Check for string operations
            if any(str_op in func_name.lower() for str_op in ['str', 'join', 'split', 'format']):
                recommendations.append(
                    f"Function {func_name} may involve string operations. "
                    "Use ''.join() for concatenation and consider f-strings for formatting."
                )
                
        self.recommendations['cpu'] = recommendations
        return recommendations
        
    def generate_from_memory_profile(self, memory_data: Dict) -> List[str]:
        """
        Generate recommendations based on memory profiling data.
        
        Args:
            memory_data: Memory profiling data from MemoryProfiler.get_stats()
            
        Returns:
            List of memory optimization recommendations
        """
        recommendations = []
        
        # Check if we have memory data
        if not memory_data or not any(k in memory_data for k in ['memory_mb', 'peak_memory']):
            recommendations.append(
                "No memory profiling data available. Run a memory profile to get recommendations."
            )
            self.recommendations['memory'] = recommendations
            return recommendations
            
        # Check for memory leaks
        if memory_data.get('memory_increase', 0) > 5:  # More than 5MB increase
            recommendations.append(
                f"Potential memory leak detected - memory increased by {memory_data.get('memory_increase', 0):.2f} MB. "
                "Check for objects that aren't being garbage collected."
            )
            
        # Check peak memory usage
        peak_memory = memory_data.get('peak_memory', 0)
        if peak_memory > 500:  # More than 500MB
            recommendations.append(
                f"High peak memory usage: {peak_memory:.2f} MB. "
                "Consider batch processing or streaming approach for large datasets."
            )
            
        # Check for memory growth rate
        timestamps = memory_data.get('timestamps', [])
        mem_usage = memory_data.get('memory_mb', [])
        
        if len(timestamps) > 1 and len(mem_usage) > 1:
            time_diff = timestamps[-1] - timestamps[0]
            mem_diff = mem_usage[-1] - mem_usage[0]
            
            if time_diff > 0:
                growth_rate = mem_diff / time_diff  # MB/s
                
                if growth_rate > 50:  # More than 50MB/s
                    recommendations.append(
                        f"High memory growth rate: {growth_rate:.2f} MB/s. "
                        "Check for unnecessary object creation in loops."
                    )
                    
        # General memory recommendations
        recommendations.append(
            "For large data processing, consider generators, iterators, or lazy evaluation."
        )
        
        # Check for final memory compared to baseline
        baseline = memory_data.get('baseline_memory', 0)
        final = memory_data.get('final_memory', 0)
        
        if final > baseline * 2 and final - baseline > 10:  # More than doubled and >10MB increase
            recommendations.append(
                f"Memory usage more than doubled from {baseline:.2f} MB to {final:.2f} MB. "
                "Consider using context managers (with) to ensure resources are released."
            )
            
        self.recommendations['memory'] = recommendations
        return recommendations
        
    def generate_from_line_profile(self, line_data: Dict) -> List[str]:
        """
        Generate recommendations based on line profiling data.
        
        Args:
            line_data: Line profiling data from LineProfiler.get_stats()
            
        Returns:
            List of line-level optimization recommendations
        """
        recommendations = []
        
        # Check if we have line profile data
        if not line_data or 'functions' not in line_data or not line_data['functions']:
            recommendations.append(
                "No line profiling data available. Run a line profile to get recommendations."
            )
            self.recommendations['algorithm'] = recommendations
            return recommendations
            
        # Analyze hotspots in each function
        for func_data in line_data.get('functions', []):
            func_name = func_data.get('function_name', 'unknown')
            lines = func_data.get('lines', {})
            
            # Find the hotspot lines (highest time percentage)
            hotspots = []
            for line_num, line_info in lines.items():
                if isinstance(line_num, str) and line_num == 'error':
                    continue
                
                if isinstance(line_num, int) and line_info.get('percentage', 0) > 5:  # >5% of time
                    hotspots.append({
                        'line_num': line_num,
                        'percentage': line_info.get('percentage', 0),
                        'time': line_info.get('time', 0),
                        'content': line_info.get('line_content', '')
                    })
                    
            # Sort hotspots by percentage
            hotspots.sort(key=lambda x: x['percentage'], reverse=True)
            
            # Generate recommendations for top hotspots
            for i, hotspot in enumerate(hotspots[:3]):  # Top 3 hotspots
                line_content = hotspot['content'].strip()
                percentage = hotspot['percentage']
                line_num = hotspot['line_num']
                
                # Basic recommendation for the hotspot
                recommendations.append(
                    f"Hotspot at line {line_num} in {func_name} ({percentage:.1f}% of time): '{line_content}'"
                )
                
                # Check for specific patterns in the line content
                if re.search(r'for\s+.*\s+in\s+', line_content):
                    # Loop hotspot
                    recommendations.append(
                        f"Consider optimizing the loop at line {line_num} - use list comprehension, vectorization, or Cython."
                    )
                elif re.search(r'if\s+.*\s+in\s+', line_content):
                    # Membership test
                    recommendations.append(
                        f"Membership test at line {line_num} - use a set instead of a list for faster lookups."
                    )
                elif '+' in line_content and re.search(r'[\'"]\s*\+', line_content):
                    # String concatenation
                    recommendations.append(
                        f"String concatenation at line {line_num} - use ''.join() or f-strings for better performance."
                    )
                elif re.search(r'\.\s*(?:append|extend|insert)', line_content):
                    # List modification
                    recommendations.append(
                        f"List modification at line {line_num} - consider preallocating the list if size is known."
                    )
                elif re.search(r'(?:sum|min|max|sorted|list|set|dict)\s*\(', line_content):
                    # Built-in function calls
                    recommendations.append(
                        f"Built-in function at line {line_num} - ensure you're using it efficiently."
                    )
                    
        # If no specific recommendations were generated
        if not recommendations:
            recommendations.append(
                "No clear line-level hotspots identified. Your code may benefit from algorithm-level optimizations."
            )
            
        self.recommendations['algorithm'] = recommendations
        return recommendations
        
    def generate_from_code_analysis(self, analysis_results: Dict) -> List[str]:
        """
        Generate recommendations based on code analysis results.
        
        Args:
            analysis_results: Code analysis results from CodeAnalyzer
            
        Returns:
            List of code structure optimization recommendations
        """
        recommendations = []
        
        # Check if we have analysis results
        if not analysis_results or 'issues' not in analysis_results:
            recommendations.append(
                "No code analysis data available. Run a code analysis to get recommendations."
            )
            self.recommendations['code_structure'] = recommendations
            return recommendations
            
        # Get issues from analysis
        issues = analysis_results.get('issues', [])
        
        # Add issues as recommendations
        for issue in issues:
            severity = issue.get('severity', 'info')
            message = issue.get('message', '')
            line = issue.get('line', '')
            
            line_info = f" at line {line}" if line else ""
            recommendations.append(f"{message}{line_info}")
            
        # Check for optimization opportunities in loops
        loops = analysis_results.get('loops', [])
        nested_loops = [loop for loop in loops if loop.get('nested', False)]
        
        if nested_loops:
            recommendations.append(
                f"Found {len(nested_loops)} nested loops. Nested loops can be performance bottlenecks. "
                "Consider restructuring or using more efficient algorithms."
            )
            
        # Check for optimization opportunities in data structures
        lists = analysis_results.get('data_structures', {}).get('lists', [])
        large_lists = [lst for lst in lists if lst.get('size', 0) > 100]
        
        if large_lists:
            recommendations.append(
                f"Found {len(large_lists)} large lists. Consider if other data structures (sets, dictionaries) "
                "would be more appropriate for your use case."
            )
            
        # Check for unused functions
        unused_funcs = analysis_results.get('unused_functions', [])
        if unused_funcs:
            recommendations.append(
                f"Found {len(unused_funcs)} unused functions. Remove dead code to improve maintainability."
            )
            
        # Import optimization recommendations
        imported_modules = analysis_results.get('imported_modules', [])
        if 'itertools' not in imported_modules and len(loops) > 3:
            recommendations.append(
                "Consider using itertools module for more efficient iteration patterns."
            )
            
        if 'collections' not in imported_modules and len(analysis_results.get('data_structures', {}).get('dicts', [])) > 3:
            recommendations.append(
                "Consider using collections.defaultdict or collections.Counter for cleaner dictionary operations."
            )
            
        self.recommendations['code_structure'] = recommendations
        return recommendations
        
    def generate_all(self, 
                    cpu_data: Optional[Dict] = None,
                    memory_data: Optional[Dict] = None,
                    line_data: Optional[Dict] = None,
                    code_analysis: Optional[Dict] = None) -> Dict[str, List[str]]:
        """
        Generate all recommendations from available profiling and analysis data.
        
        Args:
            cpu_data: CPU profiling data (optional)
            memory_data: Memory profiling data (optional)
            line_data: Line profiling data (optional)
            code_analysis: Code analysis results (optional)
            
        Returns:
            Dictionary of recommendations by category
        """
        self.reset()
        
        # Generate recommendations from each data source if available
        if cpu_data:
            self.generate_from_cpu_profile(cpu_data)
            
        if memory_data:
            self.generate_from_memory_profile(memory_data)
            
        if line_data:
            self.generate_from_line_profile(line_data)
            
        if code_analysis:
            self.generate_from_code_analysis(code_analysis)
            
        return self.recommendations
        
    def generate_from_profile_manager(self, profile_manager) -> Dict[str, List[str]]:
        """
        Generate recommendations from a ProfileManager instance.
        
        Args:
            profile_manager: ProfileManager instance with profiling results
            
        Returns:
            Dictionary of recommendations by category
        """
        self.reset()
        
        # Get the profiling results
        stats = profile_manager.get_stats()
        profilers = stats.get('profilers', {})
        
        # Generate recommendations for each profiler type
        if 'cpu' in profilers:
            self.generate_from_cpu_profile(profilers['cpu'])
            
        if 'memory' in profilers:
            self.generate_from_memory_profile(profilers['memory'])
            
        if 'line' in profilers:
            self.generate_from_line_profile(profilers['line'])
            
        return self.recommendations
        
    def get_prioritized_recommendations(self, max_per_category: int = 5) -> List[str]:
        """
        Get a prioritized list of recommendations across all categories.
        
        Args:
            max_per_category: Maximum number of recommendations per category
            
        Returns:
            List of prioritized recommendations
        """
        prioritized = []
        
        # Get top recommendations from each category
        for category, recs in self.recommendations.items():
            top_recs = recs[:max_per_category]
            for rec in top_recs:
                prioritized.append(f"[{category.upper()}] {rec}")
                
        return prioritized
