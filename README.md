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
| **PyPerfOptimizer** | ✓ | ✓ (8 patterns) | ✓ (AST rewrite) | ✓ (benchmarked) |

## Benchmarks

Real numbers. Measured on Python 3.11, Ubuntu 24.04. Reproducible via `python benchmarks/bench_regex.py`.

### Highest-Impact: Regex Precompile (NEW)

The single biggest auto-fix win. Moves `re.match/search/sub/findall` with string literal patterns out of loops into module-level `re.compile()` calls.

```
Benchmark                                           Speedup
────────────────────────────────────────────────────────────
Email validation (complex regex in loop)              2.0x
Combined log filter (regex + list→set + append)       1.8x
Realistic user processing (regex + set + append)      1.7x
Text cleaning (3× re.sub per iteration)               1.5x
Number extraction (simple regex pattern)              1.1x
────────────────────────────────────────────────────────────
```

**Key insight:** The more complex the regex pattern, the bigger the win. Simple patterns like `r"\d+"` get ~1.1x because Python's internal regex cache handles them cheaply. Complex patterns like email validation (`r"^[a-zA-Z0-9._%+-]+@..."`) get 2x+ because the compile overhead dominates per-call cost.

### All Patterns — Verified Speedups

```
Pattern                    Data Size    Original    Optimized    Speedup
─────────────────────────────────────────────────────────────────────────
Auto-memoize (fib(30))     recursive    132ms       0.07µs       320x
List→Set membership        100 items    882ms       20.7ms       42.6x
Regex precompile           5K emails    549ms       273ms        2.0x
Combined (all patterns)    3K entries   571ms       316ms        1.8x
Append loop→comprehension  100K items   382ms       270ms        1.4x
String +=→join             10K items    101ms       86ms         1.2x
Remove unnecessary list()  100K items   555µs       422µs        1.3x
─────────────────────────────────────────────────────────────────────────
```

### When Each Pattern Matters

| Pattern | Impact | When it fires |
|---------|--------|---------------|
| **Auto-memoize** | 100-10,000× | Recursive functions (fibonacci, tree traversal) |
| **List→Set membership** | 2-50× | `x in [literal, ...]` with 3+ items |
| **Regex precompile** | 1.5-2.5× | `re.match/search/sub/findall` with string patterns in functions |
| **Append→comprehension** | 1.3-1.5× | `for x: list.append(expr)` |
| **String +=→join** | 1.1-1.2× | `s += x` in loop (CPython 3.11+ optimized this) |
| **Loop-invariant hoist** | 1.05-1.1× | `obj.method` repeated in loop body |

### Combined Effect on Real Code

A realistic function with multiple anti-patterns (regex in loop + list membership + append pattern) gets **1.7x** from all patterns firing together. This is the typical real-world gain on functions that have multiple issues.

## What This Tool Is Good At

- **Catching uncompiled regex in hot paths** — the #1 value. Most developers don't realize `re.match(pattern, s)` recompiles every call. In a loop over thousands of items, precompiling gives 1.5-2.5x for free.
- **List→set membership** — `if x in ["a", "b", "c", ...]` is O(n) per check. Converting to a set literal is O(1). Massive win at scale.
- **Auto-memoization** — detects pure recursive functions and adds `@lru_cache`. Turns O(2ⁿ) into O(n).
- **Zero-risk transformations** — all changes are semantically equivalent. No behavior change.
- **Profile-guided focus** — feed profiling data to only fix functions that actually consume CPU time.

## What This Tool Is Not

- **Not a replacement for algorithmic optimization.** If your code is O(n²) and should be O(n log n), no amount of regex precompiling will save it. Use a profiler first.
- **Not a replacement for profiling.** This tool catches known anti-patterns. It doesn't find your actual bottleneck — that's what py-spy/Scalene/cProfile are for.
- **Not magic on already-clean code.** If your code doesn't have these specific anti-patterns, there's nothing to fix. The tool will correctly report "no issues found."
- **Marginal on simple patterns.** String concat optimization (1.2x) and loop hoisting (1.1x) are real but small. The big wins come from regex precompile, set membership, and memoization.
- **Not for I/O-bound code.** If your bottleneck is network/disk, CPU micro-optimizations won't help.

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

### Example: Regex Precompile Transform

**Input:**
```python
import re

def process_users(users):
    results = []
    for user in users:
        if user["role"] in ["admin", "editor", "moderator", "reviewer", "manager"]:
            name = user["first"] + " " + user["last"]
            if re.match(r"^[A-Z]", name):
                results.append({"name": name, "role": user["role"]})
    return results
```

**Output (automated):**
```python
import re

_RE_0 = re.compile(r"^[A-Z]")

def process_users(users):
    results = []
    for user in users:
        if user["role"] in {"admin", "editor", "moderator", "reviewer", "manager"}:
            name = user["first"] + " " + user["last"]
            if _RE_0.match(name):
                results.append({"name": name, "role": user["role"]})
    return results
```

**Result:** 1.72x faster. Regex precompiled to module level + list→set membership fix.

### Example: Memoization

**Input:**
```python
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)
```

**Output:**
```python
import functools

@functools.lru_cache(maxsize=None)
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)
```

**Result:** 320x faster. O(2ⁿ) → O(n).

## Optimization Patterns

### Tier 1: High Impact (auto-applied)

| # | Pattern | Detects | Transforms to | Speedup |
|---|---------|---------|---------------|---------|
| 1 | **Auto-memoize** | Pure recursive functions | `@functools.lru_cache` | 100-10,000× |
| 2 | **Membership set** | `x in [literal, ...]` (3+ items) | `x in {literal, ...}` | 2-50× |
| 3 | **Regex precompile** | `re.func(r"pattern", ...)` in functions | Module-level `re.compile()` | 1.5-2.5× |
| 4 | **Append→comprehension** | `for x: list.append(expr)` | `[expr for x in iter]` | 1.3-1.5× |
| 5 | **String concat→join** | `s += x` in loop | `''.join(...)` | 1.1-1.2× |

### Tier 2: Safe Cleanup (auto-applied)

| # | Pattern | Detects | Transforms to | Speedup |
|---|---------|---------|---------------|---------|
| 6 | **Unnecessary list()** | `for x in list(gen)` | `for x in gen` | 1.1-1.5× |
| 7 | **Loop-invariant hoist** | `obj.method` in loop body | Local variable before loop | 1.05-1.1× |
| 8 | **DataFrame vectorize** | `df.iterrows()` loops | Vectorized pandas ops | 10-1000× |

### Safety Guarantees

- **Source-preserving**: Comments, formatting, type annotations are kept intact
- **Semantically safe**: Only transforms provably equivalent code
- **Memoization guard**: Only applied to recursive functions with no side effects
- **Regex guard**: Only transforms string literal patterns (not variables)
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
python benchmarks/bench_regex.py
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
│       ├── regex_precompile.py # re.compile at module level
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
    auto_fix = True  # Set False for detection-only

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
