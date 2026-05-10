"""Detect list comprehension inside sum/min/max/any/all/join → generator."""

import libcst as cst
from libcst.metadata import PositionProvider

from .base import Match, Pattern

_FUNCS = {"sum", "min", "max", "any", "all", "sorted", "tuple", "frozenset"}


class _Detector(cst.CSTVisitor):
    METADATA_DEPENDENCIES = (PositionProvider,)

    def __init__(self):
        self.matches: list[cst.Call] = []

    def visit_Call(self, node: cst.Call) -> bool:
        is_target = (isinstance(node.func, cst.Name) and node.func.value in _FUNCS)
        is_join = (isinstance(node.func, cst.Attribute) and node.func.attr.value == "join")
        if not (is_target or is_join):
            return True
        if node.args and isinstance(node.args[0].value, cst.ListComp):
            self.matches.append(node)
        return True


class _Transform(cst.CSTTransformer):
    def __init__(self, target: cst.Call):
        self.target = target
        self.done = False

    def leave_Call(self, original_node: cst.Call, updated_node: cst.Call) -> cst.Call:
        if self.done or not original_node.deep_equals(self.target):
            return updated_node
        self.done = True
        lc = updated_node.args[0].value
        gen = cst.GeneratorExp(elt=lc.elt, for_in=lc.for_in)
        new_args = [cst.Arg(value=gen)] + list(updated_node.args[1:])
        return updated_node.with_changes(args=new_args)


class GeneratorInsteadOfListPattern(Pattern):
    name = "generator_instead_of_list"
    description = "Use generator expression instead of list comprehension in aggregation"
    expected_speedup = "1.1-1.5x (memory savings)"
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
                description="List comprehension in aggregation → use generator",
                original_code=tree.code_for_node(node).split("\n")[0],
            ))
        return matches

    def transform(self, tree: cst.Module, match: Match) -> cst.Module:
        return tree.visit(_Transform(match.node))
