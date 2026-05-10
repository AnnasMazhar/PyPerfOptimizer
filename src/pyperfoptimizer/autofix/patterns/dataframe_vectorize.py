"""Detect pandas DataFrame anti-patterns and transform to vectorized operations."""

import libcst as cst
from libcst.metadata import PositionProvider

from .base import Match, Pattern


class _DetectIterrowsArithmetic(cst.CSTVisitor):
    """Detect: results=[]; for idx,row in df.iterrows(): results.append(row['a']+row['b']); df['c']=results"""
    METADATA_DEPENDENCIES = (PositionProvider,)

    def __init__(self):
        self.matches: list[tuple[cst.For, str, str, dict]] = []  # (for_node, df_name, list_var, info)

    def visit_For(self, node: cst.For) -> bool:
        # Check: for idx, row in <df>.iterrows()
        if not (isinstance(node.iter, cst.Call)
                and isinstance(node.iter.func, cst.Attribute)
                and node.iter.func.attr.value == "iterrows"
                and isinstance(node.iter.func.value, cst.Name)
                and isinstance(node.target, cst.Tuple)
                and len(node.target.elements) == 2):
            return False

        df_name = node.iter.func.value.value
        row_var = node.target.elements[1].value
        if not isinstance(row_var, cst.Name):
            return False
        row_name = row_var.value

        body = node.body.body
        if len(body) != 1:
            return False
        stmt = body[0]

        # Pattern 1: results.append(row['a'] + row['b'])
        if isinstance(stmt, cst.SimpleStatementLine) and len(stmt.body) == 1:
            expr_stmt = stmt.body[0]
            if (isinstance(expr_stmt, cst.Expr)
                    and isinstance(expr_stmt.value, cst.Call)
                    and isinstance(expr_stmt.value.func, cst.Attribute)
                    and isinstance(expr_stmt.value.func.value, cst.Name)
                    and expr_stmt.value.func.attr.value == "append"
                    and len(expr_stmt.value.args) == 1):
                list_var = expr_stmt.value.func.value.value
                append_arg = expr_stmt.value.args[0].value
                cols = _extract_arithmetic_cols(append_arg, row_name)
                if cols:
                    self.matches.append((node, df_name, list_var,
                                         {"type": "arithmetic", "cols": cols, "op": _get_op(append_arg)}))

        # Pattern 3: if row['value'] > 10: results.append(row)
        elif isinstance(stmt, cst.If) and stmt.orelse is None:
            if_body = stmt.body.body
            if len(if_body) == 1 and isinstance(if_body[0], cst.SimpleStatementLine):
                inner = if_body[0].body
                if (len(inner) == 1
                        and isinstance(inner[0], cst.Expr)
                        and isinstance(inner[0].value, cst.Call)
                        and isinstance(inner[0].value.func, cst.Attribute)
                        and isinstance(inner[0].value.func.value, cst.Name)
                        and inner[0].value.func.attr.value == "append"):
                    list_var = inner[0].value.func.value.value
                    cond = _extract_filter_condition(stmt.test, row_name, df_name)
                    if cond:
                        self.matches.append((node, df_name, list_var,
                                             {"type": "filter", "condition": cond}))

        return False


class _DetectApplyLambda(cst.CSTVisitor):
    """Detect: df['col'].apply(lambda x: x.upper()) → df['col'].str.upper()"""
    METADATA_DEPENDENCIES = (PositionProvider,)

    def __init__(self):
        self.matches: list[tuple[cst.Assign, str, str, str]] = []  # (node, df_name, col, method)

    def visit_Assign(self, node: cst.Assign) -> bool:
        if len(node.targets) != 1:
            return False
        value = node.value
        # df['col'].apply(lambda x: x.<method>())
        if not (isinstance(value, cst.Call)
                and isinstance(value.func, cst.Attribute)
                and value.func.attr.value == "apply"
                and len(value.args) == 1):
            return False
        lam = value.args[0].value
        if not isinstance(lam, cst.Lambda):
            return False
        # lambda x: x.<method>()
        if not (len(lam.params.params) == 1
                and isinstance(lam.body, cst.Call)
                and isinstance(lam.body.func, cst.Attribute)
                and isinstance(lam.body.func.value, cst.Name)
                and lam.body.func.value.value == lam.params.params[0].name.value
                and len(lam.body.args) == 0):
            return False
        method = lam.body.func.attr.value
        # Check source is df['col']
        source = value.func.value
        if not (isinstance(source, cst.Subscript)
                and isinstance(source.value, cst.Name)):
            return False
        df_name = source.value.value
        col = _get_subscript_str(source)
        if col and method in ("upper", "lower", "strip", "lstrip", "rstrip", "title", "capitalize"):
            self.matches.append((node, df_name, col, method))
        return False


