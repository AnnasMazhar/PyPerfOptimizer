"""Pattern registry."""

from .append_to_comprehension import AppendToComprehensionPattern
from .auto_memoize import AutoMemoizePattern
from .chained_comparison import ChainedComparisonPattern
from .dataframe_vectorize import DataFrameVectorizePattern
from .defaultdict_opportunity import DefaultdictOpportunityPattern
from .dict_get import DictGetPattern
from .exception_control_flow import ExceptionControlFlowPattern
from .generator_instead_of_list import GeneratorInsteadOfListPattern
from .loop_invariant import LoopInvariantPattern
from .loop_to_any_all import LoopToAnyAllPattern
from .membership_test import MembershipTestPattern
from .multiple_isinstance import MultipleIsinstancePattern
from .regex_precompile import RegexPrecompilePattern
from .repeated_attr_in_loop import RepeatedAttrInLoopPattern
from .string_concat import StringConcatPattern
from .unnecessary_copy import UnnecessaryCopyPattern
from .unnecessary_list import UnnecessaryListPattern

ALL_PATTERNS = [
    UnnecessaryListPattern(),
    AppendToComprehensionPattern(),
    StringConcatPattern(),
    MembershipTestPattern(),
    LoopInvariantPattern(),
    AutoMemoizePattern(),
    DataFrameVectorizePattern(),
    # New patterns
    RegexPrecompilePattern(),
    LoopToAnyAllPattern(),
    DictGetPattern(),
    MultipleIsinstancePattern(),
    DefaultdictOpportunityPattern(),
    GeneratorInsteadOfListPattern(),
    RepeatedAttrInLoopPattern(),
    UnnecessaryCopyPattern(),
    ChainedComparisonPattern(),
    ExceptionControlFlowPattern(),
]

__all__ = ["ALL_PATTERNS"]
