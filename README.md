# PyPerfOptimizer

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Versions](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://pypi.org/project/pyperfoptimizer/)

A comprehensive Python package for unified performance profiling, visualization, and optimization.

## Features

- **Unified Profiling Interface**: CPU, memory, and line-by-line profiling through a consistent API
- **Interactive Visualizations**: Rich, interactive data visualization for profiling results
- **Automated Optimization**: Intelligent code analysis and optimization recommendations
- **Web Dashboard**: Browser-based dashboard for profile data exploration
- **Decorator & Context Manager Support**: Simple API with multiple usage patterns
- **Export & Sharing**: Export results to various formats

## Installation

```bash
pip install pyperfoptimizer
```

## Quick Start

```python
from pyperfoptimizer import profile_cpu, profile_memory, profile_line

# Use decorators for quick profiling
@profile_cpu()
def cpu_intensive_function():
    # Your CPU-intensive code here
    pass

# Profile memory usage
@profile_memory()
def memory_intensive_function():
    # Your memory-intensive code here
    pass

# Profile line-by-line execution time
@profile_line()
def analyze_by_line():
    # Your code to analyze line by line
    pass
```

## Using the ProfileManager

```python
from pyperfoptimizer import ProfileManager

profiler = ProfileManager(
    enable_cpu=True,
    enable_memory=True,
    enable_line=True
)

def my_function():
    # Your code here
    pass

profiler.profile_func(my_function)

# Get profiling statistics
stats = profiler.get_stats()

# Get optimization recommendations
recommendations = profiler.get_recommendations()
```

## Interactive Dashboard

```python
from pyperfoptimizer import Dashboard

dashboard = Dashboard()
dashboard.set_profile_manager_data(profiler)

# Launch interactive dashboard
dashboard.launch(port=5000)

# Or save as standalone HTML
dashboard.save_html("my_profile_results.html")
```

## Context Managers

```python
from pyperfoptimizer import cpu_profiler, memory_profiler, line_profiler

with cpu_profiler() as prof:
    # Your CPU-intensive code here
    pass

with memory_profiler() as prof:
    # Your memory-intensive code here
    pass

with line_profiler(func_to_profile=my_function) as prof:
    my_function()
```

## Automated Optimization

```python
from pyperfoptimizer.optimizers import optimize, optimize_function

@optimize(memoize=True, parallelize=True)
def slow_function(data):
    # Complex calculations
    pass

# Or transform an existing function
optimized_func = optimize_function(
    original_function,
    optimize_loops=True,
    batch_operations=True
)
```

## Examples

See the `examples/` directory for comprehensive examples:

- `examples/simple_profiling.py` — Basic profiling usage
- `examples/memory_optimization.py` — Memory optimization patterns
- `examples/integrated_dashboard.py` — Dashboard integration
- `examples/automation_example.py` — Automation workflows

## Documentation

### User Guides

- [Getting Started](docs/getting_started.md)
- [API Reference](docs/api_reference.md)
- [Dashboard Guide](docs/dashboard_guide.md)
- [Optimization Guide](docs/optimization_guide.md)

### Performance Test Results

- [Summary](docs/test_results/summary.md)
- [CPU Profiler Tests](docs/test_results/cpu_profiler_tests.md)
- [Memory Profiler Tests](docs/test_results/memory_profiler_tests.md)
- [Line Profiler Tests](docs/test_results/line_profiler_tests.md)
- [Case Studies](docs/test_results/optimization_case_studies.md)
- [Methodology](docs/test_results/methodology.md)

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
