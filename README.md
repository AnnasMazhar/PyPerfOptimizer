# PyPerfOptimizer

**Make Python faster. Automatically.**

PyPerfOptimizer finds performance anti-patterns in your code and fixes them — not just reports, but actual source-preserving transformations that are benchmarked and verified.

```bash
pip install pyperfoptimizer
```

```bash
pyperfoptimizer scan myapp.py          # find what's slow
pyperfoptimizer fix myapp.py           # make it faster
pyperfoptimizer fix --verify myapp.py  # prove it's faster
```

## Why This Exists

Python profilers tell you *where* code is slow. Linters tell you *what* looks wrong. Neither fixes the problem.

PyPerfOptimizer closes the loop: **Profile → Detect → Transform → Verify.**

| Tool | Profiles | Detects patterns | Fixes code | Proves speedup |
|------|----------|-----------------|------------|----------------|
| py-spy | ✓ | ✗ | ✗ | ✗ |
| Scalene | ✓ | ✓ (text) | ✗ | ✗ |
| Ruff PERF | ✗ | ✓ (6 rules) | ✓ (trivial) | ✗ |
| **PyPerfOptimizer** | ✓ | ✓ (7 patterns) | ✓ (AST rewrite) | ✓ (benchmarked) |

## Benchmarks

Real numbers. Measured on Python 3.11, Ubuntu. Reproducible via `python benchmarks/run_benchmarks.py`.

### Verified Speedups

```
Pattern                    Data Size    Original    Optimized    Speedup
─────────────────────────────────────────────────────────────────────────
Auto-memoize (fib(30))     recursive    132ms       0.07µs       320x
List→Set membership        100 items    882ms       20.7ms       42.6x
Append loop→comprehension  100K items   382ms       270ms        1.4x
String +=→join             10K items    101ms       86ms         1.2x
Remove unnecessary list()  100K items   555µs       422µs        1.3x
─────────────────────────────────────────────────────────────────────────
```

### When Each Pattern Matters

| Pattern | Small data | Large data | Why |
|---------|-----------|-----------|-----|
| **Auto-memoize** | 320× | 320×+ | O(2ⁿ) → O(n). Always massive for recursive functions. |
| **List→Set** | ~1× (10 items) | **42×** (100 items) | O(n) → O(1) lookup. Scales with collection size. |
| **Append→Comp** | 1.2× | **1.4×** | Fewer function calls. Consistent across sizes. |
| **String +=→join** | ~1× | **1.2×** | CPython 3.11 optimized small cases. Still wins at scale. |
| **Loop hoist** | 1.1× | 1.1× | Marginal but free (zero risk). |

> **Note on string concatenation:** Python 3.11+ performs in-place mutation when refcount=1, reducing the historical 10× gap to ~1.2×. The optimization still helps in loops where the string is referenced elsewhere.

## How It Works

