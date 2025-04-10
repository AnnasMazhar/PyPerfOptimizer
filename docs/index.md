# PyPerfOptimizer Documentation

## Introduction

PyPerfOptimizer is a comprehensive Python package for unified performance profiling, visualization, and optimization. It provides tools for CPU, memory, and line-by-line code profiling, as well as visualization and optimization recommendations.

## Installation

```bash
pip install pyperfoptimizer
```

## Core Components

### 1. Profiler

The profiler component provides tools for CPU, memory, and line-by-line profiling:

```python
from pyperfoptimizer import profile_cpu, profile_memory, profile_line

# CPU profiling
@profile_cpu()
def my_function():
    # Your code here
    pass

# Memory profiling
@profile_memory()
def memory_intensive_function():
    # Your code here
    pass

# Line profiling
@profile_line()
def analyze_by_line():
    # Your code here
    pass
```

### 2. Visualizer

The visualizer component provides tools for visualizing profiling results:

```python
from pyperfoptimizer import Dashboard, CPUVisualizer, MemoryVisualizer

# Create visualizers
cpu_vis = CPUVisualizer()
memory_vis = MemoryVisualizer()

# Create a dashboard
dashboard = Dashboard()
dashboard.set_profile_manager_data(profiler)
dashboard.launch(port=5000)
```

### 3. Optimizer

The optimizer component provides tools for analyzing code and suggesting optimizations:

```python
from pyperfoptimizer import CodeAnalyzer, Recommendations

# Analyze code
analyzer = CodeAnalyzer()
code_analysis = analyzer.analyze_function(my_function)

# Generate recommendations
recommender = Recommendations()
recommendations = recommender.generate_from_code_analysis(code_analysis)
```

## Command Line Interface

PyPerfOptimizer also provides a command-line interface:

```bash
# Profile a Python file
pyperfoptimizer profile example.py

# Profile a specific function
pyperfoptimizer profile example.py -f my_function

# Launch the dashboard
pyperfoptimizer dashboard -d results_dir
```

## Examples

See the [examples](https://github.com/yourusername/pyperfoptimizer/tree/main/examples) directory for comprehensive examples.

## API Reference

### ProfileManager

```python
from pyperfoptimizer import ProfileManager

profiler = ProfileManager(
    enable_cpu=True,
    enable_memory=True,
    enable_line=True
)

# Profile a function
profiler.profile_func(my_function)

# Get profiling statistics
stats = profiler.get_stats()

# Get optimization recommendations
recommendations = profiler.get_recommendations()
```

### Dashboard

```python
from pyperfoptimizer import Dashboard

dashboard = Dashboard(port=5000)
dashboard.set_profile_manager_data(profiler)
dashboard.launch()
```

### CLI

```bash
pyperfoptimizer profile example.py
pyperfoptimizer dashboard -d results_dir
pyperfoptimizer version
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.