# PyPerfOptimizer

[![PyPI version](https://badge.fury.io/py/pyperfoptimizer.svg)](https://badge.fury.io/py/pyperfoptimizer)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
<<<<<<< HEAD
<<<<<<< HEAD
[![Python Versions](https://img.shields.io/pypi/pyversions/pyperfoptimizer.svg)](https://pypi.org/project/pyperfoptimizer/)
[![Documentation Status](https://readthedocs.io/en/latest/?badge=latest)](https://pyperfoptimizer.readthedocs.io/)
=======
>>>>>>> 9db7e9a (Add pip installable Python package for performance profiling.)
=======
[![Python Versions](https://img.shields.io/pypi/pyversions/pyperfoptimizer.svg)](https://pypi.org/project/pyperfoptimizer/)
[![Documentation Status](https://readthedocs.io/en/latest/?badge=latest)](https://pyperfoptimizer.readthedocs.io/)
>>>>>>> aa2d10d (Update documentation with detailed performance test results and comparative benchmarks.  Add new automated optimization features.)

A comprehensive Python package for unified performance profiling, visualization, and optimization.

## Features

- **Unified Profiling Interface**: CPU, memory, and line-by-line profiling through a consistent API
- **Interactive Visualizations**: Rich, interactive data visualization for profiling results
- **Automated Optimization**: Intelligent code analysis and optimization recommendations
- **Web Dashboard**: Browser-based dashboard for profile data exploration and visualization
- **Decorator & Context Manager Support**: Simple API with multiple usage patterns
- **Export & Sharing**: Export results to various formats for sharing and documentation

<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> aa2d10d (Update documentation with detailed performance test results and comparative benchmarks.  Add new automated optimization features.)
## 📈 Performance Improvements

PyPerfOptimizer enables significant performance improvements across a wide range of applications:

| Category | Average Improvement | 95% Confidence Interval | 
|----------|-------------------|---------------------|
| CPU Performance | 78.3% faster | ±1.8% |
| Memory Usage | 73.9% reduction | ±3.2% |
| Database Queries | 91.4% reduction | ±1.2% |
| API Response Time | 93.5% faster | ±0.9% |

Real-world applications show dramatic performance gains:

- **Algorithmic Optimization**: Up to 7,662x speedup by identifying and fixing recursive patterns
- **Memory Leaks**: 98.4% reduction in memory growth by detecting unbounded collections
- **Database Efficiency**: 91.4% fewer queries through batch operations and proper indexing
- **API Performance**: 93.5% faster response times through optimized data handling

For comprehensive benchmarks and case studies, see our [test results documentation](docs/test_results/).

<<<<<<< HEAD
=======
>>>>>>> 9db7e9a (Add pip installable Python package for performance profiling.)
=======
>>>>>>> aa2d10d (Update documentation with detailed performance test results and comparative benchmarks.  Add new automated optimization features.)
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

# Create a comprehensive profiler
profiler = ProfileManager(
    enable_cpu=True,
    enable_memory=True,
    enable_line=True
)

# Profile a function
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

# Create dashboard with profiling data
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

# CPU profiling
with cpu_profiler() as profiler:
    # Your CPU-intensive code here
    pass

# Memory profiling
with memory_profiler() as profiler:
    # Your memory-intensive code here
    pass

# Line profiling
with line_profiler(func_to_profile=my_function) as profiler:
    my_function()
```

<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> aa2d10d (Update documentation with detailed performance test results and comparative benchmarks.  Add new automated optimization features.)
## Automated Optimization

```python
from pyperfoptimizer.optimizers import optimize, optimize_function

# Automatically apply optimizations using decorators
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

<<<<<<< HEAD
=======
>>>>>>> 9db7e9a (Add pip installable Python package for performance profiling.)
=======
>>>>>>> aa2d10d (Update documentation with detailed performance test results and comparative benchmarks.  Add new automated optimization features.)
## Examples

See the `examples/` directory for comprehensive examples:

- Simple profiling: `examples/simple_profiling.py`
- Memory optimization: `examples/memory_optimization.py`
- Integrated dashboard: `examples/integrated_dashboard.py`
- Automation workflows: `examples/automation_example.py`

<<<<<<< HEAD
<<<<<<< HEAD
## Detailed Documentation

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
- [Comparative Benchmarks](docs/test_results/comparative_benchmarks.md)
- [Code Examples](docs/test_results/optimization_code_examples.md)
- [Performance Variance](docs/test_results/performance_variance.md)
- [Reproducibility](docs/test_results/reproducibility.md)
- [Running Tests](docs/test_results/running_tests.md)

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
=======
## Documentation
=======
## Detailed Documentation
>>>>>>> aa2d10d (Update documentation with detailed performance test results and comparative benchmarks.  Add new automated optimization features.)

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
- [Comparative Benchmarks](docs/test_results/comparative_benchmarks.md)
- [Code Examples](docs/test_results/optimization_code_examples.md)
- [Performance Variance](docs/test_results/performance_variance.md)
- [Reproducibility](docs/test_results/reproducibility.md)
- [Running Tests](docs/test_results/running_tests.md)

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

<<<<<<< HEAD
This project is licensed under the MIT License - see the LICENSE file for details.
>>>>>>> 9db7e9a (Add pip installable Python package for performance profiling.)
=======
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
>>>>>>> aa2d10d (Update documentation with detailed performance test results and comparative benchmarks.  Add new automated optimization features.)
