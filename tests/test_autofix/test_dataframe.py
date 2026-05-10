"""Tests for DataFrame vectorization pattern."""


import libcst as cst

from pyperfoptimizer.autofix.patterns.dataframe_vectorize import (
    DataFrameVectorizePattern,
)


class TestIterrowsArithmetic:
    def test_detect(self):
        src = (
            "results = []\n"
            "for idx, row in df.iterrows():\n"
            "    results.append(row['a'] + row['b'])\n"
            "df['c'] = results\n"
        )
        tree = cst.parse_module(src)
        p = DataFrameVectorizePattern()
        matches = p.detect(tree)
        assert len(matches) == 1
        assert "arithmetic" in matches[0].description.lower() or "vectorized" in matches[0].description.lower()

    def test_transform(self):
        src = (
            "results = []\n"
            "for idx, row in df.iterrows():\n"
            "    results.append(row['a'] + row['b'])\n"
            "df['c'] = results\n"
        )
        tree = cst.parse_module(src)
        p = DataFrameVectorizePattern()
        matches = p.detect(tree)
        result = p.transform(tree, matches[0])
        code = result.code
        assert "df['c'] = df['a'] + df['b']" in code
        assert "iterrows" not in code
        assert "results = []" not in code


class TestIterrowsFilter:
    def test_detect(self):
        src = (
            "results = []\n"
            "for idx, row in df.iterrows():\n"
            "    if row['value'] > 10:\n"
            "        results.append(row)\n"
        )
        tree = cst.parse_module(src)
        p = DataFrameVectorizePattern()
        matches = p.detect(tree)
        assert len(matches) == 1
        assert "filter" in matches[0].description.lower() or "boolean" in matches[0].description.lower()

    def test_transform(self):
        src = (
            "results = []\n"
            "for idx, row in df.iterrows():\n"
            "    if row['value'] > 10:\n"
            "        results.append(row)\n"
        )
        tree = cst.parse_module(src)
        p = DataFrameVectorizePattern()
        matches = p.detect(tree)
        result = p.transform(tree, matches[0])
        code = result.code
        assert "results = df[df['value'] > 10]" in code
        assert "iterrows" not in code
        assert "results = []" not in code


class TestApplyLambda:
    def test_detect(self):
        src = "df['upper'] = df['name'].apply(lambda x: x.upper())\n"
        tree = cst.parse_module(src)
        p = DataFrameVectorizePattern()
        matches = p.detect(tree)
        assert len(matches) == 1
        assert "str.upper" in matches[0].description

    def test_transform(self):
        src = "df['upper'] = df['name'].apply(lambda x: x.upper())\n"
        tree = cst.parse_module(src)
        p = DataFrameVectorizePattern()
        matches = p.detect(tree)
        result = p.transform(tree, matches[0])
        code = result.code
        assert "df['name'].str.upper()" in code
        assert "apply" not in code


class TestNoFalsePositives:
    def test_no_detect_complex_iterrows(self):
        """Don't match iterrows with complex logic."""
        src = (
            "for idx, row in df.iterrows():\n"
            "    x = row['a'] + row['b']\n"
            "    y = x * 2\n"
            "    results.append(y)\n"
        )
        tree = cst.parse_module(src)
        p = DataFrameVectorizePattern()
        matches = p.detect(tree)
        assert len(matches) == 0

    def test_no_detect_apply_complex_lambda(self):
        """Don't match apply with complex lambda."""
        src = "df['x'] = df['a'].apply(lambda x: x + 1)\n"
        tree = cst.parse_module(src)
        p = DataFrameVectorizePattern()
        matches = p.detect(tree)
        assert len(matches) == 0
