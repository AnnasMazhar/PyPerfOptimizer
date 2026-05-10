"""Detect unnecessary list() wrapping a list literal."""

import libcst as cst
from libcst.metadata import PositionProvider

from .base import Match, Pattern


class _Detector(cst.CSTVisitor):
    METADATA_DEPENDENCIES = (PositionProvider,)

    def __init__(self):
        self.matches: list[cst.Call] = []

    def visit_Call(self, node: cst.Call) -> bool:
        if (isinstance(node.func, cst.Name) and node.func.value == "list"
                and len(node.args) == 1
                and isinstance(node.args[0].value, cst.List)):
            self.matches.append(node)
        return True


class _Transform(cst.CSTTransformer):
    def __init__(self, target: cst.Call):
        self.target = target
        self.done = False

    def leave_Call(self, original_node, updated_node):
        if self.done or not original_node.deep_equals(self.target):
            return updated_node
        self.done = True
        return updated_node.args[0].value


class UnnecessaryCopyPattern(Pattern):
    name = "unnecessary_copy"
    description = "Remove unnecessary list() wrapping a list literal"
    expected_speedup = "1.1-1.3x"
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
                description="list([...]) → just use [...]",
                original_code=tree.code_for_node(node).split("\n")[0],
            ))
        return matches

    def transform(self, tree: cst.Module, match: Match) -> cst.Module:
        return tree.visit(_Transform(match.node))
