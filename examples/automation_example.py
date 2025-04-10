"""
Automation example using PyPerfOptimizer.

This example demonstrates how to automate performance profiling and optimization
using PyPerfOptimizer in an automated workflow or CI/CD pipeline.
"""

import os
import sys
import time
import json
import argparse
import datetime
import tempfile
from pathlib import Path
import random
import inspect  # Added for inspect.getsource() which is used later

# Add src directory to path to import pyperfoptimizer in examples
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from pyperfoptimizer.profiler import ProfileManager
from pyperfoptimizer.optimizer import CodeAnalyzer, Recommendations, Optimizations
from pyperfoptimizer.utils.io import export_results, import_results
from pyperfoptimizer.visualizer import CPUVisualizer, MemoryVisualizer, TimelineVisualizer

# Example functions to profile and optimize

def slow_function(n):
    """A slow function with inefficient implementation."""
    result = []
    for i in range(n):
        # Inefficient: Creates a new list on each iteration
        result = result + [i * i]
        
    # Inefficient string concatenation
    output = ""
    for item in result:
        output += str(item) + ", "
    
    return output

def optimized_function(n):
    """An optimized version of the slow function."""
    # Efficient: Use append to modify list in-place
    result = []
    for i in range(n):
        result.append(i * i)
    
    # Efficient string concatenation
    return ", ".join(str(item) for item in result)

def recursive_sum(n):
    """Compute sum of numbers recursively (inefficient for large n)."""
    if n <= 0:
        return 0
    return n + recursive_sum(n - 1)

def iterative_sum(n):
    """Compute sum of numbers iteratively (efficient for any n)."""
    return sum(range(1, n + 1))

def process_data_inefficient(data):
    """Process data inefficiently with unnecessary operations."""
    # Create copy of data (unnecessary memory usage)
    data_copy = list(data)
    
    # Inefficient loop with unnecessary conversions
    results = []
    for i in range(len(data_copy)):
        # Convert to string and back to number unnecessarily
        value = int(str(data_copy[i]))
        
        # Check if even or odd
        if value % 2 == 0:
            results.append(value * 2)
        else:
            results.append(value * 3)
            
    # Sort the results multiple times (inefficient)
    results = sorted(results)
    results = sorted(results, reverse=True)
    results = sorted(results)
    
    return results

def process_data_efficient(data):
    """Process data efficiently with optimized operations."""
    # No unnecessary copy
    
    # Efficient loop with list comprehension
    results = [
        value * 2 if value % 2 == 0 else value * 3
        for value in data
    ]
    
    # Single sort operation
    return sorted(results)

