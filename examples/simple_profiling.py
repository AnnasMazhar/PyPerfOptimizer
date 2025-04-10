"""
Simple profiling example using PyPerfOptimizer.

This example demonstrates how to use the PyPerfOptimizer package for CPU, 
memory, and line-by-line profiling of Python code.
"""

import time
import os
import sys
from random import randint

# Add src directory to path to import pyperfoptimizer in examples
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from pyperfoptimizer.profiler import CPUProfiler, MemoryProfiler, LineProfiler, ProfileManager
from pyperfoptimizer.utils.decorators import profile_cpu, profile_memory, profile_line, profile_all
from pyperfoptimizer.utils.context_managers import cpu_profiler, memory_profiler, line_profiler

def slow_recursive_function(n):
    """A slow recursive function to demonstrate profiling."""
    if n <= 1:
        return n
    return slow_recursive_function(n - 1) + slow_recursive_function(n - 2)

def memory_intensive_function(size):
    """A function that allocates a significant amount of memory."""
    # Create a large list
    large_list = [randint(0, 100) for _ in range(size)]
    
    # Process the list
    result = {}
    for i, value in enumerate(large_list):
        result[i] = value ** 2
        
    # Create another large object
    another_list = large_list * 2
    
    # Do some more processing
    total = sum(another_list)
    
    # Clean up to release memory
    del large_list
    del another_list
    
    return total, result

def complex_algorithm(input_data, multiplier=2):
    """A more complex algorithm with various operations."""
    # Initialize results
    results = []
    
    # Process each element
    for i, item in enumerate(input_data):
        # Do some calculations
        value = item * multiplier
        
        # Conditional processing
        if value % 2 == 0:
            # Even values get squared
            value = value ** 2
        else:
            # Odd values get cubed
            value = value ** 3
            
        # Accumulate results
        results.append(value)
        
    # Generate some additional data
    additional_data = [sum(results[:i+1]) for i in range(len(results))]
    
    # Combine the results
    final_result = list(zip(results, additional_data))
    
    return final_result

def demonstrate_cpu_profiling():
    """Demonstrate CPU profiling."""
    print("\n===== CPU Profiling Demonstration =====")
    
    # Method 1: Using the CPUProfiler class directly
    print("\n--- Method 1: Using the CPUProfiler class directly ---")
    profiler = CPUProfiler()
    profiler.start()
    slow_recursive_function(20)
    profiler.stop()
    profiler.print_stats(top_n=5)
    
    # Method 2: Using the profile_func method
    print("\n--- Method 2: Using the profile_func method ---")
    profiler = CPUProfiler()
    profiler.profile_func(slow_recursive_function, 20)
    profiler.print_stats(top_n=5)
    
    # Method 3: Using the profile_cpu decorator
    print("\n--- Method 3: Using the profile_cpu decorator ---")
    
    @profile_cpu(top_n=5)
    def decorated_function():
        return slow_recursive_function(20)
        
    decorated_function()
    
    # Method 4: Using the cpu_profiler context manager
    print("\n--- Method 4: Using the cpu_profiler context manager ---")
    with cpu_profiler(top_n=5) as profiler:
        slow_recursive_function(20)
        
def demonstrate_memory_profiling():
    """Demonstrate memory profiling."""
    print("\n===== Memory Profiling Demonstration =====")
    
    try:
        # Method 1: Using the MemoryProfiler class directly
        print("\n--- Method 1: Using the MemoryProfiler class directly ---")
        profiler = MemoryProfiler(interval=0.1)
        profiler.start()
        memory_intensive_function(100000)
        profiler.stop()
        profiler.print_stats()
        
        # Method 2: Using the profile_func method
        print("\n--- Method 2: Using the profile_func method ---")
        profiler = MemoryProfiler(interval=0.1)
        profiler.profile_func(memory_intensive_function, 100000)
        profiler.print_stats()
        
        # Method 3: Using the profile_memory decorator
        print("\n--- Method 3: Using the profile_memory decorator ---")
        
        @profile_memory()
        def decorated_memory_function():
            return memory_intensive_function(100000)
            
        decorated_memory_function()
        
        # Method 4: Using the memory_profiler context manager
        print("\n--- Method 4: Using the memory_profiler context manager ---")
        with memory_profiler() as profiler:
            memory_intensive_function(100000)
            
    except ImportError as e:
        print(f"Memory profiling could not be demonstrated: {e}")
        print("Please install memory_profiler package to use this functionality")
        