def _get_subscript_str(node: cst.Subscript) -> str | None:
    """Extract string key from df['key']."""
    if len(node.slice) == 1:
        sl = node.slice[0].slice
        if isinstance(sl, cst.Index) and isinstance(sl.value, (cst.SimpleString, cst.FormattedString, cst.ConcatenatedString)):
            if isinstance(sl.value, cst.SimpleString):
                return sl.value.evaluated_value
    return None


def _extract_arithmetic_cols(expr, row_name: str) -> list[str] | None:
    """Extract column names from row['a'] + row['b']."""
    if isinstance(expr, cst.BinaryOperation):
        left = _get_row_col(expr.left, row_name)
        right = _get_row_col(expr.right, row_name)
        if left and right:
            return [left, right]
    return None


def _get_row_col(node, row_name: str) -> str | None:
    """Extract col from row['col']."""
    if (isinstance(node, cst.Subscript)
            and isinstance(node.value, cst.Name)
            and node.value.value == row_name):
        return _get_subscript_str(node)
    return None


def _get_op(expr: cst.BinaryOperation) -> str:
    """Get operator string from binary op."""
    op = expr.operator
    if isinstance(op, cst.Add):
        return "+"
    elif isinstance(op, cst.Subtract):
        return "-"
    elif isinstance(op, cst.Multiply):
        return "*"
    elif isinstance(op, cst.Divide):
        return "/"
    return "+"


def _extract_filter_condition(test, row_name: str, df_name: str) -> str | None:
    """Extract condition from row['value'] > 10 → df['value'] > 10."""
    if isinstance(test, cst.Comparison) and len(test.comparisons) == 1:
        left_col = _get_row_col(test.left, row_name)
        if left_col:
            comp = test.comparisons[0]
            # Get the comparator as code
            right_code = cst.parse_module("").code_for_node(comp.comparator) if hasattr(comp, 'comparator') else None
            # Build df['col'] <op> <value>
            op_map = {
                cst.GreaterThan: ">", cst.LessThan: "<",
                cst.GreaterThanEqual: ">=", cst.LessThanEqual: "<=",
                cst.Equal: "==", cst.NotEqual: "!=",
            }
            op_str = op_map.get(type(comp.operator))
            if op_str:
                # Store as (col, op, comparator_node)
                return (left_col, op_str, comp.comparator)
    return None