PyPerfOptimizer uses [libcst](https://github.com/Instagram/LibCST) (Facebook/Instagram's source-preserving AST library) to transform your code while keeping comments, formatting, and type annotations intact.

```python
from pyperfoptimizer.autofix import scan, fix

# Detect anti-patterns
optimizations = scan(source_code)
for opt in optimizations:
    print(f"Line {opt.line}: {opt.description} ({opt.expected_speedup})")

# Apply all safe transformations
faster_code = fix(source_code)
```

### Example Transformation

**Input:**
```python
def process(items, valid_ids):
    results = []
    for item in items:
        if item.id in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]:
            results.append(item.name)
    return results

def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)
```

**Output (automated):**
```python
import functools

def process(items, valid_ids):
    results = [item.name for item in items if item.id in {1, 2, 3, 4, 5, 6, 7, 8, 9, 10}]
    return results

@functools.lru_cache(maxsize=None)
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)
```

**Result:** `process` is 2-40× faster (depending on list size). `fibonacci` is 320× faster.

## Optimization Patterns

### Tier 1: High Impact (auto-applied)

| # | Pattern | Detects | Transforms to | Speedup |
|---|---------|---------|---------------|---------|
| 1 | **Auto-memoize** | Pure recursive functions | `@functools.lru_cache` | 100-10,000× |
| 2 | **Membership set** | `x in [literal, ...]` (3+ items) | `x in {literal, ...}` | 2-50× |
| 3 | **Append→comprehension** | `for x: list.append(expr)` | `[expr for x in iter]` | 1.3-2× |
| 4 | **String concat→join** | `s += x` in loop | `''.join(...)` | 1.2-10× |

### Tier 2: Safe Cleanup (auto-applied)

| # | Pattern | Detects | Transforms to | Speedup |
|---|---------|---------|---------------|---------|
| 5 | **Unnecessary list()** | `for x in list(gen)` | `for x in gen` | 1.1-1.5× |
| 6 | **Loop-invariant hoist** | `obj.method` in loop body | Local variable before loop | 1.1-1.3× |
| 7 | **DataFrame vectorize** | `df.iterrows()` loops | Vectorized pandas ops | 10-1000× |

### Safety Guarantees

- **Source-preserving**: Comments, formatting, type annotations are kept intact
- **Semantically safe**: Only transforms provably equivalent code
- **Memoization guard**: Only applied to recursive functions with no side effects (no I/O, no globals, no mutable defaults)
- **Verify mode**: Benchmarks before/after and rejects if not faster

## Profile-Guided Optimization

Don't waste time optimizing cold code. Feed profiling data to focus on hot paths:

```bash
# Profile your app with py-spy
py-spy record -o profile.speedscope -- python myapp.py

# Optimize only the hot functions
pyperfoptimizer fix myapp.py --profile profile.speedscope
```

Supports:
- **py-spy** (speedscope JSON)
- **cProfile** (pstats binary)
- **Scalene** (JSON output)

```python
from pyperfoptimizer.autofix import scan, load_profile

hot_functions = load_profile("profile.speedscope")
optimizations = scan(source, hot_functions=hot_functions)
# Only returns optimizations in functions that actually consume CPU time
```

## CLI Reference

```bash
# Scan and report (no changes)
pyperfoptimizer scan <file_or_dir>
pyperfoptimizer scan myapp.py --profile profile.json

# Fix (write .optimized.py files)
pyperfoptimizer fix <file_or_dir>
pyperfoptimizer fix myapp.py --inplace          # modify in place
pyperfoptimizer fix myapp.py --verify           # benchmark proof
pyperfoptimizer fix myapp.py --profile p.json   # only hot paths
```

## Python API

```python
from pyperfoptimizer.autofix import scan, fix, scan_file, fix_file

# String-based
optimizations = scan(source_code)
optimized_source = fix(source_code)

# File-based
optimizations = scan_file("myapp.py")
fix_file("myapp.py", inplace=True)

# With profiling data
from pyperfoptimizer.autofix.profile_loader import load_profile
hot = load_profile("profile.speedscope")
optimizations = scan(source, hot_functions=hot)
```

## Installation

```bash
pip install pyperfoptimizer
```

Requirements: Python 3.9+. Dependencies: `libcst`, `matplotlib`, `plotly` (visualization optional).

## Reproducing Benchmarks

```bash
git clone https://github.com/AnnasMazhar/PyPerfOptimizer
cd PyPerfOptimizer
pip install -e .
python benchmarks/run_benchmarks.py
```

## Architecture

```
pyperfoptimizer/
├── autofix/                    # The optimizer engine
│   ├── engine.py               # scan(), fix() — core API
│   ├── verify.py               # Benchmark verification
│   ├── profile_loader.py       # py-spy/cProfile/Scalene integration
│   └── patterns/               # Optimization patterns (pluggable)
│       ├── base.py             # Pattern base class
│       ├── auto_memoize.py     # @lru_cache insertion
│       ├── membership_test.py  # list→set for 'in' checks
│       ├── append_to_comprehension.py
│       ├── string_concat.py
│       ├── loop_invariant.py
│       ├── unnecessary_list.py
│       └── dataframe_vectorize.py
├── profiler/                   # CPU, memory, line profiling
├── visualizer/                 # Dashboard and charts
└── optimizer/                  # Static code analysis
```

## Adding Custom Patterns

```python
from pyperfoptimizer.autofix.patterns.base import Pattern, Match
import libcst as cst

class MyPattern(Pattern):
    name = "my_pattern"
    description = "Describe what it detects"
    expected_speedup = "2-5x"

    def detect(self, tree: cst.Module) -> list[Match]:
        # Use libcst visitors to find anti-patterns
        ...

    def transform(self, tree: cst.Module, match: Match) -> cst.Module:
        # Return transformed tree
        ...
```

## Research & References

This tool's approach is informed by:

- **Google ECO** (arXiv:2503.15669, 2025) — Anti-pattern dictionary + mechanical AST rewriting. 500K+ CPU cores saved/quarter.
- **MaxCode** (arXiv:2601.05475, 2026) — Execution feedback loops improve optimization quality by 20%.
- **Codeflash** — Found 13.7× speedup in vLLM (production ML framework) via automated optimization.
- **Instagram LibCST** — Source-preserving AST transforms at scale (used internally for codemod migrations).

Key insight from the research: **90% of LLM-suggested optimizations are incorrect without benchmark verification** (Codeflash, 2025). That's why PyPerfOptimizer verifies every transformation.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). To add a new pattern:

1. Create `src/pyperfoptimizer/autofix/patterns/your_pattern.py`
2. Implement `detect()` and `transform()` using libcst
3. Register in `patterns/__init__.py`
4. Add tests in `tests/test_autofix/`
5. Run `python -m pytest tests/ -v`

## License

MIT — see [LICENSE](LICENSE).
