"""Tests for the 10 new autofix patterns."""

import unittest

import libcst as cst

from pyperfoptimizer.autofix import fix, scan
from pyperfoptimizer.autofix.patterns.regex_precompile import RegexPrecompilePattern
from pyperfoptimizer.autofix.patterns.defaultdict_opportunity import DefaultdictOpportunityPattern
from pyperfoptimizer.autofix.patterns.repeated_attr_in_loop import RepeatedAttrInLoopPattern
from pyperfoptimizer.autofix.patterns.exception_control_flow import ExceptionControlFlowPattern


class TestRegexPrecompile(unittest.TestCase):
    def test_detect(self):
        code = 'import re\ndef check(s):\n    return re.match(r"\\d+", s)\n'
        tree = cst.parse_module(code)
        matches = RegexPrecompilePattern().detect(tree)
        self.assertEqual(len(matches), 1)

    def test_no_detect_outside_function(self):
        code = 'import re\nresult = re.match(r"\\d+", "123")\n'
        tree = cst.parse_module(code)
        matches = RegexPrecompilePattern().detect(tree)
        self.assertEqual(len(matches), 0)


class TestLoopToAnyAll(unittest.TestCase):
    def test_detect(self):
        code = 'for x in items:\n    if x > 0:\n        return True\n'
        opts = scan(code)
        self.assertTrue(any(o.pattern_name == 'loop_to_any_all' for o in opts))

    def test_no_auto_fix(self):
        """loop_to_any_all is detection-only (auto_fix=False) — fix() should not transform."""
        code = 'for x in items:\n    if x > 0:\n        return True\n'
        result = fix(code)
        self.assertNotIn('any(', result)


class TestDictGet(unittest.TestCase):
    def test_detect(self):
        code = 'try:\n    val = d["key"]\nexcept KeyError:\n    val = None\n'
        opts = scan(code)
        self.assertTrue(any(o.pattern_name == 'dict_get' for o in opts))

    def test_transform(self):
        code = 'try:\n    val = d["key"]\nexcept KeyError:\n    val = None\n'
        result = fix(code)
        self.assertIn('.get(', result)
        self.assertNotIn('except', result)


class TestMultipleIsinstance(unittest.TestCase):
    def test_detect(self):
        code = 'if isinstance(x, int) or isinstance(x, float) or isinstance(x, str):\n    pass\n'
        opts = scan(code)
        self.assertTrue(any(o.pattern_name == 'multiple_isinstance' for o in opts))

    def test_transform(self):
        code = 'if isinstance(x, int) or isinstance(x, float) or isinstance(x, str):\n    pass\n'
        result = fix(code)
        self.assertIn('isinstance(x,', result)
        self.assertNotIn(' or ', result)


class TestDefaultdictOpportunity(unittest.TestCase):
    def test_detect(self):
        code = 'if key not in d:\n    d[key] = []\n'
        tree = cst.parse_module(code)
        matches = DefaultdictOpportunityPattern().detect(tree)
        self.assertEqual(len(matches), 1)

    def test_no_detect_simple_assign(self):
        code = 'if key not in d:\n    x = 5\n'
        tree = cst.parse_module(code)
        matches = DefaultdictOpportunityPattern().detect(tree)
        self.assertEqual(len(matches), 0)


class TestGeneratorInsteadOfList(unittest.TestCase):
    def test_detect(self):
        code = 'total = sum([x * 2 for x in items])\n'
        opts = scan(code)
        self.assertTrue(any(o.pattern_name == 'generator_instead_of_list' for o in opts))

    def test_transform(self):
        code = 'total = sum([x * 2 for x in items])\n'
        result = fix(code)
        self.assertNotIn('[x * 2 for x in items]', result)
        self.assertIn('sum(', result)


class TestRepeatedAttrInLoop(unittest.TestCase):
    def test_detect(self):
        code = 'for i in items:\n    a = self.config.settings.value\n    b = self.config.settings.value + 1\n    c = self.config.settings.value * 2\n'
        tree = cst.parse_module(code)
        matches = RepeatedAttrInLoopPattern().detect(tree)
        self.assertEqual(len(matches), 1)

    def test_no_detect_few_accesses(self):
        code = 'for i in items:\n    a = self.config.settings.value\n'
        tree = cst.parse_module(code)
        matches = RepeatedAttrInLoopPattern().detect(tree)
        self.assertEqual(len(matches), 0)


class TestUnnecessaryCopy(unittest.TestCase):
    def test_detect(self):
        code = 'x = list([1, 2, 3])\n'
        opts = scan(code)
        self.assertTrue(any(o.pattern_name == 'unnecessary_copy' for o in opts))

    def test_transform(self):
        code = 'x = list([1, 2, 3])\n'
        result = fix(code)
        self.assertIn('[1, 2, 3]', result)
        self.assertNotIn('list(', result)


class TestChainedComparison(unittest.TestCase):
    def test_detect(self):
        code = 'if x >= 0 and x <= 100:\n    pass\n'
        opts = scan(code)
        self.assertTrue(any(o.pattern_name == 'chained_comparison' for o in opts))

    def test_transform(self):
        code = 'if x >= 0 and x <= 100:\n    pass\n'
        result = fix(code)
        self.assertNotIn(' and ', result)


class TestExceptionControlFlow(unittest.TestCase):
    def test_detect(self):
        code = 'for item in items:\n    try:\n        val = int(item)\n    except ValueError:\n        pass\n'
        tree = cst.parse_module(code)
        matches = ExceptionControlFlowPattern().detect(tree)
        self.assertEqual(len(matches), 1)

    def test_no_detect_outside_loop(self):
        code = 'try:\n    val = int(x)\nexcept ValueError:\n    pass\n'
        tree = cst.parse_module(code)
        matches = ExceptionControlFlowPattern().detect(tree)
        self.assertEqual(len(matches), 0)


if __name__ == '__main__':
    unittest.main()
