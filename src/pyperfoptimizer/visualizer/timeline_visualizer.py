"""
Timeline visualization functionality for PyPerfOptimizer.

This module provides tools for creating timeline visualizations of profiling
results, showing the execution flow and timing of functions.
"""

import os
import json
from typing import Dict, List, Optional, Any, Union, Tuple

# Try to import visualization libraries
try:
    import matplotlib
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    _HAS_MPL = True
except ImportError:
    _HAS_MPL = False

try:
    import plotly.graph_objects as go
    import plotly.express as px
    _HAS_PLOTLY = True
except ImportError:
    _HAS_PLOTLY = False

class TimelineVisualizer:
    """
    A class for creating timeline visualizations of profiling results.
    
    This class provides methods to visualize the execution flow of functions,
    showing when functions were called and how long they took to execute.
    """
    
    def __init__(self, 
                backend: str = 'auto',
                theme: str = 'dark',
                fig_size: Tuple[int, int] = (12, 8)):
        """
        Initialize the timeline visualizer.
        
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
                
    def create_function_timeline(self, 
                                call_data: List[Dict],
                                show: bool = True,
                                save_path: Optional[str] = None) -> Any:
        """
        Create a timeline visualization of function calls.
        
        Args:
            call_data: List of dictionaries containing function call information
                Each dict should have: {'name': 'func_name', 'start': start_time, 
                'end': end_time, 'depth': call_depth}
            show: Whether to display the plot
            save_path: Path to save the plot to (optional)
            
        Returns:
            The figure object
        """
        if not call_data:
            raise ValueError("No call data provided")
            
        # Create the figure based on the backend
        if self.backend == 'matplotlib':
            return self._create_function_timeline_mpl(call_data, show, save_path)
        else:  # plotly
            return self._create_function_timeline_plotly(call_data, show, save_path)
            
    def _create_function_timeline_mpl(self, 
                                     call_data: List[Dict],
                                     show: bool,
                                     save_path: Optional[str]) -> Any:
        """Create a function timeline plot using matplotlib."""
        fig, ax = plt.subplots(figsize=self.fig_size)
        
        # Define colors for different depths
        colors = plt.cm.viridis(
            [i / max(1, max(c['depth'] for c in call_data)) for c in call_data]
        )
        
        # Get the time range
        min_time = min(c['start'] for c in call_data)
        max_time = max(c['end'] for c in call_data)
        
        # Assign y positions to functions based on call order
        y_positions = {}
        current_position = 0
        
        for call in call_data:
            name = call['name']
            if name not in y_positions:
                y_positions[name] = current_position
                current_position += 1
                
        # Plot rectangles for each function call
        for i, call in enumerate(call_data):
            name = call['name']
            start = call['start']
            end = call['end']
            depth = call['depth']
            
            y_pos = y_positions[name]
            duration = end - start
            
            # Create rectangle for the function call
            rect = patches.Rectangle(
                (start - min_time, y_pos - 0.4),
                duration,
                0.8,
                linewidth=1,
                edgecolor='black',
                facecolor=colors[i],
                alpha=0.7
            )
            ax.add_patch(rect)
            
            # Add function name in the middle of the rectangle if it's wide enough
            if duration > (max_time - min_time) * 0.05:
                ax.text(
                    start - min_time + duration / 2,
                    y_pos,
                    name,
                    ha='center',
                    va='center',
                    fontsize=8,
                    color='white' if depth > len(call_data) / 2 else 'black'
                )
                
        # Set y-ticks to function names
        ax.set_yticks(list(y_positions.values()))
        ax.set_yticklabels(list(y_positions.keys()))
        
        # Set x-axis and title
        ax.set_xlabel('Time (seconds)')
        ax.set_title('Function Call Timeline')
        
        # Set x limits
        ax.set_xlim(-0.05 * (max_time - min_time), (max_time - min_time) * 1.05)
        
        # Set y limits with some padding
        ax.set_ylim(-1, len(y_positions))
        
        # Add a colorbar to show depth
        sm = plt.cm.ScalarMappable(
            cmap=plt.cm.viridis,
            norm=plt.Normalize(0, max(c['depth'] for c in call_data))
        )
        sm.set_array([])
        cbar = plt.colorbar(sm, ax=ax)
        cbar.set_label('Call Depth')
        
        # Adjust layout
        plt.tight_layout()
        
        # Save the figure if requested
        if save_path:
            plt.savefig(save_path, bbox_inches='tight')
            
        # Show the figure if requested
        if show:
            plt.show()
            
        return fig
        
    def _create_function_timeline_plotly(self, 
                                        call_data: List[Dict],
                                        show: bool,
                                        save_path: Optional[str]) -> Any:
        """Create a function timeline plot using plotly."""
        # Set the template based on the theme
        template = 'plotly_dark' if self.theme == 'dark' else 'plotly_white'
        
        # Get the time range
        min_time = min(c['start'] for c in call_data)
        max_time = max(c['end'] for c in call_data)
        
        # Normalize all times to start from 0
        for call in call_data:
            call['start'] = call['start'] - min_time
            call['end'] = call['end'] - min_time
            
        # Assign y positions to functions based on call order
        y_positions = {}
        current_position = 0
        
        for call in call_data:
            name = call['name']
            if name not in y_positions:
                y_positions[name] = current_position
                current_position += 1
                
        # Create the timeline figure
        fig = go.Figure()
        
        # Get the maximum depth for color scaling
        max_depth = max(c['depth'] for c in call_data) if call_data else 1
        
        # Add a bar for each function call
        for call in call_data:
            name = call['name']
            start = call['start']
            end = call['end']
            depth = call['depth']
            duration = end - start
            
            # Skip very short calls for clarity
            if duration < (max_time - min_time) * 0.001:
                continue
                
            # Add the bar
            fig.add_trace(go.Bar(
                x=[duration],
                y=[list(y_positions.keys()).index(name)],
                orientation='h',
                base=start,
                width=0.8,
                name=name,
                text=f"{name} ({duration:.6f}s)",
                marker=dict(
                    color=depth,
                    colorscale='Viridis',
                    cmin=0,
                    cmax=max_depth,
                    colorbar=dict(
                        title="Call Depth"
                    )
                ),
                showlegend=False,
                hoverinfo='text'
            ))
            
        # Update layout
        fig.update_layout(
            title='Function Call Timeline',
            xaxis_title='Time (seconds)',
            yaxis=dict(
                title='Function',
                tickmode='array',
                tickvals=list(range(len(y_positions))),
                ticktext=list(y_positions.keys())
            ),
            template=template,
            height=self.fig_size[1] * 100,
            width=self.fig_size[0] * 100,
            barmode='stack',
            bargap=0.15,
        )
        
        # Save the figure if requested
        if save_path:
            fig.write_image(save_path)
            
        # Show the figure if requested
        if show:
            fig.show()
            
        return fig
        
    def create_comparative_timeline(self, 
                                   baseline_data: List[Dict],
                                   optimized_data: List[Dict],
                                   show: bool = True,
                                   save_path: Optional[str] = None) -> Any:
        """
        Create a comparative timeline visualization for before/after optimization.
        
        Args:
            baseline_data: Function call data before optimization
            optimized_data: Function call data after optimization
            show: Whether to display the plot
            save_path: Path to save the plot to (optional)
            
        Returns:
            The figure object
        """
        if not baseline_data or not optimized_data:
            raise ValueError("Invalid baseline or optimized data")
            
        # Create the figure based on the backend
        if self.backend == 'matplotlib':
            return self._create_comparative_timeline_mpl(
                baseline_data, optimized_data, show, save_path
            )
        else:  # plotly
            return self._create_comparative_timeline_plotly(
                baseline_data, optimized_data, show, save_path
            )
            
    def _create_comparative_timeline_mpl(self, 
                                        baseline_data: List[Dict],
                                        optimized_data: List[Dict],
                                        show: bool,
                                        save_path: Optional[str]) -> Any:
        """Create a comparative timeline plot using matplotlib."""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=self.fig_size, sharex=True)
        
        # Process baseline data
        min_time_baseline = min(c['start'] for c in baseline_data)
        baseline_duration = max(c['end'] for c in baseline_data) - min_time_baseline
        
        # Process optimized data
        min_time_optimized = min(c['start'] for c in optimized_data)
        optimized_duration = max(c['end'] for c in optimized_data) - min_time_optimized
        
        # Get unique function names from both datasets
        all_names = set()
        for call in baseline_data + optimized_data:
            all_names.add(call['name'])
            
        # Assign consistent y positions across both plots
        y_positions = {name: i for i, name in enumerate(sorted(all_names))}
        
        # Define colors based on function name for consistency
        unique_names = sorted(list(all_names))
        color_map = {}
        for i, name in enumerate(unique_names):
            color_map[name] = plt.cm.tab20(i % 20)
            
        # Plot the baseline data
        for call in baseline_data:
            name = call['name']
            start = call['start'] - min_time_baseline
            end = call['end'] - min_time_baseline
            duration = end - start
            
            # Create rectangle
            rect = patches.Rectangle(
                (start, y_positions[name] - 0.4),
                duration,
                0.8,
                linewidth=1,
                edgecolor='black',
                facecolor=color_map[name],
                alpha=0.7
            )
            ax1.add_patch(rect)
            
            # Add function name in the middle of the rectangle if it's wide enough
            if duration > baseline_duration * 0.05:
                ax1.text(
                    start + duration / 2,
                    y_positions[name],
                    name,
                    ha='center',
                    va='center',
                    fontsize=8
                )
                
        # Plot the optimized data
        for call in optimized_data:
            name = call['name']
            start = call['start'] - min_time_optimized
            end = call['end'] - min_time_optimized
            duration = end - start
            
            # Create rectangle
            rect = patches.Rectangle(
                (start, y_positions[name] - 0.4),
                duration,
                0.8,
                linewidth=1,
                edgecolor='black',
                facecolor=color_map[name],
                alpha=0.7
            )
            ax2.add_patch(rect)
            
            # Add function name in the middle of the rectangle if it's wide enough
            if duration > optimized_duration * 0.05:
                ax2.text(
                    start + duration / 2,
                    y_positions[name],
                    name,
                    ha='center',
                    va='center',
                    fontsize=8
                )
                
        # Set y-ticks to function names
        y_values = list(y_positions.values())
        y_labels = list(y_positions.keys())
        
        ax1.set_yticks(y_values)
        ax1.set_yticklabels(y_labels)
        ax2.set_yticks(y_values)
        ax2.set_yticklabels(y_labels)
        
        # Set x and y limits
        max_duration = max(baseline_duration, optimized_duration)
        ax1.set_xlim(-0.05 * max_duration, max_duration * 1.05)
        ax2.set_xlim(-0.05 * max_duration, max_duration * 1.05)
        
        ax1.set_ylim(-1, len(y_positions))
        ax2.set_ylim(-1, len(y_positions))
        
        # Add titles and labels
        ax1.set_title('Baseline Performance')
        ax2.set_title('Optimized Performance')
        ax2.set_xlabel('Time (seconds)')
        
        # Calculate speedup
        speedup = baseline_duration / optimized_duration if optimized_duration > 0 else float('inf')
        fig.suptitle(f'Performance Comparison (Speedup: {speedup:.2f}x)', fontsize=14)
        
        # Add annotation showing speedup
        ax1.text(
            0.98, 0.02, 
            f"Total: {baseline_duration:.4f}s",
            ha='right',
            va='bottom',
            transform=ax1.transAxes,
            bbox=dict(facecolor='white', alpha=0.7, boxstyle='round')
        )
        
        ax2.text(
            0.98, 0.02, 
            f"Total: {optimized_duration:.4f}s",
            ha='right',
            va='bottom',
            transform=ax2.transAxes,
            bbox=dict(facecolor='white', alpha=0.7, boxstyle='round')
        )
        
        # Adjust layout
        plt.tight_layout()
        fig.subplots_adjust(top=0.9)
        
        # Save the figure if requested
        if save_path:
            plt.savefig(save_path, bbox_inches='tight')
            
        # Show the figure if requested
        if show:
            plt.show()
            
        return fig
        
    def _create_comparative_timeline_plotly(self, 
                                           baseline_data: List[Dict],
                                           optimized_data: List[Dict],
                                           show: bool,
                                           save_path: Optional[str]) -> Any:
        """Create a comparative timeline plot using plotly."""
        # Set the template based on the theme
        template = 'plotly_dark' if self.theme == 'dark' else 'plotly_white'
        
        # Process baseline data
        min_time_baseline = min(c['start'] for c in baseline_data)
        for call in baseline_data:
            call['start'] = call['start'] - min_time_baseline
            call['end'] = call['end'] - min_time_baseline
        baseline_duration = max(c['end'] for c in baseline_data)
        
        # Process optimized data
        min_time_optimized = min(c['start'] for c in optimized_data)
        for call in optimized_data:
            call['start'] = call['start'] - min_time_optimized
            call['end'] = call['end'] - min_time_optimized
        optimized_duration = max(c['end'] for c in optimized_data)
        
        # Get unique function names
        all_names = set()
        for call in baseline_data + optimized_data:
            all_names.add(call['name'])
            
        # Assign consistent y positions
        y_positions = {name: i for i, name in enumerate(sorted(all_names))}
        
        # Create the figure
        fig = go.Figure()
        
        # Add subplot titles
        baseline_title = f"Baseline Performance (Total: {baseline_duration:.4f}s)"
        optimized_title = f"Optimized Performance (Total: {optimized_duration:.4f}s)"
        
        # Calculate color mapping
        unique_names = sorted(list(all_names))
        
        # Add baseline data
        for call in baseline_data:
            name = call['name']
            start = call['start']
            end = call['end']
            duration = end - start
            
            # Skip very short calls for clarity
            if duration < baseline_duration * 0.001:
                continue
                
            fig.add_trace(go.Bar(
                x=[duration],
                y=[list(y_positions.keys()).index(name)],
                orientation='h',
                base=start,
                width=0.8,
                name=name,
                legendgroup=name,
                text=f"{name} ({duration:.6f}s)",
                marker_color=px.colors.qualitative.Plotly[unique_names.index(name) % len(px.colors.qualitative.Plotly)],
                showlegend=True,
                hoverinfo='text',
                xaxis='x1',
                yaxis='y1'
            ))
            
        # Add optimized data
        for call in optimized_data:
            name = call['name']
            start = call['start']
            end = call['end']
            duration = end - start
            
            # Skip very short calls for clarity
            if duration < optimized_duration * 0.001:
                continue
                
            fig.add_trace(go.Bar(
                x=[duration],
                y=[list(y_positions.keys()).index(name)],
                orientation='h',
                base=start,
                width=0.8,
                name=name,
                legendgroup=name,
                text=f"{name} ({duration:.6f}s)",
                marker_color=px.colors.qualitative.Plotly[unique_names.index(name) % len(px.colors.qualitative.Plotly)],
                showlegend=False,
                hoverinfo='text',
                xaxis='x2',
                yaxis='y2'
            ))
            
        # Calculate speedup
        speedup = baseline_duration / optimized_duration if optimized_duration > 0 else float('inf')
        
        # Update layout
        fig.update_layout(
            title=f"Performance Comparison (Speedup: {speedup:.2f}x)",
            template=template,
            height=self.fig_size[1] * 100,
            width=self.fig_size[0] * 100,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5
            ),
            grid=dict(rows=2, columns=1, pattern='independent'),
            xaxis1=dict(
                title='',
                domain=[0, 1],
                anchor='y1'
            ),
            yaxis1=dict(
                title='',
                domain=[0.55, 1],
                tickmode='array',
                tickvals=list(range(len(y_positions))),
                ticktext=list(y_positions.keys()),
                anchor='x1'
            ),
            xaxis2=dict(
                title='Time (seconds)',
                domain=[0, 1],
                anchor='y2'
            ),
            yaxis2=dict(
                title='',
                domain=[0, 0.45],
                tickmode='array',
                tickvals=list(range(len(y_positions))),
                ticktext=list(y_positions.keys()),
                anchor='x2'
            ),
            annotations=[
                dict(
                    text=baseline_title,
                    x=0.5,
                    y=1.0,
                    xref='paper',
                    yref='paper',
                    showarrow=False,
                    font=dict(size=14)
                ),
                dict(
                    text=optimized_title,
                    x=0.5,
                    y=0.45,
                    xref='paper',
                    yref='paper',
                    showarrow=False,
                    font=dict(size=14)
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
        
    def create_call_graph(self, 
                         call_hierarchy: Dict,
                         show: bool = True,
                         save_path: Optional[str] = None) -> Any:
        """
        Create a call graph visualization showing function call relationships.
        
        Args:
            call_hierarchy: Dictionary of function call relationships
                Format: {
                    'name': 'main_func',
                    'time': 0.5,
                    'calls': [
                        {'name': 'func1', 'time': 0.2, 'calls': [...]},
                        {'name': 'func2', 'time': 0.1, 'calls': [...]}
                    ]
                }
            show: Whether to display the plot
            save_path: Path to save the plot to (optional)
            
        Returns:
            The figure object
        """
        # Import NetworkX for graph visualization
        try:
            import networkx as nx
            has_nx = True
        except ImportError:
            has_nx = False
            
        if not has_nx:
            raise ImportError(
                "NetworkX is required for call graph visualization. "
                "Install it with: pip install networkx"
            )
            
        # Create a directed graph
        G = nx.DiGraph()
        
        # Recursively add nodes and edges
        def add_nodes_edges(node, parent=None):
            name = node['name']
            time = node['time']
            
            # Add node with time attribute
            G.add_node(name, time=time)
            
            # Add edge from parent if exists
            if parent:
                G.add_edge(parent, name)
                
            # Recurse on children
            for child in node.get('calls', []):
                add_nodes_edges(child, name)
                
        # Start with the root node
        add_nodes_edges(call_hierarchy)
        
        # Get node times for sizing
        times = nx.get_node_attributes(G, 'time')
        max_time = max(times.values()) if times else 1.0
        
        # Scale node sizes based on time
        node_sizes = {node: 300 + 1000 * (time / max_time) for node, time in times.items()}
        
        # Create the figure based on the backend
        if self.backend == 'matplotlib':
            return self._create_call_graph_mpl(G, node_sizes, show, save_path)
        else:  # plotly
            return self._create_call_graph_plotly(G, node_sizes, show, save_path)
            
    def _create_call_graph_mpl(self, 
                              G, 
                              node_sizes: Dict[str, float],
                              show: bool,
                              save_path: Optional[str]) -> Any:
        """Create a call graph using matplotlib and networkx."""
        import networkx as nx
        
        # Create figure
        fig, ax = plt.subplots(figsize=self.fig_size)
        
        # Use a hierarchical layout
        pos = nx.nx_agraph.graphviz_layout(G, prog='dot') if hasattr(nx, 'nx_agraph') else nx.spring_layout(G)
        
        # Draw the graph
        nx.draw_networkx_nodes(
            G, pos,
            node_size=[node_sizes[node] for node in G.nodes()],
            node_color='skyblue',
            alpha=0.8,
            ax=ax
        )
        
        nx.draw_networkx_edges(
            G, pos,
            width=1.0,
            arrowsize=15,
            arrowstyle='->',
            edge_color='gray',
            alpha=0.6,
            ax=ax
        )
        
        nx.draw_networkx_labels(
            G, pos,
            font_size=8,
            font_weight='bold',
            ax=ax
        )
        
        # Add node time labels
        times = nx.get_node_attributes(G, 'time')
        time_labels = {node: f"{time:.4f}s" for node, time in times.items()}
        
        # Position the time labels below the nodes
        time_pos = {node: (pos[node][0], pos[node][1] - 15) for node in pos}
        nx.draw_networkx_labels(
            G, time_pos,
            labels=time_labels,
            font_size=7,
            font_color='darkred',
            ax=ax
        )
        
        # Set the title
        ax.set_title('Function Call Graph')
        
        # Remove axis
        ax.axis('off')
        
        # Adjust layout
        plt.tight_layout()
        
        # Save the figure if requested
        if save_path:
            plt.savefig(save_path, bbox_inches='tight')
            
        # Show the figure if requested
        if show:
            plt.show()
            
        return fig
        
    def _create_call_graph_plotly(self, 
                                 G, 
                                 node_sizes: Dict[str, float],
                                 show: bool,
                                 save_path: Optional[str]) -> Any:
        """Create a call graph using plotly."""
        try:
            import networkx as nx
        except ImportError:
            raise ImportError("NetworkX is required for call graph visualization")
            
        # Set the template based on the theme
        template = 'plotly_dark' if self.theme == 'dark' else 'plotly_white'
        
        # Create a layout for the graph
        try:
            # Try to use a hierarchical layout if graphviz is available
            pos = nx.nx_agraph.graphviz_layout(G, prog='dot')
        except:
            # Fall back to spring layout
            pos = nx.spring_layout(G)
            
        # Create edge traces
        edge_trace = go.Scatter(
            x=[],
            y=[],
            line=dict(width=1, color='#888'),
            hoverinfo='none',
            mode='lines'
        )
        
        # Add edges
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_trace['x'] += (x0, x1, None)
            edge_trace['y'] += (y0, y1, None)
            
        # Create node trace
        node_trace = go.Scatter(
            x=[],
            y=[],
            text=[],
            mode='markers+text',
            hoverinfo='text',
            marker=dict(
                showscale=True,
                colorscale='YlGnBu',
                size=[],
                color=[],
                colorbar=dict(
                    thickness=15,
                    title='Execution Time (s)',
                    xanchor='left',
                    titleside='right'
                ),
                line=dict(width=2)
            ),
            textposition='bottom center'
        )
        
        # Add nodes
        for node in G.nodes():
            x, y = pos[node]
            node_trace['x'] += (x,)
            node_trace['y'] += (y,)
            
        # Add node attributes
        times = nx.get_node_attributes(G, 'time')
        
        for node in G.nodes():
            time = times.get(node, 0)
            node_trace['marker']['size'] += (node_sizes[node],)
            node_trace['marker']['color'] += (time,)
            node_trace['text'] += (f"{node}<br>{time:.4f}s",)
            
        # Create the figure
        fig = go.Figure(
            data=[edge_trace, node_trace],
            layout=go.Layout(
                title='Function Call Graph',
                showlegend=False,
                hovermode='closest',
                margin=dict(b=20, l=5, r=5, t=40),
                annotations=[
                    dict(
                        text="Node size indicates execution time",
                        showarrow=False,
                        xref="paper", yref="paper",
                        x=0.01, y=-0.01
                    )
                ],
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                template=template,
                height=self.fig_size[1] * 100,
                width=self.fig_size[0] * 100,
            )
        )
        
        # Save the figure if requested
        if save_path:
            fig.write_image(save_path)
            
        # Show the figure if requested
        if show:
            fig.show()
            
        return fig
        
    def save_interactive_html(self,
                             call_data: List[Dict],
                             call_hierarchy: Optional[Dict] = None,
                             filename: str = "timeline_profile.html") -> None:
        """
        Create an interactive HTML report with timeline visualizations.
        
        Args:
            call_data: List of dictionaries containing function call information
            call_hierarchy: Dictionary of function call relationships (optional)
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
        
        # Create the timeline figure
        fig1 = self.create_function_timeline(call_data, show=False)
        
        if call_hierarchy:
            try:
                # Try to create the call graph
                fig2 = self.create_call_graph(call_hierarchy, show=False)
                
                # Combine the figures
                from plotly.subplots import make_subplots
                
                # Create a grid of subplots
                combined_fig = make_subplots(
                    rows=2, 
                    cols=1,
                    subplot_titles=(
                        'Function Call Timeline',
                        'Function Call Graph'
                    ),
                    vertical_spacing=0.1,
                    specs=[
                        [{"type": "scatter"}],
                        [{"type": "scatter"}]
                    ]
                )
                
                # Add timeline traces
                for trace in fig1.data:
                    combined_fig.add_trace(trace, row=1, col=1)
                    
                # Add call graph traces
                for trace in fig2.data:
                    combined_fig.add_trace(trace, row=2, col=1)
                    
                # Update layout
                combined_fig.update_layout(
                    title='Execution Timeline Analysis',
                    height=1200,
                    width=1000,
                    template='plotly_dark' if self.theme == 'dark' else 'plotly_white',
                    showlegend=False
                )
                
                # Write the combined figure to HTML
                combined_fig.write_html(filename)
            except Exception as e:
                # Fall back to just the timeline if call graph fails
                print(f"Warning: Failed to create call graph: {str(e)}")
                fig1.write_html(filename)
        else:
            # Just write the timeline to HTML
            fig1.write_html(filename)
            
        # Restore the original backend
        self.backend = old_backend
