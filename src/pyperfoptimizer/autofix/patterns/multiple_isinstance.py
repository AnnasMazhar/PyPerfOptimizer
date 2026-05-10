"""Detect chained isinstance() calls → tuple form."""

import libcst as cst
from libcst.metadata import PositionProvider

from .base import Match, Pattern


def _collect_chain(node: cst.BooleanOperation) -> list[cst.Call] | None:
    if not isinstance(node.operator, cst.Or):
        return None
    calls = []
    for part in (node.left, node.right):
        if isinstance(part, cst.BooleanOperation):
            sub = _collect_chain(part)
            if sub is None:
                return None
            calls.extend(sub)
        elif (isinstance(part, cst.Call) and isinstance(part.func, cst.Name)
              and part.func.value == "isinstance" and len(part.args) == 2):
            calls.append(part)
        else:
            return None
    if len(calls) < 2:
        return None
    first = calls[0].args[0].value
    if not all(first.deep_equals(c.args[0].value) for c in calls[1:]):
        return None
    return calls


class _Detector(cst.CSTVisitor):
    METADATA_DEPENDENCIES = (PositionProvider,)

    def __init__(self):
        self.matches: list[tuple[cst.BooleanOperation, list[cst.Call]]] = []

    def visit_BooleanOperation(self, node: cst.BooleanOperation) -> bool:
        calls = _collect_chain(node)
        if calls:
            self.matches.append((node, calls))
            return False
        return True


class _Transform(cst.CSTTransformer):
    def __init__(self, target, calls):
        self.target = target
        self.calls = calls
        self.done = False

    def leave_BooleanOperation(self, original_node, updated_node):
        if self.done or not original_node.deep_equals(self.target):
            return updated_node
        self.done = True
        types = [c.args[1].value for c in self.calls]
        tup = cst.Tuple(elements=[cst.Element(value=t) for t in types])
        return cst.Call(
            func=cst.Name("isinstance"),
            args=[cst.Arg(self.calls[0].args[0].value), cst.Arg(tup)],
        )


class MultipleIsinstancePattern(Pattern):
    name = "multiple_isinstance"
    description = "Merge chained isinstance() calls into tuple form"
    expected_speedup = "1.1-1.5x"
    auto_fix = True

    def detect(self, tree: cst.Module) -> list[Match]:
        wrapper = cst.metadata.MetadataWrapper(tree)
        visitor = _Detector()
        wrapper.visit(visitor)
        matches = []
        for node, _ in visitor.matches:
            pos = wrapper.resolve(PositionProvider).get(node)
            line = pos.start.line if pos else 0
            matches.append(Match(
                node=node, line=line,
                description="Chained isinstance() → isinstance(x, (A, B, ...))",
                original_code=tree.code_for_node(node).split("\n")[0],
            ))
        return matches

    def transform(self, tree: cst.Module, match: Match) -> cst.Module:
        calls = _collect_chain(match.node)
        return tree.visit(_Transform(match.node, calls))