class PerformanceProfiler:
    """A class to automate performance profiling and optimization."""
    
    def __init__(self, output_dir=None):
        """
        Initialize the performance profiler.
        
        Args:
            output_dir: Directory to save profiling results
        """
        self.output_dir = output_dir or tempfile.mkdtemp()
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.profile_manager = ProfileManager()
        self.analyzer = CodeAnalyzer()
        self.recommender = Recommendations()
        self.optimizer = Optimizations()
        
        self.results = {}
        
    def profile_function(self, func, *args, **kwargs):
        """
        Profile a function with comprehensive profiling.
        
        Args:
            func: Function to profile
            *args: Arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function
            
        Returns:
            Dictionary with profiling results
        """
        print(f"\n===== Profiling {func.__name__} =====")
        
        # Profile the function
        self.profile_manager.profile_func(func, *args, **kwargs)
        
        # Get profiling stats
        stats = self.profile_manager.get_stats()
        
        # Analyze the function code
        code_analysis = self.analyzer.analyze_function(func)
        
        # Generate recommendations
        recommendations = self.recommender.generate_from_profile_manager(self.profile_manager)
        code_recs = self.recommender.generate_from_code_analysis(code_analysis)
        recommendations['code_structure'] = code_recs
        
        # Generate optimizations
        optimization_suggestions = self.optimizer.suggest_optimizations(
            inspect.getsource(func)
        )
        
        # Combine all results
        result = {
            'function_name': func.__name__,
            'timestamp': datetime.datetime.now().isoformat(),
            'profiling_stats': stats,
            'code_analysis': code_analysis,
            'recommendations': recommendations,
            'optimization_suggestions': optimization_suggestions,
        }
        
        # Store the results
        self.results[func.__name__] = result
        
        # Create a unique filename
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{func.__name__}_{timestamp}"
        
        # Export the results
        result_files = export_results(
            result,
            self.output_dir,
            prefix=filename,
            formats=['json', 'html']
        )
        
        print(f"Profiling results saved to:")
        for fmt, path in result_files.items():
            print(f"  - {fmt}: {path}")
            
        return result
        
    def compare_functions(self, original_func, optimized_func, *args, **kwargs):
        """
        Compare performance between original and optimized functions.
        
        Args:
            original_func: Original function
            optimized_func: Optimized function
            *args: Arguments to pass to both functions
            **kwargs: Keyword arguments to pass to both functions
            
        Returns:
            Dictionary with comparison results
        """
        print(f"\n===== Comparing {original_func.__name__} vs {optimized_func.__name__} =====")
        
        # Profile original function
        original_profile = self.profile_function(original_func, *args, **kwargs)
        
        # Profile optimized function
        optimized_profile = self.profile_function(optimized_func, *args, **kwargs)
        
        # Extract profiling stats
        original_cpu = original_profile['profiling_stats']['profilers'].get('cpu', {})
        optimized_cpu = optimized_profile['profiling_stats']['profilers'].get('cpu', {})
        
        original_memory = original_profile['profiling_stats']['profilers'].get('memory', {})
        optimized_memory = optimized_profile['profiling_stats']['profilers'].get('memory', {})
        
        # Calculate improvement metrics
        cpu_time_original = original_cpu.get('total_time', 0)
        cpu_time_optimized = optimized_cpu.get('total_time', 0)
        
        memory_peak_original = original_memory.get('peak_memory', 0)
        memory_peak_optimized = optimized_memory.get('peak_memory', 0)
        
        # Calculate improvements
        if cpu_time_original > 0:
            cpu_improvement = (cpu_time_original - cpu_time_optimized) / cpu_time_original * 100
        else:
            cpu_improvement = 0
            
        if memory_peak_original > 0:
            memory_improvement = (memory_peak_original - memory_peak_optimized) / memory_peak_original * 100
        else:
            memory_improvement = 0
            
        # Create comparison visualization
        try:
            # CPU time comparison
            cpu_vis = CPUVisualizer()
            cpu_chart_path = os.path.join(self.output_dir, f"comparison_cpu_{original_func.__name__}_vs_{optimized_func.__name__}.html")
            cpu_vis.save_interactive_html(
                original_cpu,
                cpu_chart_path
            )
            
            # Memory usage comparison
            if original_memory and optimized_memory:
                memory_vis = MemoryVisualizer()
                memory_chart_path = os.path.join(self.output_dir, f"comparison_memory_{original_func.__name__}_vs_{optimized_func.__name__}.html")
                memory_vis.save_interactive_html(
                    original_memory,
                    filename=memory_chart_path
                )
        except Exception as e:
            print(f"Error creating visualizations: {e}")
            
        # Prepare comparison results
        comparison = {
            'original_function': original_func.__name__,
            'optimized_function': optimized_func.__name__,
            'timestamp': datetime.datetime.now().isoformat(),
            'cpu_time_original': cpu_time_original,
            'cpu_time_optimized': cpu_time_optimized,
            'cpu_improvement_percent': cpu_improvement,
            'memory_peak_original': memory_peak_original,
            'memory_peak_optimized': memory_peak_optimized,
            'memory_improvement_percent': memory_improvement,
            'original_profile': original_profile,
            'optimized_profile': optimized_profile
        }
        
        # Print comparison summary
        print("\n=== Performance Comparison Summary ===")
        print(f"Original CPU Time: {cpu_time_original:.6f} seconds")
        print(f"Optimized CPU Time: {cpu_time_optimized:.6f} seconds")
        print(f"CPU Time Improvement: {cpu_improvement:.2f}%")
        print(f"Original Peak Memory: {memory_peak_original:.2f} MB")
        print(f"Optimized Peak Memory: {memory_peak_optimized:.2f} MB")
        print(f"Memory Usage Improvement: {memory_improvement:.2f}%")
        
        # Save comparison results
        comparison_file = os.path.join(
            self.output_dir, 
            f"comparison_{original_func.__name__}_vs_{optimized_func.__name__}.json"
        )
        with open(comparison_file, 'w') as f:
            json.dump(comparison, f, indent=2, default=str)
            
        print(f"\nComparison results saved to: {comparison_file}")
        
        return comparison
        
    def batch_profile(self, functions_dict, args_dict=None):
        """
        Profile multiple functions in batch mode.
        
        Args:
            functions_dict: Dictionary mapping function names to functions
            args_dict: Dictionary mapping function names to (args, kwargs) tuples
            
        Returns:
            Dictionary with batch profiling results
        """
        print("\n===== Batch Profiling =====")
        
        args_dict = args_dict or {}
        batch_results = {}
        
        for name, func in functions_dict.items():
            print(f"\nProfiling function: {name}")
            
            # Get the arguments for this function
            args, kwargs = args_dict.get(name, ((), {}))
            
            # Profile the function
            try:
                result = self.profile_function(func, *args, **kwargs)
                batch_results[name] = result
            except Exception as e:
                print(f"Error profiling {name}: {e}")
                
        # Create a batch summary report
        summary = {
            'timestamp': datetime.datetime.now().isoformat(),
            'functions_profiled': list(batch_results.keys()),
            'summaries': {}
        }
        
        for name, result in batch_results.items():
            # Extract key metrics for summary
            cpu_data = result['profiling_stats']['profilers'].get('cpu', {})
            memory_data = result['profiling_stats']['profilers'].get('memory', {})
            
            summary['summaries'][name] = {
                'cpu_time': cpu_data.get('total_time', 0),
                'peak_memory': memory_data.get('peak_memory', 0),
                'recommendations_count': sum(len(recs) for recs in result['recommendations'].values()),
                'optimization_suggestions_count': len(result.get('optimization_suggestions', []))
            }
            
        # Save the batch summary
        summary_file = os.path.join(
            self.output_dir, 
            f"batch_profile_summary_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
            
        print(f"\nBatch profiling summary saved to: {summary_file}")
        
        return batch_results
        
    def generate_report(self):
        """
        Generate a comprehensive report of all profiling results.
        
        Returns:
            Path to the generated report file
        """
        print("\n===== Generating Comprehensive Report =====")
        
        # Compile all results
        report = {
            'timestamp': datetime.datetime.now().isoformat(),
            'functions_profiled': list(self.results.keys()),
            'results': self.results,
            'summary': {
                'total_functions': len(self.results),
                'cpu_time_total': sum(
                    result['profiling_stats']['profilers'].get('cpu', {}).get('total_time', 0)
                    for result in self.results.values()
                ),
                'recommendations_total': sum(
                    sum(len(recs) for recs in result['recommendations'].values())
                    for result in self.results.values()
                )
            }
        }
        
        # Save the report
        report_file = os.path.join(
            self.output_dir, 
            f"comprehensive_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
            
        # Generate HTML report
        html_report = self._generate_html_report(report)
        html_report_file = os.path.join(
            self.output_dir, 
            f"comprehensive_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        )
        with open(html_report_file, 'w') as f:
            f.write(html_report)
            
        print(f"\nComprehensive report saved to:")
        print(f"  - JSON: {report_file}")
        print(f"  - HTML: {html_report_file}")
        
        return html_report_file
        
    def _generate_html_report(self, report):
        """Generate an HTML report from the profiling results."""
        # Create a simple HTML report
        html = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>PyPerfOptimizer Performance Report</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    margin: 0;
                    padding: 20px;
                    color: #333;
                }
                h1, h2, h3 {
                    color: #2c3e50;
                }
                .report-header {
                    background-color: #2c3e50;
                    color: white;
                    padding: 20px;
                    margin-bottom: 20px;
                    border-radius: 5px;
                }
                .summary {
                    background-color: #f8f9fa;
                    padding: 15px;
                    margin-bottom: 20px;
                    border-radius: 5px;
                    border-left: 5px solid #2c3e50;
                }
                .function-card {
                    background-color: #fff;
                    border: 1px solid #ddd;
                    border-radius: 5px;
                    padding: 15px;
                    margin-bottom: 15px;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                }
                .metrics {
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
                    gap: 10px;
                    margin-bottom: 15px;
                }
                .metric {
                    background-color: #e9ecef;
                    padding: 10px;
                    border-radius: 5px;
                    text-align: center;
                }
                .metric-value {
                    font-size: 1.5em;
                    font-weight: bold;
                    color: #2c3e50;
                }
                .recommendations {
                    background-color: #f8f9fa;
                    padding: 15px;
                    border-radius: 5px;
                }
            </style>
        </head>
        <body>
            <div class="report-header">
                <h1>PyPerfOptimizer Performance Report</h1>
                <p>Generated: """ + report['timestamp'] + """</p>
            </div>
            
            <div class="summary">
                <h2>Summary</h2>
                <div class="metrics">
                    <div class="metric">
                        <p>Functions Profiled</p>
                        <p class="metric-value">""" + str(report['summary']['total_functions']) + """</p>
                    </div>
                    <div class="metric">
                        <p>Total CPU Time</p>
                        <p class="metric-value">""" + f"{report['summary']['cpu_time_total']:.6f}s" + """</p>
                    </div>
                    <div class="metric">
                        <p>Total Recommendations</p>
                        <p class="metric-value">""" + str(report['summary']['recommendations_total']) + """</p>
                    </div>
                </div>
            </div>
            
            <h2>Function Details</h2>
        """
        
        # Add details for each function
        for func_name, result in report['results'].items():
            # Extract key metrics
            cpu_data = result['profiling_stats']['profilers'].get('cpu', {})
            memory_data = result['profiling_stats']['profilers'].get('memory', {})
            
            cpu_time = cpu_data.get('total_time', 0)
            peak_memory = memory_data.get('peak_memory', 0)
            
            # Add function card
            html += f"""
            <div class="function-card">
                <h3>{func_name}</h3>
                <div class="metrics">
                    <div class="metric">
                        <p>CPU Time</p>
                        <p class="metric-value">{cpu_time:.6f}s</p>
                    </div>
                    <div class="metric">
                        <p>Peak Memory</p>
                        <p class="metric-value">{peak_memory:.2f} MB</p>
                    </div>
                </div>
                
                <h4>Top Recommendations</h4>
                <div class="recommendations">
                    <ul>
            """
            
            # Add top recommendations from each category
            for category, recs in result['recommendations'].items():
                if recs:
                    # Take top 2 recommendations from each category
                    for rec in recs[:2]:
                        html += f"<li><strong>{category.upper()}:</strong> {rec}</li>\n"
                        
            html += """
                    </ul>
                </div>
            </div>
            """
            
        # Close the HTML document
        html += """
        </body>
        </html>
        """
        
        return html

def run_profiling_demos():
    """Run the automated profiling demonstrations."""
    # Set up the profiler with output to current directory
    output_dir = os.path.join(os.getcwd(), "profiling_results")
    profiler = PerformanceProfiler(output_dir=output_dir)
    
    print("\n=== PyPerfOptimizer Automation Example ===")
    print(f"Profiling results will be saved to: {output_dir}")
    
    # Demo 1: Compare slow and optimized functions
    test_size = 5000
    profiler.compare_functions(
        slow_function,
        optimized_function,
        test_size
    )
    
    # Demo 2: Compare recursive and iterative sum functions
    sum_size = 500
    profiler.compare_functions(
        recursive_sum,
        iterative_sum,
        sum_size
    )
    
    # Demo 3: Batch profile multiple functions
    test_data = [random.randint(1, 100) for _ in range(1000)]
    functions = {
        "inefficient_process": process_data_inefficient,
        "efficient_process": process_data_efficient,
        "slow_func": slow_function,
        "optimized_func": optimized_function
    }
    
    args = {
        "inefficient_process": ((test_data,), {}),
        "efficient_process": ((test_data,), {}),
        "slow_func": ((1000,), {}),
        "optimized_func": ((1000,), {})
    }
    
    profiler.batch_profile(functions, args)
    
    # Generate comprehensive report
    report_path = profiler.generate_report()
    
    print("\n=== Profiling Complete ===")
    print(f"Open the report at: {report_path}")
    
if __name__ == "__main__":
    # Check for required modules
    try:
        import inspect  # Needed for source code inspection
        run_profiling_demos()
    except ImportError as e:
        print(f"ERROR: Missing required module: {e}")
        sys.exit(1)
