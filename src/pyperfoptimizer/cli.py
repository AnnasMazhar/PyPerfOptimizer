#!/usr/bin/env python3
"""
Command-line interface for PyPerfOptimizer.
"""

import os
import sys
import argparse
import importlib.util
import inspect
from typing import List, Optional, Dict, Any, Union, Callable

from pyperfoptimizer.profiler import ProfileManager
from pyperfoptimizer.visualizer import Dashboard
from pyperfoptimizer.optimizer import Recommendations, CodeAnalyzer
from pyperfoptimizer.utils.io import export_results


def import_module_from_file(file_path: str) -> Any:
    """Import a module from a file path."""
    module_name = os.path.basename(file_path).replace('.py', '')
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module from {file_path}")
    
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def find_functions_in_module(module: Any) -> Dict[str, Callable]:
    """Find all functions in a module."""
    return {
        name: obj for name, obj in inspect.getmembers(module, inspect.isfunction)
        if obj.__module__ == module.__name__
    }


def profile_file(file_path: str, function_name: Optional[str] = None,
                enable_cpu: bool = True, enable_memory: bool = True,
                enable_line: bool = True, output_dir: Optional[str] = None) -> Dict[str, Any]:
    """Profile a Python file."""
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    # Import the module
    try:
        module = import_module_from_file(file_path)
    except Exception as e:
        raise ImportError(f"Error importing module from {file_path}: {e}")
    
    # Find functions to profile
    functions = find_functions_in_module(module)
    
    if not functions:
        raise ValueError(f"No functions found in {file_path}")
    
    # If function_name is specified, profile only that function
    if function_name:
        if function_name not in functions:
            raise ValueError(f"Function '{function_name}' not found in {file_path}")
        
        func = functions[function_name]
        profile_manager = ProfileManager(
            enable_cpu=enable_cpu,
            enable_memory=enable_memory,
            enable_line=enable_line
        )
        
        # Profile the function
        profile_manager.profile_func(func)
        
        # Get the results
        results = {
            'file_path': file_path,
            'function_name': function_name,
            'profile_data': profile_manager.get_stats()
        }
        
        # Generate recommendations
        if output_dir:
            # Create the output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            # Generate recommendations
            recommender = Recommendations()
            recommendations = recommender.generate_from_profile_manager(profile_manager)
            
            # Code analysis
            analyzer = CodeAnalyzer()
            code_analysis = analyzer.analyze_function(func)
            code_recs = recommender.generate_from_code_analysis(code_analysis)
            recommendations['code_structure'] = code_recs
            
            results['recommendations'] = recommendations
            
            # Export results
            export_results(
                results,
                output_dir,
                prefix=f"{os.path.basename(file_path)}_{function_name}",
                formats=['json', 'html']
            )
            
            # Create and save dashboard
            dashboard = Dashboard()
            dashboard.set_profile_manager_data(profile_manager)
            dashboard.set_recommendations(recommendations)
            dashboard.save_html(os.path.join(output_dir, f"{function_name}_dashboard.html"))
        
        return results
    
    # Otherwise, profile all functions
    results = {}
    for name, func in functions.items():
        print(f"Profiling function: {name}")
        
        profile_manager = ProfileManager(
            enable_cpu=enable_cpu,
            enable_memory=enable_memory,
            enable_line=enable_line
        )
        
        # Profile the function
        try:
            profile_manager.profile_func(func)
            
            # Get the results
            function_results = {
                'file_path': file_path,
                'function_name': name,
                'profile_data': profile_manager.get_stats()
            }
            
            # Generate recommendations
            if output_dir:
                # Create the output directory if it doesn't exist
                os.makedirs(output_dir, exist_ok=True)
                
                # Generate recommendations
                recommender = Recommendations()
                recommendations = recommender.generate_from_profile_manager(profile_manager)
                
                # Code analysis
                analyzer = CodeAnalyzer()
                code_analysis = analyzer.analyze_function(func)
                code_recs = recommender.generate_from_code_analysis(code_analysis)
                recommendations['code_structure'] = code_recs
                
                function_results['recommendations'] = recommendations
                
                # Export results
                export_results(
                    function_results,
                    output_dir,
                    prefix=f"{os.path.basename(file_path)}_{name}",
                    formats=['json', 'html']
                )
            
            results[name] = function_results
            
        except Exception as e:
            print(f"Error profiling function {name}: {e}")
    
    if output_dir and results:
        # Create and save a combined dashboard
        dashboard = Dashboard()
        dashboard.set_title(f"Profile Results: {os.path.basename(file_path)}")
        
        # Add data for each function
        for name, result in results.items():
            if 'profile_data' in result:
                dashboard.add_profile_data(name, result['profile_data'])
        
        dashboard.save_html(os.path.join(output_dir, f"{os.path.basename(file_path)}_dashboard.html"))
    
    return results


