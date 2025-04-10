"""
I/O utilities for PyPerfOptimizer.

This module provides utilities for saving and loading profiling results.
"""

import os
import json
import pickle
from datetime import datetime
from typing import Dict, List, Optional, Any, Union, BinaryIO, TextIO

def save_profile(
    profile_data: Dict,
    filename: str,
    format: str = 'json'
) -> str:
    """
    Save profiling data to a file.
    
    Args:
        profile_data: Profiling data to save
        filename: Path to save the data to
        format: File format ('json' or 'pickle')
        
    Returns:
        Path to the saved file
    """
    # Ensure the directory exists
    os.makedirs(os.path.dirname(filename) if os.path.dirname(filename) else '.', exist_ok=True)
    
    # Save the data in the specified format
    if format.lower() == 'json':
        with open(filename, 'w') as f:
            json.dump(profile_data, f, indent=2, default=str)
    elif format.lower() == 'pickle':
        with open(filename, 'wb') as f:
            pickle.dump(profile_data, f)
    else:
        raise ValueError(f"Unsupported format: {format}. Use 'json' or 'pickle'.")
        
    return filename

def load_profile(
    filename: str,
    format: Optional[str] = None
) -> Dict:
    """
    Load profiling data from a file.
    
    Args:
        filename: Path to load the data from
        format: File format (if None, determined from file extension)
        
    Returns:
        Loaded profiling data
    """
    # Determine the format from the file extension if not specified
    if format is None:
        _, ext = os.path.splitext(filename)
        if ext.lower() in ['.json']:
            format = 'json'
        elif ext.lower() in ['.pkl', '.pickle']:
            format = 'pickle'
        else:
            raise ValueError(f"Could not determine format from file extension: {ext}. Specify the format explicitly.")
    
    # Load the data from the file
    if format.lower() == 'json':
        with open(filename, 'r') as f:
            return json.load(f)
    elif format.lower() == 'pickle':
        with open(filename, 'rb') as f:
            return pickle.load(f)
    else:
        raise ValueError(f"Unsupported format: {format}. Use 'json' or 'pickle'.")

def export_results(
    results: Dict,
    directory: str,
    prefix: Optional[str] = None,
    formats: List[str] = ['json'],
    include_timestamp: bool = True
) -> Dict[str, str]:
    """
    Export profiling results to files in various formats.
    
    Args:
        results: Profiling results to export
        directory: Directory to save the files to
        prefix: Prefix for the filenames
        formats: List of formats to export to
        include_timestamp: Whether to include a timestamp in the filenames
        
    Returns:
        Dictionary mapping formats to filenames
    """
    # Ensure the directory exists
    os.makedirs(directory, exist_ok=True)
    
    # Generate a prefix if not provided
    if prefix is None:
        prefix = "profile"
        
    # Add a timestamp if requested
    if include_timestamp:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        prefix = f"{prefix}_{timestamp}"
        
    # Export the results in each format
    filenames = {}
    
    for format in formats:
        if format.lower() == 'json':
            filename = os.path.join(directory, f"{prefix}.json")
            save_profile(results, filename, 'json')
            filenames['json'] = filename
        elif format.lower() == 'pickle':
            filename = os.path.join(directory, f"{prefix}.pkl")
            save_profile(results, filename, 'pickle')
            filenames['pickle'] = filename
        elif format.lower() == 'html':
            filename = os.path.join(directory, f"{prefix}.html")
            _export_html(results, filename)
            filenames['html'] = filename
        elif format.lower() == 'csv':
            filename = os.path.join(directory, f"{prefix}.csv")
            _export_csv(results, filename)
            filenames['csv'] = filename
        else:
            raise ValueError(f"Unsupported format: {format}")
            
    return filenames

def import_results(
    filename: str
) -> Dict:
    """
    Import profiling results from a file.
    
    Args:
        filename: Path to the file to import
        
    Returns:
        Imported profiling results
    """
    # Determine the format from the file extension
    _, ext = os.path.splitext(filename)
    
    if ext.lower() == '.json':
        format = 'json'
    elif ext.lower() in ['.pkl', '.pickle']:
        format = 'pickle'
    elif ext.lower() == '.csv':
        return _import_csv(filename)
    else:
        raise ValueError(f"Unsupported file format: {ext}")
        
    # Load the results
    return load_profile(filename, format)

