"""Pattern registry."""

from .append_to_comprehension import AppendToComprehensionPattern
from .auto_memoize import AutoMemoizePattern
from .dataframe_vectorize import DataFrameVectorizePattern
from .loop_invariant import LoopInvariantPattern
from .membership_test import MembershipTestPattern
from .string_concat import StringConcatPattern
from .unnecessary_list import UnnecessaryListPattern

ALL_PATTERNS = [
    UnnecessaryListPattern(),
    AppendToComprehensionPattern(),
    StringConcatPattern(),
    MembershipTestPattern(),
    LoopInvariantPattern(),
    AutoMemoizePattern(),
    DataFrameVectorizePattern(),
]

__all__ = ["ALL_PATTERNS"]
