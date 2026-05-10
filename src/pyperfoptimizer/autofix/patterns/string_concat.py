"""Convert string concatenation in loops to str.join."""

import libcst as cst
from libcst.metadata import PositionProvider

from .base import Match, Pattern


class _DetectStringConcat(cst.CSTVisitor):
    METADATA_DEPENDENCIES = (PositionProvider,)

    def __init__(self):
        self.matches: list[tuple[cst.For, str, cst.BaseExpression]] = []

    def visit_For(self, node: cst.For) -> bool:
        body = node.body.body
        if len(body) != 1:
            return False
        stmt = body[0]
        if not isinstance(stmt, cst.SimpleStatementLine) or len(stmt.body) != 1:
            return False
        aug = stmt.body[0]
        # s += expr
        if (isinstance(aug, cst.AugAssign)
                and isinstance(aug.target, cst.Name)
                and isinstance(aug.operator, cst.AddAssign)):
            self.matches.append((node, aug.target.value, aug.value))
        return False


class StringConcatPattern(Pattern):
    name = "string_concat_to_join"
    description = "Convert string concatenation in loops to str.join"
    expected_speedup = "2-10x"

    def detect(self, tree: cst.Module) -> list[Match]:
        wrapper = cst.metadata.MetadataWrapper(tree)
        visitor = _DetectStringConcat()
        wrapper.visit(visitor)
        matches = []
        for for_node, var, expr in visitor.matches:
            pos = wrapper.resolve(PositionProvider).get(for_node)
            line = pos.start.line if pos else 0
            code = tree.code_for_node(for_node).split("\n")[0]
            matches.append(Match(
                node=(for_node, var, expr),
                line=line,
                description=f"Convert `{var} +=` loop to `''.join(...)`",
                original_code=code,
            ))
        return matches

    def transform(self, tree: cst.Module, match: Match) -> cst.Module:
        for_node, var, expr = match.node

        # Build: var = ''.join(expr for target in iter)
        genexp = cst.GeneratorExp(
            elt=expr,
            for_in=cst.CompFor(target=for_node.target, iter=for_node.iter),
        )
        join_call = cst.Call(
            func=cst.Attribute(value=cst.SimpleString("''"), attr=cst.Name("join")),
            args=[cst.Arg(value=genexp)],
        )
        assign = cst.SimpleStatementLine(body=[
            cst.Assign(
                targets=[cst.AssignTarget(target=cst.Name(var))],
                value=join_call,
            )
        ])

        class _Replace(cst.CSTTransformer):
            def __init__(self):
                self.done = False

            def leave_For(self, original, updated):
                if self.done or not original.deep_equals(for_node):
                    return updated
                self.done = True
                return cst.FlattenSentinel([assign])

        return tree.visit(_Replace())
