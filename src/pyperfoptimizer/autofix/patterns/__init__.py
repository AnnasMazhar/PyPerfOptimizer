"""Pattern registry."""

from .append_to_comprehension import AppendToComprehensionPattern
from .loop_invariant import LoopInvariantPattern
from .membership_test import MembershipTestPattern
from .string_concat import StringConcatPattern
from .unnecessary_list import UnnecessaryListPattern

ALL_PATTERNS = [
    LoopInvariantPattern(),
    AppendToComprehensionPattern(),
    StringConcatPattern(),
    UnnecessaryListPattern(),
    MembershipTestPattern(),
]

__all__ = ["ALL_PATTERNS"]
