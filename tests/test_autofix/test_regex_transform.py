"""Tests for regex precompile auto-fix transform."""

import unittest

import libcst as cst

from pyperfoptimizer.autofix import fix, scan
from pyperfoptimizer.autofix.patterns.regex_precompile import RegexPrecompilePattern


class TestRegexPrecompileTransform(unittest.TestCase):
    def test_detect(self):
        code = 'import re\ndef check(s):\n    return re.match(r"\\d+", s)\n'
        tree = cst.parse_module(code)
        matches = RegexPrecompilePattern().detect(tree)
        self.assertEqual(len(matches), 1)

    def test_transform_match(self):
        code = 'import re\n\ndef validate(s):\n    return re.match(r"^\\w+$", s)\n'
        pattern = RegexPrecompilePattern()
        tree = cst.parse_module(code)
        matches = pattern.detect(tree)
        self.assertEqual(len(matches), 1)
        result = pattern.transform(tree, matches[0])
        output = result.code
        self.assertIn('_RE_0 = re.compile(r"^\\w+$")', output)
        self.assertIn('_RE_0.match(s)', output)
        self.assertNotIn('re.match(', output)

    def test_transform_sub(self):
        code = 'import re\n\ndef clean(text):\n    return re.sub(r"[^a-z]", "", text)\n'
        pattern = RegexPrecompilePattern()
        tree = cst.parse_module(code)
        matches = pattern.detect(tree)
        self.assertEqual(len(matches), 1)
        result = pattern.transform(tree, matches[0])
        output = result.code
        self.assertIn('_RE_0 = re.compile(r"[^a-z]")', output)
        self.assertIn('_RE_0.sub("", text)', output)
        self.assertNotIn('re.sub(', output)

    def test_transform_with_flags(self):
        code = 'import re\n\ndef check(s):\n    return re.match(r"^hello$", s, re.IGNORECASE)\n'
        pattern = RegexPrecompilePattern()
        tree = cst.parse_module(code)
        matches = pattern.detect(tree)
        self.assertEqual(len(matches), 1)
        result = pattern.transform(tree, matches[0])
        output = result.code
        self.assertIn('re.compile(r"^hello$", re.IGNORECASE)', output)
        self.assertIn('_RE_0.match(s)', output)
        self.assertNotIn('re.match(', output)

    def test_no_transform_variable_pattern(self):
        code = 'import re\n\ndef check(s, pat):\n    return re.match(pat, s)\n'
        pattern = RegexPrecompilePattern()
        tree = cst.parse_module(code)
        matches = pattern.detect(tree)
        self.assertEqual(len(matches), 0)

    def test_multiple_patterns(self):
        code = (
            'import re\n\n'
            'def validate(s):\n'
            '    return re.match(r"^\\w+$", s)\n\n'
            'def clean(text):\n'
            '    return re.sub(r"[^a-z]", "", text)\n'
        )
        pattern = RegexPrecompilePattern()
        tree = cst.parse_module(code)
        matches = pattern.detect(tree)
        self.assertEqual(len(matches), 2)
        result = pattern.transform(tree, matches[0])
        output = result.code
        self.assertIn('_RE_0', output)
        self.assertIn('_RE_1', output)

    def test_fix_integration(self):
        """Test that fix() works with regex pattern via the engine."""
        code = 'import re\n\ndef check(s):\n    return re.match(r"\\d+", s)\n'
        result = fix(code, patterns=[RegexPrecompilePattern()])
        self.assertIn('_RE_0 = re.compile(', result)
        self.assertIn('_RE_0.match(s)', result)

    def test_scan_integration(self):
        """Test that scan() works and shows preview."""
        code = 'import re\n\ndef check(s):\n    return re.match(r"\\d+", s)\n'
        opts = scan(code, patterns=[RegexPrecompilePattern()])
        self.assertEqual(len(opts), 1)
        self.assertEqual(opts[0].pattern_name, "regex_precompile")
        self.assertNotEqual(opts[0].optimized_code, "(detection only — manual fix required)")


if __name__ == "__main__":
    unittest.main()
