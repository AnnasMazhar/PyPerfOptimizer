"""
Code analysis functionality for PyPerfOptimizer.

This module provides tools for analyzing Python code to identify
potential performance issues and optimization opportunities.
"""

import os
import ast
import inspect
import builtins
import importlib
from typing import Dict, List, Set, Tuple, Optional, Any, Union, Callable
import re
import itertools

class CodeAnalyzer:
    """
    A class for analyzing Python code to identify optimization opportunities.
    
    This class inspects source code to detect common patterns that may lead
    to performance issues, such as inefficient loops, unnecessary function calls,
    suboptimal data structures, and more.
    """
    
    def __init__(self):
        """Initialize the code analyzer."""
        self.issues = []
        self.imported_modules = set()
        self.used_builtins = set()
        self.defined_functions = {}
        self.called_functions = set()
        self.comprehensions = []
        self.loops = []
        self.conditionals = []
        self.exception_handling = []
        self.data_structures = {
            'lists': [],
            'dicts': [],
            'sets': [],
            'tuples': []
        }
        
    def reset(self) -> None:
        """Reset the analyzer state."""
        self.__init__()
        
    def analyze_function(self, func: Callable) -> Dict:
        """
        Analyze a function for optimization opportunities.
        
        Args:
            func: The function to analyze
            
        Returns:
            Dictionary containing analysis results
        """
        # Get the source code of the function
        try:
            source = inspect.getsource(func)
        except (IOError, TypeError):
            self.issues.append({
                'severity': 'error',
                'message': f"Could not retrieve source code for {func.__name__}"
            })
            return self._get_results()
            
        # Get the module where the function is defined
        module = inspect.getmodule(func)
        module_name = module.__name__ if module else None
        
        # Analyze the source code
        return self.analyze_code(source, module_name)
        
    def analyze_code(self, code: str, module_name: Optional[str] = None) -> Dict:
        """
        Analyze code for optimization opportunities.
        
        Args:
            code: The source code to analyze
            module_name: Name of the module containing the code
            
        Returns:
            Dictionary containing analysis results
        """
        self.reset()
        
        try:
            # Parse the code into an AST
            tree = ast.parse(code)
            
            # Analyze the AST
            self._analyze_ast(tree, module_name)
            
            # Check for specific patterns
            self._check_for_patterns(code)
            
            # Get the results
            return self._get_results()
        except SyntaxError as e:
            self.issues.append({
                'severity': 'error',
                'message': f"Syntax error in code: {str(e)}"
            })
            return self._get_results()
            
    def analyze_file(self, filename: str) -> Dict:
        """
        Analyze a Python file for optimization opportunities.
        
        Args:
            filename: Path to the Python file to analyze
            
        Returns:
            Dictionary containing analysis results
        """
        if not os.path.exists(filename):
            self.issues.append({
                'severity': 'error',
                'message': f"File {filename} does not exist"
            })
            return self._get_results()
            
        try:
            with open(filename, 'r') as f:
                code = f.read()
                
            # Determine the module name from the filename
            module_name = os.path.basename(filename).replace('.py', '')
            
            return self.analyze_code(code, module_name)
        except Exception as e:
            self.issues.append({
                'severity': 'error',
                'message': f"Error analyzing file {filename}: {str(e)}"
            })
            return self._get_results()
            
    def _analyze_ast(self, tree: ast.AST, module_name: Optional[str] = None) -> None:
        """
        Analyze an AST for optimization opportunities.
        
        Args:
            tree: The AST to analyze
            module_name: Name of the module containing the code
        """
        # Create a visitor to analyze the AST
        visitor = CodeVisitor(module_name)
        visitor.visit(tree)
        
        # Collect analysis results
        self.imported_modules = visitor.imported_modules
        self.used_builtins = visitor.used_builtins
        self.defined_functions = visitor.defined_functions
        self.called_functions = visitor.called_functions
        self.comprehensions = visitor.comprehensions
        self.loops = visitor.loops
        self.conditionals = visitor.conditionals
        self.exception_handling = visitor.exception_handling
        self.data_structures = visitor.data_structures
        
        # Collect issues found during AST analysis
        self.issues.extend(visitor.issues)
        
    def _check_for_patterns(self, code: str) -> None:
        """
        Check for specific patterns in the code that may indicate issues.
        
        Args:
            code: The source code to analyze
        """
        # Check for global variables
        global_pattern = r'^[A-Z_][A-Z0-9_]*\s*='
        if re.search(global_pattern, code, re.MULTILINE):
            self.issues.append({
                'severity': 'warning',
                'message': "Global variables detected. Consider encapsulating in functions or classes."
            })
            
        # Check for multiple calls to len() in loops
        len_in_loop_pattern = r'for\s+.*\s+in\s+.*:\s*.*len\('
        if re.search(len_in_loop_pattern, code):
            self.issues.append({
                'severity': 'warning',
                'message': "Multiple calls to len() in loop. Calculate length once before the loop."
            })
            
        # Check for unnecessary list conversions
        list_conv_pattern = r'list\(\s*range\('
        if re.search(list_conv_pattern, code):
            self.issues.append({
                'severity': 'info',
                'message': "Unnecessary list conversion of range(). Use range directly in Python 3."
            })
            
        # Check for inefficient string concatenation in loops
        str_concat_pattern = r'for\s+.*\s+in\s+.*:\s*.*\s*\+='
        if re.search(str_concat_pattern, code):
            self.issues.append({
                'severity': 'warning',
                'message': "String concatenation in a loop. Use ''.join() or a list comprehension instead."
            })
            
    def _get_results(self) -> Dict:
        """
        Get the analysis results.
        
        Returns:
            Dictionary containing analysis results
        """
        # Count different types of issues
        issue_counts = {'error': 0, 'warning': 0, 'info': 0}
        for issue in self.issues:
            severity = issue.get('severity', 'info')
            issue_counts[severity] += 1
            
        # Count different types of constructs
        construct_counts = {
            'functions': len(self.defined_functions),
            'comprehensions': len(self.comprehensions),
            'loops': len(self.loops),
            'conditionals': len(self.conditionals),
            'exception_blocks': len(self.exception_handling),
            'data_structures': sum(len(ds) for ds in self.data_structures.values())
        }
        
        # Get unused functions
        unused_functions = set(self.defined_functions.keys()) - self.called_functions
        
        # Prepare the results
        results = {
            'issues': self.issues,
            'issue_counts': issue_counts,
            'construct_counts': construct_counts,
            'imported_modules': list(self.imported_modules),
            'used_builtins': list(self.used_builtins),
            'defined_functions': self.defined_functions,
            'unused_functions': list(unused_functions),
            'comprehensions': self.comprehensions,
            'loops': self.loops,
            'conditionals': self.conditionals,
            'exception_handling': self.exception_handling,
            'data_structures': self.data_structures
        }
        
        return results
        
    def get_optimization_opportunities(self) -> List[Dict]:
        """
        Get a list of optimization opportunities based on the analysis.
        
        Returns:
            List of dictionaries containing optimization opportunities
        """
        opportunities = []
        
        # Check for optimization opportunities in loops
        for loop in self.loops:
            if loop.get('nested', False):
                opportunities.append({
                    'type': 'loop',
                    'severity': 'warning',
                    'message': f"Nested loop at line {loop.get('line', '?')}. Consider optimizing or using a different algorithm.",
                    'line': loop.get('line')
                })
                
        # Check for optimization opportunities in data structures
        for list_info in self.data_structures['lists']:
            if list_info.get('comprehension', False):
                continue  # List comprehensions are generally efficient
                
            opportunities.append({
                'type': 'data_structure',
                'severity': 'info',
                'message': f"List created at line {list_info.get('line', '?')}. Consider if a different data structure would be more efficient.",
                'line': list_info.get('line')
            })
            
        # Check for unused functions
        unused_functions = set(self.defined_functions.keys()) - self.called_functions
        for func_name in unused_functions:
            func_info = self.defined_functions.get(func_name, {})
            opportunities.append({
                'type': 'function',
                'severity': 'info',
                'message': f"Function '{func_name}' at line {func_info.get('line', '?')} is defined but not called.",
                'line': func_info.get('line')
            })
            
        # Include all issues as opportunities
        for issue in self.issues:
            opportunities.append({
                'type': 'issue',
                'severity': issue.get('severity', 'info'),
                'message': issue.get('message', ''),
                'line': issue.get('line')
            })
            
        return opportunities
        

