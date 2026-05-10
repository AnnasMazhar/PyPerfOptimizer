"""Analyze functions and recommend compilation strategies."""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class Compiler(Enum):
    MYPYC = "mypyc"
    NUMBA = "numba"
    CYTHON = "cython"
    NONE = "none"


class Bottleneck(Enum):
    CPU_BOUND = "cpu"
    IO_BOUND = "io"
    MEMORY_BOUND = "memory"
    UNKNOWN = "unknown"


@dataclass
class CompileCandidate:
    name: str
    file: str
    line: int
    lines: int
    compiler: Compiler
    estimated_speedup: str
    eligible: bool
    blockers: list[str]
    missing_annotations: list[str]
    bottleneck: Bottleneck
    confidence: float


# --- Constants ---

_NUMERIC_TYPES = {"int", "float", "complex", "np.ndarray", "ndarray"}
_NUMERIC_BUILTINS = {"range", "len", "abs", "min", "max", "sum", "round", "enumerate", "zip"}
_NUMERIC_MODULES = {"math", "numpy", "np"}
_IO_CALLS = {"requests", "urllib", "socket", "sqlalchemy", "psycopg2", "aiohttp", "httpx"}
_IO_FUNCS = {"open"}
_DYNAMIC_FUNCS = {"eval", "exec", "getattr", "setattr", "delattr"}


class _FuncAnalyzer(ast.NodeVisitor):
    """Collects facts about a single function body."""

    def __init__(self) -> None:
        self.has_loops = False
        self.has_yield = False
        self.has_try = False
        self.has_string_ops = False
        self.has_dict_set_creation = False
        self.has_dynamic = False
        self.has_io = False
        self.has_global_mutation = False
        self.has_kwargs_dynamic = False
        self.non_numeric_calls: list[str] = []
        self.large_struct_in_loop = False
        self._in_loop = False

    def visit_For(self, node: ast.For) -> None:
        self.has_loops = True
        old = self._in_loop
        self._in_loop = True
        self.generic_visit(node)
        self._in_loop = old

    def visit_While(self, node: ast.While) -> None:
        self.has_loops = True
        old = self._in_loop
        self._in_loop = True
        self.generic_visit(node)
        self._in_loop = old

    def visit_Yield(self, node: ast.Yield) -> None:
        self.has_yield = True
        self.generic_visit(node)

    def visit_YieldFrom(self, node: ast.YieldFrom) -> None:
        self.has_yield = True
        self.generic_visit(node)

    def visit_Try(self, node: ast.Try) -> None:
        self.has_try = True
        self.generic_visit(node)

    # Python 3.11+
    def visit_TryStar(self, node: ast.AST) -> None:
        self.has_try = True
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        name = _call_name(node)
        if name:
            if name in _DYNAMIC_FUNCS:
                self.has_dynamic = True
            if name in _IO_FUNCS:
                self.has_io = True
            parts = name.split(".")
            if parts[0] in _IO_CALLS:
                self.has_io = True
            # Check non-numeric calls for numba
            if not _is_numeric_call(name):
                self.non_numeric_calls.append(name)
            # Large struct in loop
            if self._in_loop and name in ("list", "dict", "set"):
                self.large_struct_in_loop = True
        self.generic_visit(node)

    def visit_Dict(self, node: ast.Dict) -> None:
        self.has_dict_set_creation = True
        self.generic_visit(node)

    def visit_Set(self, node: ast.Set) -> None:
        self.has_dict_set_creation = True
        self.generic_visit(node)

    def visit_JoinedStr(self, node: ast.JoinedStr) -> None:
        self.has_string_ops = True
        self.generic_visit(node)

    def visit_BinOp(self, node: ast.BinOp) -> None:
        # String concat detection: str + str or % formatting
        if isinstance(node.op, (ast.Mod, ast.Add)):
            if isinstance(node.left, ast.Constant) and isinstance(node.left.value, str):
                self.has_string_ops = True
        self.generic_visit(node)

    def visit_Global(self, node: ast.Global) -> None:
        self.has_global_mutation = True
        self.generic_visit(node)

    def visit_keyword(self, node: ast.keyword) -> None:
        if node.arg is None:  # **kwargs unpacking
            self.has_kwargs_dynamic = True
        self.generic_visit(node)


