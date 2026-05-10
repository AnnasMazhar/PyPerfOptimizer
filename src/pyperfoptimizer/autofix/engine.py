"""Core auto-optimization engine."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import libcst as cst

from .patterns import ALL_PATTERNS
from .patterns.base import Match, Optimization, Pattern

if TYPE_CHECKING:
    from .profile_loader import HotFunction


def _in_hot_path(line: int, hot_functions: list[HotFunction] | None) -> bool:
    """Check if a line falls within any hot function (within 50 lines of start)."""
    if hot_functions is None:
        return True
    return any(hf.line <= line <= hf.line + 50 for hf in hot_functions)


def scan(source: str, patterns: list[Pattern] | None = None, hot_functions: list[HotFunction] | None = None) -> list[Optimization]:
    """Scan source code and return detected optimizations.

    If hot_functions is provided, only returns optimizations in hot paths.
    """
    patterns = patterns or ALL_PATTERNS
    tree = cst.parse_module(source)
    optimizations = []

    for pattern in patterns:
        matches = pattern.detect(tree)
        for match in matches:
            if not _in_hot_path(match.line, hot_functions):
                continue
            # Generate optimized code preview
            try:
                transformed = pattern.transform(tree, match)
                optimized_code = transformed.code[:200]
            except NotImplementedError:
                optimized_code = "(detection only — manual fix required)"
            optimizations.append(Optimization(
                pattern_name=pattern.name,
                line=match.line,
                description=match.description,
                original_code=match.original_code,
                optimized_code=optimized_code,
                expected_speedup=pattern.expected_speedup,
            ))

    return optimizations


def fix(source: str, patterns: list[Pattern] | None = None, hot_functions: list[HotFunction] | None = None) -> str:
    """Apply all safe optimizations and return transformed source.

    If hot_functions is provided, only fixes optimizations in hot paths.
    Skips patterns with auto_fix=False.
    """
    patterns = patterns or ALL_PATTERNS
    tree = cst.parse_module(source)

    for pattern in patterns:
        if not getattr(pattern, "auto_fix", True):
            continue
        matches = pattern.detect(tree)
        for match in matches:
            if not _in_hot_path(match.line, hot_functions):
                continue
            tree = pattern.transform(tree, match)
            # Re-detect after each transform (tree changed)
            break  # one at a time per pattern to avoid stale refs

    return tree.code


def scan_file(path: str | Path, hot_functions: list[HotFunction] | None = None) -> list[Optimization]:
    """Scan a file for optimizations."""
    source = Path(path).read_text()
    return scan(source, hot_functions=hot_functions)


def fix_file(path: str | Path, inplace: bool = False, hot_functions: list[HotFunction] | None = None) -> str:
    """Fix a file. Returns transformed source. Writes if inplace=True."""
    p = Path(path)
    source = p.read_text()
    result = fix(source, hot_functions=hot_functions)
    if inplace:
        p.write_text(result)
    return result
