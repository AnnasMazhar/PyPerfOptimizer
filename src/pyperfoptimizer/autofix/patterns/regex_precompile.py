"""Detect and fix re.match/search/sub/findall with string pattern inside functions."""

import libcst as cst
from libcst.metadata import PositionProvider

from .base import Match, Pattern

_RE_FUNCS = {"match", "search", "sub", "findall", "fullmatch", "split"}


def _is_re_call_with_literal(node: cst.Call) -> bool:
    return (isinstance(node.func, cst.Attribute)
            and isinstance(node.func.value, cst.Name)
            and node.func.value.value == "re"
            and node.func.attr.value in _RE_FUNCS
            and node.args
            and isinstance(node.args[0].value, (cst.SimpleString, cst.ConcatenatedString, cst.FormattedString)))


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
        if _is_re_call_with_literal(node):
            self.matches.append(node)
        return False


# Positional index of 'flags' arg (0-based) for each re function
_FLAGS_POS = {
    "match": 2, "search": 2, "fullmatch": 2,
    "findall": 2, "sub": 4, "split": 3,
}


class _RegexTransformer(cst.CSTTransformer):
    """Single-pass transformer: replaces re.func(pattern, ...) with _RE_N.func(...)."""

    def __init__(self):
        self.assignments: list[cst.SimpleStatementLine] = []
        self._counter = 0
        self._in_function = 0

    def visit_FunctionDef(self, node: cst.FunctionDef) -> bool:
        self._in_function += 1
        return True

    def leave_FunctionDef(self, original: cst.FunctionDef, updated: cst.FunctionDef) -> cst.FunctionDef:
        self._in_function -= 1
        return updated

    def leave_Call(self, original: cst.Call, updated: cst.Call) -> cst.BaseExpression:
        if self._in_function == 0:
            return updated
        if not _is_re_call_with_literal(original):
            return updated

        func_name = original.func.attr.value
        pattern_arg = updated.args[0].value
        remaining_args = list(updated.args[1:])

        # Extract flags
        flags_arg = None
        new_remaining = []
        flags_pos = _FLAGS_POS.get(func_name, -1)

        for i, arg in enumerate(remaining_args):
            if arg.keyword and arg.keyword.value == "flags":
                flags_arg = arg.value
            elif not arg.keyword and (i + 1) == flags_pos:
                flags_arg = arg.value
            else:
                new_remaining.append(arg)

        # Build compile args
        compile_args = [cst.Arg(value=pattern_arg)]
        if flags_arg:
            compile_args.append(cst.Arg(value=flags_arg))

        # Create variable
        var_name = f"_RE_{self._counter}"
        self._counter += 1

        assign = cst.SimpleStatementLine(body=[
            cst.Assign(
                targets=[cst.AssignTarget(target=cst.Name(var_name))],
                value=cst.Call(
                    func=cst.Attribute(value=cst.Name("re"), attr=cst.Name("compile")),
                    args=compile_args,
                ),
            )
        ])
        self.assignments.append(assign)

        # Strip trailing comma from last remaining arg
        if new_remaining:
            last = new_remaining[-1]
            new_remaining[-1] = last.with_changes(comma=cst.MaybeSentinel.DEFAULT)

        return cst.Call(
            func=cst.Attribute(value=cst.Name(var_name), attr=cst.Name(func_name)),
            args=new_remaining,
        )


class RegexPrecompilePattern(Pattern):
    name = "regex_precompile"
    description = "Compile regex patterns at module level instead of per-call"
    expected_speedup = "2-10x for hot paths"
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
                description=f"re.{node.func.attr.value}() with string pattern — precompile at module level",
                original_code=tree.code_for_node(node).split("\n")[0],
            ))
        return matches

    def transform(self, tree: cst.Module, match: Match) -> cst.Module:
        transformer = _RegexTransformer()
        new_tree = tree.visit(transformer)

        if not transformer.assignments:
            return tree

        # Insert assignments after imports, before first function/class
        new_body = list(new_tree.body)
        insert_idx = 0
        for i, stmt in enumerate(new_body):
            if isinstance(stmt, cst.SimpleStatementLine):
                if stmt.body and isinstance(stmt.body[0], (cst.Import, cst.ImportFrom)):
                    insert_idx = i + 1
            elif isinstance(stmt, (cst.FunctionDef, cst.ClassDef)):
                break
            else:
                insert_idx = i + 1

        # Add blank line before assignments block
        assignments = list(transformer.assignments)
        assignments[0] = assignments[0].with_changes(leading_lines=[cst.EmptyLine()])

        new_body = new_body[:insert_idx] + assignments + new_body[insert_idx:]
        return new_tree.with_changes(body=new_body)