def launch_dashboard(results_dir: str, port: int = 5000) -> None:
    """Launch the dashboard with results from a directory."""
    if not os.path.isdir(results_dir):
        raise FileNotFoundError(f"Directory not found: {results_dir}")
    
    dashboard = Dashboard(port=port)
    
    # Load results from the directory
    for filename in os.listdir(results_dir):
        if filename.endswith(".json"):
            file_path = os.path.join(results_dir, filename)
            try:
                # Load the results
                with open(file_path, 'r') as f:
                    import json
                    data = json.load(f)
                
                # Add the data to the dashboard
                if 'function_name' in data and 'profile_data' in data:
                    dashboard.add_profile_data(data['function_name'], data['profile_data'])
                    
                    if 'recommendations' in data:
                        dashboard.add_recommendations(data['function_name'], data['recommendations'])
            except Exception as e:
                print(f"Error loading results from {file_path}: {e}")
    
    # Launch the dashboard
    print(f"Launching dashboard on http://localhost:{port}")
    dashboard.launch(debug=False, open_browser=True)


def parse_args(args: List[str]) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="PyPerfOptimizer - A comprehensive Python package for performance profiling and optimization.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Profile command
    profile_parser = subparsers.add_parser("profile", help="Profile a Python file")
    profile_parser.add_argument("file", help="Python file to profile")
    profile_parser.add_argument("-f", "--function", help="Function to profile (if not specified, all functions will be profiled)")
    profile_parser.add_argument("--no-cpu", action="store_true", help="Disable CPU profiling")
    profile_parser.add_argument("--no-memory", action="store_true", help="Disable memory profiling")
    profile_parser.add_argument("--no-line", action="store_true", help="Disable line-by-line profiling")
    profile_parser.add_argument("-o", "--output-dir", help="Directory to save results")
    
    # Dashboard command
    dashboard_parser = subparsers.add_parser("dashboard", help="Launch the dashboard")
    dashboard_parser.add_argument("-d", "--results-dir", required=True, help="Directory with profiling results")
    dashboard_parser.add_argument("-p", "--port", type=int, default=5000, help="Port to use for the dashboard")
    
    # Version command
    version_parser = subparsers.add_parser("version", help="Show version information")
    
    return parser.parse_args(args)


def main() -> int:
    """Main entry point for the CLI."""
    args = parse_args(sys.argv[1:])
    
    if args.command == "profile":
        try:
            profile_file(
                args.file,
                function_name=args.function,
                enable_cpu=not args.no_cpu,
                enable_memory=not args.no_memory,
                enable_line=not args.no_line,
                output_dir=args.output_dir
            )
            return 0
        except Exception as e:
            print(f"Error: {e}")
            return 1
    
    elif args.command == "dashboard":
        try:
            launch_dashboard(args.results_dir, port=args.port)
            return 0
        except Exception as e:
            print(f"Error: {e}")
            return 1
    
    elif args.command == "version":
        from pyperfoptimizer import __version__
        print(f"PyPerfOptimizer version {__version__}")
        return 0
    
    else:
        # If no command is specified, show the help message
        parse_args(["-h"])
        return 1


if __name__ == "__main__":
    sys.exit(main())