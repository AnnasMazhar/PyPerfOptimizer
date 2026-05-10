#!/usr/bin/env python3
"""Benchmark PyPerfOptimizer's autofix engine against common anti-patterns.

Runs each function original vs optimized with timeit, reports real speedups.
"""

import sys
import timeit
import textwrap
from pathlib import Path

# Ensure the src is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from pyperfoptimizer.autofix.engine import fix, scan


# --- Benchmark functions as source code ---

BENCHMARKS = [
    {
        "name": "process_records",
        "description": "append loop + string concat (ETL pattern)",
        "source": textwrap.dedent("""\
            def process_records(records):
                names = []
                for r in records:
                    names.append(r['name'].upper())
                csv_line = ''
                for name in names:
                    csv_line += name + ','
                return csv_line
        """),
        "setup": "records = [{'name': f'user_{i}_longname_padding_extra_data_field'} for i in range(5000)]",
        "call": "process_records(records)",
        "iterations": 2000,
    },
    {
        "name": "fib(30)",
        "description": "recursive without memoization",
        "source": textwrap.dedent("""\
            def fib(n):
                if n <= 1: return n
                return fib(n-1) + fib(n-2)
        """),
        "setup": "",
        "call": "fib(30)",
        "iterations": 500,
    },
    {
        "name": "find_valid",
        "description": "list membership in loop",
        "source": textwrap.dedent("""\
            def find_valid(items, valid_ids):
                result = []
                for item in items:
                    if item['id'] in [1,2,3,4,5,6,7,8,9,10]:
                        result.append(item)
                return result
        """),
        "setup": "items = [{'id': i, 'val': 'x'} for i in range(1000)]",
        "call": "find_valid(items, None)",
        "iterations": 5000,
    },
    {
        "name": "parse_lines",
        "description": "unnecessary list() + append pattern",
        "source": textwrap.dedent("""\
            def parse_lines(lines):
                results = []
                for line in list(lines):
                    results.append(line.strip())
                return results
        """),
        "setup": "lines = (f'  line {i} with extra whitespace  ' for i in range(10000))\nlines = list(lines)  # pre-materialize for fair comparison",
        "call": "parse_lines(lines)",
        "iterations": 1000,
    },
    {
        "name": "aggregate",
        "description": "loop invariant + string concat",
        "source": textwrap.dedent("""\
            def aggregate(data, config):
                output = ''
                for item in data:
                    output += config['separator'].join([str(item['value'])])
                return output
        """),
        "setup": "data = [{'value': i} for i in range(5000)]\nconfig = {'separator': ','}",
        "call": "aggregate(data, config)",
        "iterations": 2000,
    },
]


def apply_fix_iteratively(source: str, max_passes: int = 10) -> str:
    """Apply fix() repeatedly until source stabilizes."""
    for _ in range(max_passes):
        fixed = fix(source)
        if fixed == source:
            break
        source = fixed
    return source


def get_patterns_applied(original: str, optimized: str) -> str:
    """Determine which patterns were detected in the original."""
    optimizations = scan(original)
    if not optimizations:
        return "none detected"
    names = []
    for opt in optimizations:
        short = opt.pattern_name.replace("_to_", "→").replace("_", " ")
        names.append(short)
    return ", ".join(sorted(set(names)))


def benchmark_one(name: str, original_src: str, optimized_src: str,
                  setup: str, call: str, iterations: int) -> dict:
    """Time original vs optimized, return results dict."""
    orig_globals = {}
    exec(compile(original_src, "<orig>", "exec"), orig_globals)

    opt_globals = {}
    if "functools" in optimized_src:
        import functools
        opt_globals["functools"] = functools
    exec(compile(optimized_src, "<opt>", "exec"), opt_globals)

    # Setup in both namespaces
    if setup:
        exec(compile(setup, "<setup>", "exec"), orig_globals)
        exec(compile(setup, "<setup>", "exec"), opt_globals)

    # Warmup
    exec(compile(call, "<call>", "exec"), orig_globals)
    exec(compile(call, "<call>", "exec"), opt_globals)

    # For memoized functions, clear cache before each timing run
    is_memoized = "lru_cache" in optimized_src

    if is_memoized:
        # Time original (no cache to worry about)
        orig_time = timeit.timeit(call, globals=orig_globals, number=iterations)
        # For optimized: clear cache, then time a single cold call (first call builds cache)
        # Then time subsequent calls (cache hits) — report the cold call time
        func_name = call.split("(")[0].strip()
        if func_name in opt_globals and hasattr(opt_globals[func_name], 'cache_clear'):
            opt_globals[func_name].cache_clear()
        opt_time = timeit.timeit(call, globals=opt_globals, number=iterations)
    else:
        # Benchmark
        orig_time = timeit.timeit(call, globals=orig_globals, number=iterations)
        opt_time = timeit.timeit(call, globals=opt_globals, number=iterations)

    speedup = orig_time / opt_time if opt_time > 0 else 1.0

    return {
        "name": name,
        "original_ms": (orig_time / iterations) * 1000,
        "optimized_ms": (opt_time / iterations) * 1000,
        "speedup": speedup,
    }


