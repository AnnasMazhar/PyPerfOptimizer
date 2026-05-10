# PyPerfOptimizer

A Python performance linter that catches patterns no other tool catches — and auto-fixes them.

## What It Does

Detects uncompiled regex and list-as-set membership tests in your code. Auto-fixes them with verified 2× speedup. Works as a linter (exit code 1 on issues) for CI/pre-commit.

**No other Python linter (Ruff, Pylint, Flake8) catches these patterns.** Verified by running all tools with all rules enabled on the same code.

## Install

```bash
pip install pyperfoptimizer
```

## Usage

### Scan (lint mode)

```bash
$ pyperfoptimizer scan myapp.py
```

```
━━━ Source Fixes (auto-fixable) ━━━━━━━━━━━━━━━━━━━━━━━━━━
  myapp.py:6  membership_test_set  2-4x
  myapp.py:8  regex_precompile     2-10x for hot paths

━━━ Compilation Candidates ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  myapp.py:3  process_users    blocked
    Status: blocked (not all parameters have numeric type annotations)

━━━ Architecture Suggestions ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  No architecture suggestions.
```

Exit code 1 when issues found, 0 when clean. Use in CI.

### Fix (auto-apply)

```bash
$ pyperfoptimizer fix myapp.py
Written to: myapp.optimized.py
```

**Before:**
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

**After (automated):**
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

### Verify (prove it's faster)

```bash
$ pyperfoptimizer fix --verify myapp.py
Written to: myapp.optimized.py
  Speedup: 1.34x | PASS
```

Benchmarks the function with test data. Reports PASS (>1.1×) or FAIL.

### Pre-commit hook

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/AnnasMazhar/PyPerfOptimizer
    rev: v0.2.1
    hooks:
      - id: pyperfoptimizer
        entry: pyperfoptimizer scan
        types: [python]
```

### Profile-guided (focus on hot paths)

```bash
$ py-spy record -o profile.json -- python myapp.py
$ pyperfoptimizer scan myapp.py --profile profile.json
```

Only reports issues in functions that consume significant CPU time.

## Verified Speedups

Measured with `python3 -m timeit`, Python 3.12:

```
re.match(pattern, s)  vs  compiled.match(s):  510ns → 208ns = 2.45×
x in [5 literals]     vs  x in {5 literals}:  varies by size, 1.9-4.2×
```

Tested on 76 files across FastAPI, Flask, Django, Strands SDK: **0 breaks**.

## What This Catches That Others Don't

| Pattern | Ruff | Pylint | Flake8 | **PyPerfOptimizer** |
|---------|------|--------|--------|---------------------|
| `re.match(string, x)` in function | ✗ | ✗ | ✗ | **✓ auto-fix** |
| `x in [literal, literal, ...]` | ✗ | ✗ | ✗ | **✓ auto-fix** |

Verified by running `ruff check --select ALL`, `pylint`, and `flake8+perflint` on the same file. Zero warnings from any of them.

## What This Tool Is Not

- Not a general Python accelerator (CPython 3.11+ already optimizes most micro-patterns)
- Not a profiler (use py-spy or Scalene, then feed output here with `--profile`)
- Not a compiler (use mypyc for typed compute-heavy code)

## Key Finding

CPython caches compiled regex internally (up to 512 patterns). The 2× speedup comes from eliminating the **cache lookup overhead** (dict key creation + hash + comparison) — not from avoiding recompilation. In hot loops, this adds up.

## Contributing

135 tests: `python -m pytest tests/ -v`

## License

MIT
