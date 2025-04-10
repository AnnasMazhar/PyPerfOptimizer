"""
CPU visualization functionality for PyPerfOptimizer.

This module provides tools for visualizing CPU profiling results 
using various chart types and formats.
"""

import os
import json
from typing import Dict, List, Optional, Any, Union, Tuple

# Try to import visualization libraries
try:
    import matplotlib
    import matplotlib.pyplot as plt
    _HAS_MPL = True
except ImportError:
    _HAS_MPL = False

try:
    import plotly.graph_objects as go
    import plotly.express as px
    _HAS_PLOTLY = True
except ImportError:
    _HAS_PLOTLY = False

class CPUVisualizer:
    """
    A class for visualizing CPU profiling results.
    
    This class provides methods to create various charts and visualizations
    of CPU profiling data, including function call times, call graphs, and more.
    """
    
    def __init__(self, 
                backend: str = 'auto',
                theme: str = 'dark',
                fig_size: Tuple[int, int] = (10, 6)):
        """
        Initialize the CPU visualizer.
        
        Args:
            backend: Visualization backend ('matplotlib', 'plotly', or 'auto')
            theme: Color theme ('light' or 'dark')
            fig_size: Figure size as (width, height) in inches
        """
        # Determine the backend to use
        if backend == 'auto':
            if _HAS_PLOTLY:
                self.backend = 'plotly'
            elif _HAS_MPL:
                self.backend = 'matplotlib'
            else:
                raise ImportError(
                    "No visualization backend available. "
                    "Install matplotlib or plotly: pip install matplotlib plotly"
                )
        elif backend == 'matplotlib':
            if not _HAS_MPL:
                raise ImportError(
                    "Matplotlib is not installed. Install it with: pip install matplotlib"
                )
            self.backend = 'matplotlib'
        elif backend == 'plotly':
            if not _HAS_PLOTLY:
                raise ImportError(
                    "Plotly is not installed. Install it with: pip install plotly"
                )
            self.backend = 'plotly'
        else:
            raise ValueError(f"Unsupported backend: {backend}")
            
        self.theme = theme
        self.fig_size = fig_size
        
        # Set up the theme for matplotlib
        if self.backend == 'matplotlib':
            if theme == 'dark':
                plt.style.use('dark_background')
            else:
                plt.style.use('default')
                
    def plot_function_times(self, 
                           profile_data: Dict,
                           top_n: int = 10,
                           sort_by: str = 'cumtime',
                           show: bool = True,
                           save_path: Optional[str] = None) -> Any:
        """
        Plot time spent in different functions.
        
        Args:
            profile_data: CPU profiling data (from CPUProfiler.get_stats())
            top_n: Number of top functions to display
            sort_by: Sorting criteria ('cumtime' or 'tottime')
            show: Whether to display the plot
            save_path: Path to save the plot to (optional)
            
        Returns:
            The figure object
        """
        if not profile_data or 'functions' not in profile_data:
            raise ValueError("Invalid profile data. Missing 'functions' key.")
            
        # Extract function data
        functions = profile_data.get('functions', [])
        
        # Sort functions by the specified criteria
        if sort_by == 'cumtime':
            sort_key = 'cumtime'
        elif sort_by == 'tottime':
            sort_key = 'tottime'
        else:
            raise ValueError(f"Invalid sort_by value: {sort_by}")
            
        sorted_funcs = sorted(
            functions, 
            key=lambda x: float(x.get(sort_key, 0)), 
            reverse=True
        )
        
        # Take the top N functions
        top_funcs = sorted_funcs[:top_n]
        
        # Extract function names and times
        func_names = [func.get('function', '').split('/')[-1] for func in top_funcs]
        func_times = [float(func.get(sort_key, 0)) for func in top_funcs]
        
        # Reverse the order for better visualization (matplotlib plots from bottom to top)
        func_names.reverse()
        func_times.reverse()
        
        # Create the figure based on the backend
        if self.backend == 'matplotlib':
            return self._plot_function_times_mpl(func_names, func_times, sort_by, show, save_path)
        else:  # plotly
            return self._plot_function_times_plotly(func_names, func_times, sort_by, show, save_path)
            
    def _plot_function_times_mpl(self, 
                                func_names: List[str],
                                func_times: List[float],
                                sort_by: str,
                                show: bool,
                                save_path: Optional[str]) -> Any:
        """Create a function times plot using matplotlib."""
        fig, ax = plt.subplots(figsize=self.fig_size)
        
        # Create a horizontal bar chart
        y_pos = range(len(func_names))
        bars = ax.barh(y_pos, func_times, align='center')
        
        # Add labels and format the plot
        ax.set_yticks(y_pos)
        ax.set_yticklabels(func_names)
        ax.set_xlabel('Time (seconds)')
        time_type = 'Cumulative' if sort_by == 'cumtime' else 'Total'
        ax.set_title(f'{time_type} Time by Function')
        
        # Add time values as text at the end of bars
        for i, v in enumerate(func_times):
            ax.text(v + 0.01 * max(func_times), i, f'{v:.4f}s', va='center')
            
        # Adjust layout
        plt.tight_layout()
        
        # Save the figure if requested
        if save_path:
            plt.savefig(save_path, bbox_inches='tight')
            
        # Show the figure if requested
        if show:
            plt.show()
            
        return fig
        
    def _plot_function_times_plotly(self, 
                                   func_names: List[str],
                                   func_times: List[float],
                                   sort_by: str,
                                   show: bool,
                                   save_path: Optional[str]) -> Any:
        """Create a function times plot using plotly."""
        # Set the template based on the theme
        template = 'plotly_dark' if self.theme == 'dark' else 'plotly_white'
        
        # Create a horizontal bar chart
        time_type = 'Cumulative' if sort_by == 'cumtime' else 'Total'
        fig = go.Figure(data=[
            go.Bar(
                x=func_times,
                y=func_names,
                orientation='h',
                text=[f'{t:.4f}s' for t in func_times],
                textposition='outside',
                marker_color='royalblue'
            )
        ])
        
        # Update layout
        fig.update_layout(
            title=f'{time_type} Time by Function',
            xaxis_title='Time (seconds)',
            yaxis_title='Function',
            template=template,
            height=self.fig_size[1] * 100,
            width=self.fig_size[0] * 100,
        )
        
        # Save the figure if requested
        if save_path:
            fig.write_image(save_path)
            
        # Show the figure if requested
        if show:
            fig.show()
            
        return fig
        
    def plot_call_counts(self, 
                        profile_data: Dict,
                        top_n: int = 10,
                        show: bool = True,
                        save_path: Optional[str] = None) -> Any:
        """
        Plot function call counts.
        
        Args:
            profile_data: CPU profiling data (from CPUProfiler.get_stats())
            top_n: Number of top functions to display
            show: Whether to display the plot
            save_path: Path to save the plot to (optional)
            
        Returns:
            The figure object
        """
        if not profile_data or 'functions' not in profile_data:
            raise ValueError("Invalid profile data. Missing 'functions' key.")
            
        # Extract function data
        functions = profile_data.get('functions', [])
        
        # Extract call counts and sort
        func_data = []
        for func in functions:
            if 'ncalls' in func:
                try:
                    # Handle recursive functions (format: 'n/m')
                    ncalls_str = func['ncalls'].split('/')[0]
                    ncalls = int(ncalls_str)
                    func_data.append({
                        'name': func.get('function', '').split('/')[-1],
                        'calls': ncalls
                    })
                except (ValueError, IndexError):
                    continue
                    
        # Sort by call count and take top N
        sorted_funcs = sorted(func_data, key=lambda x: x['calls'], reverse=True)
        top_funcs = sorted_funcs[:top_n]
        
        # Extract names and call counts
        func_names = [func['name'] for func in top_funcs]
        call_counts = [func['calls'] for func in top_funcs]
        
        # Reverse for better visualization
        func_names.reverse()
        call_counts.reverse()
        
        # Create the figure based on the backend
        if self.backend == 'matplotlib':
            return self._plot_call_counts_mpl(func_names, call_counts, show, save_path)
        else:  # plotly
            return self._plot_call_counts_plotly(func_names, call_counts, show, save_path)
            
    def _plot_call_counts_mpl(self, 
                             func_names: List[str],
                             call_counts: List[int],
                             show: bool,
                             save_path: Optional[str]) -> Any:
        """Create a call counts plot using matplotlib."""
        fig, ax = plt.subplots(figsize=self.fig_size)
        
        # Create a horizontal bar chart
        y_pos = range(len(func_names))
        bars = ax.barh(y_pos, call_counts, align='center')
        
        # Add labels and format the plot
        ax.set_yticks(y_pos)
        ax.set_yticklabels(func_names)
        ax.set_xlabel('Number of Calls')
        ax.set_title('Function Call Counts')
        
        # Add call counts as text at the end of bars
        for i, v in enumerate(call_counts):
            ax.text(v + 0.01 * max(call_counts), i, str(v), va='center')
            
        # Adjust layout
        plt.tight_layout()
        
        # Save the figure if requested
        if save_path:
            plt.savefig(save_path, bbox_inches='tight')
            
        # Show the figure if requested
        if show:
            plt.show()
            
        return fig
        
    def _plot_call_counts_plotly(self, 
                                func_names: List[str],
                                call_counts: List[int],
                                show: bool,
                                save_path: Optional[str]) -> Any:
        """Create a call counts plot using plotly."""
        # Set the template based on the theme
        template = 'plotly_dark' if self.theme == 'dark' else 'plotly_white'
        
        # Create a horizontal bar chart
        fig = go.Figure(data=[
            go.Bar(
                x=call_counts,
                y=func_names,
                orientation='h',
                text=call_counts,
                textposition='outside',
                marker_color='lightsalmon'
            )
        ])
        
        # Update layout
        fig.update_layout(
            title='Function Call Counts',
            xaxis_title='Number of Calls',
            yaxis_title='Function',
            template=template,
            height=self.fig_size[1] * 100,
            width=self.fig_size[0] * 100,
        )
        
        # Save the figure if requested
        if save_path:
            fig.write_image(save_path)
            
        # Show the figure if requested
        if show:
            fig.show()
            
        return fig
        
    def plot_time_per_call(self, 
                          profile_data: Dict,
                          top_n: int = 10,
                          show: bool = True,
                          save_path: Optional[str] = None) -> Any:
        """
        Plot time per call for functions.
        
        Args:
            profile_data: CPU profiling data (from CPUProfiler.get_stats())
            top_n: Number of top functions to display
            show: Whether to display the plot
            save_path: Path to save the plot to (optional)
            
        Returns:
            The figure object
        """
        if not profile_data or 'functions' not in profile_data:
            raise ValueError("Invalid profile data. Missing 'functions' key.")
            
        # Extract function data
        functions = profile_data.get('functions', [])
        
        # Calculate time per call and sort
        func_data = []
        for func in functions:
            if 'percall_cumtime' in func and 'function' in func:
                try:
                    time_per_call = float(func['percall_cumtime'])
                    func_data.append({
                        'name': func.get('function', '').split('/')[-1],
                        'time_per_call': time_per_call
                    })
                except ValueError:
                    continue
                    
        # Sort by time per call and take top N
        sorted_funcs = sorted(func_data, key=lambda x: x['time_per_call'], reverse=True)
        top_funcs = sorted_funcs[:top_n]
        
        # Extract names and times per call
        func_names = [func['name'] for func in top_funcs]
        times_per_call = [func['time_per_call'] for func in top_funcs]
        
        # Reverse for better visualization
        func_names.reverse()
        times_per_call.reverse()
        
        # Create the figure based on the backend
        if self.backend == 'matplotlib':
            return self._plot_time_per_call_mpl(func_names, times_per_call, show, save_path)
        else:  # plotly
            return self._plot_time_per_call_plotly(func_names, times_per_call, show, save_path)
            
    def _plot_time_per_call_mpl(self, 
                               func_names: List[str],
                               times_per_call: List[float],
                               show: bool,
                               save_path: Optional[str]) -> Any:
        """Create a time per call plot using matplotlib."""
        fig, ax = plt.subplots(figsize=self.fig_size)
        
        # Create a horizontal bar chart
        y_pos = range(len(func_names))
        bars = ax.barh(y_pos, times_per_call, align='center')
        
        # Add labels and format the plot
        ax.set_yticks(y_pos)
        ax.set_yticklabels(func_names)
        ax.set_xlabel('Time per Call (seconds)')
        ax.set_title('Time per Call by Function')
        
        # Add times as text at the end of bars
        for i, v in enumerate(times_per_call):
            ax.text(v + 0.01 * max(times_per_call), i, f'{v:.6f}s', va='center')
            
        # Adjust layout
        plt.tight_layout()
        
        # Save the figure if requested
        if save_path:
            plt.savefig(save_path, bbox_inches='tight')
            
        # Show the figure if requested
        if show:
            plt.show()
            
        return fig
        
    def _plot_time_per_call_plotly(self, 
                                  func_names: List[str],
                                  times_per_call: List[float],
                                  show: bool,
                                  save_path: Optional[str]) -> Any:
        """Create a time per call plot using plotly."""
        # Set the template based on the theme
        template = 'plotly_dark' if self.theme == 'dark' else 'plotly_white'
        
        # Create a horizontal bar chart
        fig = go.Figure(data=[
            go.Bar(
                x=times_per_call,
                y=func_names,
                orientation='h',
                text=[f'{t:.6f}s' for t in times_per_call],
                textposition='outside',
                marker_color='lightgreen'
            )
        ])
        
        # Update layout
        fig.update_layout(
            title='Time per Call by Function',
            xaxis_title='Time per Call (seconds)',
            yaxis_title='Function',
            template=template,
            height=self.fig_size[1] * 100,
            width=self.fig_size[0] * 100,
        )
        
        # Save the figure if requested
        if save_path:
            fig.write_image(save_path)
            
        # Show the figure if requested
        if show:
            fig.show()
            
        return fig
        
    def save_interactive_html(self,
                             profile_data: Dict,
                             filename: str,
                             include_all: bool = True) -> None:
        """
        Create an interactive HTML report with profiling visualizations.
        
        Args:
            profile_data: CPU profiling data (from CPUProfiler.get_stats())
            filename: Path to save the HTML file to
            include_all: Whether to include all plot types
        """
        if not _HAS_PLOTLY:
            raise ImportError(
                "Plotly is required for interactive HTML reports. "
                "Install it with: pip install plotly"
            )
            
        # Ensure the directory exists
        os.makedirs(os.path.dirname(filename) if os.path.dirname(filename) else '.', exist_ok=True)
        
        # Force backend to plotly for HTML output
        old_backend = self.backend
        self.backend = 'plotly'
        
        # Create figures
        fig1 = self.plot_function_times(profile_data, show=False)
        
        if include_all:
            fig2 = self.plot_call_counts(profile_data, show=False)
            fig3 = self.plot_time_per_call(profile_data, show=False)
            
            # Combine the figures
            from plotly.subplots import make_subplots
            
            # Create a grid of subplots
            combined_fig = make_subplots(
                rows=3, 
                cols=1,
                subplot_titles=(
                    'Cumulative Time by Function',
                    'Function Call Counts',
                    'Time per Call by Function'
                ),
                vertical_spacing=0.1
            )
            
            # Add traces from each figure
            for trace in fig1.data:
                combined_fig.add_trace(trace, row=1, col=1)
                
            for trace in fig2.data:
                combined_fig.add_trace(trace, row=2, col=1)
                
            for trace in fig3.data:
                combined_fig.add_trace(trace, row=3, col=1)
                
            # Update layout
            combined_fig.update_layout(
                title='CPU Profiling Results',
                height=1200,
                width=1000,
                template='plotly_dark' if self.theme == 'dark' else 'plotly_white',
                showlegend=False
            )
            
            # Write the combined figure to HTML
            combined_fig.write_html(filename)
        else:
            # Just write the first figure to HTML
            fig1.write_html(filename)
            
        # Restore the original backend
        self.backend = old_backend
