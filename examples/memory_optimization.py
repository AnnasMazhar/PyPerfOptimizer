"""
Memory optimization example using PyPerfOptimizer.

This example demonstrates how to identify and optimize memory usage
in Python code using the PyPerfOptimizer package.
"""

import os
import sys
import time
import random
from functools import lru_cache

# Add src directory to path to import pyperfoptimizer in examples
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from pyperfoptimizer.profiler import MemoryProfiler, ProfileManager
from pyperfoptimizer.utils.decorators import profile_memory
from pyperfoptimizer.utils.context_managers import memory_profiler
from pyperfoptimizer.visualizer import MemoryVisualizer
from pyperfoptimizer.optimizer import Recommendations

# Example 1: Memory leak in a class
class LeakyClass:
    """A class that demonstrates a memory leak through a class variable."""
    
    _history = []  # Class variable that accumulates data
    
    def __init__(self, name):
        self.name = name
        
    def add_data(self, data):
        """Add data to the history."""
        LeakyClass._history.append((self.name, data))
        
    def process(self, items):
        """Process a list of items."""
        result = []
        for item in items:
            result.append(item * 2)
            # Store processing history
            self.add_data(f"Processed {item} to {item * 2}")
        return result
        
class OptimizedClass:
    """An optimized version of LeakyClass with proper memory management."""
    
    def __init__(self, name, max_history=100):
        self.name = name
        self.history = []  # Instance variable instead of class variable
        self.max_history = max_history
        
    def add_data(self, data):
        """Add data to the history with a fixed size limit."""
        self.history.append((self.name, data))
        # Limit the history size
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
            
    def process(self, items):
        """Process a list of items."""
        result = []
        for item in items:
            result.append(item * 2)
            # Store processing history
            self.add_data(f"Processed {item} to {item * 2}")
        return result

# Example 2: Memory inefficient list operations
def inefficient_list_builder(n):
    """Build a list inefficiently using += for concatenation."""
    result = []
    for i in range(n):
        # Inefficient: creates a new list each time
        result += [i * 2]
    return result

def efficient_list_builder(n):
    """Build a list efficiently using append."""
    result = []
    for i in range(n):
        # Efficient: appends in place
        result.append(i * 2)
    return result

def very_efficient_list_builder(n):
    """Build a list very efficiently using a list comprehension."""
    return [i * 2 for i in range(n)]

# Example 3: Memory leak with closures and mutable defaults
def create_leaky_function(data=[]):  # Mutable default!
    """Create a function that has a memory leak due to mutable default arguments."""
    def append_data(value):
        data.append(value)
        return data
    return append_data

def create_optimized_function(initial_data=None):
    """Create a function that properly handles mutable defaults."""
    if initial_data is None:
        data = []
    else:
        data = list(initial_data)  # Make a copy
        
    def append_data(value):
        data.append(value)
        return data
    return append_data

# Example 4: Memory-intensive recursion vs. dynamic programming
def recursive_fibonacci(n):
    """Compute Fibonacci number using naive recursion (memory-intensive)."""
    if n <= 1:
        return n
    return recursive_fibonacci(n-1) + recursive_fibonacci(n-2)

@lru_cache(maxsize=None)
def memoized_fibonacci(n):
    """Compute Fibonacci number using memoization (memory-efficient)."""
    if n <= 1:
        return n
    return memoized_fibonacci(n-1) + memoized_fibonacci(n-2)

def iterative_fibonacci(n):
    """Compute Fibonacci number iteratively (very memory-efficient)."""
    if n <= 1:
        return n
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b

