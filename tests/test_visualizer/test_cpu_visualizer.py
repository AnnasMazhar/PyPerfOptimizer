"""
Tests for the CPU visualizer component of PyPerfOptimizer.
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

from pyperfoptimizer.visualizer.cpu_visualizer import CPUVisualizer
from pyperfoptimizer.profiler.cpu_profiler import CPUProfiler

def generate_sample_profile_data():
    """Generate sample CPU profile data for testing."""
    profiler = CPUProfiler()
    
    def fibonacci(n):
        if n <= 1:
            return n
        return fibonacci(n-1) + fibonacci(n-2)
    
    def test_function():
        fibonacci(10)
        time.sleep(0.01)
        return sum(range(1000))
    
    profiler.profile_func(test_function)
    return profiler.get_stats()

@unittest.skipUnless(_HAS_MPL or _HAS_PLOTLY, "Neither matplotlib nor plotly is installed")
class TestCPUVisualizer(unittest.TestCase):
    """Test cases for the CPUVisualizer class."""

    def setUp(self):
        """Set up test fixtures."""
        # Determine which backend to use for testing
        if _HAS_PLOTLY:
            backend = 'plotly'
        elif _HAS_MPL:
            backend = 'matplotlib'
        else:
            self.skipTest("No visualization backend available")
            
        self.visualizer = CPUVisualizer(backend=backend, theme='light')
        self.sample_data = generate_sample_profile_data()
        
    def tearDown(self):
        """Tear down test fixtures."""
        self.visualizer = None
        self.sample_data = None
        
        # Close any open matplotlib figures
        if _HAS_MPL:
            plt.close('all')
        
    def test_plot_function_times(self):
        """Test plotting function times."""
        # Skip show to avoid blocking
        fig = self.visualizer.plot_function_times(
            self.sample_data, 
            top_n=5, 
            show=False
        )
        
        self.assertIsNotNone(fig)
        
        # Test saving to a temporary file
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            temp_path = tmp.name
            
        try:
            self.visualizer.plot_function_times(
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
                
    def test_plot_call_counts(self):
        """Test plotting function call counts."""
        # Skip show to avoid blocking
        fig = self.visualizer.plot_call_counts(
            self.sample_data, 
            top_n=5, 
            show=False
        )
        
        self.assertIsNotNone(fig)
        
        # Test saving to a temporary file
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            temp_path = tmp.name
            
        try:
            self.visualizer.plot_call_counts(
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
                
    def test_plot_time_per_call(self):
        """Test plotting time per call."""
        # Skip show to avoid blocking
        fig = self.visualizer.plot_time_per_call(
            self.sample_data, 
            top_n=5, 
            show=False
        )
        
        self.assertIsNotNone(fig)
        
        # Test saving to a temporary file
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            temp_path = tmp.name
            
        try:
            self.visualizer.plot_time_per_call(
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
                filename=temp_path,
                include_all=True
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

if __name__ == '__main__':
    unittest.main()
