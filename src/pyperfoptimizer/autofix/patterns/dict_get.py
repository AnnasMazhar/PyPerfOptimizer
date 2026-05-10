"""Detect try/except KeyError → dict.get()."""

import libcst as cst
from libcst.metadata import PositionProvider

from .base import Match, Pattern


class _Detector(cst.CSTVisitor):
    METADATA_DEPENDENCIES = (PositionProvider,)

    def __init__(self):
        self.matches: list[cst.Try] = []

    def visit_Try(self, node: cst.Try) -> bool:
        if len(node.handlers) != 1:
            return False
        handler = node.handlers[0]
        if not (isinstance(handler.type, cst.Name) and handler.type.value == "KeyError"):
            return False
        try_body = node.body.body
        if not (len(try_body) == 1 and isinstance(try_body[0], cst.SimpleStatementLine)
                and len(try_body[0].body) == 1 and isinstance(try_body[0].body[0], cst.Assign)):
            return False
        assign = try_body[0].body[0]
        if not isinstance(assign.value, cst.Subscript):
            return False
        exc_body = handler.body.body
        if not (len(exc_body) == 1 and isinstance(exc_body[0], cst.SimpleStatementLine)
                and len(exc_body[0].body) == 1 and isinstance(exc_body[0].body[0], cst.Assign)):
            return False
        self.matches.append(node)
        return False


class _Transform(cst.CSTTransformer):
    def __init__(self, target: cst.Try):
        self.target = target
        self.done = False

    def leave_Try(self, original_node: cst.Try, updated_node: cst.Try) -> cst.BaseStatement:
        if self.done or not original_node.deep_equals(self.target):
            return updated_node
        self.done = True
        assign = updated_node.body.body[0].body[0]
        subscript = assign.value
        default_val = updated_node.handlers[0].body.body[0].body[0].value
        dict_name = subscript.value
        key = subscript.slice[0].slice.value
        call = cst.Call(
            func=cst.Attribute(value=dict_name, attr=cst.Name("get")),
            args=[cst.Arg(value=key), cst.Arg(value=default_val)],
        )
        new_assign = assign.with_changes(value=call)
        return cst.SimpleStatementLine(body=[new_assign])


class DictGetPattern(Pattern):
    name = "dict_get"
    description = "Replace try/except KeyError with dict.get(key, default)"
    expected_speedup = "1.5-3x"
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
                description="try/except KeyError → dict.get(key, default)",
                original_code=tree.code_for_node(node).split("\n")[0],
            ))
        return matches

    def transform(self, tree: cst.Module, match: Match) -> cst.Module:
        return tree.visit(_Transform(match.node))