def demonstrate_memory_leak():
    """Demonstrate and analyze a memory leak."""
    print("\n===== Memory Leak Demonstration =====")
    
    # Use the memory_profiler context manager
    with memory_profiler() as profiler:
        # Create instances and process data
        objects = []
        for i in range(100):
            obj = LeakyClass(f"Object-{i}")
            obj.process([random.randint(1, 100) for _ in range(100)])
            objects.append(obj)
            
            # Force some garbage collection to show only the leak
            if i % 10 == 0:
                # Clear local references
                objects = objects[-10:]
                
    # Get memory stats
    memory_stats = profiler.get_stats()
    
    # Create a visualizer and plot memory usage
    visualizer = MemoryVisualizer()
    visualizer.plot_memory_usage(memory_stats)
    
    # Generate recommendations
    recommender = Recommendations()
    recommendations = recommender.generate_from_memory_profile(memory_stats)
    
    # Print recommendations
    print("\nMemory Optimization Recommendations:")
    for rec in recommendations:
        print(f"- {rec}")
        
    # Show optimized version
    print("\n--- Using Optimized Class ---")
    with memory_profiler() as profiler:
        # Create instances and process data
        objects = []
        for i in range(100):
            obj = OptimizedClass(f"Object-{i}", max_history=10)
            obj.process([random.randint(1, 100) for _ in range(100)])
            objects.append(obj)
            
            # Same garbage collection pattern
            if i % 10 == 0:
                objects = objects[-10:]
                
    # Plot optimized memory usage
    visualizer.plot_memory_usage(profiler.get_stats())

def compare_list_building_methods():
    """Compare different methods of building lists."""
    print("\n===== List Building Methods Comparison =====")
    
    n = 100000
    
    # Compare inefficient vs efficient list building
    print(f"\nBuilding lists of size {n}:")
    
    # Profile inefficient list builder
    print("\n--- Inefficient List Builder ---")
    with memory_profiler() as profiler:
        result = inefficient_list_builder(n)
        
    # Get memory stats
    inefficient_stats = profiler.get_stats()
    print(f"Memory increase: {inefficient_stats.get('memory_increase', 0):.2f} MB")
    
    # Profile efficient list builder
    print("\n--- Efficient List Builder ---")
    with memory_profiler() as profiler:
        result = efficient_list_builder(n)
        
    # Get memory stats
    efficient_stats = profiler.get_stats()
    print(f"Memory increase: {efficient_stats.get('memory_increase', 0):.2f} MB")
    
    # Profile very efficient list builder
    print("\n--- Very Efficient List Builder (List Comprehension) ---")
    with memory_profiler() as profiler:
        result = very_efficient_list_builder(n)
        
    # Get memory stats
    very_efficient_stats = profiler.get_stats()
    print(f"Memory increase: {very_efficient_stats.get('memory_increase', 0):.2f} MB")
    
    # Create visualization comparing all three
    visualizer = MemoryVisualizer()
    
    # Create a side-by-side visualization
    import matplotlib.pyplot as plt
    plt.figure(figsize=(12, 6))
    
    # Plot all on the same graph with labels
    plt.plot(inefficient_stats['timestamps'], inefficient_stats['memory_mb'], 
             label='Inefficient (+= operator)')
    plt.plot(efficient_stats['timestamps'], efficient_stats['memory_mb'], 
             label='Efficient (append method)')
    plt.plot(very_efficient_stats['timestamps'], very_efficient_stats['memory_mb'], 
             label='Very Efficient (list comprehension)')
    
    plt.xlabel('Time (seconds)')
    plt.ylabel('Memory Usage (MB)')
    plt.title('Memory Usage Comparison: List Building Methods')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()

def demonstrate_mutable_defaults():
    """Demonstrate memory issues with mutable default arguments."""
    print("\n===== Mutable Default Arguments =====")
    
    # Create leaky functions
    leaky_func1 = create_leaky_function()
    leaky_func2 = create_leaky_function()  # Shares the same default list!
    
    # Create optimized functions
    optimized_func1 = create_optimized_function()
    optimized_func2 = create_optimized_function()  # Different list
    
    # Demonstrate the leak
    print("\n--- Using leaky functions ---")
    print("Initial leaky_func1:", leaky_func1(1))
    print("Initial leaky_func2:", leaky_func2(2))
    print("After adding to leaky_func1:", leaky_func1(3))
    print("leaky_func2 is affected:", leaky_func2(4))
    
    # Demonstrate the fix
    print("\n--- Using optimized functions ---")
    print("Initial optimized_func1:", optimized_func1(1))
    print("Initial optimized_func2:", optimized_func2(2))
    print("After adding to optimized_func1:", optimized_func1(3))
    print("optimized_func2 is not affected:", optimized_func2(4))
    
    # Memory profile numerous function creation and usage
    print("\n--- Memory profiling of function creation and use ---")
    
    def use_leaky_functions(n):
        """Create and use many leaky functions."""
        functions = []
        for i in range(n):
            func = create_leaky_function()
            for j in range(10):
                func(f"Data-{i}-{j}")
            functions.append(func)
        return functions
    
    def use_optimized_functions(n):
        """Create and use many optimized functions."""
        functions = []
        for i in range(n):
            func = create_optimized_function()
            for j in range(10):
                func(f"Data-{i}-{j}")
            functions.append(func)
        return functions
    
    # Profile leaky functions
    with memory_profiler() as profiler:
        leaky_functions = use_leaky_functions(1000)
    
    leaky_stats = profiler.get_stats()
    
    # Profile optimized functions
    with memory_profiler() as profiler:
        optimized_functions = use_optimized_functions(1000)
    
    optimized_stats = profiler.get_stats()
    
    # Compare memory usage
    print(f"Leaky functions memory increase: {leaky_stats.get('memory_increase', 0):.2f} MB")
    print(f"Optimized functions memory increase: {optimized_stats.get('memory_increase', 0):.2f} MB")

