"""Tests for the compilation advisor."""

import pytest

from pyperfoptimizer.advisor.compile_advisor import (
    Bottleneck,
    CompileCandidate,
    Compiler,
    advise,
)


class TestNumbaEligible:
    """Pure numeric function → numba eligible, high confidence."""

    def test_pure_numeric_with_loop(self):
        source = '''
import numpy as np

def compute_distance(x: float, y: float, z: float) -> float:
    total = 0.0
    for i in range(1000):
        total += x * x + y * y + z * z
    return total
'''
        results = advise(source)
        assert len(results) == 1
        c = results[0]
        assert c.name == "compute_distance"
        assert c.compiler == Compiler.NUMBA
        assert c.eligible is True
        assert c.blockers == []
        assert c.bottleneck == Bottleneck.CPU_BOUND
        assert c.confidence >= 0.2

    def test_numpy_function(self):
        source = '''
import numpy as np

def dot_product(a: np.ndarray, b: np.ndarray) -> float:
    result = 0.0
    for i in range(len(a)):
        result += a[i] * b[i]
    return result
'''
        results = advise(source)
        c = results[0]
        assert c.compiler == Compiler.NUMBA
        assert c.eligible is True


class TestMypycEligible:
    """Typed data processing function → mypyc eligible."""

    def test_typed_processing(self):
        source = '''
def process_items(items: list, threshold: int) -> list:
    result = []
    for item in items:
        if item > threshold:
            result.append(item)
    return result
'''
        results = advise(source)
        c = results[0]
        assert c.compiler == Compiler.MYPYC
        assert c.eligible is True
        assert c.bottleneck == Bottleneck.CPU_BOUND


class TestNotEligibleGetattr:
    """Function with getattr → not eligible, blocker reported."""

    def test_getattr_blocks(self):
        source = '''
def dynamic_access(obj, attr_name: str) -> str:
    value = getattr(obj, attr_name)
    return str(value)
'''
        results = advise(source)
        c = results[0]
        assert c.eligible is False
        assert c.compiler == Compiler.NONE
        assert any("eval/exec/getattr/setattr" in b for b in c.blockers)


class TestIOFunction:
    """I/O function (calls requests.get) → not compilable."""

    def test_requests_call(self):
        source = '''
import requests

def fetch_data(url: str) -> dict:
    response = requests.get(url)
    return response.json()
'''
        results = advise(source)
        c = results[0]
        assert c.eligible is False
        assert c.compiler == Compiler.NONE
        assert c.bottleneck == Bottleneck.IO_BOUND
        assert any("I/O bound" in b for b in c.blockers)

    def test_open_call(self):
        source = '''
def read_file(path: str) -> str:
    with open(path) as f:
        return f.read()
'''
        results = advise(source)
        c = results[0]
        assert c.eligible is False
        assert c.bottleneck == Bottleneck.IO_BOUND


class TestUntypedFunction:
    """Untyped function → mypyc blocked, reports missing annotations."""

    def test_missing_annotations(self):
        source = '''
def transform(data, factor, offset):
    result = []
    for item in data:
        result.append(item * factor + offset)
    return result
'''
        results = advise(source)
        c = results[0]
        assert c.eligible is False
        assert "data" in c.missing_annotations
        assert "factor" in c.missing_annotations
        assert "offset" in c.missing_annotations


class TestNumbaWithLoop:
    """Function with loop + numeric → numba, high confidence."""

    def test_loop_numeric_high_confidence(self):
        source = '''
def matrix_sum(n: int) -> float:
    total = 0.0
    for i in range(n):
        for j in range(n):
            total += i * j
    return total
'''
        results = advise(source, profile_data={"matrix_sum": 45.0})
        c = results[0]
        assert c.compiler == Compiler.NUMBA
        assert c.eligible is True
        assert c.confidence >= 0.6


class TestTrivialFunction:
    """Trivial function (3 lines) → low confidence."""

    def test_short_function_low_confidence(self):
        source = '''
def add(x: int, y: int) -> int:
    return x + y
'''
        results = advise(source)
        c = results[0]
        assert c.confidence <= 0.3


class TestProfileDataIntegration:
    """Profile data increases confidence."""

    def test_hot_function_high_confidence(self):
        source = '''
def hot_loop(data: list, multiplier: int) -> list:
    result = []
    for item in data:
        result.append(item * multiplier)
    return result
'''
        results = advise(source, profile_data={"hot_loop": 35.0})
        c = results[0]
        assert c.confidence >= 0.6

    def test_cold_function_lower_confidence(self):
        source = '''
def cold_loop(data: list, multiplier: int) -> list:
    result = []
    for item in data:
        result.append(item * multiplier)
    return result
'''
        results_hot = advise(source, profile_data={"cold_loop": 35.0})
        results_cold = advise(source, profile_data={"cold_loop": 1.0})
        assert results_hot[0].confidence > results_cold[0].confidence


class TestGeneratorBlocked:
    """Generator functions blocked for both compilers."""

    def test_yield_blocks(self):
        source = '''
def gen_items(n: int) -> int:
    for i in range(n):
        yield i
'''
        results = advise(source)
        c = results[0]
        assert c.eligible is False
        assert any("generator" in b or "yield" in b for b in c.blockers)
