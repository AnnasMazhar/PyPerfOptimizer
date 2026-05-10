"""Base class for optimization patterns."""

from dataclasses import dataclass, field
from typing import Any

import libcst as cst


@dataclass
class Match:
    """A detected anti-pattern instance."""
    node: Any
    line: int
    description: str
    original_code: str


@dataclass
class Optimization:
    """A proposed optimization."""
    pattern_name: str
    line: int
    description: str
    original_code: str
    optimized_code: str
    expected_speedup: str


class Pattern:
    """Base class for optimization patterns."""

    name: str = ""
    description: str = ""
    expected_speedup: str = ""

    def detect(self, tree: cst.Module) -> list[Match]:
        """Find all instances of this anti-pattern."""
        raise NotImplementedError

    def transform(self, tree: cst.Module, match: Match) -> cst.Module:
        """Apply the optimization for a specific match."""
        raise NotImplementedError
