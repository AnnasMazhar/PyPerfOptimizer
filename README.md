# PyPerfOptimizer

A Python performance analysis tool that finds where your code wastes time and applies safe, verified fixes.

## What It Actually Does

PyPerfOptimizer detects specific patterns where CPython does unnecessary repeated work. It auto-fixes the safe ones and reports the rest with actionable guidance.

**Tested against:** FastAPI, Flask, Django, Strands SDK (76 files, 0 breaks).

## Verified Results

Every number below was measured 3× for stability on Python 3.11/3.12, Ubuntu 24.04.

### Patterns That Give Real Speedups

| Pattern | Speedup | Why it works |
|---------|---------|-------------|
| Uncompiled regex in functions | **2.0-2.5×** | `re.match(string, x)` recompiles the pattern every call. Precompiling eliminates this. |
| List literal for membership test | **1.9-4.2×** | `x in [a,b,c,d,e]` builds a new list and does O(n) scan. `x in {set}` is O(1). |
| Combined (regex + set) | **1.7-2.0×** | On realistic functions with both patterns. |

### Patterns That Don't Help (on CPython 3.11+)

I tested these and they gave negligible or zero improvement on real framework code:

| Pattern | Measured | Why |
|---------|----------|-----|
| `any()`/`all()` vs manual loop | **0.45×** (slower) | Generator overhead exceeds any benefit |
| `isinstance()` → `__class__ is` | **0.91-1.02×** | CPython's adaptive interpreter already specializes this |
| Loop-invariant hoisting | **1.01-1.06×** | CPython 3.11 inline caching handles attribute lookups |
| String `+=` → `join()` | **1.1-1.2×** | CPython 3.11 does in-place resize when refcount=1 |
| Append loop → comprehension | **1.2×** | Real but marginal |

### What I Found in Real Frameworks

```
Project     Files Scanned    Fixable Issues    Speedup on Fixed Code
──────────────────────────────────────────────────────────────────────
FastAPI     48               7 (regex)         1.41× (verified)
Django      47               7 (regex)         ~2× (per function)
Strands     172              7 (regex)         1.8× (verified)
Flask       24               6 (mixed)         1.33× (verified)
```

## Installation

```bash
pip install pyperfoptimizer
```

## Usage

```bash
# Find issues
pyperfoptimizer scan myapp.py

# Fix the safe ones (regex precompile, set membership)
pyperfoptimizer fix myapp.py

# Fix and prove it's faster
pyperfoptimizer fix --verify myapp.py

# Only look at hot paths (from profiling data)
pyperfoptimizer scan myapp.py --profile profile.speedscope
```

## What This Tool Is

- A detector of **specific, proven** performance waste patterns
- Safe: 0% break rate across 76 files in 4 major frameworks
- Honest: reports measured speedups, not theoretical claims
- Focused: does 2 things well (regex precompile, set membership) 

## What This Tool Is Not

- Not a general-purpose Python accelerator (CPython's interpreter is the bottleneck, not code patterns)
- Not a replacement for profiling (use py-spy or Scalene first)
- Not a compiler (use mypyc for 1.4-2.8× on typed compute-heavy code)
- Not magic (most Python performance problems are architectural — N+1 queries, redundant serialization, unnecessary copies — and require human judgment to fix)

## Key Findings From Building This Tool

1. **CPython 3.11+ already optimizes most micro-patterns.** The adaptive interpreter does inline caching, specialization, and quickening. Source-level tricks that worked on Python 3.9 are now pointless.

2. **`any()` is slower than a for loop.** Generator creation overhead dominates. Use `any()` for readability, not performance.

3. **The real performance killers are architectural**, not syntactic: `deepcopy` in loops (600× overhead), redundant serialization, uncompiled regex in hot paths. Only regex is safely auto-fixable.

4. **mypyc compilation gives 1.4-2.8×** on typed, compute-heavy code — but fails on complex code with dynamic features, and gives ~1× on data-structure-heavy code.

## Reproducing My Results

```bash
git clone https://github.com/AnnasMazhar/PyPerfOptimizer
cd PyPerfOptimizer
pip install -e .
python benchmarks/run_benchmarks.py
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). 135 tests: `python -m pytest tests/ -v`

## License

MIT