def _export_html(results: Dict, filename: str) -> None:
    """
    Export profiling results to HTML format.
    
    Args:
        results: Profiling results to export
        filename: Path to save the HTML file to
    """
    # Create a simple HTML representation of the results
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>PyPerfOptimizer Results</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            h1 { color: #333; }
            h2 { color: #555; }
            table { border-collapse: collapse; width: 100%; margin-bottom: 20px; }
            th, td { padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }
            th { background-color: #f2f2f2; }
            tr:hover { background-color: #f5f5f5; }
            .section { margin-bottom: 30px; }
        </style>
    </head>
    <body>
        <h1>PyPerfOptimizer Profiling Results</h1>
    """
    
    # Add timestamp
    if 'timestamp' in results:
        html += f"<p>Generated: {results['timestamp']}</p>"
    else:
        html += f"<p>Generated: {datetime.now().isoformat()}</p>"
        
    # Add profiler results
    profilers = results.get('profilers', {})
    
    for profiler_name, profiler_data in profilers.items():
        html += f"<div class='section'><h2>{profiler_name.upper()} Profiling Results</h2>"
        
        if profiler_name == 'cpu' and 'functions' in profiler_data:
            html += """
            <table>
                <tr>
                    <th>Function</th>
                    <th>Calls</th>
                    <th>Total Time (s)</th>
                    <th>Time/Call (s)</th>
                    <th>Cumulative Time (s)</th>
                </tr>
            """
            
            for func in profiler_data['functions'][:20]:  # Top 20 functions
                html += f"""
                <tr>
                    <td>{func.get('function', '')}</td>
                    <td>{func.get('ncalls', '')}</td>
                    <td>{func.get('tottime', 0)}</td>
                    <td>{func.get('percall', 0)}</td>
                    <td>{func.get('cumtime', 0)}</td>
                </tr>
                """
                
            html += "</table>"
            
        elif profiler_name == 'memory':
            html += "<p>"
            if 'peak_memory' in profiler_data:
                html += f"Peak Memory: {profiler_data['peak_memory']:.2f} MB<br>"
            if 'baseline_memory' in profiler_data:
                html += f"Baseline Memory: {profiler_data['baseline_memory']:.2f} MB<br>"
            if 'memory_increase' in profiler_data:
                html += f"Memory Increase: {profiler_data['memory_increase']:.2f} MB<br>"
            html += "</p>"
            
        elif profiler_name == 'line' and 'functions' in profiler_data:
            for func in profiler_data['functions']:
                html += f"<h3>Function: {func.get('function_name', '')}</h3>"
                html += f"<p>Total Time: {func.get('total_time', 0):.4f}s</p>"
                
                html += """
                <table>
                    <tr>
                        <th>Line</th>
                        <th>Hits</th>
                        <th>Time (s)</th>
                        <th>Time/Hit (s)</th>
                        <th>% Time</th>
                        <th>Code</th>
                    </tr>
                """
                
                for line_num, line_info in func.get('lines', {}).items():
                    if isinstance(line_num, str) and line_num == 'error':
                        continue
                        
                    if isinstance(line_num, int):
                        html += f"""
                        <tr>
                            <td>{line_num}</td>
                            <td>{line_info.get('hits', 0)}</td>
                            <td>{line_info.get('time', 0):.6f}</td>
                            <td>{line_info.get('time_per_hit', 0):.6f}</td>
                            <td>{line_info.get('percentage', 0):.1f}%</td>
                            <td>{line_info.get('line_content', '')}</td>
                        </tr>
                        """
                        
                html += "</table>"
                
        html += "</div>"
        
    # Add recommendations if available
    if 'recommendations' in results:
        html += "<div class='section'><h2>Recommendations</h2>"
        
        for category, items in results['recommendations'].items():
            if items:
                html += f"<h3>{category.upper()}</h3><ul>"
                for item in items:
                    html += f"<li>{item}</li>"
                html += "</ul>"
                
        html += "</div>"
        
    # Close the HTML
    html += """
    </body>
    </html>
    """
    
    # Write the HTML to the file
    with open(filename, 'w') as f:
        f.write(html)

def _export_csv(results: Dict, filename: str) -> None:
    """
    Export profiling results to CSV format.
    
    Args:
        results: Profiling results to export
        filename: Path to save the CSV file to
    """
    # Focus on function-level data which is most suitable for CSV
    csv_data = "Category,Function,Calls,TotalTime,TimePerCall,CumulativeTime\n"
    
    profilers = results.get('profilers', {})
    
    # Export CPU data
    if 'cpu' in profilers and 'functions' in profilers['cpu']:
        for func in profilers['cpu']['functions']:
            line = (
                f"CPU,"
                f"\"{func.get('function', '')}\","
                f"{func.get('ncalls', '')},"
                f"{func.get('tottime', 0)},"
                f"{func.get('percall', 0)},"
                f"{func.get('cumtime', 0)}\n"
            )
            csv_data += line
            
    # Export line profiling data
    if 'line' in profilers and 'functions' in profilers['line']:
        for func in profilers['line']['functions']:
            func_name = func.get('function_name', '')
            filename = func.get('filename', '')
            
            for line_num, line_info in func.get('lines', {}).items():
                if isinstance(line_num, str) and line_num == 'error':
                    continue
                    
                if isinstance(line_num, int):
                    line = (
                        f"LINE,"
                        f"\"{func_name}:{filename}:{line_num}\","
                        f"{line_info.get('hits', 0)},"
                        f"{line_info.get('time', 0)},"
                        f"{line_info.get('time_per_hit', 0)},"
                        f"{line_info.get('percentage', 0)}%\n"
                    )
                    csv_data += line
                    
    # Write the CSV data to the file
    with open(filename, 'w') as f:
        f.write(csv_data)

def _import_csv(filename: str) -> Dict:
    """
    Import profiling results from CSV format.
    
    Args:
        filename: Path to the CSV file to import
        
    Returns:
        Imported profiling results
    """
    results = {
        'profilers': {
            'cpu': {'functions': []},
            'line': {'functions': []}
        }
    }
    
    try:
        with open(filename, 'r') as f:
            # Skip header
            next(f)
            
            for line in f:
                parts = line.strip().split(',')
                
                if len(parts) < 6:
                    continue
                    
                category = parts[0]
                func_name = parts[1].strip('"')
                calls = parts[2]
                total_time = float(parts[3])
                time_per_call = float(parts[4])
                cumulative_time = float(parts[5].rstrip('%'))
                
                if category == 'CPU':
                    results['profilers']['cpu']['functions'].append({
                        'function': func_name,
                        'ncalls': calls,
                        'tottime': total_time,
                        'percall': time_per_call,
                        'cumtime': cumulative_time
                    })
                elif category == 'LINE':
                    # Extract function name, filename and line number
                    func_parts = func_name.split(':')
                    if len(func_parts) >= 3:
                        func_name = func_parts[0]
                        filename = func_parts[1]
                        line_num = int(func_parts[2])
                        
                        # Find or create function entry
                        func_entry = None
                        for func in results['profilers']['line']['functions']:
                            if func.get('function_name') == func_name and func.get('filename') == filename:
                                func_entry = func
                                break
                                
                        if func_entry is None:
                            func_entry = {
                                'function_name': func_name,
                                'filename': filename,
                                'lines': {}
                            }
                            results['profilers']['line']['functions'].append(func_entry)
                            
                        # Add line info
                        func_entry['lines'][line_num] = {
                            'hits': int(calls),
                            'time': total_time,
                            'time_per_hit': time_per_call,
                            'percentage': cumulative_time
                        }
    except Exception as e:
        raise ValueError(f"Error importing CSV file: {str(e)}")
        
    return results
