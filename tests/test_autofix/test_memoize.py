"""Tests for auto_memoize pattern."""

import libcst as cst
import pytest

from pyperfoptimizer.autofix.patterns.auto_memoize import AutoMemoizePattern


class TestAutoMemoize:
    def test_detect_recursive_function(self):
        src = "def fib(n):\n    if n <= 1:\n        return n\n    return fib(n-1) + fib(n-2)\n"
        tree = cst.parse_module(src)
        p = AutoMemoizePattern()
        matches = p.detect(tree)
        assert len(matches) == 1
        assert "fib" in matches[0].description

    def test_transform_adds_decorator_and_import(self):
        src = "def fib(n):\n    if n <= 1:\n        return n\n    return fib(n-1) + fib(n-2)\n"
        tree = cst.parse_module(src)
        p = AutoMemoizePattern()
        matches = p.detect(tree)
        result = p.transform(tree, matches[0])
        code = result.code
        assert "import functools" in code
        assert "@functools.lru_cache(maxsize=None)" in code

    def test_skip_impure_function(self):
        src = "def compute(n):\n    print(n)\n    if n <= 1:\n        return n\n    return compute(n-1)\n"
        tree = cst.parse_module(src)
        p = AutoMemoizePattern()
        matches = p.detect(tree)
        assert len(matches) == 0

    def test_skip_mutable_defaults(self):
        src = "def recurse(n, memo=[]):\n    if n <= 0:\n        return memo\n    return recurse(n-1, memo)\n"
        tree = cst.parse_module(src)
        p = AutoMemoizePattern()
        matches = p.detect(tree)
        assert len(matches) == 0

    def test_skip_non_recursive(self):
        src = "def add(a, b):\n    x = a + b\n    return x\n"
        tree = cst.parse_module(src)
        p = AutoMemoizePattern()
        matches = p.detect(tree)
        assert len(matches) == 0

    def test_skip_generator(self):
        src = "def gen(n):\n    if n > 0:\n        yield n\n        yield from gen(n-1)\n"
        tree = cst.parse_module(src)
        p = AutoMemoizePattern()
        matches = p.detect(tree)
        assert len(matches) == 0

    def test_skip_already_decorated(self):
        src = "import functools\n\n@functools.lru_cache(maxsize=None)\ndef fib(n):\n    if n <= 1:\n        return n\n    return fib(n-1) + fib(n-2)\n"
        tree = cst.parse_module(src)
        p = AutoMemoizePattern()
        matches = p.detect(tree)
        assert len(matches) == 0

    def test_no_duplicate_import(self):
        src = "import functools\n\ndef fib(n):\n    if n <= 1:\n        return n\n    return fib(n-1) + fib(n-2)\n"
        tree = cst.parse_module(src)
        p = AutoMemoizePattern()
        matches = p.detect(tree)
        result = p.transform(tree, matches[0])
        code = result.code
        assert code.count("import functools") == 1
