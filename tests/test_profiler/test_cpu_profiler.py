"""
Tests for the CPU profiler component of PyPerfOptimizer.
"""

import unittest
import time
import os
import tempfile

from pyperfoptimizer.profiler.cpu_profiler import CPUProfiler

class TestCPUProfiler(unittest.TestCase):
    """Test cases for the CPUProfiler class."""

    def setUp(self):
        """Set up test fixtures."""
        self.profiler = CPUProfiler()
        
    def tearDown(self):
        """Tear down test fixtures."""
        self.profiler = None
        
    def test_start_stop(self):
        """Test starting and stopping the profiler."""
        self.profiler.start()
        time.sleep(0.1)  # Do something that takes time
        self.profiler.stop()
        
        # Make sure profiling data was captured
        stats = self.profiler.get_stats()
        self.assertIsInstance(stats, dict)
        self.assertIn('total_time', stats)
        self.assertGreater(stats['total_time'], 0)
        
    def test_profile_func(self):
        """Test profiling a function."""
        def fibonacci(n):
            if n <= 1:
                return n
            return fibonacci(n-1) + fibonacci(n-2)
        
        result = self.profiler.profile_func(fibonacci, 10)
        
        # Check that the function's result is correct
        self.assertEqual(result, 55)
        
        # Check that profiling data was captured
        stats = self.profiler.get_stats()
        self.assertIsInstance(stats, dict)
        self.assertIn('functions', stats)
        self.assertGreater(len(stats['functions']), 0)
        
    def test_get_stats(self):
        """Test retrieving profiling statistics."""
        def busy_function():
            result = 0
            for i in range(10000):
                result += i
            return result
        
        self.profiler.profile_func(busy_function)
        stats = self.profiler.get_stats()
        
        # Check that the stats contain expected keys
        self.assertIn('total_time', stats)
        self.assertIn('raw_output', stats)
        self.assertIn('functions', stats)
        self.assertIn('timestamp', stats)
        
        # Check that functions data contains expected information
        functions = stats['functions']
        self.assertGreater(len(functions), 0)
        func = functions[0]  # First function should be busy_function
        self.assertIn('ncalls', func)
        self.assertIn('tottime', func)
        self.assertIn('percall', func)
        self.assertIn('cumtime', func)
        self.assertIn('function', func)
        
    def test_save_load_stats(self):
        """Test saving and loading profiling statistics."""
        def example_function():
            time.sleep(0.1)
            return sum(range(1000))
        
        self.profiler.profile_func(example_function)
        
        # Save stats to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.prof') as temp:
            temp_path = temp.name
            
        try:
            # Save stats
            self.profiler.save_stats(temp_path)
            self.assertTrue(os.path.exists(temp_path))
            
            # Create a new profiler and load stats
            new_profiler = CPUProfiler()
            new_profiler.load_stats(temp_path)
            
            # Check that the loaded stats match the original
            original_stats = self.profiler.get_stats()
            loaded_stats = new_profiler.get_stats()
            
            self.assertEqual(len(original_stats['functions']), len(loaded_stats['functions']))
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.unlink(temp_path)
                
    def test_get_top_functions(self):
        """Test getting the top N functions by cumulative time."""
        def func1():
            time.sleep(0.03)
            
        def func2():
            time.sleep(0.02)
            
        def func3():
            time.sleep(0.01)
            
        def main():
            func1()
            func2()
            func3()
            
        self.profiler.profile_func(main)
        
        # Get top 2 functions
        top_funcs = self.profiler.get_top_functions(2)
        self.assertIsInstance(top_funcs, list)
        self.assertLessEqual(len(top_funcs), 2)
        
        # Check that they're sorted by cumulative time
        if len(top_funcs) >= 2:
            self.assertGreaterEqual(top_funcs[0]['cumtime'], top_funcs[1]['cumtime'])
            
    def test_clear(self):
        """Test clearing profiling results."""
        def simple_func():
            return sum(range(1000))
            
        self.profiler.profile_func(simple_func)
        stats_before = self.profiler.get_stats()
        self.assertGreater(len(stats_before.get('functions', [])), 0)
        
        # Clear the results
        self.profiler.clear()
        
        # Check that results were cleared
        with self.assertRaises(Exception):
            self.profiler.results.print_stats()  # This should raise since results is None

if __name__ == '__main__':
    unittest.main()
