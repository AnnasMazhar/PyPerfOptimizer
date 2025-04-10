"""
Integrated dashboard example using PyPerfOptimizer.

This example demonstrates how to use the PyPerfOptimizer dashboard
to visualize and analyze profiling results.
"""

import os
import sys
import time
import random
import threading
from functools import lru_cache

# Add src directory to path to import pyperfoptimizer in examples
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from pyperfoptimizer.profiler import ProfileManager
from pyperfoptimizer.visualizer import Dashboard
from pyperfoptimizer.optimizer import Recommendations, CodeAnalyzer

# Example functions to profile

def fibonacci(n):
    """Recursive Fibonacci implementation."""
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

@lru_cache(maxsize=None)
def fibonacci_cached(n):
    """Memoized Fibonacci implementation."""
    if n <= 1:
        return n
    return fibonacci_cached(n-1) + fibonacci_cached(n-2)

def process_data(data):
    """Process a list of data with various operations."""
    result = []
    
    # Process each item
    for item in data:
        # Do some string manipulation
        if isinstance(item, str):
            processed = item.upper() + item.lower()
            result.append(processed)
        # Do some numeric calculations
        elif isinstance(item, (int, float)):
            # Perform different calculations based on value
            if item % 2 == 0:
                # Even numbers
                processed = item ** 2
            else:
                # Odd numbers
                processed = item ** 3
            result.append(processed)
        # Handle lists or other iterables
        elif hasattr(item, '__iter__') and not isinstance(item, str):
            # Recursively process nested lists
            processed = process_data(item)
            result.append(processed)
        else:
            # Just append anything else
            result.append(item)
    
    # Do some aggregation
    if result and all(isinstance(x, (int, float)) for x in result):
        # Calculate sum and average for numeric lists
        total = sum(result)
        average = total / len(result)
        return [total, average, result]
    
    return result

def memory_intensive_task(size=100000):
    """A memory-intensive task that builds large data structures."""
    # Create a large list
    large_list = [random.randint(0, 100) for _ in range(size)]
    
    # Create a dictionary with the list elements as keys
    large_dict = {i: x for i, x in enumerate(large_list)}
    
    # Process the data
    result = []
    for i in range(len(large_list)):
        if i in large_dict:
            result.append(large_dict[i] * 2)
    
    # Create another large structure
    matrix = [[random.random() for _ in range(100)] for _ in range(100)]
    
    # Process the matrix
    for i in range(len(matrix)):
        for j in range(len(matrix[i])):
            matrix[i][j] *= 2
    
    # Clean up to free some memory
    del large_list
    del large_dict
    
    return result, matrix

def cpu_intensive_task(n=25):
    """A CPU-intensive task with different algorithmic approaches."""
    # Standard recursive fibonacci
    fib_result = fibonacci(n)
    
    # Optimized memoized fibonacci
    fib_cached_result = fibonacci_cached(n)
    
    # Generate some test data
    test_data = [
        random.randint(1, 100) for _ in range(1000)
    ] + [
        random.choice(['a', 'b', 'c', 'd', 'e']) for _ in range(500)
    ] + [
        [random.randint(1, 10) for _ in range(5)] for _ in range(200)
    ]
    
    # Process the data
    processed_data = process_data(test_data)
    
    return {
        'fibonacci': fib_result,
        'fibonacci_cached': fib_cached_result,
        'processed_data_length': len(processed_data)
    }

def combined_benchmark():
    """A benchmark that combines CPU and memory-intensive tasks."""
    # Start with CPU-intensive work
    cpu_results = cpu_intensive_task(22)
    
    # Then do some memory-intensive work
    memory_results = memory_intensive_task(50000)
    
    # Combine the results in some way
    result = {
        'cpu_results': cpu_results,
        'memory_results_length': len(memory_results[0])
    }
    
    return result

def run_dashboard_with_profiling():
    """Run the PyPerfOptimizer dashboard with profiling data."""
    print("Starting the PyPerfOptimizer Dashboard...")
    
    # Create a profile manager for comprehensive profiling
    profile_manager = ProfileManager(
        enable_cpu=True,
        enable_memory=True,
        enable_line=True
    )
    
    # Profile the combined benchmark
    print("Profiling benchmark functions...")
    profile_manager.profile_func(combined_benchmark)
    
    # Create a code analyzer for the functions we're profiling
    analyzer = CodeAnalyzer()
    code_analysis = analyzer.analyze_function(combined_benchmark)
    
    # Get recommendations for optimizations
    recommender = Recommendations()
    
    # Generate recommendations from the profile manager
    recommendations = recommender.generate_from_profile_manager(profile_manager)
    
    # Add code structure recommendations
    code_structure_recs = recommender.generate_from_code_analysis(code_analysis)
    recommendations['code_structure'] = code_structure_recs
    
    # Create the dashboard
    dashboard = Dashboard(
        host='0.0.0.0',
        port=5000,
        theme='dark'
    )
    
    # Set the profile data in the dashboard
    dashboard.set_profile_manager_data(profile_manager)
    
    # Set recommendations in the dashboard
    dashboard.set_recommendations(recommendations)
    
    # Create a timeline for the dashboard (simplified example)
    timeline_data = [
        {
            'name': 'combined_benchmark',
            'start': 0.0,
            'end': 0.5,
            'depth': 0
        },
        {
            'name': 'cpu_intensive_task',
            'start': 0.05,
            'end': 0.25,
            'depth': 1
        },
        {
            'name': 'fibonacci',
            'start': 0.06,
            'end': 0.15,
            'depth': 2
        },
        {
            'name': 'fibonacci_cached',
            'start': 0.15,
            'end': 0.16,
            'depth': 2
        },
        {
            'name': 'process_data',
            'start': 0.16,
            'end': 0.24,
            'depth': 2
        },
        {
            'name': 'memory_intensive_task',
            'start': 0.25,
            'end': 0.45,
            'depth': 1
        }
    ]
    dashboard.set_timeline_data(timeline_data)
    
    # Save HTML version (for environments without a web server)
    print("Saving dashboard to HTML file...")
    html_file = dashboard.save_html("pyperfoptimizer_dashboard.html")
    print(f"Dashboard saved to: {html_file}")
    print("You can open this file in a web browser to view the dashboard.")
    
    # Launch the dashboard
    print("\nLaunching interactive dashboard web server...")
    print("Dashboard URL: http://localhost:5000")
    print("Press Ctrl+C to exit")
    
    try:
        dashboard.launch(debug=False, open_browser=True)
    except KeyboardInterrupt:
        print("\nDashboard server stopped.")

if __name__ == "__main__":
    # Check for dependencies
    try:
        import flask
        run_dashboard_with_profiling()
    except ImportError:
        print("ERROR: The Flask package is required for the dashboard.")
        print("Please install it using: pip install flask")
        sys.exit(1)
