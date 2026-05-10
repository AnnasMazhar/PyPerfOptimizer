"""Hoist loop-invariant method lookups (e.g., list.append)."""

import libcst as cst
from libcst.metadata import PositionProvider

from .base import Match, Pattern


class _DetectAppendInLoop(cst.CSTVisitor):
    METADATA_DEPENDENCIES = (PositionProvider,)

    def __init__(self):
        self.matches: list[tuple[cst.For, str]] = []

    def visit_For(self, node: cst.For) -> bool:
        # Look for `<name>.append(...)` in the loop body
        for stmt in node.body.body:
            if isinstance(stmt, cst.SimpleStatementLine):
                for expr_stmt in stmt.body:
                    if isinstance(expr_stmt, cst.Expr) and isinstance(expr_stmt.value, cst.Call):
                        call = expr_stmt.value
                        if (isinstance(call.func, cst.Attribute)
                                and isinstance(call.func.value, cst.Name)
                                and call.func.attr.value == "append"):
                            self.matches.append((node, call.func.value.value))
                            break
        return False


class _HoistAppend(cst.CSTTransformer):
    """Transform: hoist `name.append` before the loop."""

    def __init__(self, target_var: str):
        self.target_var = target_var
        self.done = False

    def leave_For(self, original_node: cst.For, updated_node: cst.For) -> cst.FlattenSentinel | cst.For:
        if self.done:
            return updated_node

        # Check this loop has target_var.append
        for stmt in updated_node.body.body:
            if isinstance(stmt, cst.SimpleStatementLine):
                for expr_stmt in stmt.body:
                    if (isinstance(expr_stmt, cst.Expr)
                            and isinstance(expr_stmt.value, cst.Call)
                            and isinstance(expr_stmt.value.func, cst.Attribute)
                            and isinstance(expr_stmt.value.func.value, cst.Name)
                            and expr_stmt.value.func.value.value == self.target_var
                            and expr_stmt.value.func.attr.value == "append"):
                        break
                else:
                    continue
                break
        else:
            return updated_node

        self.done = True
        local_name = f"_{self.target_var}_append"

        # Replace name.append(...) with local_name(...) in body
        new_body = []
        for stmt in updated_node.body.body:
            if isinstance(stmt, cst.SimpleStatementLine):
                new_stmts = []
                for expr_stmt in stmt.body:
                    if (isinstance(expr_stmt, cst.Expr)
                            and isinstance(expr_stmt.value, cst.Call)
                            and isinstance(expr_stmt.value.func, cst.Attribute)
                            and isinstance(expr_stmt.value.func.value, cst.Name)
                            and expr_stmt.value.func.value.value == self.target_var
                            and expr_stmt.value.func.attr.value == "append"):
                        new_call = expr_stmt.value.with_changes(func=cst.Name(local_name))
                        new_stmts.append(expr_stmt.with_changes(value=new_call))
                    else:
                        new_stmts.append(expr_stmt)
                new_body.append(stmt.with_changes(body=new_stmts))
            else:
                new_body.append(stmt)

        new_for = updated_node.with_changes(body=updated_node.body.with_changes(body=new_body))

        # Create assignment: _name_append = name.append
        assign = cst.SimpleStatementLine(body=[
            cst.Assign(
                targets=[cst.AssignTarget(target=cst.Name(local_name))],
                value=cst.Attribute(value=cst.Name(self.target_var), attr=cst.Name("append")),
            )
        ])

        return cst.FlattenSentinel([assign, new_for])


class LoopInvariantPattern(Pattern):
    name = "loop_invariant_hoist"
    description = "Hoist repeated method lookups (list.append) out of loops"
    expected_speedup = "1.1-1.3x"

    def detect(self, tree: cst.Module) -> list[Match]:
        wrapper = cst.metadata.MetadataWrapper(tree)
        visitor = _DetectAppendInLoop()
        wrapper.visit(visitor)
        matches = []
        for for_node, var_name in visitor.matches:
            code = tree.code_for_node(for_node).split("\n")[0]
            pos = wrapper.resolve(PositionProvider).get(for_node)
            line = pos.start.line if pos else 0
            matches.append(Match(
                node=for_node,
                line=line,
                description=f"Hoist `{var_name}.append` out of loop",
                original_code=code,
            ))
        return matches

    def transform(self, tree: cst.Module, match: Match) -> cst.Module:
        # Extract var name from description
        var_name = match.description.split("`")[1].split(".")[0]
        return tree.visit(_HoistAppend(var_name))
