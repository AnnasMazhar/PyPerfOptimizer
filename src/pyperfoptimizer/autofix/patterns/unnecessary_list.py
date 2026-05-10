"""Remove unnecessary list() wrapping in for loops."""

import libcst as cst
from libcst.metadata import PositionProvider

from .base import Match, Pattern


class _DetectUnnecessaryList(cst.CSTVisitor):
    METADATA_DEPENDENCIES = (PositionProvider,)

    def __init__(self):
        self.matches: list[cst.For] = []

    def visit_For(self, node: cst.For) -> bool:
        # for x in list(something): ...
        if (isinstance(node.iter, cst.Call)
                and isinstance(node.iter.func, cst.Name)
                and node.iter.func.value == "list"
                and len(node.iter.args) == 1
                and node.iter.args[0].keyword is None):
            self.matches.append(node)
        return False


class UnnecessaryListPattern(Pattern):
    name = "unnecessary_list"
    description = "Remove unnecessary list() wrapping in for-loop iterables"
    expected_speedup = "1.1-1.5x"

    def detect(self, tree: cst.Module) -> list[Match]:
        wrapper = cst.metadata.MetadataWrapper(tree)
        visitor = _DetectUnnecessaryList()
        wrapper.visit(visitor)
        matches = []
        for for_node in visitor.matches:
            pos = wrapper.resolve(PositionProvider).get(for_node)
            line = pos.start.line if pos else 0
            code = tree.code_for_node(for_node).split("\n")[0]
            matches.append(Match(
                node=for_node,
                line=line,
                description="Remove unnecessary `list()` wrapping",
                original_code=code,
            ))
        return matches

    def transform(self, tree: cst.Module, match: Match) -> cst.Module:
        for_node = match.node

        class _RemoveList(cst.CSTTransformer):
            def __init__(self):
                self.done = False

            def leave_For(self, original, updated):
                if self.done or not original.deep_equals(for_node):
                    return updated
                self.done = True
                # Replace list(x) with x
                inner = updated.iter.args[0].value
                return updated.with_changes(iter=inner)

        return tree.visit(_RemoveList())
