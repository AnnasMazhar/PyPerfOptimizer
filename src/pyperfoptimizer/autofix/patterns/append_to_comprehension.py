"""Convert append-in-loop to list comprehension."""

import libcst as cst
from libcst.metadata import PositionProvider

from .base import Match, Pattern


class _DetectAppendLoop(cst.CSTVisitor):
    METADATA_DEPENDENCIES = (PositionProvider,)

    def __init__(self):
        self.matches: list[tuple[cst.For, str, cst.BaseExpression, cst.BaseExpression | None]] = []

    def visit_For(self, node: cst.For) -> bool:
        body = node.body.body
        if len(body) != 1:
            return False
        stmt = body[0]

        # Simple: result.append(expr)
        if isinstance(stmt, cst.SimpleStatementLine) and len(stmt.body) == 1:
            expr_stmt = stmt.body[0]
            if (isinstance(expr_stmt, cst.Expr)
                    and isinstance(expr_stmt.value, cst.Call)
                    and isinstance(expr_stmt.value.func, cst.Attribute)
                    and isinstance(expr_stmt.value.func.value, cst.Name)
                    and expr_stmt.value.func.attr.value == "append"
                    and len(expr_stmt.value.args) == 1):
                var = expr_stmt.value.func.value.value
                append_arg = expr_stmt.value.args[0].value
                self.matches.append((node, var, append_arg, None))

        # Conditional: if cond: result.append(expr)
        elif isinstance(stmt, cst.If) and stmt.orelse is None:
            if_body = stmt.body.body
            if len(if_body) == 1 and isinstance(if_body[0], cst.SimpleStatementLine):
                inner = if_body[0].body
                if (len(inner) == 1
                        and isinstance(inner[0], cst.Expr)
                        and isinstance(inner[0].value, cst.Call)
                        and isinstance(inner[0].value.func, cst.Attribute)
                        and isinstance(inner[0].value.func.value, cst.Name)
                        and inner[0].value.func.attr.value == "append"
                        and len(inner[0].value.args) == 1):
                    var = inner[0].value.func.value.value
                    append_arg = inner[0].value.args[0].value
                    self.matches.append((node, var, append_arg, stmt.test))

        return False


class _ReplaceAppendLoop(cst.CSTTransformer):
    def __init__(self, for_node: cst.For, var: str, expr: cst.BaseExpression,
                 condition: cst.BaseExpression | None):
        self.for_node = for_node
        self.var = var
        self.expr = expr
        self.condition = condition
        self.done = False

    def leave_For(self, original_node: cst.For, updated_node: cst.For) -> cst.RemovalSentinel | cst.For:
        if self.done or not original_node.deep_equals(self.for_node):
            return updated_node
        self.done = True
        return cst.RemovalSentinel.REMOVE

    def leave_SimpleStatementLine(self, original_node, updated_node):
        return updated_node


class AppendToComprehensionPattern(Pattern):
    name = "append_to_comprehension"
    description = "Convert append-in-loop to list comprehension"
    expected_speedup = "1.3-2x"

    def detect(self, tree: cst.Module) -> list[Match]:
        wrapper = cst.metadata.MetadataWrapper(tree)
        visitor = _DetectAppendLoop()
        wrapper.visit(visitor)
        matches = []
        for for_node, var, expr, cond in visitor.matches:
            pos = wrapper.resolve(PositionProvider).get(for_node)
            line = pos.start.line if pos else 0
            code = tree.code_for_node(for_node).split("\n")[0]
            desc = f"Convert `{var}.append` loop to list comprehension"
            matches.append(Match(node=(for_node, var, expr, cond), line=line,
                                 description=desc, original_code=code))
        return matches

    def transform(self, tree: cst.Module, match: Match) -> cst.Module:
        for_node, var, expr, condition = match.node

        # Build comprehension
        comp_for = cst.CompFor(
            target=for_node.target,
            iter=for_node.iter,
            ifs=[cst.CompIf(test=condition)] if condition else [],
        )
        listcomp = cst.ListComp(elt=expr, for_in=comp_for)

        # Build: var = [expr for target in iter (if cond)]
        assign = cst.SimpleStatementLine(body=[
            cst.Assign(
                targets=[cst.AssignTarget(target=cst.Name(var))],
                value=listcomp,
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