def demonstrate_line_profiling():
    """Demonstrate line-by-line profiling."""
    print("\n===== Line Profiling Demonstration =====")
    
    try:
        # Method 1: Using the LineProfiler class directly
        print("\n--- Method 1: Using the LineProfiler class directly ---")
        profiler = LineProfiler()
        profiler.add_function(complex_algorithm)
        profiler.enable()
        complex_algorithm(list(range(1000)), 3)
        profiler.disable()
        profiler.print_stats()
        
        # Method 2: Using the profile_func method
        print("\n--- Method 2: Using the profile_func method ---")
        profiler = LineProfiler()
        profiler.profile_func(complex_algorithm, list(range(1000)), 3)
        profiler.print_stats()
        
        # Method 3: Using the profile_line decorator
        print("\n--- Method 3: Using the profile_line decorator ---")
        
        @profile_line()
        def decorated_line_function():
            return complex_algorithm(list(range(1000)), 3)
            
        decorated_line_function()
        
        # Method 4: Using the line_profiler context manager
        print("\n--- Method 4: Using the line_profiler context manager ---")
        with line_profiler(func_to_profile=complex_algorithm) as profiler:
            complex_algorithm(list(range(1000)), 3)
            
        # Example of finding hotspots
        print("\n--- Finding Line Hotspots ---")
        profiler = LineProfiler()
        profiler.profile_func(complex_algorithm, list(range(1000)), 3)
        hotspots = profiler.get_hotspots(n=3)
        print(f"Top {len(hotspots)} hotspots:")
        for i, spot in enumerate(hotspots):
            print(f"{i+1}. Line {spot['line']}: {spot['content']} - {spot['time']:.6f}s ({spot['percentage']:.1f}%)")
            
    except ImportError as e:
        print(f"Line profiling could not be demonstrated: {e}")
        print("Please install line_profiler package to use this functionality")
        
def demonstrate_comprehensive_profiling():
    """Demonstrate comprehensive profiling with all profilers."""
    print("\n===== Comprehensive Profiling Demonstration =====")
    
    try:
        # Create a temporary directory for saving profile results
        import tempfile
        output_dir = tempfile.mkdtemp()
        print(f"Profile results will be saved to: {output_dir}")
        
        # Method 1: Using the ProfileManager directly
        print("\n--- Method 1: Using the ProfileManager directly ---")
        profile_manager = ProfileManager()
        profile_manager.profile_func(
            complex_algorithm, 
            [randint(1, 100) for _ in range(500)], 
            3
        )
        profile_manager.print_stats()
        
        # Method 2: Using the profile_all decorator
        print("\n--- Method 2: Using the profile_all decorator ---")
        
        @profile_all(save_dir=output_dir, prefix="comprehensive")
        def complex_combined_function():
            # Do some CPU intensive work
            fib_result = slow_recursive_function(20)
            
            # Do some memory intensive work
            mem_result = memory_intensive_function(50000)
            
            # Do some complex algorithmic work
            alg_result = complex_algorithm([i for i in range(500)], 3)
            
            return fib_result, mem_result, alg_result
            
        complex_combined_function()
        
        # Show recommendations
        print("\n--- Optimization Recommendations ---")
        profile_manager = ProfileManager()
        profile_manager.profile_func(complex_algorithm, list(range(1000)), 3)
        recommendations = profile_manager.get_recommendations()
        
        for category, items in recommendations.items():
            if items:
                print(f"\n{category.upper()}:")
                for item in items:
                    print(f"  - {item}")
                    
        print(f"\nProfile files saved to: {output_dir}")
        
    except Exception as e:
        print(f"Comprehensive profiling could not be demonstrated: {e}")
        
if __name__ == "__main__":
    demonstrate_cpu_profiling()
    demonstrate_memory_profiling()
    demonstrate_line_profiling()
    demonstrate_comprehensive_profiling()
