"""
Dashboard visualization functionality for PyPerfOptimizer.

This module provides a web-based dashboard for interactive exploration
of profiling results from CPU, memory, and line profilers.
"""

import os
import json
import tempfile
import webbrowser
from typing import Dict, List, Optional, Any, Union, Tuple
import datetime

# Try to import Flask for the web dashboard
try:
    from flask import Flask, render_template_string, request, jsonify
    _HAS_FLASK = True
except ImportError:
    _HAS_FLASK = False

class Dashboard:
    """
    A class for creating an interactive web dashboard to visualize profiling results.
    
    This class provides methods to display profiling results from CPU, memory, and
    line profilers in an interactive web-based dashboard.
    """
    
    def __init__(self, 
                host: str = '0.0.0.0',
                port: int = 5000,
                theme: str = 'dark'):
        """
        Initialize the dashboard.
        
        Args:
            host: Host address to run the dashboard on
            port: Port to run the dashboard on
            theme: Color theme ('light' or 'dark')
        """
        if not _HAS_FLASK:
            raise ImportError(
                "Flask is required for the interactive dashboard. "
                "Install it with: pip install flask"
            )
            
        self.host = host
        self.port = port
        self.theme = theme
        self.data = {
            'cpu': None,
            'memory': None,
            'line': None,
            'timeline': None,
            'recommendations': None
        }
        self.app = Flask(__name__)
        self._setup_routes()
        
    def _setup_routes(self) -> None:
        """Set up the Flask routes for the dashboard."""
        app = self.app
        
        @app.route('/')
        def index():
            return render_template_string(self._get_dashboard_html())
            
        @app.route('/api/data')
        def get_data():
            return jsonify(self.data)
            
        @app.route('/api/cpu')
        def get_cpu_data():
            return jsonify(self.data.get('cpu', {}))
            
        @app.route('/api/memory')
        def get_memory_data():
            return jsonify(self.data.get('memory', {}))
            
        @app.route('/api/line')
        def get_line_data():
            return jsonify(self.data.get('line', {}))
            
        @app.route('/api/timeline')
        def get_timeline_data():
            return jsonify(self.data.get('timeline', {}))
            
        @app.route('/api/recommendations')
        def get_recommendations():
            return jsonify(self.data.get('recommendations', {}))
            
    def _get_dashboard_html(self) -> str:
        """
        Get the HTML template for the dashboard.
        
        Returns:
            HTML template string for the dashboard
        """
        # Determine CSS theme
        bootstrap_css = "https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css"
        charts_theme = "dark" if self.theme == "dark" else "light"
        
        # Create the HTML template
        return '''
<!DOCTYPE html>
<html lang="en" data-bs-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PyPerfOptimizer Dashboard</title>
    <!-- Bootstrap CSS -->
    <link href="''' + bootstrap_css + '''" rel="stylesheet">
    <!-- Plotly JS -->
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <!-- jQuery -->
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <style>
        .card {
            margin-bottom: 20px;
        }
        .recommendations {
            padding: 10px;
            border-radius: 5px;
        }
        .recommendation-item {
            margin-bottom: 5px;
            padding: 5px;
            border-radius: 3px;
        }
    </style>
</head>
<body>
    <div class="container mt-4">
        <h1 class="mb-4">PyPerfOptimizer Dashboard</h1>
        
        <div class="row mb-4">
            <div class="col-md-12">
                <div class="card">
                    <div class="card-header">
                        <h2 class="card-title">Performance Summary</h2>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-4">
                                <div class="card bg-primary text-white">
                                    <div class="card-body">
                                        <h5 class="card-title">CPU Profile</h5>
                                        <p id="cpu-summary">Loading...</p>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="card bg-success text-white">
                                    <div class="card-body">
                                        <h5 class="card-title">Memory Profile</h5>
                                        <p id="memory-summary">Loading...</p>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="card bg-info text-white">
                                    <div class="card-body">
                                        <h5 class="card-title">Line Profile</h5>
                                        <p id="line-summary">Loading...</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="row mb-4">
            <div class="col-md-12">
                <div class="card">
                    <div class="card-header">
                        <h2 class="card-title">Recommendations</h2>
                    </div>
                    <div class="card-body">
                        <div id="recommendations" class="recommendations">Loading...</div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="row mb-4">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h2 class="card-title">CPU Profile</h2>
                    </div>
                    <div class="card-body">
                        <div id="cpu-chart" style="width:100%;height:400px;">Loading...</div>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h2 class="card-title">Memory Profile</h2>
                    </div>
                    <div class="card-body">
                        <div id="memory-chart" style="width:100%;height:400px;">Loading...</div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="row mb-4">
            <div class="col-md-12">
                <div class="card">
                    <div class="card-header">
                        <h2 class="card-title">Timeline</h2>
                    </div>
                    <div class="card-body">
                        <div id="timeline-chart" style="width:100%;height:400px;">Loading...</div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="row mb-4">
            <div class="col-md-12">
                <div class="card">
                    <div class="card-header">
                        <h2 class="card-title">Line Hotspots</h2>
                    </div>
                    <div class="card-body">
                        <div id="line-hotspots" style="width:100%;height:400px;">Loading...</div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // Function to fetch and display data
        function loadData() {
            $.getJSON('/api/data', function(data) {
                // Update CPU summary and chart
                if (data.cpu) {
                    updateCPUSummary(data.cpu);
                    createCPUChart(data.cpu);
                }
                
                // Update Memory summary and chart
                if (data.memory) {
                    updateMemorySummary(data.memory);
                    createMemoryChart(data.memory);
                }
                
                // Update Line summary and chart
                if (data.line) {
                    updateLineSummary(data.line);
                    createLineHotspotsChart(data.line);
                }
                
                // Update Timeline chart
                if (data.timeline) {
                    createTimelineChart(data.timeline);
                }
                
                // Update Recommendations
                if (data.recommendations) {
                    updateRecommendations(data.recommendations);
                }
            });
        }
        
        // CPU Summary update
        function updateCPUSummary(cpuData) {
            let summary = '';
            if (cpuData.total_time) {
                summary += `Total time: ${cpuData.total_time.toFixed(4)}s<br>`;
            }
            
            if (cpuData.functions && cpuData.functions.length > 0) {
                const topFunc = cpuData.functions[0];
                summary += `Top function: ${topFunc.function}<br>`;
                summary += `Time: ${parseFloat(topFunc.cumtime).toFixed(4)}s`;
            }
            
            $('#cpu-summary').html(summary);
        }
        
        // Memory Summary update
        function updateMemorySummary(memData) {
            let summary = '';
            if (memData.peak_memory) {
                summary += `Peak memory: ${memData.peak_memory.toFixed(2)} MB<br>`;
            }
            
            if (memData.memory_increase) {
                summary += `Memory increase: ${memData.memory_increase.toFixed(2)} MB<br>`;
            }
            
            if (memData.final_memory) {
                summary += `Final memory: ${memData.final_memory.toFixed(2)} MB`;
            }
            
            $('#memory-summary').html(summary);
        }
        
        // Line Summary update
        function updateLineSummary(lineData) {
            let summary = '';
            if (lineData.functions && lineData.functions.length > 0) {
                const func = lineData.functions[0];
                summary += `Function: ${func.function_name}<br>`;
                summary += `Total time: ${func.total_time.toFixed(4)}s<br>`;
                
                // Find hotspot
                let hotspotLine = null;
                let maxTime = 0;
                
                for (const lineNum in func.lines) {
                    if (lineNum === 'error') continue;
                    
                    const line = func.lines[lineNum];
                    if (line.time > maxTime) {
                        maxTime = line.time;
                        hotspotLine = {num: lineNum, ...line};
                    }
                }
                
                if (hotspotLine) {
                    summary += `Hotspot: Line ${hotspotLine.num} (${(hotspotLine.percentage).toFixed(1)}%)`;
                }
            } else {
                summary = "No line profiling data available";
            }
            
            $('#line-summary').html(summary);
        }
        
        // Recommendations update
        function updateRecommendations(recommendations) {
            let html = '';
            
            for (const category in recommendations) {
                const items = recommendations[category];
                if (items && items.length > 0) {
                    html += `<h5>${category.toUpperCase()}</h5>`;
                    html += '<ul>';
                    
                    items.forEach(item => {
                        html += `<li class="recommendation-item">${item}</li>`;
                    });
                    
                    html += '</ul>';
                }
            }
            
            if (html === '') {
                html = 'No recommendations available';
            }
            
            $('#recommendations').html(html);
        }
        
        // Create CPU chart
        function createCPUChart(cpuData) {
            if (!cpuData.functions || cpuData.functions.length === 0) {
                $('#cpu-chart').html('No CPU data available');
                return;
            }
            
            const topFuncs = cpuData.functions.slice(0, 10);
            const funcNames = topFuncs.map(f => f.function.split('/')[-1]);
            const cumTimes = topFuncs.map(f => parseFloat(f.cumtime));
            
            const data = [{
                x: cumTimes.reverse(),
                y: funcNames.reverse(),
                type: 'bar',
                orientation: 'h',
                marker: {
                    color: 'rgba(55, 128, 191, 0.8)'
                }
            }];
            
            const layout = {
                title: 'Top Functions by Cumulative Time',
                xaxis: {
                    title: 'Time (seconds)'
                },
                yaxis: {
                    title: 'Function'
                },
                template: '''' + charts_theme + '''',
                margin: { t: 40, r: 20, l: 150, b: 40 }
            };
            
            Plotly.newPlot('cpu-chart', data, layout);
        }
        
        // Create Memory chart
        function createMemoryChart(memData) {
            if (!memData.timestamps || !memData.memory_mb) {
                $('#memory-chart').html('No memory data available');
                return;
            }
            
            const data = [{
                x: memData.timestamps,
                y: memData.memory_mb,
                type: 'scatter',
                mode: 'lines',
                name: 'Memory Usage',
                line: {
                    color: 'rgba(50, 171, 96, 1)',
                    width: 2
                }
            }];
            
            if (memData.baseline_memory) {
                data.push({
                    x: [memData.timestamps[0], memData.timestamps[memData.timestamps.length - 1]],
                    y: [memData.baseline_memory, memData.baseline_memory],
                    type: 'scatter',
                    mode: 'lines',
                    name: 'Baseline',
                    line: {
                        color: 'rgba(219, 64, 82, 1)',
                        width: 2,
                        dash: 'dash'
                    }
                });
            }
            
            const layout = {
                title: 'Memory Usage Over Time',
                xaxis: {
                    title: 'Time (seconds)'
                },
                yaxis: {
                    title: 'Memory (MB)'
                },
                template: '''' + charts_theme + '''',
                margin: { t: 40, r: 20, l: 70, b: 40 }
            };
            
            Plotly.newPlot('memory-chart', data, layout);
        }
        
        // Create Timeline chart
        function createTimelineChart(timelineData) {
            if (!timelineData || !timelineData.length) {
                $('#timeline-chart').html('No timeline data available');
                return;
            }
            
            // Create a dictionary of function names to y-positions
            const funcNames = {};
            let position = 0;
            
            timelineData.forEach(call => {
                if (!(call.name in funcNames)) {
                    funcNames[call.name] = position++;
                }
            });
            
            // Min start time for normalization
            const minStart = Math.min(...timelineData.map(call => call.start));
            
            // Create data for the chart
            const data = [];
            
            timelineData.forEach(call => {
                const normalizedStart = call.start - minStart;
                const normalizedEnd = call.end - minStart;
                const duration = normalizedEnd - normalizedStart;
                
                // Skip very short calls for clarity
                if (duration < 0.001) return;
                
                data.push({
                    x: [duration],
                    y: [funcNames[call.name]],
                    name: call.name,
                    orientation: 'h',
                    marker: {
                        color: call.depth,
                        colorscale: 'Viridis',
                        cmin: 0,
                        cmax: Math.max(...timelineData.map(c => c.depth))
                    },
                    text: `${call.name} (${duration.toFixed(6)}s)`,
                    hoverinfo: 'text',
                    type: 'bar',
                    base: normalizedStart,
                    showlegend: false
                });
            });
            
            const layout = {
                title: 'Function Call Timeline',
                xaxis: {
                    title: 'Time (seconds)'
                },
                yaxis: {
                    title: 'Function',
                    tickmode: 'array',
                    tickvals: Object.values(funcNames),
                    ticktext: Object.keys(funcNames)
                },
                barmode: 'stack',
                template: '''' + charts_theme + '''',
                margin: { t: 40, r: 20, l: 150, b: 40 }
            };
            
            Plotly.newPlot('timeline-chart', data, layout);
        }
        
        // Create Line Hotspots chart
        function createLineHotspotsChart(lineData) {
            if (!lineData.functions || lineData.functions.length === 0) {
                $('#line-hotspots').html('No line profiling data available');
                return;
            }
            
            // Collect hotspot data
            const hotspots = [];
            
            lineData.functions.forEach(func => {
                for (const lineNum in func.lines) {
                    if (lineNum === 'error') continue;
                    
                    const line = func.lines[lineNum];
                    if (line.time > 0) {
                        hotspots.push({
                            function: func.function_name,
                            line: lineNum,
                            content: line.line_content,
                            time: line.time,
                            percentage: line.percentage
                        });
                    }
                }
            });
            
            // Sort by time and take top 10
            hotspots.sort((a, b) => b.time - a.time);
            const topHotspots = hotspots.slice(0, 10);
            
            // Format data for the chart
            const labels = topHotspots.map(h => {
                const content = h.content.length > 30 ? h.content.substring(0, 30) + '...' : h.content;
                return `Line ${h.line}: ${content}`;
            }).reverse();
            
            const times = topHotspots.map(h => h.time).reverse();
            const percentages = topHotspots.map(h => h.percentage).reverse();
            
            const data = [{
                x: times,
                y: labels,
                text: percentages.map(p => `${p.toFixed(1)}%`),
                textposition: 'auto',
                type: 'bar',
                orientation: 'h',
                marker: {
                    color: 'rgba(158,202,225,0.8)',
                    line: {
                        color: 'rgba(8,48,107,1.0)',
                        width: 1
                    }
                }
            }];
            
            const layout = {
                title: 'Line Execution Hotspots',
                xaxis: {
                    title: 'Time (seconds)'
                },
                yaxis: {
                    title: 'Code Line'
                },
                template: '''' + charts_theme + '''',
                margin: { t: 40, r: 20, l: 250, b: 40 }
            };
            
            Plotly.newPlot('line-hotspots', data, layout);
        }
        
        // Initial data load
        $(document).ready(function() {
            loadData();
        });
    </script>
</body>
</html>
'''
        
    def set_cpu_data(self, cpu_data: Dict) -> None:
        """
        Set CPU profiling data for the dashboard.
        
        Args:
            cpu_data: CPU profiling data from CPUProfiler.get_stats()
        """
        self.data['cpu'] = cpu_data
        
    def set_memory_data(self, memory_data: Dict) -> None:
        """
        Set memory profiling data for the dashboard.
        
        Args:
            memory_data: Memory profiling data from MemoryProfiler.get_stats()
        """
        self.data['memory'] = memory_data
        
    def set_line_data(self, line_data: Dict) -> None:
        """
        Set line profiling data for the dashboard.
        
        Args:
            line_data: Line profiling data from LineProfiler.get_stats()
        """
        self.data['line'] = line_data
        
    def set_timeline_data(self, timeline_data: List[Dict]) -> None:
        """
        Set timeline data for the dashboard.
        
        Args:
            timeline_data: Timeline data for function calls
        """
        self.data['timeline'] = timeline_data
        
    def set_recommendations(self, recommendations: Dict[str, List[str]]) -> None:
        """
        Set optimization recommendations for the dashboard.
        
        Args:
            recommendations: Dictionary of optimization recommendations
        """
        self.data['recommendations'] = recommendations
        
    def set_profile_manager_data(self, profile_manager) -> None:
        """
        Set all data from a ProfileManager instance.
        
        Args:
            profile_manager: ProfileManager instance with profiling results
        """
        stats = profile_manager.get_stats()
        profilers = stats.get('profilers', {})
        
        if 'cpu' in profilers:
            self.set_cpu_data(profilers['cpu'])
            
        if 'memory' in profilers:
            self.set_memory_data(profilers['memory'])
            
        if 'line' in profilers:
            self.set_line_data(profilers['line'])
            
        # Get recommendations
        self.set_recommendations(profile_manager.get_recommendations())
        
    def launch(self, debug: bool = False, open_browser: bool = True) -> None:
        """
        Launch the dashboard web server.
        
        Args:
            debug: Whether to run in debug mode
            open_browser: Whether to automatically open a browser
        """
        if open_browser:
            # Open browser after a short delay to ensure server is up
            import threading
            def open_browser_delayed():
                import time
                time.sleep(1.5)
                webbrowser.open(f'http://localhost:{self.port}')
                
            threading.Thread(target=open_browser_delayed).start()
            
        # Run the Flask app
        self.app.run(host=self.host, port=self.port, debug=debug)
        
    def save_html(self, filename: str) -> str:
        """
        Save the dashboard as a standalone HTML file.
        
        Args:
            filename: Path to save the HTML file to
            
        Returns:
            Path to the saved HTML file
        """
        # Create a simple Flask app to render the template
        html = self._get_dashboard_html()
        
        # Add the data directly to the HTML to make it standalone
        data_json = json.dumps(self.data)
        standalone_js = f'''
        <script>
            // Replace the loadData function to use embedded data
            function loadData() {{
                const data = {data_json};
                
                // Update CPU summary and chart
                if (data.cpu) {{
                    updateCPUSummary(data.cpu);
                    createCPUChart(data.cpu);
                }}
                
                // Update Memory summary and chart
                if (data.memory) {{
                    updateMemorySummary(data.memory);
                    createMemoryChart(data.memory);
                }}
                
                // Update Line summary and chart
                if (data.line) {{
                    updateLineSummary(data.line);
                    createLineHotspotsChart(data.line);
                }}
                
                // Update Timeline chart
                if (data.timeline) {{
                    createTimelineChart(data.timeline);
                }}
                
                // Update Recommendations
                if (data.recommendations) {{
                    updateRecommendations(data.recommendations);
                }}
            }}
        </script>
        '''
        
        # Insert the standalone JS before the closing body tag
        html = html.replace('</body>', f'{standalone_js}\n</body>')
        
        # Ensure the directory exists
        os.makedirs(os.path.dirname(filename) if os.path.dirname(filename) else '.', exist_ok=True)
        
        # Write the HTML to the file
        with open(filename, 'w') as f:
            f.write(html)
            
        return filename
