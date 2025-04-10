"""
Tests for the recommendations component of PyPerfOptimizer.
"""

import unittest

from pyperfoptimizer.optimizer.recommendations import Recommendations

class TestRecommendations(unittest.TestCase):
    """Test cases for the Recommendations class."""

    def setUp(self):
        """Set up test fixtures."""
        self.recommender = Recommendations()
        
    def tearDown(self):
        """Tear down test fixtures."""
        self.recommender = None
        
    def test_generate_from_cpu_profile(self):
        """Test generating recommendations from CPU profile data."""
        # Sample CPU profile data
        cpu_data = {
            'total_time': 2.5,
            'functions': [
                {
                    'function': 'test_module.sort_data',
                    'ncalls': '1',
                    'tottime': 1.0,
                    'percall': 1.0,
                    'cumtime': 1.5,
                    'percall_cumtime': 1.5
                },
                {
                    'function': 'test_module.read_file',
                    'ncalls': '10',
                    'tottime': 0.5,
                    'percall': 0.05,
                    'cumtime': 0.8,
                    'percall_cumtime': 0.08
                },
                {
                    'function': 'test_module.process_strings',
                    'ncalls': '100',
                    'tottime': 0.3,
                    'percall': 0.003,
                    'cumtime': 0.3,
                    'percall_cumtime': 0.003
                }
            ],
            'timestamp': '2023-01-01T00:00:00'
        }
        
        recommendations = self.recommender.generate_from_cpu_profile(cpu_data)
        
        # Check that recommendations were generated
        self.assertIsInstance(recommendations, list)
        self.assertGreater(len(recommendations), 0)
        
        # Check that the top function was identified
        self.assertTrue(any('sort_data' in rec for rec in recommendations))
        
        # Check for specific recommendations about sorting
        self.assertTrue(any('sort' in rec.lower() and 'algorithm' in rec.lower() 
                           for rec in recommendations))
                           
        # Check for I/O recommendations
        self.assertTrue(any('I/O' in rec and 'read_file' in rec 
                           for rec in recommendations))
                           
        # Check for string processing recommendations
        self.assertTrue(any('string' in rec.lower() and 'process_strings' in rec 
                           for rec in recommendations))
        
    def test_generate_from_memory_profile(self):
        """Test generating recommendations from memory profile data."""
        # Sample memory profile data
        memory_data = {
            'timestamps': [0.0, 0.5, 1.0, 1.5, 2.0],
            'memory_mb': [100.0, 150.0, 200.0, 600.0, 550.0],
            'baseline_memory': 100.0,
            'peak_memory': 600.0,
            'min_memory': 100.0,
            'avg_memory': 320.0,
            'final_memory': 550.0,
            'memory_increase': 450.0,
            'duration': 2.0,
            'timestamp': '2023-01-01T00:00:00'
        }
        
        recommendations = self.recommender.generate_from_memory_profile(memory_data)
        
        # Check that recommendations were generated
        self.assertIsInstance(recommendations, list)
        self.assertGreater(len(recommendations), 0)
        
        # Check for memory leak recommendation
        self.assertTrue(any('memory leak' in rec.lower() for rec in recommendations))
        
        # Check for high peak memory recommendation
        self.assertTrue(any('peak memory' in rec.lower() and '600.0' in rec 
                           for rec in recommendations))
                           
        # Check for memory growth recommendation
        growth_rate = 450.0 / 2.0  # 225 MB/s
        self.assertTrue(any('growth rate' in rec.lower() for rec in recommendations))
        
    def test_generate_from_line_profile(self):
        """Test generating recommendations from line profile data."""
        # Sample line profile data
        line_data = {
            'functions': [
                {
                    'filename': 'test_file.py',
                    'line_number': 10,
                    'function_name': 'process_data',
                    'total_time': 1.0,
                    'lines': {
                        11: {
                            'hits': 1,
                            'time': 0.1,
                            'time_per_hit': 0.1,
                            'percentage': 10.0,
                            'line_content': 'data = [x for x in range(1000)]'
                        },
                        12: {
                            'hits': 1000,
                            'time': 0.6,
                            'time_per_hit': 0.0006,
                            'percentage': 60.0,
                            'line_content': 'for i in range(len(data)):'
                        },
                        13: {
                            'hits': 1000,
                            'time': 0.3,
                            'time_per_hit': 0.0003,
                            'percentage': 30.0,
                            'line_content': '    result += data[i] * 2'
                        }
                    }
                }
            ],
            'timestamp': '2023-01-01T00:00:00'
        }
        
        recommendations = self.recommender.generate_from_line_profile(line_data)
        
        # Check that recommendations were generated
        self.assertIsInstance(recommendations, list)
        self.assertGreater(len(recommendations), 0)
        
        # Check for hotspot recommendation
        self.assertTrue(any('Hotspot at line 12' in rec for rec in recommendations))
        
        # Check for loop optimization recommendation (range(len()))
        self.assertTrue(any('loop at line 12' in rec.lower() for rec in recommendations))
        
    def test_generate_from_code_analysis(self):
        """Test generating recommendations from code analysis results."""
        # Sample code analysis results
        code_analysis = {
            'issues': [
                {
                    'severity': 'warning',
                    'message': 'String concatenation in a loop. Use \'\'.join() instead.',
                    'line': 15
                },
                {
                    'severity': 'info',
                    'message': 'Unnecessary list conversion of range()',
                    'line': 20
                }
            ],
            'loops': [
                {'line': 10, 'nested': False},
                {'line': 12, 'nested': True},
                {'line': 13, 'nested': True}
            ],
            'data_structures': {
                'lists': [
                    {'line': 5, 'size': 10, 'comprehension': False},
                    {'line': 8, 'size': 200, 'comprehension': False}
                ],
                'dicts': [],
                'sets': [],
                'tuples': []
            },
            'unused_functions': ['helper_func', 'utility_func'],
            'imported_modules': ['os', 'sys', 'math']
        }
        
        recommendations = self.recommender.generate_from_code_analysis(code_analysis)
        
        # Check that recommendations were generated
        self.assertIsInstance(recommendations, list)
        self.assertGreater(len(recommendations), 0)
        
        # Check for string concatenation issue
        self.assertTrue(any('String concatenation in a loop' in rec for rec in recommendations))
        
        # Check for unnecessary list conversion issue
        self.assertTrue(any('Unnecessary list conversion of range()' in rec for rec in recommendations))
        
        # Check for nested loops recommendation
        self.assertTrue(any('nested loops' in rec.lower() for rec in recommendations))
        
        # Check for unused functions recommendation
        self.assertTrue(any('unused functions' in rec.lower() for rec in recommendations))
        
    def test_generate_all(self):
        """Test generating all recommendations from various data sources."""
        # Sample CPU profile data
        cpu_data = {
            'total_time': 1.5,
            'functions': [
                {
                    'function': 'main.process',
                    'ncalls': '1',
                    'tottime': 1.0,
                    'percall': 1.0,
                    'cumtime': 1.2,
                    'percall_cumtime': 1.2
                }
            ]
        }
        
        # Sample memory profile data
        memory_data = {
            'peak_memory': 550.0,
            'baseline_memory': 100.0,
            'memory_increase': 300.0,
            'timestamps': [0, 1],
            'memory_mb': [100, 400]
        }
        
        recommendations = self.recommender.generate_all(
            cpu_data=cpu_data, 
            memory_data=memory_data
        )
        
        # Check that all recommendation types are present
        self.assertIsInstance(recommendations, dict)
        self.assertIn('cpu', recommendations)
        self.assertIn('memory', recommendations)
        self.assertIn('algorithm', recommendations)
        self.assertIn('code_structure', recommendations)
        
        # Check that we got CPU and memory recommendations
        self.assertGreater(len(recommendations['cpu']), 0)
        self.assertGreater(len(recommendations['memory']), 0)
        
    def test_get_prioritized_recommendations(self):
        """Test getting prioritized recommendations."""
        # Generate some recommendations
        cpu_data = {
            'total_time': 1.0,
            'functions': [
                {
                    'function': 'main.process',
                    'ncalls': '1',
                    'tottime': 0.5,
                    'percall': 0.5,
                    'cumtime': 0.8,
                    'percall_cumtime': 0.8
                }
            ]
        }
        self.recommender.generate_from_cpu_profile(cpu_data)
        
        # Get prioritized recommendations
        prioritized = self.recommender.get_prioritized_recommendations(max_per_category=2)
        
        # Check that recommendations were prioritized
        self.assertIsInstance(prioritized, list)
        self.assertGreater(len(prioritized), 0)
        
        # Check that they're formatted with category prefix
        self.assertTrue(all(rec.startswith('[') for rec in prioritized))
        
    def test_reset(self):
        """Test resetting recommendations."""
        # Generate some recommendations
        cpu_data = {
            'total_time': 1.0,
            'functions': [
                {
                    'function': 'main.process',
                    'ncalls': '1',
                    'tottime': 0.5,
                    'percall': 0.5,
                    'cumtime': 0.8,
                    'percall_cumtime': 0.8
                }
            ]
        }
        self.recommender.generate_from_cpu_profile(cpu_data)
        
        # Check that we have recommendations
        self.assertGreater(len(self.recommender.recommendations['cpu']), 0)
        
        # Reset
        self.recommender.reset()
        
        # Check that recommendations were cleared
        self.assertEqual(len(self.recommender.recommendations['cpu']), 0)
        self.assertEqual(len(self.recommender.recommendations['memory']), 0)
        self.assertEqual(len(self.recommender.recommendations['algorithm']), 0)
        self.assertEqual(len(self.recommender.recommendations['code_structure']), 0)

if __name__ == '__main__':
    unittest.main()
