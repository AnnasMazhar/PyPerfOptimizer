# Running Tests with PyPerfOptimizer

This document provides instructions for running performance tests using PyPerfOptimizer and interpreting the results. The examples included demonstrate how the package helps you identify and solve performance bottlenecks in your Python code.

## Prerequisites

Before running the tests, ensure you have PyPerfOptimizer installed:

```bash
pip install pyperfoptimizer
```

## Basic Usage

### Command Line Interface

PyPerfOptimizer provides a command-line interface for quick profiling:

```bash
# Profile a Python file
pyperfoptimizer profile example.py

# Profile a specific function within a file
pyperfoptimizer profile example.py -f slow_function

# Profile with specific profilers
pyperfoptimizer profile example.py --cpu --memory

# Launch the dashboard with results
pyperfoptimizer dashboard --results-dir profile_results/
```

### Python API

You can also use PyPerfOptimizer directly in your Python code:

```python
from pyperfoptimizer import ProfileManager, Dashboard
from pyperfoptimizer.decorators import profile_cpu, profile_memory, profile_line

# Method 1: Using the ProfileManager
profiler = ProfileManager(enable_cpu=True, enable_memory=True, enable_line=True)
result = profiler.profile_func(slow_function, *args, **kwargs)

# Get results and recommendations
stats = profiler.get_stats()
recommendations = profiler.get_recommendations()

# Method 2: Using decorators
@profile_cpu()
def my_cpu_intensive_function():
    # Function code
    pass

@profile_memory()
def my_memory_intensive_function():
    # Function code
    pass

@profile_line()
def my_function_with_line_profiling():
    # Function code
    pass
```

## Example Test: Fibonacci Performance Comparison

This example compares different implementations of the Fibonacci sequence calculator:

```python
# Create a test file: fibonacci_test.py
from pyperfoptimizer import ProfileManager
import time

def fibonacci_recursive(n):
    """Recursive Fibonacci implementation (inefficient)."""
    if n <= 1:
        return n
    else:
        return fibonacci_recursive(n-1) + fibonacci_recursive(n-2)

def fibonacci_memoized(n, memo={}):
    """Memoized Fibonacci implementation (efficient)."""
    if n in memo:
        return memo[n]
    if n <= 1:
        return n
    else:
        memo[n] = fibonacci_memoized(n-1, memo) + fibonacci_memoized(n-2, memo)
        return memo[n]

def fibonacci_iterative(n):
    """Iterative Fibonacci implementation (most efficient)."""
    if n <= 1:
        return n
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b

def run_test():
    # Create profile manager
    profiler = ProfileManager(enable_cpu=True, enable_memory=True, enable_line=True)
    
    # Profile recursive implementation
    profiler.profile_func(fibonacci_recursive, 30)
    recursive_stats = profiler.get_stats()
    
    # Profile memoized implementation
    profiler.clear()
    profiler.profile_func(fibonacci_memoized, 30)
    memoized_stats = profiler.get_stats()
    
    # Profile iterative implementation
    profiler.clear()
    profiler.profile_func(fibonacci_iterative, 30)
    iterative_stats = profiler.get_stats()
    
    # Print results
    print("=== Fibonacci Performance Comparison ===")
    print(f"Recursive: {recursive_stats['cpu']['total_time']:.6f}s, {recursive_stats['memory']['peak_memory']:.2f}MB")
    print(f"Memoized:  {memoized_stats['cpu']['total_time']:.6f}s, {memoized_stats['memory']['peak_memory']:.2f}MB")
    print(f"Iterative: {iterative_stats['cpu']['total_time']:.6f}s, {iterative_stats['memory']['peak_memory']:.2f}MB")
    
    # Get recommendations
    recommendations = profiler.get_recommendations()
    print("\n=== Optimization Recommendations ===")
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec.title}: {rec.description}")
    
    # Launch dashboard
    dashboard = Dashboard()
    dashboard.set_profile_data(profiler)
    dashboard.launch(port=5000)

if __name__ == "__main__":
    run_test()
```

### Running the Test