def _call_name(node: ast.Call) -> str | None:
    """Extract dotted call name from a Call node."""
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        parts = []
        n = node.func
        while isinstance(n, ast.Attribute):
            parts.append(n.attr)
            n = n.value
        if isinstance(n, ast.Name):
            parts.append(n.id)
            return ".".join(reversed(parts))
    return None


def _is_numeric_call(name: str) -> bool:
    parts = name.split(".")
    if parts[0] in _NUMERIC_MODULES:
        return True
    if parts[0] in _NUMERIC_BUILTINS:
        return True
    return False


def _get_annotations(func: ast.FunctionDef) -> tuple[list[str], list[str]]:
    """Return (annotated_params, unannotated_params)."""
    annotated = []
    unannotated = []
    for arg in func.args.args + func.args.posonlyargs + func.args.kwonlyargs:
        if arg.arg == "self":
            continue
        if arg.annotation:
            annotated.append(arg.arg)
        else:
            unannotated.append(arg.arg)
    return annotated, unannotated


def _annotation_is_numeric(ann: ast.expr | None) -> bool:
    if ann is None:
        return False
    if isinstance(ann, ast.Name):
        return ann.id in _NUMERIC_TYPES
    if isinstance(ann, ast.Attribute):
        # np.ndarray
        if isinstance(ann.value, ast.Name) and ann.value.id == "np" and ann.attr == "ndarray":
            return True
    if isinstance(ann, ast.Subscript):
        # e.g. list[int] — not numeric for numba
        return False
    return False


def _all_params_numeric(func: ast.FunctionDef) -> bool:
    for arg in func.args.args + func.args.posonlyargs + func.args.kwonlyargs:
        if arg.arg == "self":
            continue
        if not _annotation_is_numeric(arg.annotation):
            return False
    # Must have at least one param (besides self)
    params = [a for a in func.args.args + func.args.posonlyargs + func.args.kwonlyargs if a.arg != "self"]
    return len(params) > 0


def _has_return_annotation(func: ast.FunctionDef) -> bool:
    return func.returns is not None


def _detect_bottleneck(analyzer: _FuncAnalyzer) -> Bottleneck:
    if analyzer.has_io:
        return Bottleneck.IO_BOUND
    if analyzer.large_struct_in_loop:
        return Bottleneck.MEMORY_BOUND
    if analyzer.has_loops:
        return Bottleneck.CPU_BOUND
    return Bottleneck.UNKNOWN


def _compute_confidence(
    func: ast.FunctionDef,
    analyzer: _FuncAnalyzer,
    annotated: list[str],
    unannotated: list[str],
    profile_data: dict | None,
    func_lines: int,
) -> float:
    confidence = 0.0
    # Profile data
    if profile_data and func.name in profile_data and profile_data[func.name] > 5.0:
        confidence += 0.4
    if analyzer.has_loops:
        confidence += 0.2
    if func_lines > 20:
        confidence += 0.1
    if len(annotated) > 0 and len(unannotated) == 0:
        confidence += 0.2
    elif len(annotated) > len(unannotated):
        confidence += 0.1
    return min(confidence, 1.0)


