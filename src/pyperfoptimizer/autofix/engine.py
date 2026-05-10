"""Core auto-optimization engine."""

from pathlib import Path

import libcst as cst

from .patterns import ALL_PATTERNS
from .patterns.base import Match, Optimization, Pattern


def scan(source: str, patterns: list[Pattern] | None = None) -> list[Optimization]:
    """Scan source code and return detected optimizations."""
    patterns = patterns or ALL_PATTERNS
    tree = cst.parse_module(source)
    optimizations = []

    for pattern in patterns:
        matches = pattern.detect(tree)
        for match in matches:
            # Generate optimized code preview
            transformed = pattern.transform(tree, match)
            optimizations.append(Optimization(
                pattern_name=pattern.name,
                line=match.line,
                description=match.description,
                original_code=match.original_code,
                optimized_code=transformed.code[:200],  # preview
                expected_speedup=pattern.expected_speedup,
            ))

    return optimizations


def fix(source: str, patterns: list[Pattern] | None = None) -> str:
    """Apply all safe optimizations and return transformed source."""
    patterns = patterns or ALL_PATTERNS
    tree = cst.parse_module(source)

    for pattern in patterns:
        matches = pattern.detect(tree)
        for match in matches:
            tree = pattern.transform(tree, match)
            # Re-detect after each transform (tree changed)
            break  # one at a time per pattern to avoid stale refs

    return tree.code


def scan_file(path: str | Path) -> list[Optimization]:
    """Scan a file for optimizations."""
    source = Path(path).read_text()
    return scan(source)


def fix_file(path: str | Path, inplace: bool = False) -> str:
    """Fix a file. Returns transformed source. Writes if inplace=True."""
    p = Path(path)
    source = p.read_text()
    result = fix(source)
    if inplace:
        p.write_text(result)
    return result
