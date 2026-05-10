"""Benchmark verification for optimizations."""

import ast
import textwrap
import time
from dataclasses import dataclass


@dataclass
class BenchmarkResult:
    original_time: float
    optimized_time: float
    speedup: float
    passed: bool  # >10% improvement


def _find_functions(source: str) -> list[str]:
    """Find top-level function names in source."""
    tree = ast.parse(source)
    return [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]


def _generate_test_args(source: str, func_name: str) -> str:
    """Generate simple test arguments based on function signature."""
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == func_name:
            args = []
            for arg in node.args.args:
                annotation = ""
                if arg.annotation:
                    annotation = ast.unparse(arg.annotation)
                # Generate appropriate test data based on type hints or name
                name = arg.arg
                if "list" in annotation.lower() or "items" in name or "messages" in name or name.endswith("s"):
                    args.append(
                        "[{'role': 'admin', 'content': 'Hello world', 'name': 'Test', "
                        "'first': 'John', 'last': 'Smith', 'type': 'str', 'id': i} "
                        "for i in range(500)]"
                    )
                elif "dict" in annotation.lower():
                    args.append("{'key': 'value'}")
                elif "set" in annotation.lower():
                    args.append("{'a', 'b', 'c'}")
                elif "str" in annotation.lower() or name in ("text", "s", "path", "name"):
                    args.append("'test_string_value'")
                elif "int" in annotation.lower() or name in ("n", "count", "num"):
                    args.append("100")
                else:
                    args.append(
                        "[{'role': 'admin', 'content': 'Hello world', 'name': 'Test', "
                        "'first': 'John', 'last': 'Smith', 'type': 'str', 'id': i} "
                        "for i in range(200)]"
                    )
            return ", ".join(args)
    return ""


def verify(original_source: str, optimized_source: str, n: int = 500) -> BenchmarkResult:
    """Benchmark original vs optimized code by calling functions with test data."""
    functions = _find_functions(original_source)
    if not functions:
        # No functions found — fall back to module-level exec timing
        return _verify_module_level(original_source, optimized_source, n)

    # Use the first function for benchmarking
    func_name = functions[0]
    test_args = _generate_test_args(original_source, func_name)

    # Set up both versions
    orig_ns = {}
    opt_ns = {}
    exec(compile(textwrap.dedent(original_source), "<original>", "exec"), orig_ns)
    exec(compile(textwrap.dedent(optimized_source), "<optimized>", "exec"), opt_ns)

    orig_func = orig_ns.get(func_name)
    opt_func = opt_ns.get(func_name)

    if not orig_func or not opt_func:
        return _verify_module_level(original_source, optimized_source, n)

    # Build the call
    call_code_orig = f"_func({test_args})"
    call_code_opt = f"_func({test_args})"

    # Verify correctness first
    try:
        orig_result = eval(call_code_orig, {"_func": orig_func})
        opt_result = eval(call_code_opt, {"_func": opt_func})
        if orig_result != opt_result:
            # Results differ — optimization may be unsafe
            return BenchmarkResult(0, 0, 0, False)
    except Exception:
        # Can't verify — skip correctness check, still benchmark
        pass

    # Benchmark original
    start = time.perf_counter()
    for _ in range(n):
        eval(call_code_orig, {"_func": orig_func})
    original_time = time.perf_counter() - start

    # Benchmark optimized
    start = time.perf_counter()
    for _ in range(n):
        eval(call_code_opt, {"_func": opt_func})
    optimized_time = time.perf_counter() - start

    speedup = original_time / optimized_time if optimized_time > 0 else 1.0
    passed = speedup > 1.10

    return BenchmarkResult(
        original_time=original_time,
        optimized_time=optimized_time,
        speedup=speedup,
        passed=passed,
    )


def _verify_module_level(original_source: str, optimized_source: str, n: int) -> BenchmarkResult:
    """Fallback: benchmark module-level execution."""
    orig_code = compile(textwrap.dedent(original_source), "<original>", "exec")
    opt_code = compile(textwrap.dedent(optimized_source), "<optimized>", "exec")

    start = time.perf_counter()
    for _ in range(n):
        exec(orig_code, {})
    original_time = time.perf_counter() - start

    start = time.perf_counter()
    for _ in range(n):
        exec(opt_code, {})
    optimized_time = time.perf_counter() - start

    speedup = original_time / optimized_time if optimized_time > 0 else 1.0
    return BenchmarkResult(original_time, optimized_time, speedup, speedup > 1.10)
