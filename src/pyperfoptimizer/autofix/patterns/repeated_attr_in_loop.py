"""Detect repeated dotted attribute access (3+) in loops → suggest local variable."""

import libcst as cst
from libcst.metadata import PositionProvider

from .base import Match, Pattern


def _attr_to_str(node: cst.BaseExpression) -> str | None:
    if isinstance(node, cst.Name):
        return node.value
    if isinstance(node, cst.Attribute):
        base = _attr_to_str(node.value)
        return f"{base}.{node.attr.value}" if base else None
    return None


def _count_attrs(node: cst.CSTNode, counts: dict[str, int]):
    if isinstance(node, cst.Attribute):
        path = _attr_to_str(node)
        if path and path.count(".") >= 2:
            counts[path] = counts.get(path, 0) + 1
    for child in node.children:
        if isinstance(child, cst.CSTNode):
            _count_attrs(child, counts)


class _Detector(cst.CSTVisitor):
    METADATA_DEPENDENCIES = (PositionProvider,)

    def __init__(self):
        self.matches: list[cst.For] = []

    def visit_For(self, node: cst.For) -> bool:
        counts: dict[str, int] = {}
        _count_attrs(node.body, counts)
        if any(c >= 3 for c in counts.values()):
            self.matches.append(node)
        return False


class RepeatedAttrInLoopPattern(Pattern):
    name = "repeated_attr_in_loop"
    description = "Hoist repeated dotted attribute access out of loops"
    expected_speedup = "1.1-1.4x"
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
                description="Repeated dotted attribute in loop → hoist to local",
                original_code=tree.code_for_node(node).split("\n")[0],
            ))
        return matches

    def transform(self, tree: cst.Module, match: Match) -> cst.Module:
        raise NotImplementedError("Detection only — auto_fix=False")