```bash
python fibonacci_test.py
```

### Sample Output

```
=== Fibonacci Performance Comparison ===
Recursive: 0.832156s, 14.25MB
Memoized:  0.000213s, 0.08MB
Iterative: 0.000012s, 0.05MB

=== Optimization Recommendations ===
1. Replace recursive algorithm: The recursive implementation shows exponential time complexity. Consider using memoization or an iterative approach.
2. Memory usage concern: The recursive implementation uses significantly more memory than alternatives. This indicates excessive stack frame creation.
3. Reduce function call overhead: The recursive implementation makes 2,692,537 function calls, while the iterative makes just 1.
```

## Example Dashboard

After running the test, a dashboard will launch at http://localhost:5000 showing:

1. **Overview Tab**: Summary statistics and key findings
2. **CPU Profiling Tab**: Function call graph, hotspots, and call hierarchy
3. **Memory Profiling Tab**: Memory usage over time, allocation patterns
4. **Line Profiling Tab**: Line-by-line execution times with heatmap
5. **Recommendations Tab**: Suggested optimizations with code examples

## Interpreting the Results

### CPU Profiler Results

The CPU profiler shows which functions consume the most CPU time:

```
Function Call Profile:
- fibonacci_recursive: 0.832156s (99.7% of total time)
  - 2,692,537 function calls
  - 0.000000309s per call (recursive)
  
Hotspots:
1. fibonacci_recursive: 0.832156s (99.7%)
2. run_test: 0.002134s (0.3%)
```

### Memory Profiler Results

The memory profiler shows memory usage patterns:

```
Memory Usage Profile:
- Baseline: 8.12 MB
- Peak: 14.25 MB (recursive), 0.08 MB (memoized), 0.05 MB (iterative)
- Growth pattern: Exponential growth in recursive implementation
- No memory leaks detected
```

### Line Profiler Results

The line profiler shows execution time for each line:

```
Line-by-Line Profile for fibonacci_recursive:
Line #  Hits         Time  Per Hit   % Time  Line Contents
------------------------------------------------------
1       1           0.5      0.5      0.0    def fibonacci_recursive(n):
2       2692537     536.1    0.0      0.1        if n <= 1:
3       1346269     402.9    0.0      0.0            return n
4                                              else:
5       1346268   830804.8   0.6     99.9            return fibonacci_recursive(n-1) + fibonacci_recursive(n-2)
```

## Custom Test Scenarios

You can create custom test scenarios to profile your specific code:

1. **API Performance Testing**:
   ```python
   profiler.profile_func(api_handler.process_request, test_request)
   ```

2. **Data Processing Optimization**:
   ```python
   profiler.profile_func(data_processor.transform_data, large_dataset)
   ```

3. **Database Query Analysis**:
   ```python
   profiler.profile_func(db_manager.get_user_report, user_id, start_date, end_date)
   ```

## Continuous Integration Testing

You can integrate PyPerfOptimizer into your CI pipeline to catch performance regressions:

```yaml
# In your GitHub Actions workflow
jobs:
  performance_test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          pip install pyperfoptimizer
      - name: Run performance tests
        run: |
          pyperfoptimizer profile tests/performance_tests.py --ci-mode
          # Will fail if performance degrades beyond thresholds
```

## Export and Sharing

You can export profiling results for sharing or archiving:

```python
# In Python
profiler.save_stats('profile_results.json')

# Later or in another process
new_profiler = ProfileManager()
new_profiler.load_stats('profile_results.json')
```

## Tips for Effective Profiling

1. **Profile with realistic data**: Use data that represents your production workload
2. **Focus on hotspots**: Optimize the 20% of code that causes 80% of performance issues
3. **Compare implementations**: Test different approaches to see their relative performance
4. **Check all dimensions**: Look at CPU, memory, and line-level performance
5. **Run multiple times**: Average results to account for variance
6. **Validate optimizations**: Re-profile after changes to confirm improvements

By using PyPerfOptimizer to run these tests, you'll gain comprehensive insights into your code's performance characteristics, helping you identify and fix bottlenecks efficiently.