"""Detect memoization candidates and add @functools.lru_cache."""

import libcst as cst
from libcst.metadata import PositionProvider

from .base import Match, Pattern

# Functions that indicate side effects or impurity
IMPURE_CALLS = frozenset({
    "print", "input", "open", "write", "random", "randint", "randrange",
    "choice", "shuffle", "sample", "time", "sleep", "exit", "quit",
})

# Types known to be unhashable (mutable defaults)
MUTABLE_TYPES = frozenset({"list", "dict", "set"})


class _FunctionAnalyzer(cst.CSTTransformer):
    """Analyze a function body for purity and recursion."""

    def __init__(self, func_name: str):
        super().__init__()
        self.func_name = func_name
        self.has_side_effects = False
        self.is_recursive = False
        self.calls_impure = False

    def visit_Call(self, node: cst.Call) -> bool:
        # Check for self-recursion
        if isinstance(node.func, cst.Name) and node.func.value == self.func_name:
            self.is_recursive = True
        # Check for impure calls
        if isinstance(node.func, cst.Name) and node.func.value in IMPURE_CALLS:
            self.calls_impure = True
        if (isinstance(node.func, cst.Attribute)
                and isinstance(node.func.attr, cst.Name)
                and node.func.attr.value in ("write", "writelines", "send")):
            self.has_side_effects = True
        return True

    def visit_Global(self, node: cst.Global) -> bool:
        self.has_side_effects = True
        return False

    def visit_Nonlocal(self, node: cst.Nonlocal) -> bool:
        self.has_side_effects = True
        return False

    def visit_Yield(self, node: cst.Yield) -> bool:
        self.has_side_effects = True
        return False


class _DetectMemoizable(cst.CSTVisitor):
    METADATA_DEPENDENCIES = (PositionProvider,)

    def __init__(self):
        self.matches: list[cst.FunctionDef] = []

    def visit_FunctionDef(self, node: cst.FunctionDef) -> bool:
        # Skip async, generators, already-decorated with lru_cache
        if isinstance(node.asynchronous, cst.Asynchronous):
            return False
        for dec in node.decorators:
            if isinstance(dec.decorator, cst.Name) and dec.decorator.value == "lru_cache":
                return False
            if isinstance(dec.decorator, cst.Call):
                if isinstance(dec.decorator.func, cst.Name) and dec.decorator.func.value == "lru_cache":
                    return False
                if (isinstance(dec.decorator.func, cst.Attribute)
                        and dec.decorator.func.attr.value == "lru_cache"):
                    return False

        # Skip trivial bodies (1 statement that's just `return <constant>`)
        body_stmts = node.body.body
        if len(body_stmts) <= 1:
            if len(body_stmts) == 1 and isinstance(body_stmts[0], cst.SimpleStatementLine):
                inner = body_stmts[0].body
                if len(inner) == 1 and isinstance(inner[0], cst.Return):
                    ret_val = inner[0].value
                    if isinstance(ret_val, (cst.Integer, cst.Float, cst.SimpleString, type(None))):
                        return False
            return False

        # Check for mutable default args
        if _has_mutable_defaults(node):
            return False

        # Check for hashable params
        if not _params_hashable(node):
            return False

        # Analyze body
        func_name = node.name.value
        analyzer = _FunctionAnalyzer(func_name)
        # Visit the function body
        cst.Module(body=[node]).visit(analyzer)

        if analyzer.has_side_effects or analyzer.calls_impure:
            return False

        # Must be recursive to auto-apply
        if analyzer.is_recursive:
            self.matches.append(node)

        return False


def _has_mutable_defaults(node: cst.FunctionDef) -> bool:
    """Check if function has mutable default arguments."""
    params = node.params
    for param in (*params.params, *params.kwonly_params):
        if param.default is not None:
            if isinstance(param.default, (cst.List, cst.Dict, cst.Set)):
                return True
            if isinstance(param.default, cst.Call):
                if isinstance(param.default.func, cst.Name) and param.default.func.value in MUTABLE_TYPES:
                    return True
    return False


def _params_hashable(node: cst.FunctionDef) -> bool:
    """Check annotations don't indicate unhashable types."""
    params = node.params
    for param in (*params.params, *params.kwonly_params):
        if param.annotation is not None:
            ann = param.annotation.annotation
            if isinstance(ann, cst.Name) and ann.value in MUTABLE_TYPES:
                return False
    return True


class _AddLruCache(cst.CSTTransformer):
    """Add @functools.lru_cache(maxsize=None) to a target function."""

    def __init__(self, target: cst.FunctionDef):
        self.target = target
        self.done = False

    def leave_FunctionDef(self, original_node, updated_node):
        if self.done or not original_node.deep_equals(self.target):
            return updated_node
        self.done = True
        decorator = cst.Decorator(
            decorator=cst.Call(
                func=cst.Attribute(value=cst.Name("functools"), attr=cst.Name("lru_cache")),
                args=[cst.Arg(
                    keyword=cst.Name("maxsize"),
                    value=cst.Name("None"),
                    equal=cst.AssignEqual(
                        whitespace_before=cst.SimpleWhitespace(""),
                        whitespace_after=cst.SimpleWhitespace(""),
                    ),
                )],
            )
        )
        return updated_node.with_changes(decorators=[decorator, *updated_node.decorators])


class _EnsureFunctoolsImport(cst.CSTTransformer):
    """Add `import functools` if not already present."""

    def __init__(self):
        self.has_import = False

    def visit_ImportFrom(self, node: cst.ImportFrom) -> bool:
        if isinstance(node.module, cst.Attribute):
            pass
        elif isinstance(node.module, cst.Name) and node.module.value == "functools":
            self.has_import = True
        return False

    def visit_Import(self, node: cst.Import) -> bool:
        if isinstance(node.names, cst.ImportStar):
            return False
        for alias in node.names:
            if isinstance(alias.name, cst.Name) and alias.name.value == "functools":
                self.has_import = True
        return False

    def leave_Module(self, original_node, updated_node):
        if self.has_import:
            return updated_node
        import_stmt = cst.SimpleStatementLine(body=[
            cst.Import(names=[cst.ImportAlias(name=cst.Name("functools"))])
        ])
        return updated_node.with_changes(body=[import_stmt, *updated_node.body])


class AutoMemoizePattern(Pattern):
    name = "auto_memoize"
    description = "Add @functools.lru_cache to recursive pure functions"
    expected_speedup = "10-1000x for recursive functions"

    def detect(self, tree: cst.Module) -> list[Match]:
        wrapper = cst.metadata.MetadataWrapper(tree)
        visitor = _DetectMemoizable()
        wrapper.visit(visitor)
        matches = []
        for func_node in visitor.matches:
            pos = wrapper.resolve(PositionProvider).get(func_node)
            line = pos.start.line if pos else 0
            code = f"def {func_node.name.value}(...)"
            matches.append(Match(
                node=func_node,
                line=line,
                description=f"Memoize recursive function `{func_node.name.value}`",
                original_code=code,
            ))
        return matches

    def transform(self, tree: cst.Module, match: Match) -> cst.Module:
        tree = tree.visit(_AddLruCache(match.node))
        import_adder = _EnsureFunctoolsImport()
        tree = tree.visit(import_adder)
        return tree
