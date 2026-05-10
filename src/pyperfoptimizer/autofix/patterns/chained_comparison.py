"""Detect x >= a and x <= b → a <= x <= b."""

import libcst as cst
from libcst.metadata import PositionProvider

from .base import Match, Pattern

_FLIP = {cst.LessThan: cst.GreaterThan(), cst.LessThanEqual: cst.GreaterThanEqual(),
         cst.GreaterThan: cst.LessThan(), cst.GreaterThanEqual: cst.LessThanEqual()}


class _Detector(cst.CSTVisitor):
    METADATA_DEPENDENCIES = (PositionProvider,)

    def __init__(self):
        self.matches: list[cst.BooleanOperation] = []

    def visit_BooleanOperation(self, node: cst.BooleanOperation) -> bool:
        if not isinstance(node.operator, cst.And):
            return True
        left, right = node.left, node.right
        if not (isinstance(left, cst.Comparison) and isinstance(right, cst.Comparison)):
            return True
        if len(left.comparisons) != 1 or len(right.comparisons) != 1:
            return True
        # Both must compare the same variable
        l_var = self._get_var(left)
        r_var = self._get_var(right)
        if l_var and r_var and l_var.deep_equals(r_var):
            self.matches.append(node)
        return False

    def _get_var(self, cmp: cst.Comparison):
        op = cmp.comparisons[0].operator
        if isinstance(op, (cst.LessThan, cst.LessThanEqual)):
            return cmp.left
        if isinstance(op, (cst.GreaterThan, cst.GreaterThanEqual)):
            return cmp.left
        return None


class _Transform(cst.CSTTransformer):
    def __init__(self, target):
        self.target = target
        self.done = False

    def leave_BooleanOperation(self, original_node, updated_node):
        if self.done or not original_node.deep_equals(self.target):
            return updated_node
        self.done = True
        left_cmp = updated_node.left
        right_cmp = updated_node.right
        # Normalize: extract (bound, op, var) from each comparison
        # e.g. "x >= 0" → var=x, op=>=, bound=0 → becomes "0 <= x"
        l_var, l_bound, l_op = self._normalize(left_cmp)
        r_var, r_bound, r_op = self._normalize(right_cmp)
        if l_var is None or r_var is None:
            return updated_node
        return cst.Comparison(
            left=l_bound,
            comparisons=[
                cst.ComparisonTarget(operator=l_op, comparator=l_var),
                cst.ComparisonTarget(operator=r_op, comparator=r_bound),
            ],
        )

    def _normalize(self, cmp: cst.Comparison):
        """Return (var, bound, op_for_chain) where chain reads: bound op var."""
        op = cmp.comparisons[0].operator
        left = cmp.left
        right = cmp.comparisons[0].comparator
        # x >= 0 → 0 <= x (flip)
        if isinstance(op, (cst.GreaterThan, cst.GreaterThanEqual)):
            return left, right, _FLIP[type(op)]
        # x <= 100 → x <= 100 (keep)
        if isinstance(op, (cst.LessThan, cst.LessThanEqual)):
            return left, right, op
        return None, None, None


class ChainedComparisonPattern(Pattern):
    name = "chained_comparison"
    description = "Merge x >= a and x <= b into a <= x <= b"
    expected_speedup = "1.1-1.2x"
    auto_fix = True

    def detect(self, tree: cst.Module) -> list[Match]:
        wrapper = cst.metadata.MetadataWrapper(tree)
        visitor = _Detector()
        wrapper.visit(visitor)
        matches = []
        for node in visitor.matches:
            pos = wrapper.resolve(PositionProvider).get(node)
            line = pos.start.line if pos else 0
            matches.append(Match(
                node=node, line=line,
                description="Chained comparison → use Python's a <= x <= b",
                original_code=tree.code_for_node(node).split("\n")[0],
            ))
        return matches

    def transform(self, tree: cst.Module, match: Match) -> cst.Module:
        return tree.visit(_Transform(match.node))
