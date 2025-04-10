# Reproducibility Guide

This document provides detailed instructions for reproducing the performance tests and benchmarks for PyPerfOptimizer. We provide a Docker environment, dependency specifications, and step-by-step guides to ensure consistent results.

## Docker Environment

The following Dockerfile creates a reproducible environment for running all benchmarks:

```dockerfile
FROM python:3.11.4-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV LANG=C.UTF-8
ENV TZ=UTC

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    sqlite3 \
    libsqlite3-dev \
    && rm -rf /var/lib/apt/lists/*

# Set up a non-root user
RUN useradd -m -d /app -s /bin/bash benchmark
WORKDIR /app
USER benchmark

# Create virtual environment
RUN python -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

# Install Python dependencies
COPY --chown=benchmark:benchmark requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy benchmark code
COPY --chown=benchmark:benchmark benchmarks/ benchmarks/
COPY --chown=benchmark:benchmark data/ data/
COPY --chown=benchmark:benchmark scripts/ scripts/

# Set up entry point
ENTRYPOINT ["python", "scripts/run_benchmarks.py"]
```

## Dependencies

The exact dependencies used for all benchmarks are specified in the requirements.txt file:

```
# Core dependencies
pyperfoptimizer==1.0.0
numpy==1.24.3
pandas==2.0.3
scikit-learn==1.3.0
matplotlib==3.7.2
plotly==5.15.0
pydantic==2.0.3
orjson==3.9.1

# Database dependencies
sqlalchemy==2.0.19
psycopg2-binary==2.9.6
pymysql==1.1.0
sqlite-utils==3.35

# Web framework dependencies
flask==2.3.2
django==4.2.3
fastapi==0.100.0
uvicorn==0.22.0

# Testing and benchmarking
pytest==7.4.0
pytest-benchmark==4.0.0
memory-profiler==0.61.0
line-profiler==4.1.1
py-spy==0.3.14
asv==0.6.1

# Comparison libraries
scalene==1.5.20
pyinstrument==4.6.0
```

## Raw Benchmark Data

All raw benchmark data is available for independent verification and analysis:

1. **CSV Format Data**: [pyperfoptimizer-benchmarks/raw_data](https://github.com/AnnasMazhar/pyperfoptimizer-benchmarks/tree/main/raw_data)
2. **JSON Results**: [pyperfoptimizer-benchmarks/json_results](https://github.com/AnnasMazhar/pyperfoptimizer-benchmarks/tree/main/json_results)
3. **Jupyter Notebooks**: [pyperfoptimizer-benchmarks/notebooks](https://github.com/AnnasMazhar/pyperfoptimizer-benchmarks/tree/main/notebooks)

## Step-by-Step Reproduction

### 1. Build and Run the Docker Container

```bash
# Clone the repository
git clone https://github.com/AnnasMazhar/pyperfoptimizer-benchmarks.git
cd pyperfoptimizer-benchmarks

# Build the Docker image
docker build -t pyperfoptimizer-benchmarks .

# Run all benchmarks
docker run --rm pyperfoptimizer-benchmarks

# Run a specific benchmark category
docker run --rm pyperfoptimizer-benchmarks --category cpu_profiler
docker run --rm pyperfoptimizer-benchmarks --category memory_profiler
docker run --rm pyperfoptimizer-benchmarks --category line_profiler
docker run --rm pyperfoptimizer-benchmarks --category optimizations

# Run a specific benchmark
docker run --rm pyperfoptimizer-benchmarks --benchmark fibonacci
```

### 2. Running Without Docker

If you prefer to run without Docker, follow these steps:

```bash
# Clone the repository
git clone https://github.com/AnnasMazhar/pyperfoptimizer-benchmarks.git
cd pyperfoptimizer-benchmarks

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run all benchmarks
python scripts/run_benchmarks.py

# Run specific benchmarks
python scripts/run_benchmarks.py --category cpu_profiler
python scripts/run_benchmarks.py --benchmark fibonacci
```

### 3. Verifying Results

To verify the results match our published findings:

```bash
# Generate verification report
python scripts/verify_results.py --results-dir results/ --compare-with reference_results/

# The verification script will:
# 1. Compare your results with the reference results
# 2. Calculate the statistical significance of any differences
# 3. Generate a verification report in results/verification/
```

## Benchmark Structure

Each benchmark is structured as follows:

```python
class BenchmarkName:
    """Benchmark for specific functionality."""
    
    def setup(self):
        """Set up the benchmark environment."""
        # Initialize data, connections, etc.
        
    def teardown(self):
        """Clean up after the benchmark."""
        # Close connections, clean temporary files, etc.
        
    def time_original(self):
        """Time the original implementation."""
        # Run the original code
        
    def time_optimized(self):
        """Time the optimized implementation."""
        # Run the optimized code
        
    def track_memory_original(self):
        """Track memory usage of original implementation."""
        # Run the original code and measure memory
        
    def track_memory_optimized(self):
        """Track memory usage of optimized implementation."""
        # Run the optimized code and measure memory
```

## Data Sets

All benchmarks use the following datasets:

1. **Synthetic Data**:
   - Generated with fixed random seeds for reproducibility
   - Various sizes: small (1K), medium (100K), large (10M)
   - Located in `data/synthetic/`

2. **Public Datasets**:
   - UCI Machine Learning Repository datasets (unmodified)
   - Financial time series from Yahoo Finance (2010-2023)
   - Located in `data/public/`

3. **Database Data**:
   - SQL dumps for database benchmarks
   - Located in `data/databases/`

## Hardware Specifications

For reference, our benchmarks were executed on the following hardware:

```
CPU: AMD Ryzen 9 7950X (32 threads, 4.5GHz)
RAM: 64GB DDR5-6000
Storage: 2TB NVMe SSD (Samsung 990 Pro, 7000MB/s read, 5000MB/s write)
OS: Ubuntu 22.04 LTS
```

Results may vary on different hardware, but relative improvements should be similar.

## Customizing Benchmarks

To adapt the benchmarks to your own scenarios:

1. **Custom Data**:
   ```bash
   # Place your data in the custom_data directory
   mkdir -p data/custom/
   cp /path/to/your/data.csv data/custom/
   
   # Run benchmarks with custom data
   python scripts/run_benchmarks.py --data data/custom/data.csv
   ```

2. **Custom Code**:
   ```bash
   # Create a custom benchmark module
   cp benchmarks/templates/custom_benchmark.py.template benchmarks/custom_benchmark.py
   
   # Edit the file to include your code
   # Then run your custom benchmark
   python scripts/run_benchmarks.py --benchmark custom_benchmark
   ```

## Known Variations

The following conditions may cause variations in results:

1. **CPU Frequency Scaling**: Ensure consistent CPU governor settings
2. **System Load**: Run benchmarks on systems with minimal background processes
3. **Thermal Throttling**: Monitor CPU temperatures during long benchmark runs
4. **Memory Fragmentation**: Consider restarting the environment between benchmark sets
5. **I/O Contention**: Minimize disk and network activity during benchmarks

## Reporting Discrepancies

If you find significant discrepancies between your results and our published findings:

1. Run the verification script to quantify the differences
2. Check the troubleshooting guide in `docs/troubleshooting.md`
3. Submit an issue on GitHub with:
   - Your complete environment details (OS, hardware, Docker/native)
   - The full output of the verification script
   - Any modifications to the benchmark code or data

## Conclusion

This reproducibility guide ensures that all performance results can be independently verified. By following these procedures, you can validate the performance improvements reported for PyPerfOptimizer in your own environment and with your own data.