def _analyze_function(
    func: ast.FunctionDef, file: str, profile_data: dict | None
) -> CompileCandidate:
    analyzer = _FuncAnalyzer()
    analyzer.generic_visit(func)

    func_lines = (func.end_lineno or func.lineno) - func.lineno + 1
    annotated, unannotated = _get_annotations(func)
    bottleneck = _detect_bottleneck(analyzer)

    blockers: list[str] = []
    compiler = Compiler.NONE
    speedup = "1x"

    # Not compilable checks
    if analyzer.has_dynamic:
        blockers.append("uses eval/exec/getattr/setattr (dynamic dispatch)")
    if analyzer.has_io:
        blockers.append("I/O bound (not suitable for compilation)")

    if blockers:
        confidence = _compute_confidence(func, analyzer, annotated, unannotated, profile_data, func_lines)
        return CompileCandidate(
            name=func.name, file=file, line=func.lineno, lines=func_lines,
            compiler=Compiler.NONE, estimated_speedup="1x", eligible=False,
            blockers=blockers, missing_annotations=unannotated,
            bottleneck=bottleneck, confidence=confidence,
        )

    # Try numba first (stricter, higher speedup)
    numba_blockers: list[str] = []
    if not _all_params_numeric(func):
        numba_blockers.append("not all parameters have numeric type annotations")
    if analyzer.has_string_ops:
        numba_blockers.append("contains string operations")
    if analyzer.has_dict_set_creation:
        numba_blockers.append("creates dict/set objects")
    if analyzer.has_try:
        numba_blockers.append("contains try/except")
    if analyzer.has_yield:
        numba_blockers.append("is a generator (yield)")
    if analyzer.non_numeric_calls:
        unique = sorted(set(analyzer.non_numeric_calls))[:5]
        numba_blockers.append(f"calls non-numeric functions: {', '.join(unique)}")
    if not analyzer.has_loops:
        numba_blockers.append("no loops (numba not worth it)")

    if not numba_blockers:
        compiler = Compiler.NUMBA
        speedup = "5-100x"
        confidence = _compute_confidence(func, analyzer, annotated, unannotated, profile_data, func_lines)
        return CompileCandidate(
            name=func.name, file=file, line=func.lineno, lines=func_lines,
            compiler=compiler, estimated_speedup=speedup, eligible=True,
            blockers=[], missing_annotations=[],
            bottleneck=bottleneck, confidence=confidence,
        )

    # Try mypyc
    mypyc_blockers: list[str] = []
    has_annotations = _has_return_annotation(func) and len(annotated) > len(unannotated)
    if not has_annotations:
        mypyc_blockers.append("insufficient type annotations")
    if analyzer.has_yield:
        mypyc_blockers.append("is a generator (yield)")
    if analyzer.has_global_mutation:
        mypyc_blockers.append("mutates global state")
    if analyzer.has_kwargs_dynamic:
        mypyc_blockers.append("uses dynamic **kwargs")

    if not mypyc_blockers:
        compiler = Compiler.MYPYC
        speedup = "2-5x"
        confidence = _compute_confidence(func, analyzer, annotated, unannotated, profile_data, func_lines)
        return CompileCandidate(
            name=func.name, file=file, line=func.lineno, lines=func_lines,
            compiler=compiler, estimated_speedup=speedup, eligible=True,
            blockers=[], missing_annotations=unannotated,
            bottleneck=bottleneck, confidence=confidence,
        )

    # Not eligible for either
    all_blockers = numba_blockers + mypyc_blockers
    # Deduplicate
    seen = set()
    unique_blockers = []
    for b in all_blockers:
        if b not in seen:
            seen.add(b)
            unique_blockers.append(b)

    confidence = _compute_confidence(func, analyzer, annotated, unannotated, profile_data, func_lines)
    return CompileCandidate(
        name=func.name, file=file, line=func.lineno, lines=func_lines,
        compiler=Compiler.NONE, estimated_speedup="1x", eligible=False,
        blockers=unique_blockers, missing_annotations=unannotated,
        bottleneck=bottleneck, confidence=confidence,
    )


def _normalize_profile(profile_data) -> dict | None:
    """Convert profile_data to {func_name: time_pct} dict."""
    if profile_data is None:
        return None
    if isinstance(profile_data, dict):
        return profile_data
    # Support list of HotFunction-like objects
    if isinstance(profile_data, list):
        return {item.name: item.time_pct for item in profile_data if hasattr(item, "name")}
    return None


def advise(source: str, profile_data=None) -> list[CompileCandidate]:
    """Analyze source and return compilation recommendations."""
    tree = ast.parse(source)
    prof = _normalize_profile(profile_data)
    candidates = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if isinstance(node, ast.AsyncFunctionDef):
                continue  # async functions not compilable
            candidates.append(_analyze_function(node, "<string>", prof))
    return candidates


def advise_file(path: str | Path, profile_data=None) -> list[CompileCandidate]:
    """Analyze a file and return compilation recommendations."""
    p = Path(path)
    source = p.read_text()
    tree = ast.parse(source)
    prof = _normalize_profile(profile_data)
    candidates = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if isinstance(node, ast.AsyncFunctionDef):
                continue
            candidate = _analyze_function(node, str(p), prof)
            candidates.append(candidate)
    return candidates