def compare_fibonacci_implementations():
    """Compare different Fibonacci implementations for memory usage."""
    print("\n===== Fibonacci Implementations Comparison =====")
    
    # Test parameters
    n = 30  # Fibonacci number to compute
    
    # Recursive Fibonacci (very inefficient)
    print(f"\nComputing Fibonacci({n}):")
    
    print("\n--- Recursive Fibonacci (Memory-Intensive) ---")
    with memory_profiler() as profiler:
        start = time.time()
        result = recursive_fibonacci(n)
        end = time.time()
    
    recursive_stats = profiler.get_stats()
    print(f"Result: {result}")
    print(f"Time taken: {end - start:.4f} seconds")
    print(f"Memory increase: {recursive_stats.get('memory_increase', 0):.2f} MB")
    
    # Memoized Fibonacci
    print("\n--- Memoized Fibonacci (Memory-Efficient) ---")
    with memory_profiler() as profiler:
        start = time.time()
        result = memoized_fibonacci(n)
        end = time.time()
    
    memoized_stats = profiler.get_stats()
    print(f"Result: {result}")
    print(f"Time taken: {end - start:.4f} seconds")
    print(f"Memory increase: {memoized_stats.get('memory_increase', 0):.2f} MB")
    
    # Iterative Fibonacci
    print("\n--- Iterative Fibonacci (Very Memory-Efficient) ---")
    with memory_profiler() as profiler:
        start = time.time()
        result = iterative_fibonacci(n)
        end = time.time()
    
    iterative_stats = profiler.get_stats()
    print(f"Result: {result}")
    print(f"Time taken: {end - start:.4f} seconds")
    print(f"Memory increase: {iterative_stats.get('memory_increase', 0):.2f} MB")
    
    # Visualize memory usage
    visualizer = MemoryVisualizer()
    
    # Create a side-by-side visualization
    import matplotlib.pyplot as plt
    plt.figure(figsize=(12, 6))
    
    # Normalize the timescales
    def normalize_times(data):
        return [t - data['timestamps'][0] for t in data['timestamps']]
    
    # Plot all on the same graph with labels
    plt.plot(normalize_times(recursive_stats), recursive_stats['memory_mb'], 
             label='Recursive (Memory-Intensive)')
    plt.plot(normalize_times(memoized_stats), memoized_stats['memory_mb'], 
             label='Memoized (Memory-Efficient)')
    plt.plot(normalize_times(iterative_stats), iterative_stats['memory_mb'], 
             label='Iterative (Very Memory-Efficient)')
    
    plt.xlabel('Time (seconds)')
    plt.ylabel('Memory Usage (MB)')
    plt.title(f'Memory Usage Comparison: Fibonacci({n}) Implementations')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    # Check if memory_profiler is available
    try:
        profiler = MemoryProfiler()
        
        # Run the demonstrations
        demonstrate_memory_leak()
        compare_list_building_methods()
        demonstrate_mutable_defaults()
        compare_fibonacci_implementations()
        
    except ImportError as e:
        print(f"ERROR: {e}")
        print("\nPlease install the memory_profiler package to run this example:")
        print("pip install memory_profiler")
