"""Detect if-not-in-dict pattern → suggest defaultdict."""

import libcst as cst
from libcst.metadata import PositionProvider

from .base import Match, Pattern


class _Detector(cst.CSTVisitor):
    METADATA_DEPENDENCIES = (PositionProvider,)

    def __init__(self):
        self.matches: list[cst.If] = []

    def visit_If(self, node: cst.If) -> bool:
        test = node.test
        if not (isinstance(test, cst.Comparison) and len(test.comparisons) == 1
                and isinstance(test.comparisons[0].operator, cst.NotIn)):
            return True
        body = node.body.body
        if not (len(body) == 1 and isinstance(body[0], cst.SimpleStatementLine)
                and len(body[0].body) == 1 and isinstance(body[0].body[0], cst.Assign)):
            return True
        assign = body[0].body[0]
        if len(assign.targets) == 1 and isinstance(assign.targets[0].target, cst.Subscript):
            self.matches.append(node)
        return True


class DefaultdictOpportunityPattern(Pattern):
    name = "defaultdict_opportunity"
    description = "Replace if-not-in-dict init pattern with collections.defaultdict"
    expected_speedup = "1.2-1.5x"
    auto_fix = False

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
                description="if-not-in-dict init → use collections.defaultdict",
                original_code=tree.code_for_node(node).split("\n")[0],
            ))
        return matches

    def transform(self, tree: cst.Module, match: Match) -> cst.Module:
        raise NotImplementedError("Detection only — auto_fix=False")
