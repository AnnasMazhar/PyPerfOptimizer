# PyPerfOptimizer

**Make Python faster. Automatically.**

PyPerfOptimizer detects performance anti-patterns in your Python code and transforms them into faster equivalents — with verified, reproducible speedups.

```bash
pip install pyperfoptimizer
pyperfoptimizer fix myapp.py --verify
```

## Verified Results

All benchmarks run 3× for stability. Python 3.11, Ubuntu 24.04. Reproduce with `python benchmarks/run_benchmarks.py`.

| Optimization | Speedup (mean of 3 runs) | Variance |
|---|---|---|
| Regex precompile (`re.match` → compiled) | **2.04×** | ±0.10 |
| Set membership (`in [list]` → `in {set}`) | **4.22×** | ±0.15 |
| Combined (regex + set on realistic function) | **1.69×** | ±0.02 |
| Auto-memoize (recursive → `@lru_cache`) | **9,674×** | stable |

### Real-World Validation

I scanned 3 major open-source projects to verify these patterns exist in production code:

```
Project     Files Scanned    Issues Found    Top Pattern
──────────────────────────────────────────────────────────────
Django      47               36              regex_precompile (7)
FastAPI     48               35              auto_memoize (12)
Flask       24               15              defaultdict_opportunity (5)
──────────────────────────────────────────────────────────────
Total       119              86 optimizations
```

These are well-maintained projects by experienced developers. If they have these issues, most codebases do.

## How It Works

```bash
# Scan — find anti-patterns, report expected speedups
pyperfoptimizer scan myapp.py

# Fix — apply safe transformations
pyperfoptimizer fix myapp.py

# Fix with proof — benchmark before/after, reject if not faster
pyperfoptimizer fix --verify myapp.py

# Focus on hot paths only
pyperfoptimizer fix myapp.py --profile profile.speedscope
```

### Example

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

**Output (fully automated):**
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

**Measured speedup: 1.69×** (2000 users, 300 iterations, mean of 3 runs)

## Why These Optimizations Work

### Regex Precompilation (2×)
`re.match(pattern, string)` recompiles the pattern on every call. CPython caches the last few patterns, but in loops with multiple patterns or high call frequency, recompilation dominates. Precompiling once eliminates this entirely.

### Set Membership (4×)
`x in [1, 2, 3]` creates a new list and does O(n) linear scan every time. `x in {1, 2, 3}` uses a frozen set with O(1) hash lookup. The gap grows with collection size — 4× at 10 items, 42× at 100 items.

### Memoization (9,674×)
Recursive functions like `fib(n)` have O(2ⁿ) call trees. `@lru_cache` stores results, reducing to O(n) unique computations. This is the single highest-impact optimization possible for recursive pure functions.

## All 17 Patterns

### Auto-Fix Patterns (applied automatically)

| Pattern | What it does | Speedup |
|---------|-------------|---------|
| `regex_precompile` | `re.match(str, x)` → precompiled at module level | 2× |
| `membership_test_set` | `x in [literals]` → `x in {literals}` | 4× |
| `auto_memoize` | Pure recursive functions → `@lru_cache` | 9,674× |
| `append_to_comprehension` | Append-in-loop → list comprehension | 1.4× |
| `string_concat_to_join` | `s += x` in loop → `''.join()` | 1.2× |
| `dict_get` | `try: d[k] except KeyError` → `d.get(k, default)` | 2× |
| `multiple_isinstance` | Chained `isinstance()` → tuple form | 1.4× |
| `generator_instead_of_list` | `sum([x for x])` → `sum(x for x)` | 1.1× |
| `unnecessary_list` | `for x in list(gen)` → `for x in gen` | 1.3× |
| `unnecessary_copy` | `list([1,2,3])` → `[1,2,3]` | 1.5× |
| `chained_comparison` | `x > 0 and x < 10` → `0 < x < 10` | 1.1× |
| `loop_invariant_hoist` | Hoist `list.append` lookup out of loop | 1.1× |

### Detection-Only Patterns (reported, not auto-fixed)

| Pattern | What it detects | Why not auto-fix |
|---------|----------------|-----------------|
| `defaultdict_opportunity` | `if k not in d: d[k] = []` | Requires import + type change |
| `repeated_attr_in_loop` | `self.config.x` accessed 5× in loop | Too many edge cases |
| `exception_control_flow` | `try/except` in loop for type conversion | Intent-dependent |
| `loop_to_any_all` | `for+if+return True` → `any()` | **No speedup** (generator overhead) |
| `dataframe_vectorize` | `df.iterrows()` in loop | Complex transform |

### Honest Finding: `any()/all()` Is NOT Faster

My benchmarks revealed that `any(x < 0 for x in items)` is **slower** than a manual `for` loop in CPython due to generator creation overhead. I mark this as readability-only, not a performance improvement. This contradicts common advice — I reported what I measure, not what's assumed.

## Profile-Guided Optimization

Don't optimize cold code. Feed profiling data to focus on what matters:

```bash
py-spy record -o profile.speedscope -- python myapp.py
pyperfoptimizer fix myapp.py --profile profile.speedscope
```

Supports: **py-spy** (speedscope JSON), **cProfile** (pstats), **Scalene** (JSON).

## How to Verify Our Claims

Every claim in this README is reproducible:

```bash
git clone https://github.com/AnnasMazhar/PyPerfOptimizer
cd PyPerfOptimizer
pip install -e .
python benchmarks/run_benchmarks.py        # Reproduce all speedup numbers
python benchmarks/bench_regex.py           # Regex-specific benchmarks
python -c "
from pyperfoptimizer.autofix import scan_file
import glob
files = glob.glob('/path/to/your/project/**/*.py', recursive=True)
for f in files:
    opts = scan_file(f)
    if opts:
        print(f'{f}: {len(opts)} optimizations')
"
```

## What This Tool Is Good At

- Catching **uncompiled regex** in functions (the #1 hidden performance killer)
- Converting **list membership to set** (scales from 4× to 42×)
- Finding **memoization candidates** in recursive functions
- Providing **verified speedups** — every auto-fix is benchmarkable

## What This Tool Is Not

- Not a profiler (use py-spy or Scalene for that, then feed output here)
- Not an algorithmic optimizer (won't change your O(n²) sort to O(n log n))
- Not an LLM (deterministic AST transforms — same input always gives same output)
- Not a replacement for understanding your code (it catches patterns, not design issues)

## Installation

```bash
pip install pyperfoptimizer
```

Python 3.9+. Core dependency: `libcst`.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Run tests: `python -m pytest tests/ -v` (123 tests).

## License

MIT — see [LICENSE](LICENSE).