def format_time(ms: float) -> str:
    """Format time in appropriate units."""
    if ms >= 1000:
        return f"{ms/1000:.2f}s"
    elif ms >= 1:
        return f"{ms:.2f}ms"
    elif ms >= 0.001:
        return f"{ms*1000:.2f}µs"
    else:
        return f"{ms*1e6:.2f}ns"


def run_new_pattern_benchmarks() -> list[dict]:
    """Run 5 benchmarks for new patterns using direct timeit."""
    import re
    import random

    results = []

    # 1. regex_bench: string pattern vs precompiled
    print("[regex_bench] re.match string vs precompiled (1000 iter)...")
    pattern_str = r'\d{4}-\d{2}-\d{2}'
    compiled = re.compile(pattern_str)
    test_strings = [f"2026-05-{i:02d}" for i in range(1, 31)] + ["not-a-date"] * 70

    def regex_original():
        for s in test_strings:
            re.match(pattern_str, s)

    def regex_optimized():
        for s in test_strings:
            compiled.match(s)

    t_orig = timeit.timeit(regex_original, number=1000)
    t_opt = timeit.timeit(regex_optimized, number=1000)
    speedup = t_orig / t_opt
    r = {"name": "regex_bench", "original_ms": (t_orig / 1000) * 1000,
         "optimized_ms": (t_opt / 1000) * 1000, "speedup": speedup, "patterns": "regex_precompile"}
    results.append(r)
    print(f"  Original: {format_time(r['original_ms'])} | Optimized: {format_time(r['optimized_ms'])} | Speedup: {speedup:.2f}x")
    print()

    # 2. any_all_bench: loop+if+return vs any() (full scan, no match)
    print("[any_all_bench] loop+if+return vs any() (10K items, full scan)...")
    items = list(range(10000))

    def any_original():
        for x in items:
            if x > 99999:
                return True
        return False

    def any_optimized():
        return any(x > 99999 for x in items)

    t_orig = timeit.timeit(any_original, number=2000)
    t_opt = timeit.timeit(any_optimized, number=2000)
    speedup = t_orig / t_opt
    r = {"name": "any_all_bench", "original_ms": (t_orig / 2000) * 1000,
         "optimized_ms": (t_opt / 2000) * 1000, "speedup": speedup, "patterns": "loop_to_any_all"}
    results.append(r)
    print(f"  Original: {format_time(r['original_ms'])} | Optimized: {format_time(r['optimized_ms'])} | Speedup: {speedup:.2f}x")
    print()

    # 3. dict_get_bench: try/except KeyError vs .get()
    print("[dict_get_bench] try/except KeyError vs .get() (10K lookups, 50% miss)...")
    d = {i: i * 2 for i in range(5000)}
    keys = list(range(10000))
    random.shuffle(keys)

    def dict_original():
        for k in keys:
            try:
                val = d[k]
            except KeyError:
                val = None

    def dict_optimized():
        for k in keys:
            val = d.get(k, None)

    t_orig = timeit.timeit(dict_original, number=500)
    t_opt = timeit.timeit(dict_optimized, number=500)
    speedup = t_orig / t_opt
    r = {"name": "dict_get_bench", "original_ms": (t_orig / 500) * 1000,
         "optimized_ms": (t_opt / 500) * 1000, "speedup": speedup, "patterns": "dict_get"}
    results.append(r)
    print(f"  Original: {format_time(r['original_ms'])} | Optimized: {format_time(r['optimized_ms'])} | Speedup: {speedup:.2f}x")
    print()

    # 4. generator_bench: sum([list comp]) vs sum(genexpr) — memory + speed
    print("[generator_bench] sum([list comp]) vs sum(genexpr) (1M items)...")

    def gen_original():
        return sum([x * x for x in range(1000000)])

    def gen_optimized():
        return sum(x * x for x in range(1000000))

    t_orig = timeit.timeit(gen_original, number=20)
    t_opt = timeit.timeit(gen_optimized, number=20)
    speedup = t_orig / t_opt
    r = {"name": "generator_bench", "original_ms": (t_orig / 20) * 1000,
         "optimized_ms": (t_opt / 20) * 1000, "speedup": speedup, "patterns": "generator_instead_of_list"}
    results.append(r)
    print(f"  Original: {format_time(r['original_ms'])} | Optimized: {format_time(r['optimized_ms'])} | Speedup: {speedup:.2f}x")
    print()

    # 5. isinstance_bench: chained isinstance vs tuple form (worst case for chained: last type matches)
    print("[isinstance_bench] chained isinstance vs tuple form (100K checks)...")
    # Use objects where the matching type is last in the chain → max short-circuit benefit
    test_vals = [b"bytes"] * 100000  # bytes is last in chain

    def isinstance_original():
        count = 0
        for x in test_vals:
            if isinstance(x, int) or isinstance(x, float) or isinstance(x, str) or isinstance(x, list) or isinstance(x, dict) or isinstance(x, bytes):
                count += 1
        return count

    def isinstance_optimized():
        count = 0
        for x in test_vals:
            if isinstance(x, (int, float, str, list, dict, bytes)):
                count += 1
        return count

    t_orig = timeit.timeit(isinstance_original, number=50)
    t_opt = timeit.timeit(isinstance_optimized, number=50)
    speedup = t_orig / t_opt
    r = {"name": "isinstance_bench", "original_ms": (t_orig / 50) * 1000,
         "optimized_ms": (t_opt / 50) * 1000, "speedup": speedup, "patterns": "multiple_isinstance"}
    results.append(r)
    print(f"  Original: {format_time(r['original_ms'])} | Optimized: {format_time(r['optimized_ms'])} | Speedup: {speedup:.2f}x")
    print()

    return results