class CodeVisitor(ast.NodeVisitor):
    """
    A visitor that analyzes Python AST nodes to detect optimization opportunities.
    """
    
    def __init__(self, module_name: Optional[str] = None):
        """
        Initialize the code visitor.
        
        Args:
            module_name: Name of the module being analyzed
        """
        self.module_name = module_name
        self.issues = []
        self.imported_modules = set()
        self.used_builtins = set()
        self.defined_functions = {}
        self.called_functions = set()
        self.comprehensions = []
        self.loops = []
        self.conditionals = []
        self.exception_handling = []
        self.data_structures = {
            'lists': [],
            'dicts': [],
            'sets': [],
            'tuples': []
        }
        self.current_function = None
        self.loop_depth = 0
        
    def visit_Import(self, node: ast.Import) -> None:
        """Visit an Import node."""
        for name in node.names:
            self.imported_modules.add(name.name)
        self.generic_visit(node)
        
    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Visit an ImportFrom node."""
        if node.module:
            self.imported_modules.add(node.module)
        self.generic_visit(node)
        
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit a FunctionDef node."""
        old_function = self.current_function
        self.current_function = node.name
        
        # Store information about the function
        self.defined_functions[node.name] = {
            'line': node.lineno,
            'args': [arg.arg for arg in node.args.args],
            'defaults': len(node.args.defaults),
            'decorators': [self._get_decorator_name(d) for d in node.decorator_list]
        }
        
        # Check for issues with default arguments
        if node.args.defaults:
            for default in node.args.defaults:
                if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                    self.issues.append({
                        'severity': 'warning',
                        'message': f"Mutable default argument in function '{node.name}' at line {node.lineno}",
                        'line': node.lineno
                    })
                    
        # Analyze function body
        self.generic_visit(node)
        
        # Restore previous function
        self.current_function = old_function
        
    def visit_Call(self, node: ast.Call) -> None:
        """Visit a Call node."""
        # Get the function name
        func_name = self._get_call_name(node.func)
        
        # Record the function call
        if func_name:
            self.called_functions.add(func_name)
            
            # Check for built-in functions
            if hasattr(builtins, func_name):
                self.used_builtins.add(func_name)
                
                # Check for inefficient built-in usage
                if func_name == 'len' and self.loop_depth > 0:
                    self.issues.append({
                        'severity': 'warning',
                        'message': f"Call to len() inside a loop at line {node.lineno}. Calculate length once before loop.",
                        'line': node.lineno
                    })
                elif func_name == 'sorted' and self.loop_depth > 0:
                    self.issues.append({
                        'severity': 'warning',
                        'message': f"Call to sorted() inside a loop at line {node.lineno}. Sort once before loop if possible.",
                        'line': node.lineno
                    })
                    
        # Analyze call arguments
        self.generic_visit(node)
        
    def visit_For(self, node: ast.For) -> None:
        """Visit a For node."""
        # Increment loop depth
        self.loop_depth += 1
        
        # Record loop information
        loop_info = {
            'line': node.lineno,
            'nested': self.loop_depth > 1,
            'target_type': self._get_node_type(node.target),
            'iter_type': self._get_node_type(node.iter)
        }
        self.loops.append(loop_info)
        
        # Check for specific loop patterns
        iter_name = self._get_call_name(node.iter)
        if iter_name == 'range' and isinstance(node.iter, ast.Call) and len(node.iter.args) == 1:
            # Check for range(len(...)) pattern
            if (isinstance(node.iter.args[0], ast.Call) and 
                self._get_call_name(node.iter.args[0]) == 'len'):
                self.issues.append({
                    'severity': 'info',
                    'message': f"range(len(...)) at line {node.lineno}. Consider using enumerate() for cleaner code.",
                    'line': node.lineno
                })
                
        # Analyze loop body
        self.generic_visit(node)
        
        # Decrement loop depth
        self.loop_depth -= 1
        
    def visit_While(self, node: ast.While) -> None:
        """Visit a While node."""
        # Increment loop depth
        self.loop_depth += 1
        
        # Record loop information
        loop_info = {
            'line': node.lineno,
            'nested': self.loop_depth > 1,
            'test_type': self._get_node_type(node.test)
        }
        self.loops.append(loop_info)
        
        # Analyze loop body
        self.generic_visit(node)
        
        # Decrement loop depth
        self.loop_depth -= 1
        
    def visit_If(self, node: ast.If) -> None:
        """Visit an If node."""
        # Record conditional information
        cond_info = {
            'line': node.lineno,
            'test_type': self._get_node_type(node.test),
            'has_else': bool(node.orelse)
        }
        self.conditionals.append(cond_info)
        
        # Analyze the If statement and its blocks
        self.generic_visit(node)
        
    def visit_Try(self, node: ast.Try) -> None:
        """Visit a Try node."""
        # Record exception handling information
        ex_info = {
            'line': node.lineno,
            'num_handlers': len(node.handlers),
            'has_finally': bool(node.finalbody),
            'has_else': bool(node.orelse)
        }
        self.exception_handling.append(ex_info)
        
        # Analyze the Try block and its handlers
        self.generic_visit(node)
        
    def visit_ListComp(self, node: ast.ListComp) -> None:
        """Visit a ListComp node."""
        # Record list comprehension information
        comp_info = {
            'line': node.lineno,
            'type': 'list',
            'num_generators': len(node.generators)
        }
        self.comprehensions.append(comp_info)
        
        # Record list information
        list_info = {
            'line': node.lineno,
            'comprehension': True
        }
        self.data_structures['lists'].append(list_info)
        
        # Analyze the comprehension
        self.generic_visit(node)
        
    def visit_DictComp(self, node: ast.DictComp) -> None:
        """Visit a DictComp node."""
        # Record dict comprehension information
        comp_info = {
            'line': node.lineno,
            'type': 'dict',
            'num_generators': len(node.generators)
        }
        self.comprehensions.append(comp_info)
        
        # Record dict information
        dict_info = {
            'line': node.lineno,
            'comprehension': True
        }
        self.data_structures['dicts'].append(dict_info)
        
        # Analyze the comprehension
        self.generic_visit(node)
        
    def visit_SetComp(self, node: ast.SetComp) -> None:
        """Visit a SetComp node."""
        # Record set comprehension information
        comp_info = {
            'line': node.lineno,
            'type': 'set',
            'num_generators': len(node.generators)
        }
        self.comprehensions.append(comp_info)
        
        # Record set information
        set_info = {
            'line': node.lineno,
            'comprehension': True
        }
        self.data_structures['sets'].append(set_info)
        
        # Analyze the comprehension
        self.generic_visit(node)
        
    def visit_GeneratorExp(self, node: ast.GeneratorExp) -> None:
        """Visit a GeneratorExp node."""
        # Record generator expression information
        comp_info = {
            'line': node.lineno,
            'type': 'generator',
            'num_generators': len(node.generators)
        }
        self.comprehensions.append(comp_info)
        
        # Analyze the generator expression
        self.generic_visit(node)
        
    def visit_List(self, node: ast.List) -> None:
        """Visit a List node."""
        # Record list information
        list_info = {
            'line': node.lineno,
            'size': len(node.elts),
            'comprehension': False
        }
        self.data_structures['lists'].append(list_info)
        
        # Analyze the list elements
        self.generic_visit(node)
        
    def visit_Dict(self, node: ast.Dict) -> None:
        """Visit a Dict node."""
        # Record dict information
        dict_info = {
            'line': node.lineno,
            'size': len(node.keys),
            'comprehension': False
        }
        self.data_structures['dicts'].append(dict_info)
        
        # Analyze the dict elements
        self.generic_visit(node)
        
    def visit_Set(self, node: ast.Set) -> None:
        """Visit a Set node."""
        # Record set information
        set_info = {
            'line': node.lineno,
            'size': len(node.elts),
            'comprehension': False
        }
        self.data_structures['sets'].append(set_info)
        
        # Analyze the set elements
        self.generic_visit(node)
        
    def visit_Tuple(self, node: ast.Tuple) -> None:
        """Visit a Tuple node."""
        # Record tuple information
        tuple_info = {
            'line': node.lineno if hasattr(node, 'lineno') else 0,
            'size': len(node.elts)
        }
        self.data_structures['tuples'].append(tuple_info)
        
        # Analyze the tuple elements
        self.generic_visit(node)
        
    def _get_call_name(self, node: ast.AST) -> Optional[str]:
        """
        Get the name of a function call.
        
        Args:
            node: AST node representing a function call
            
        Returns:
            Name of the function being called, or None if it can't be determined
        """
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return node.attr
        return None
        
    def _get_decorator_name(self, node: ast.AST) -> str:
        """
        Get the name of a decorator.
        
        Args:
            node: AST node representing a decorator
            
        Returns:
            Name of the decorator
        """
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_decorator_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.Call):
            return self._get_decorator_name(node.func)
        return "unknown"
        
    def _get_node_type(self, node: ast.AST) -> str:
        """
        Get a string representation of the node type.
        
        Args:
            node: AST node
            
        Returns:
            String representing the node type
        """
        return node.__class__.__name__
