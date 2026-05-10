"""Tests for autofix patterns."""

import libcst as cst
import pytest

from pyperfoptimizer.autofix import fix, scan
from pyperfoptimizer.autofix.patterns.append_to_comprehension import AppendToComprehensionPattern
from pyperfoptimizer.autofix.patterns.loop_invariant import LoopInvariantPattern
from pyperfoptimizer.autofix.patterns.membership_test import MembershipTestPattern
from pyperfoptimizer.autofix.patterns.string_concat import StringConcatPattern
from pyperfoptimizer.autofix.patterns.unnecessary_list import UnnecessaryListPattern


class TestLoopInvariant:
    def test_detect(self):
        src = "for item in items:\n    result.append(item)\n"
        tree = cst.parse_module(src)
        p = LoopInvariantPattern()
        matches = p.detect(tree)
        assert len(matches) == 1
        assert "result" in matches[0].description

    def test_transform(self):
        src = "for item in items:\n    result.append(item)\n"
        tree = cst.parse_module(src)
        p = LoopInvariantPattern()
        matches = p.detect(tree)
        result = p.transform(tree, matches[0])
        code = result.code
        assert "_result_append = result.append" in code
        assert "_result_append(item)" in code


class TestAppendToComprehension:
    def test_detect_simple(self):
        src = "result = []\nfor x in items:\n    result.append(x * 2)\n"
        tree = cst.parse_module(src)
        p = AppendToComprehensionPattern()
        matches = p.detect(tree)
        assert len(matches) == 1

    def test_transform_simple(self):
        src = "result = []\nfor x in items:\n    result.append(x * 2)\n"
        tree = cst.parse_module(src)
        p = AppendToComprehensionPattern()
        matches = p.detect(tree)
        result = p.transform(tree, matches[0])
        code = result.code
        assert "result = [x * 2 for x in items]" in code

    def test_detect_conditional(self):
        src = "result = []\nfor x in items:\n    if x > 0:\n        result.append(x)\n"
        tree = cst.parse_module(src)
        p = AppendToComprehensionPattern()
        matches = p.detect(tree)
        assert len(matches) == 1

    def test_transform_conditional(self):
        src = "result = []\nfor x in items:\n    if x > 0:\n        result.append(x)\n"
        tree = cst.parse_module(src)
        p = AppendToComprehensionPattern()
        matches = p.detect(tree)
        result = p.transform(tree, matches[0])
        code = result.code
        assert "for x in items" in code
        assert "if x > 0" in code


class TestStringConcat:
    def test_detect(self):
        src = "s = ''\nfor x in items:\n    s += str(x)\n"
        tree = cst.parse_module(src)
        p = StringConcatPattern()
        matches = p.detect(tree)
        assert len(matches) == 1

    def test_transform(self):
        src = "s = ''\nfor x in items:\n    s += str(x)\n"
        tree = cst.parse_module(src)
        p = StringConcatPattern()
        matches = p.detect(tree)
        result = p.transform(tree, matches[0])
        code = result.code
        assert "''.join" in code
        assert "str(x)" in code


class TestUnnecessaryList:
    def test_detect(self):
        src = "for x in list(gen()):\n    print(x)\n"
        tree = cst.parse_module(src)
        p = UnnecessaryListPattern()
        matches = p.detect(tree)
        assert len(matches) == 1

    def test_transform(self):
        src = "for x in list(gen()):\n    print(x)\n"
        tree = cst.parse_module(src)
        p = UnnecessaryListPattern()
        matches = p.detect(tree)
        result = p.transform(tree, matches[0])
        code = result.code
        assert "list(" not in code
        assert "for x in gen():" in code


class TestMembershipTest:
    def test_detect(self):
        src = "if x in [1, 2, 3, 4, 5]:\n    pass\n"
        tree = cst.parse_module(src)
        p = MembershipTestPattern()
        matches = p.detect(tree)
        assert len(matches) == 1

    def test_transform(self):
        src = "if x in [1, 2, 3, 4, 5]:\n    pass\n"
        tree = cst.parse_module(src)
        p = MembershipTestPattern()
        matches = p.detect(tree)
        result = p.transform(tree, matches[0])
        code = result.code
        assert "{1, 2, 3, 4, 5}" in code
        assert "[1, 2, 3, 4, 5]" not in code

    def test_no_detect_short_list(self):
        src = "if x in [1, 2]:\n    pass\n"
        tree = cst.parse_module(src)
        p = MembershipTestPattern()
        matches = p.detect(tree)
        assert len(matches) == 0


class TestEngine:
    def test_scan(self):
        src = "for x in list(items):\n    print(x)\n"
        opts = scan(src)
        assert len(opts) >= 1
        assert any(o.pattern_name == "unnecessary_list" for o in opts)

    def test_fix(self):
        src = "for x in list(items):\n    print(x)\n"
        result = fix(src)
        assert "list(" not in result
