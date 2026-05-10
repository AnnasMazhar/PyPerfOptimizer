"""Detect re.match/search/sub/findall with string pattern inside functions."""

import libcst as cst
from libcst.metadata import PositionProvider

from .base import Match, Pattern

_RE_FUNCS = {"match", "search", "sub", "findall", "fullmatch", "split"}


class _Detector(cst.CSTVisitor):
    METADATA_DEPENDENCIES = (PositionProvider,)

    def __init__(self):
        self.matches: list[cst.Call] = []
        self._in_function = 0

    def visit_FunctionDef(self, node: cst.FunctionDef) -> bool:
        self._in_function += 1
        return True

    def leave_FunctionDef(self, node: cst.FunctionDef) -> None:
        self._in_function -= 1

    def visit_Call(self, node: cst.Call) -> bool:
        if self._in_function == 0:
            return False
        if (isinstance(node.func, cst.Attribute)
                and isinstance(node.func.value, cst.Name)
                and node.func.value.value == "re"
                and node.func.attr.value in _RE_FUNCS
                and node.args
                and isinstance(node.args[0].value, (cst.SimpleString, cst.ConcatenatedString))):
            self.matches.append(node)
        return False


class RegexPrecompilePattern(Pattern):
    name = "regex_precompile"
    description = "Compile regex patterns at module level instead of per-call"
    expected_speedup = "2-10x for hot paths"
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
                description=f"re.{node.func.attr.value}() with string pattern — precompile at module level",
                original_code=tree.code_for_node(node).split("\n")[0],
            ))
        return matches

    def transform(self, tree: cst.Module, match: Match) -> cst.Module:
        raise NotImplementedError("Detection only — auto_fix=False")
