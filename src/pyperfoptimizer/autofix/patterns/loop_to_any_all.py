"""Detect for+if+return True/False → any()/all()."""

import libcst as cst
from libcst.metadata import PositionProvider

from .base import Match, Pattern


class _Detector(cst.CSTVisitor):
    METADATA_DEPENDENCIES = (PositionProvider,)

    def __init__(self):
        self.matches: list[cst.For] = []

    def visit_For(self, node: cst.For) -> bool:
        body = node.body.body
        if len(body) != 1 or not isinstance(body[0], cst.If):
            return False
        if_node = body[0]
        if_body = if_node.body.body
        if not (len(if_body) == 1 and isinstance(if_body[0], cst.SimpleStatementLine)):
            return False
        stmts = if_body[0].body
        if len(stmts) == 1 and isinstance(stmts[0], cst.Return):
            ret = stmts[0]
            if isinstance(ret.value, cst.Name) and ret.value.value in ("True", "False"):
                self.matches.append(node)
        return False


class _Transform(cst.CSTTransformer):
    def __init__(self, target: cst.For):
        self.target = target
        self.done = False

    def leave_For(self, original_node: cst.For, updated_node: cst.For) -> cst.BaseStatement:
        if self.done or not original_node.deep_equals(self.target):
            return updated_node
        self.done = True
        if_node = updated_node.body.body[0]
        ret_val = if_node.body.body[0].body[0].value.value
        condition = if_node.test
        func = "any" if ret_val == "True" else "all"
        if func == "all":
            condition = cst.UnaryOperation(operator=cst.Not(), expression=condition)
        gen = cst.GeneratorExp(
            elt=condition,
            for_in=cst.CompFor(target=updated_node.target, iter=updated_node.iter),
        )
        call = cst.Call(func=cst.Name(func), args=[cst.Arg(value=gen)])
        return cst.SimpleStatementLine(body=[cst.Return(value=call)])


class LoopToAnyAllPattern(Pattern):
    name = "loop_to_any_all"
    description = "Replace for+if+return True/False with any()/all() (readability)"
    expected_speedup = "readability (no speed gain)"
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
                description="for+if+return pattern → use any()/all()",
                original_code=tree.code_for_node(node).split("\n")[0],
            ))
        return matches

    def transform(self, tree: cst.Module, match: Match) -> cst.Module:
        return tree.visit(_Transform(match.node))
