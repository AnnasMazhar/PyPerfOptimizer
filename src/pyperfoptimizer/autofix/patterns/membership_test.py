"""Convert list membership tests to set literals."""

import libcst as cst
from libcst.metadata import PositionProvider

from .base import Match, Pattern


class _DetectListMembership(cst.CSTVisitor):
    METADATA_DEPENDENCIES = (PositionProvider,)

    def __init__(self):
        self.matches: list[cst.Comparison] = []

    def visit_Comparison(self, node: cst.Comparison) -> bool:
        # x in [1, 2, 3] or x not in [1, 2, 3]
        for target in node.comparisons:
            op = target.operator
            if isinstance(op, (cst.In, cst.NotIn)):
                if (isinstance(target.comparator, cst.List)
                        and len(target.comparator.elements) >= 3
                        and all(isinstance(el.value, (cst.Integer, cst.Float,
                                                       cst.SimpleString, cst.ConcatenatedString,
                                                       cst.FormattedString, cst.Name))
                                for el in target.comparator.elements)):
                    self.matches.append(node)
        return False


class MembershipTestPattern(Pattern):
    name = "membership_test_set"
    description = "Convert list literal in membership test to set literal"
    expected_speedup = "2-4x"

    def detect(self, tree: cst.Module) -> list[Match]:
        wrapper = cst.metadata.MetadataWrapper(tree)
        visitor = _DetectListMembership()
        wrapper.visit(visitor)
        matches = []
        for comp_node in visitor.matches:
            pos = wrapper.resolve(PositionProvider).get(comp_node)
            line = pos.start.line if pos else 0
            code = tree.code_for_node(comp_node)
            matches.append(Match(
                node=comp_node,
                line=line,
                description="Use set literal instead of list for membership test",
                original_code=code,
            ))
        return matches

    def transform(self, tree: cst.Module, match: Match) -> cst.Module:
        comp_node = match.node

        class _ListToSet(cst.CSTTransformer):
            def __init__(self):
                self.done = False

            def leave_Comparison(self, original, updated):
                if self.done or not original.deep_equals(comp_node):
                    return updated
                self.done = True
                new_comparisons = []
                for target in updated.comparisons:
                    if (isinstance(target.operator, (cst.In, cst.NotIn))
                            and isinstance(target.comparator, cst.List)):
                        # Convert List to Set
                        elements = [cst.Element(value=el.value) for el in target.comparator.elements]
                        set_node = cst.Set(elements=elements)
                        new_comparisons.append(target.with_changes(comparator=set_node))
                    else:
                        new_comparisons.append(target)
                return updated.with_changes(comparisons=new_comparisons)

        return tree.visit(_ListToSet())
