"""Compilation advisor — analyzes functions for compiler eligibility."""

from .compile_advisor import (
    Bottleneck,
    CompileCandidate,
    Compiler,
    advise,
    advise_file,
)

__all__ = ["Bottleneck", "CompileCandidate", "Compiler", "advise", "advise_file"]
