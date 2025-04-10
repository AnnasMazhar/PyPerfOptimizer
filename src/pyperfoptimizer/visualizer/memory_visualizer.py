"""
Memory visualization functionality for PyPerfOptimizer.

This module provides tools for visualizing memory profiling results
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

class MemoryVisualizer:
    """
    A class for visualizing memory profiling results.
    
    This class provides methods to create various charts and visualizations
    of memory profiling data, including time series, line-by-line memory, etc.
    """
    
    def __init__(self, 
                backend: str = 'auto',
                theme: str = 'dark',
                fig_size: Tuple[int, int] = (10, 6)):
        """
        Initialize the memory visualizer.
        
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
                
    def plot_memory_usage(self, 
                         profile_data: Dict,
                         show: bool = True,
                         save_path: Optional[str] = None,
                         include_baseline: bool = True) -> Any:
        """
        Plot memory usage over time.
        
        Args:
            profile_data: Memory profiling data (from MemoryProfiler.get_stats())
            show: Whether to display the plot
            save_path: Path to save the plot to (optional)
            include_baseline: Whether to include a baseline line
            
        Returns:
            The figure object
        """
        if not profile_data:
            raise ValueError("Invalid profile data.")
            
        # Extract memory usage data
        timestamps = profile_data.get('timestamps', [])
        memory_mb = profile_data.get('memory_mb', [])
        
        if not timestamps or not memory_mb or len(timestamps) != len(memory_mb):
            raise ValueError("Invalid memory data format.")
            
        # Adjust timestamps to start from 0
        if timestamps:
            start_time = timestamps[0]
            timestamps = [t - start_time for t in timestamps]
            
        # Get baseline if available
        baseline = profile_data.get('baseline_memory', None)
        
        # Create the figure based on the backend
        if self.backend == 'matplotlib':
            return self._plot_memory_usage_mpl(
                timestamps, memory_mb, baseline if include_baseline else None,
                show, save_path
            )
        else:  # plotly
            return self._plot_memory_usage_plotly(
                timestamps, memory_mb, baseline if include_baseline else None,
                show, save_path
            )
            
    def _plot_memory_usage_mpl(self, 
                              timestamps: List[float],
                              memory_mb: List[float],
                              baseline: Optional[float],
                              show: bool,
                              save_path: Optional[str]) -> Any:
        """Create a memory usage plot using matplotlib."""
        fig, ax = plt.subplots(figsize=self.fig_size)
        
        # Plot the memory usage line
        ax.plot(timestamps, memory_mb, '-', label='Memory Usage', linewidth=2)
        
        # Add a baseline if provided
        if baseline is not None:
            ax.axhline(y=baseline, color='r', linestyle='--', 
                      label=f'Baseline ({baseline:.2f} MB)')
            
        # Add labels and format the plot
        ax.set_xlabel('Time (seconds)')
        ax.set_ylabel('Memory Usage (MB)')
        ax.set_title('Memory Usage Over Time')
        ax.grid(True, alpha=0.3)
        
        # Add a legend
        ax.legend()
        
        # Add memory stats
        if memory_mb:
            peak_memory = max(memory_mb)
            text = f"Peak: {peak_memory:.2f} MB\n"
            
            if baseline is not None:
                text += f"Increase: {memory_mb[-1] - baseline:.2f} MB"
                
            props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
            ax.text(0.02, 0.98, text, transform=ax.transAxes, fontsize=10,
                   verticalalignment='top', bbox=props)
            
        # Adjust layout
        plt.tight_layout()
        
        # Save the figure if requested
        if save_path:
            plt.savefig(save_path, bbox_inches='tight')
            
        # Show the figure if requested
        if show:
            plt.show()
            
        return fig
        
    def _plot_memory_usage_plotly(self, 
                                 timestamps: List[float],
                                 memory_mb: List[float],
                                 baseline: Optional[float],
                                 show: bool,
                                 save_path: Optional[str]) -> Any:
        """Create a memory usage plot using plotly."""
        # Set the template based on the theme
        template = 'plotly_dark' if self.theme == 'dark' else 'plotly_white'
        
        # Create the figure
        fig = go.Figure()
        
        # Add the memory usage line
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=memory_mb,
            mode='lines',
            name='Memory Usage',
            line=dict(width=3, color='royalblue')
        ))
        
        # Add a baseline if provided
        if baseline is not None:
            fig.add_trace(go.Scatter(
                x=[timestamps[0], timestamps[-1]],
                y=[baseline, baseline],
                mode='lines',
                name=f'Baseline ({baseline:.2f} MB)',
                line=dict(width=2, color='red', dash='dash')
            ))
            
        # Add memory stats annotation
        if memory_mb:
            peak_memory = max(memory_mb)
            annotation_text = f"Peak: {peak_memory:.2f} MB<br>"
            
            if baseline is not None:
                annotation_text += f"Increase: {memory_mb[-1] - baseline:.2f} MB"
                
            fig.add_annotation(
                x=0.02,
                y=0.98,
                xref="paper",
                yref="paper",
                text=annotation_text,
                showarrow=False,
                bgcolor="rgba(255, 255, 255, 0.7)" if self.theme == 'dark' else "rgba(0, 0, 0, 0.1)",
                bordercolor="black",
                borderwidth=1,
                borderpad=4
            )
            
        # Update layout
        fig.update_layout(
            title='Memory Usage Over Time',
            xaxis_title='Time (seconds)',
            yaxis_title='Memory Usage (MB)',
            template=template,
            height=self.fig_size[1] * 100,
            width=self.fig_size[0] * 100,
            hovermode='x',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        # Save the figure if requested
        if save_path:
            fig.write_image(save_path)
            
        # Show the figure if requested
        if show:
            fig.show()
            
        return fig
        
    def plot_line_memory(self, 
                        line_profile_data: Dict,
                        top_n: int = 10,
                        show: bool = True,
                        save_path: Optional[str] = None) -> Any:
        """
        Plot memory usage by line.
        
        Args:
            line_profile_data: Line-by-line memory profiling data
            top_n: Number of top lines to display
            show: Whether to display the plot
            save_path: Path to save the plot to (optional)
            
        Returns:
            The figure object
        """
        if not line_profile_data or 'line_stats' not in line_profile_data:
            raise ValueError("Invalid line profile data.")
            
        # Extract line statistics
        line_stats = line_profile_data.get('line_stats', [])
        
        # Sort by increment and take top N
        sorted_lines = sorted(
            line_stats, 
            key=lambda x: abs(x.get('increment_mb', 0)), 
            reverse=True
        )
        top_lines = sorted_lines[:top_n]
        
        # Extract line numbers, increments, and code snippets
        line_nums = [f"Line {line.get('line_num', 0)}" for line in top_lines]
        increments = [line.get('increment_mb', 0) for line in top_lines]
        code_snippets = [line.get('code', '').strip() for line in top_lines]
        
        # Create labels with line number and code
        labels = [f"{num}: {code[:40]}..." if len(code) > 40 else f"{num}: {code}" 
                 for num, code in zip(line_nums, code_snippets)]
        
        # Reverse for better visualization
        labels.reverse()
        increments.reverse()
        
        # Create the figure based on the backend
        if self.backend == 'matplotlib':
            return self._plot_line_memory_mpl(labels, increments, show, save_path)
        else:  # plotly
            return self._plot_line_memory_plotly(labels, increments, show, save_path)
            
    def _plot_line_memory_mpl(self, 
                             labels: List[str],
                             increments: List[float],
                             show: bool,
                             save_path: Optional[str]) -> Any:
        """Create a line memory plot using matplotlib."""
        fig, ax = plt.subplots(figsize=self.fig_size)
        
        # Create a horizontal bar chart
        y_pos = range(len(labels))
        bars = ax.barh(y_pos, increments, align='center')
        
        # Color bars based on increment (positive/negative)
        for i, inc in enumerate(increments):
            bars[i].set_color('red' if inc > 0 else 'green')
            
        # Add labels and format the plot
        ax.set_yticks(y_pos)
        ax.set_yticklabels(labels)
        ax.set_xlabel('Memory Change (MB)')
        ax.set_title('Memory Usage by Line')
        
        # Add memory values as text at the end of bars
        for i, v in enumerate(increments):
            ax.text(v + 0.01 * max(increments) if v > 0 else v - 0.05 * abs(min(increments)) if min(increments) < 0 else v + 0.01,
                   i, f'{v:.2f} MB', va='center')
            
        # Add a zero line
        ax.axvline(x=0, color='k', linestyle='-', alpha=0.3)
        
        # Adjust layout
        plt.tight_layout()
        
        # Save the figure if requested
        if save_path:
            plt.savefig(save_path, bbox_inches='tight')
            
        # Show the figure if requested
        if show:
            plt.show()
            
        return fig
        
    def _plot_line_memory_plotly(self, 
                                labels: List[str],
                                increments: List[float],
                                show: bool,
                                save_path: Optional[str]) -> Any:
        """Create a line memory plot using plotly."""
        # Set the template based on the theme
        template = 'plotly_dark' if self.theme == 'dark' else 'plotly_white'
        
        # Create a horizontal bar chart with colors based on increment
        colors = ['rgba(255,0,0,0.7)' if inc > 0 else 'rgba(0,255,0,0.7)' for inc in increments]
        
        fig = go.Figure(data=[
            go.Bar(
                x=increments,
                y=labels,
                orientation='h',
                text=[f'{i:.2f} MB' for i in increments],
                textposition='outside',
                marker_color=colors
            )
        ])
        
        # Update layout
        fig.update_layout(
            title='Memory Usage by Line',
            xaxis_title='Memory Change (MB)',
            yaxis_title='Code Line',
            template=template,
            height=self.fig_size[1] * 100,
            width=self.fig_size[0] * 100,
            shapes=[
                dict(
                    type='line',
                    x0=0,
                    x1=0,
                    y0=-0.5,
                    y1=len(increments) - 0.5,
                    line=dict(
                        color='white' if self.theme == 'dark' else 'black',
                        width=1,
                        dash='solid'
                    )
                )
            ]
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
                             line_data: Optional[Dict] = None,
                             filename: str = "memory_profile.html") -> None:
        """
        Create an interactive HTML report with memory profiling visualizations.
        
        Args:
            profile_data: Memory profiling data
            line_data: Line-by-line memory profiling data (optional)
            filename: Path to save the HTML file to
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
        
        # Create the memory usage figure
        fig1 = self.plot_memory_usage(profile_data, show=False)
        
        if line_data and 'line_stats' in line_data:
            # Create the line memory figure
            fig2 = self.plot_line_memory(line_data, show=False)
            
            # Combine the figures
            from plotly.subplots import make_subplots
            
            # Create a grid of subplots
            combined_fig = make_subplots(
                rows=2, 
                cols=1,
                subplot_titles=(
                    'Memory Usage Over Time',
                    'Memory Usage by Line'
                ),
                vertical_spacing=0.1
            )
            
            # Add traces from each figure
            for trace in fig1.data:
                combined_fig.add_trace(trace, row=1, col=1)
                
            for trace in fig2.data:
                combined_fig.add_trace(trace, row=2, col=1)
                
            # Update layout
            combined_fig.update_layout(
                title='Memory Profiling Results',
                height=1000,
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
