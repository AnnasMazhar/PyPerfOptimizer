"""
Tests for the memory visualizer component of PyPerfOptimizer.
"""

import unittest
import os
import tempfile
import time

try:
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend for testing
    import matplotlib.pyplot as plt
    _HAS_MPL = True
except ImportError:
    _HAS_MPL = False

try:
    import plotly
    _HAS_PLOTLY = True
except ImportError:
    _HAS_PLOTLY = False

try:
    import memory_profiler
    _HAS_MEMORY_PROFILER = True
except ImportError:
    _HAS_MEMORY_PROFILER = False

from pyperfoptimizer.visualizer.memory_visualizer import MemoryVisualizer

def generate_sample_memory_data():
    """Generate sample memory profile data for testing."""
    # Create sample memory profile data
    return {
        'timestamps': [0.0, 0.1, 0.2, 0.3, 0.4, 0.5],
        'memory_mb': [100.0, 110.0, 120.0, 115.0, 105.0, 100.0],
        'duration': 0.5,
        'baseline_memory': 100.0,
        'peak_memory': 120.0,
        'min_memory': 100.0,
        'avg_memory': 108.33,
        'final_memory': 100.0,
        'memory_increase': 0.0,
        'timestamp': '2023-01-01T00:00:00'
    }

def generate_sample_line_data():
    """Generate sample line-by-line memory profile data for testing."""
    return {
        'filename': 'test_file.py',
        'function': 'test_function',
        'line_stats': [
            {
                'line_num': 10,
                'memory_mb': 105.0,
                'increment_mb': 5.0,
                'code': 'large_list = [0] * 100000  # Allocate memory'
            },
            {
                'line_num': 11,
                'memory_mb': 115.0,
                'increment_mb': 10.0,
                'code': 'another_list = [0] * 200000  # Allocate more memory'
            },
            {
                'line_num': 12,
                'memory_mb': 110.0,
                'increment_mb': -5.0,
                'code': 'del large_list  # Free memory'
            }
        ],
        'raw_output': 'Sample output'
    }

@unittest.skipUnless(_HAS_MPL or _HAS_PLOTLY, "Neither matplotlib nor plotly is installed")
class TestMemoryVisualizer(unittest.TestCase):
    """Test cases for the MemoryVisualizer class."""

    def setUp(self):
        """Set up test fixtures."""
        # Determine which backend to use for testing
        if _HAS_PLOTLY:
            backend = 'plotly'
        elif _HAS_MPL:
            backend = 'matplotlib'
        else:
            self.skipTest("No visualization backend available")
            
        self.visualizer = MemoryVisualizer(backend=backend, theme='light')
        self.sample_data = generate_sample_memory_data()
        self.sample_line_data = generate_sample_line_data()
        
    def tearDown(self):
        """Tear down test fixtures."""
        self.visualizer = None
        self.sample_data = None
        
        # Close any open matplotlib figures
        if _HAS_MPL:
            plt.close('all')
        
    def test_plot_memory_usage(self):
        """Test plotting memory usage over time."""
        # Skip show to avoid blocking
        fig = self.visualizer.plot_memory_usage(
            self.sample_data, 
            show=False,
            include_baseline=True
        )
        
        self.assertIsNotNone(fig)
        
        # Test saving to a temporary file
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            temp_path = tmp.name
            
        try:
            self.visualizer.plot_memory_usage(
                self.sample_data,
                show=False,
                save_path=temp_path
            )
            self.assertTrue(os.path.exists(temp_path))
            self.assertGreater(os.path.getsize(temp_path), 0)
        finally:
            # Clean up
            if os.path.exists(temp_path):
                os.unlink(temp_path)
                
    def test_plot_line_memory(self):
        """Test plotting memory usage by line."""
        # Skip show to avoid blocking
        fig = self.visualizer.plot_line_memory(
            self.sample_line_data, 
            top_n=3, 
            show=False
        )
        
        self.assertIsNotNone(fig)
        
        # Test saving to a temporary file
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            temp_path = tmp.name
            
        try:
            self.visualizer.plot_line_memory(
                self.sample_line_data,
                show=False,
                save_path=temp_path
            )
            self.assertTrue(os.path.exists(temp_path))
            self.assertGreater(os.path.getsize(temp_path), 0)
        finally:
            # Clean up
            if os.path.exists(temp_path):
                os.unlink(temp_path)
                
    @unittest.skipUnless(_HAS_PLOTLY, "Plotly is required for HTML reports")
    def test_save_interactive_html(self):
        """Test saving an interactive HTML report."""
        with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as tmp:
            temp_path = tmp.name
            
        try:
            # Force backend to plotly for HTML output
            old_backend = self.visualizer.backend
            self.visualizer.backend = 'plotly'
            
            # Save HTML report
            self.visualizer.save_interactive_html(
                self.sample_data,
                line_data=self.sample_line_data,
                filename=temp_path
            )
            
            # Restore original backend
            self.visualizer.backend = old_backend
            
            # Check that the file was created and has content
            self.assertTrue(os.path.exists(temp_path))
            self.assertGreater(os.path.getsize(temp_path), 0)
            
            # Verify it contains some HTML elements we expect
            with open(temp_path, 'r') as f:
                content = f.read()
                self.assertIn('<!DOCTYPE html>', content)
                self.assertIn('<html>', content)
                self.assertIn('</html>', content)
                self.assertIn('Plotly.newPlot', content)  # Plotly JavaScript call
        finally:
            # Clean up
            if os.path.exists(temp_path):
                os.unlink(temp_path)
                
    def test_error_handling(self):
        """Test error handling with invalid data."""
        # Test with empty data
        with self.assertRaises(ValueError):
            self.visualizer.plot_memory_usage({})
            
        # Test with incomplete data
        with self.assertRaises(ValueError):
            self.visualizer.plot_memory_usage({'timestamps': [0, 1], 'memory_mb': []})
            
        # Test with invalid line data
        with self.assertRaises(ValueError):
            self.visualizer.plot_line_memory({})

if __name__ == '__main__':
    unittest.main()