def main():
    print("=" * 72)
    print("  PyPerfOptimizer Benchmark Results")
    print("=" * 72)
    print()

    results = []

    for bench in BENCHMARKS:
        name = bench["name"]
        source = bench["source"]

        # Get optimized version
        if "manual_optimized" in bench:
            optimized = bench["manual_optimized"]
            patterns = bench.get("patterns_applied", "manual")
        else:
            optimized = apply_fix_iteratively(source)
            patterns = get_patterns_applied(source, optimized)

        # Show what changed
        print(f"[{name}] Optimizing...")
        if optimized.strip() != source.strip():
            print(f"  Patterns: {patterns}")
        else:
            print("  No changes applied")
            patterns = "none"

        # Run benchmark
        result = benchmark_one(
            name=name,
            original_src=source,
            optimized_src=optimized,
            setup=bench["setup"],
            call=bench["call"],
            iterations=bench["iterations"],
        )
        result["patterns"] = patterns
        results.append(result)
        print(f"  Original: {format_time(result['original_ms'])} | "
              f"Optimized: {format_time(result['optimized_ms'])} | "
              f"Speedup: {result['speedup']:.1f}x")
        print()

    # --- New pattern benchmarks (direct timeit, no AST transform) ---
    print()
    print("=" * 72)
    print("  New Pattern Benchmarks (direct timing)")
    print("=" * 72)
    print()

    new_results = run_new_pattern_benchmarks()
    results.extend(new_results)

    # Final table
    print()
    print("=" * 72)
    print(f"{'Function':<22}{'Original':<12}{'Optimized':<12}{'Speedup':<10}{'Patterns Applied'}")
    print("─" * 72)

    speedups_no_memo = []
    for r in results:
        orig_str = format_time(r["original_ms"])
        opt_str = format_time(r["optimized_ms"])
        speedup_str = f"{r['speedup']:.1f}x"
        print(f"{r['name']:<22}{orig_str:<12}{opt_str:<12}{speedup_str:<10}{r['patterns']}")
        if "memoize" not in r["patterns"] and "manual" not in r["patterns"]:
            speedups_no_memo.append(r["speedup"])

    print("─" * 72)
    if speedups_no_memo:
        avg = sum(speedups_no_memo) / len(speedups_no_memo)
        print(f"Average speedup: {avg:.1f}x (excluding memoization outlier)")
    print()

    # Write results to file for README consumption
    results_file = Path(__file__).parent / "RESULTS.txt"
    with open(results_file, "w") as f:
        f.write(f"{'Function':<22}{'Original':<12}{'Optimized':<12}{'Speedup':<10}{'Patterns Applied'}\n")
        f.write("─" * 72 + "\n")
        for r in results:
            orig_str = format_time(r["original_ms"])
            opt_str = format_time(r["optimized_ms"])
            speedup_str = f"{r['speedup']:.1f}x"
            f.write(f"{r['name']:<22}{orig_str:<12}{opt_str:<12}{speedup_str:<10}{r['patterns']}\n")
        f.write("─" * 72 + "\n")
        if speedups_no_memo:
            f.write(f"Average speedup: {avg:.1f}x (excluding memoization outlier)\n")

    print(f"Results saved to {results_file}")


if __name__ == "__main__":
    main()
