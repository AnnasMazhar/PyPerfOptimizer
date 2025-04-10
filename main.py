from flask import Flask, render_template, request, redirect, url_for
import os
import sys
from datetime import datetime

# Add src to the Python path to make pyperfoptimizer importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

# Create Flask application
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev_secret_key")

@app.route('/')
def index():
    """Render the main dashboard page."""
    return render_template('index.html', title="PyPerfOptimizer Dashboard")

@app.route('/run/<example>')
def run_example(example):
    """Run a specific example and display its results."""
    # Map example names to their file paths
    examples = {
        'simple': 'examples/simple_profiling.py',
        'memory': 'examples/memory_optimization.py',
        'integrated': 'examples/integrated_dashboard.py',
        'automation': 'examples/automation_example.py'
    }
    
    if example not in examples:
        return redirect(url_for('index'))
    
    # Execute the example (in a real app, this would be done asynchronously)
    # Here we'll just redirect to the results page
    return redirect(url_for('results', example=example))

@app.route('/results/<example>')
def results(example):
    """Display the results of an executed example."""
    # In a real app, this would fetch actual results
    example_titles = {
        'simple': 'Simple Profiling Example',
        'memory': 'Memory Optimization Example',
        'integrated': 'Integrated Dashboard Example',
        'automation': 'Automation Example'
    }
    
    title = example_titles.get(example, 'Example Results')
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    return render_template('results.html', title=title, example=example, timestamp=timestamp)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)