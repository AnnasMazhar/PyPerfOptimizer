"""Detect try/except in loop for type conversion → suggest check first."""

import libcst as cst
from libcst.metadata import PositionProvider

from .base import Match, Pattern

_CONVERSION_FUNCS = {"int", "float", "complex"}
_CAUGHT_ERRORS = {"ValueError", "TypeError"}


class _Detector(cst.CSTVisitor):
    METADATA_DEPENDENCIES = (PositionProvider,)

    def __init__(self):
        self.matches: list[cst.For] = []

    def visit_For(self, node: cst.For) -> bool:
        for stmt in node.body.body:
            if isinstance(stmt, cst.Try) and self._is_conversion_try(stmt):
                self.matches.append(node)
                break
        return False

    def _is_conversion_try(self, node: cst.Try) -> bool:
        if not node.handlers:
            return False
        handler = node.handlers[0]
        if not (isinstance(handler.type, cst.Name) and handler.type.value in _CAUGHT_ERRORS):
            return False
        # Check try body has a call to int/float/complex anywhere
        return self._has_conversion(node.body)

    def _has_conversion(self, node) -> bool:
        if isinstance(node, cst.Call) and isinstance(node.func, cst.Name):
            if node.func.value in _CONVERSION_FUNCS:
                return True
        for child in node.children:
            if isinstance(child, cst.CSTNode) and self._has_conversion(child):
                return True
        return False


class ExceptionControlFlowPattern(Pattern):
    name = "exception_control_flow"
    description = "Avoid try/except for type conversion in loops — check first"
    expected_speedup = "2-5x when exceptions are frequent"
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
                description="try/except for conversion in loop → use .isdigit() or filter",
                original_code=tree.code_for_node(node).split("\n")[0],
            ))
        return matches

    def transform(self, tree: cst.Module, match: Match) -> cst.Module:
        raise NotImplementedError("Detection only — auto_fix=False")