class DataFrameVectorizePattern(Pattern):
    name = "dataframe_vectorize"
    description = "Convert iterrows/apply anti-patterns to vectorized pandas operations"
    expected_speedup = "10-100x"

    def detect(self, tree: cst.Module) -> list[Match]:
        wrapper = cst.metadata.MetadataWrapper(tree)
        matches = []

        # Detect iterrows patterns (arithmetic + filter)
        v1 = _DetectIterrowsArithmetic()
        wrapper.visit(v1)
        for for_node, df_name, list_var, info in v1.matches:
            pos = wrapper.resolve(PositionProvider).get(for_node)
            line = pos.start.line if pos else 0
            code = tree.code_for_node(for_node).split("\n")[0]
            if info["type"] == "arithmetic":
                desc = f"Replace iterrows arithmetic with vectorized: df['{info['cols'][0]}'] {info['op']} df['{info['cols'][1]}']"
            else:
                col, op, _ = info["condition"]
                desc = f"Replace iterrows filter with boolean indexing: df[df['{col}'] {op} ...]"
            matches.append(Match(
                node=(for_node, df_name, list_var, info),
                line=line, description=desc, original_code=code,
            ))

        # Detect apply lambda patterns
        v2 = _DetectApplyLambda()
        wrapper.visit(v2)
        for assign_node, df_name, col, method in v2.matches:
            pos = wrapper.resolve(PositionProvider).get(assign_node)
            line = pos.start.line if pos else 0
            code = tree.code_for_node(assign_node)
            desc = f"Replace apply(lambda) with df['{col}'].str.{method}()"
            matches.append(Match(
                node=(assign_node, df_name, col, method),
                line=line, description=desc, original_code=code,
            ))

        return matches

    def transform(self, tree: cst.Module, match: Match) -> cst.Module:
        node_data = match.node

        if len(node_data) == 4 and isinstance(node_data[3], dict):
            # iterrows pattern
            for_node, df_name, list_var, info = node_data
            if info["type"] == "arithmetic":
                return self._transform_arithmetic(tree, for_node, df_name, list_var, info)
            else:
                return self._transform_filter(tree, for_node, df_name, list_var, info)
        else:
            # apply lambda pattern
            assign_node, df_name, col, method = node_data
            return self._transform_apply(tree, assign_node, df_name, col, method)

    def _transform_arithmetic(self, tree, for_node, df_name, list_var, info):
        """Transform iterrows arithmetic to vectorized assignment."""
        cols = info["cols"]
        op = info["op"]

        # Find df['target'] = list_var after the loop in module body
        target_col = None
        found_loop = False
        for stmt in tree.body:
            if isinstance(stmt, cst.For) and stmt.deep_equals(for_node):
                found_loop = True
                continue
            if found_loop and isinstance(stmt, cst.SimpleStatementLine):
                for s in stmt.body:
                    if (isinstance(s, cst.Assign)
                            and len(s.targets) == 1
                            and isinstance(s.targets[0].target, cst.Subscript)
                            and isinstance(s.targets[0].target.value, cst.Name)
                            and s.targets[0].target.value.value == df_name
                            and isinstance(s.value, cst.Name)
                            and s.value.value == list_var):
                        target_col = _get_subscript_str(s.targets[0].target)
                        break
                if target_col:
                    break

        target_col = target_col or "result"

        # Build: df['target'] = df['a'] + df['b']
        new_code = f"{df_name}['{target_col}'] = {df_name}['{cols[0]}'] {op} {df_name}['{cols[1]}']\n"
        new_stmt = cst.parse_statement(new_code)

        class _Replace(cst.CSTTransformer):
            def __init__(self):
                self.removed_for = False
                self.removed_assign = False

            def leave_SimpleStatementLine(self, original, updated):
                # Remove `results = []`
                if not self.removed_for:
                    for s in updated.body:
                        if (isinstance(s, cst.Assign)
                                and len(s.targets) == 1
                                and isinstance(s.targets[0].target, cst.Name)
                                and s.targets[0].target.value == list_var
                                and isinstance(s.value, cst.List)
                                and len(s.value.elements) == 0):
                            return cst.RemovalSentinel.REMOVE
                    return updated
                # Replace `df['c'] = results` with vectorized
                if not self.removed_assign and target_col:
                    for s in updated.body:
                        if (isinstance(s, cst.Assign)
                                and len(s.targets) == 1
                                and isinstance(s.targets[0].target, cst.Subscript)
                                and isinstance(s.value, cst.Name)
                                and s.value.value == list_var):
                            self.removed_assign = True
                            return cst.FlattenSentinel([new_stmt])
                    return updated
                return updated

            def leave_For(self, original, updated):
                if original.deep_equals(for_node):
                    self.removed_for = True
                    return cst.RemovalSentinel.REMOVE
                return updated

        return tree.visit(_Replace())

    def _transform_filter(self, tree, for_node, df_name, list_var, info):
        """Transform iterrows filter to boolean indexing."""
        col, op, comparator = info["condition"]
        comp_code = tree.code_for_node(comparator).strip()
        new_code = f"{list_var} = {df_name}[{df_name}['{col}'] {op} {comp_code}]\n"
        new_stmt = cst.parse_statement(new_code)

        class _Replace(cst.CSTTransformer):
            def __init__(self):
                self.removed_for = False

            def leave_SimpleStatementLine(self, original, updated):
                if not self.removed_for:
                    for stmt in updated.body:
                        if (isinstance(stmt, cst.Assign)
                                and len(stmt.targets) == 1
                                and isinstance(stmt.targets[0].target, cst.Name)
                                and stmt.targets[0].target.value == list_var
                                and isinstance(stmt.value, cst.List)
                                and len(stmt.value.elements) == 0):
                            return cst.RemovalSentinel.REMOVE
                return updated

            def leave_For(self, original, updated):
                if original.deep_equals(for_node):
                    self.removed_for = True
                    return cst.FlattenSentinel([new_stmt])
                return updated

        return tree.visit(_Replace())

    def _transform_apply(self, tree, assign_node, df_name, col, method):
        """Transform apply(lambda x: x.method()) to .str.method()."""
        new_code = f"{df_name}['{col}'].str.{method}()"

        class _Replace(cst.CSTTransformer):
            def __init__(self):
                self.done = False

            def leave_Assign(self, original, updated):
                if self.done or not original.deep_equals(assign_node):
                    return updated
                self.done = True
                new_value = cst.parse_expression(new_code)
                return updated.with_changes(value=new_value)

        return tree.visit(_Replace())
