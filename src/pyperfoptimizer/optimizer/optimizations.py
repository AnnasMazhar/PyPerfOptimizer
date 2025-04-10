"""
Optimizations functionality for PyPerfOptimizer.

This module provides tools for automatically optimizing Python code
based on profiling results and common performance patterns.
"""

import ast
import re
import astor
from typing import Dict, List, Set, Tuple, Optional, Any, Union, Callable
import inspect
import sys

class Optimizations:
    """
    A class for automatically applying optimizations to Python code.
    
    This class provides methods to analyze and transform Python code to improve
    performance based on common optimization patterns and profiling results.
    """
    
    def __init__(self):
        """Initialize the optimizations engine."""
        self.transformations_applied = {}
        
    def optimize_function(self, func: Callable, 
                         aggressive: bool = False) -> Optional[Callable]:
        """
        Optimize a function by applying performance improvements.
        
        Args:
            func: The function to optimize
            aggressive: Whether to apply more aggressive optimizations
            
        Returns:
            Optimized function or None if optimization failed
        """
        try:
            # Get the source code of the function
            source = inspect.getsource(func)
            
            # Apply optimizations to the source code
            optimized_source = self.optimize_code(source, aggressive)
            
            # If no optimizations were applied, return the original function
            if source == optimized_source:
                return func
                
            # Compile the optimized source code
            namespace = {}
            exec(optimized_source, func.__globals__, namespace)
            
            # Get the optimized function from the namespace
            optimized_func = namespace[func.__name__]
            
            # Copy over any attributes from the original function
            for attr_name in dir(func):
                if attr_name.startswith('__') and attr_name.endswith('__'):
                    continue
                    
                try:
                    attr_value = getattr(func, attr_name)
                    if not callable(attr_value):
                        setattr(optimized_func, attr_name, attr_value)
                except (AttributeError, TypeError):
                    pass
                    
            return optimized_func
        except Exception as e:
            print(f"Error optimizing function {func.__name__}: {str(e)}")
            return None
            
    def optimize_code(self, code: str, aggressive: bool = False) -> str:
        """
        Optimize Python code by applying performance improvements.
        
        Args:
            code: The source code to optimize
            aggressive: Whether to apply more aggressive optimizations
            
        Returns:
            Optimized source code
        """
        # Reset the transformations tracking
        self.transformations_applied = {}
        
        try:
            # Parse the code into an AST
            tree = ast.parse(code)
            
            # Apply optimizations to the AST
            optimizer = CodeOptimizer(aggressive)
            optimized_tree = optimizer.visit(tree)
            
            # Track applied transformations
            self.transformations_applied = optimizer.transformations
            
            # Generate source code from the optimized AST
            optimized_code = astor.to_source(optimized_tree)
            
            # Apply pattern-based optimizations
            optimized_code = self._apply_pattern_optimizations(optimized_code, aggressive)
            
            return optimized_code
        except Exception as e:
            print(f"Error optimizing code: {str(e)}")
            return code
            
    def _apply_pattern_optimizations(self, code: str, aggressive: bool) -> str:
        """
        Apply pattern-based optimizations to code.
        
        Args:
            code: Source code to optimize
            aggressive: Whether to apply more aggressive optimizations
            
        Returns:
            Optimized source code
        """
        optimized_code = code
        
        # Optimize list comprehensions over map/filter
        map_pattern = r'list\(map\(lambda\s+([a-zA-Z0-9_]+)\s*:\s*(.+?),\s*(.+?)\)\)'
        optimized_code = re.sub(
            map_pattern,
            r'[\2 for \1 in \3]',
            optimized_code
        )
        
        # Optimize filter expressions
        filter_pattern = r'list\(filter\(lambda\s+([a-zA-Z0-9_]+)\s*:\s*(.+?),\s*(.+?)\)\)'
        optimized_code = re.sub(
            filter_pattern,
            r'[\1 for \1 in \3 if \2]',
            optimized_code
        )
        
        # Optimize string concatenation in loops
        if aggressive:
            concat_pattern = r'(for\s+.+?\s+in\s+.+?:\s*\n\s+.+?\s*\+=\s*[\'"](.*?)[\'"])'
            concat_repl = r'\1  # Consider using a list and "".join() for string concatenation'
            optimized_code = re.sub(concat_pattern, concat_repl, optimized_code)
            
        return optimized_code
        
    def get_applied_transformations(self) -> Dict[str, int]:
        """
        Get the transformations applied during optimization.
        
        Returns:
            Dictionary mapping transformation types to counts
        """
        return self.transformations_applied
        
    def suggest_optimizations(self, code: str) -> List[Dict]:
        """
        Suggest optimizations without modifying the code.
        
        Args:
            code: Source code to analyze
            
        Returns:
            List of suggested optimizations
        """
        suggestions = []
        
        try:
            # Parse the code into an AST
            tree = ast.parse(code)
            
            # Create a suggestion visitor
            suggester = OptimizationSuggester()
            suggester.visit(tree)
            
            # Get the suggestions
            suggestions = suggester.suggestions
            
            # Add pattern-based suggestions
            self._add_pattern_suggestions(code, suggestions)
            
            return suggestions
        except Exception as e:
            print(f"Error suggesting optimizations: {str(e)}")
            return [{'type': 'error', 'message': str(e)}]
            
    def _add_pattern_suggestions(self, code: str, suggestions: List[Dict]) -> None:
        """
        Add pattern-based optimization suggestions.
        
        Args:
            code: Source code to analyze
            suggestions: List to add suggestions to
        """
        # Check for range(len(...)) pattern
        range_len_pattern = r'range\(len\((.+?)\)\)'
        for match in re.finditer(range_len_pattern, code):
            lineno = code[:match.start()].count('\n') + 1
            suggestions.append({
                'type': 'range_len',
                'message': f"Use 'enumerate({match.group(1)})' instead of 'range(len({match.group(1)}))'",
                'line': lineno
            })
            
        # Check for repeated dictionary access in loops
        dict_access_pattern = r'for\s+(.+?)\s+in\s+(.+?):\s*\n(\s+.*?)\[(.*?)\]'
        for match in re.finditer(dict_access_pattern, code):
            lineno = code[:match.start()].count('\n') + 1
            suggestions.append({
                'type': 'repeated_dict_access',
                'message': "Consider extracting dictionary values before the loop",
                'line': lineno
            })
            
        # Check for inefficient string concatenation
        concat_pattern = r'for\s+.+?\s+in\s+.+?:\s*\n\s+.+?\s*\+=\s*[\'"]'
        for match in re.finditer(concat_pattern, code):
            lineno = code[:match.start()].count('\n') + 1
            suggestions.append({
                'type': 'string_concat',
                'message': "Use a list and ''.join() for string concatenation in loops",
                'line': lineno
            })
            
        # Check for list() conversion of range()
        list_range_pattern = r'list\(range\('
        for match in re.finditer(list_range_pattern, code):
            lineno = code[:match.start()].count('\n') + 1
            suggestions.append({
                'type': 'list_range',
                'message': "Unnecessary list conversion of range(). Use range directly in Python 3.",
                'line': lineno
            })


class CodeOptimizer(ast.NodeTransformer):
    """
    AST NodeTransformer that applies optimizations to Python code.
    """
    
    def __init__(self, aggressive: bool = False):
        """
        Initialize the code optimizer.
        
        Args:
            aggressive: Whether to apply more aggressive optimizations
        """
        self.aggressive = aggressive
        self.transformations = {
            'list_comp_to_generator': 0,
            'unnecessary_list': 0,
            'loop_invariant': 0,
            'unnecessary_copy': 0,
            'dict_lookup': 0,
            'redundant_conversion': 0
        }
        
    def visit_Call(self, node: ast.Call) -> ast.AST:
        """Visit a Call node and apply optimizations."""
        # Optimize list() conversion of range() or other iterables
        if (isinstance(node.func, ast.Name) and node.func.id == 'list' and 
            len(node.args) == 1):
            arg = node.args[0]
            
            # Check for list(range(...))
            if isinstance(arg, ast.Call) and isinstance(arg.func, ast.Name) and arg.func.id == 'range':
                # Don't convert if it might be used in multiple iterations
                if not self.aggressive:
                    return node
                    
                self.transformations['unnecessary_list'] += 1
                return arg  # Just use range directly
                
        # Optimize sorted() with key function
        if (isinstance(node.func, ast.Name) and node.func.id == 'sorted'):
            # Pass the node through for any standard optimizations
            pass
            
        # Visit children and return the node
        return self.generic_visit(node)
        
    def visit_ListComp(self, node: ast.ListComp) -> ast.AST:
        """Visit a ListComp node and apply optimizations."""
        # If aggressive, consider converting list comprehensions to generator expressions
        if self.aggressive and not self._is_immediately_consumed(node):
            self.transformations['list_comp_to_generator'] += 1
            return ast.GeneratorExp(
                elt=node.elt,
                generators=node.generators
            )
            
        return self.generic_visit(node)
        
    def visit_For(self, node: ast.For) -> ast.AST:
        """Visit a For node and apply optimizations."""
        # Optimize range(len(...)) pattern
        if (isinstance(node.iter, ast.Call) and 
            isinstance(node.iter.func, ast.Name) and node.iter.func.id == 'range' and
            len(node.iter.args) == 1 and
            isinstance(node.iter.args[0], ast.Call) and
            isinstance(node.iter.args[0].func, ast.Name) and node.iter.args[0].func.id == 'len'):
            
            # Get the sequence being measured
            sequence = node.iter.args[0].args[0]
            
            # Create an enumerate call
            enumerate_call = ast.Call(
                func=ast.Name(id='enumerate', ctx=ast.Load()),
                args=[sequence],
                keywords=[]
            )
            
            # Replace the target with a tuple (index, item)
            if isinstance(node.target, ast.Name):
                # Current target is just an index, create a tuple target
                index_var = node.target
                item_var = ast.Name(id='_item', ctx=ast.Store())  # Create a new name for the item
                
                # Create a tuple target (index, item)
                tuple_target = ast.Tuple(
                    elts=[index_var, item_var],
                    ctx=ast.Store()
                )
                
                # Replace the original target with the tuple
                node.target = tuple_target
                
                # Replace range(len(...)) with enumerate(...)
                node.iter = enumerate_call
                
                self.transformations['loop_invariant'] += 1
                
        return self.generic_visit(node)
        
    def visit_BinOp(self, node: ast.BinOp) -> ast.AST:
        """Visit a BinOp node and apply optimizations."""
        # Optimize string concatenation in a loop
        # This is a complex optimization and may require context
        # that's not available in a simple AST transformer
        return self.generic_visit(node)
        
    def visit_Subscript(self, node: ast.Subscript) -> ast.AST:
        """Visit a Subscript node and apply optimizations."""
        # Optimize repeated dictionary lookups
        # This requires context that's not easily available in a simple transformer
        return self.generic_visit(node)
        
    def _is_immediately_consumed(self, node: ast.AST) -> bool:
        """
        Check if a node is immediately consumed (e.g., inside another call).
        
        Args:
            node: AST node to check
            
        Returns:
            Whether the node is immediately consumed
        """
        # This is a simplification - a full implementation would require
        # more context about the parent node
        return False


class OptimizationSuggester(ast.NodeVisitor):
    """
    AST NodeVisitor that suggests optimizations without modifying the code.
    """
    
    def __init__(self):
        """Initialize the optimization suggester."""
        self.suggestions = []
        
    def visit_Call(self, node: ast.Call) -> None:
        """Visit a Call node and suggest optimizations."""
        # Check for list() conversion of range()
        if (isinstance(node.func, ast.Name) and node.func.id == 'list' and 
            len(node.args) == 1 and
            isinstance(node.args[0], ast.Call) and
            isinstance(node.args[0].func, ast.Name) and node.args[0].func.id == 'range'):
            
            self.suggestions.append({
                'type': 'unnecessary_list',
                'message': "Unnecessary list conversion of range(). Use range directly in Python 3.",
                'line': node.lineno
            })
            
        # Check for range(len(...)) pattern
        if (isinstance(node.func, ast.Name) and node.func.id == 'range' and
            len(node.args) == 1 and
            isinstance(node.args[0], ast.Call) and
            isinstance(node.args[0].func, ast.Name) and node.args[0].func.id == 'len'):
            
            self.suggestions.append({
                'type': 'range_len',
                'message': f"Use 'enumerate({astor.to_source(node.args[0].args[0]).strip()})' instead of 'range(len(...))'",
                'line': node.lineno
            })
            
        # Check for sorted() with a more complex key function
        if (isinstance(node.func, ast.Name) and node.func.id == 'sorted'):
            for keyword in node.keywords:
                if keyword.arg == 'key' and isinstance(keyword.value, ast.Lambda):
                    lambda_body = keyword.value.body
                    if isinstance(lambda_body, ast.Subscript):
                        self.suggestions.append({
                            'type': 'sorted_key',
                            'message': "Consider using operator.itemgetter/attrgetter for sorted() key functions",
                            'line': node.lineno
                        })
                        
        self.generic_visit(node)
        
    def visit_For(self, node: ast.For) -> None:
        """Visit a For node and suggest optimizations."""
        # Check for loops that could benefit from enumerate()
        if (isinstance(node.iter, ast.Call) and 
            isinstance(node.iter.func, ast.Name) and 
            node.iter.func.id == 'range' and 
            len(node.iter.args) == 1):
            
            # If not already a range(len(...)) pattern
            if not (isinstance(node.iter.args[0], ast.Call) and 
                   isinstance(node.iter.args[0].func, ast.Name) and 
                   node.iter.args[0].func.id == 'len'):
                   
                self.suggestions.append({
                    'type': 'for_enumerate',
                    'message': "Consider using enumerate() for cleaner counter variables",
                    'line': node.lineno
                })
                
        # Look for loop invariant computations
        self._check_loop_invariants(node)
        
        self.generic_visit(node)
        
    def visit_ListComp(self, node: ast.ListComp) -> None:
        """Visit a ListComp node and suggest optimizations."""
        # Check if it could be a generator expression
        self.suggestions.append({
            'type': 'list_comp_to_generator',
            'message': "Consider using a generator expression if the list is only iterated once",
            'line': getattr(node, 'lineno', '?')
        })
        
        self.generic_visit(node)
        
    def visit_BinOp(self, node: ast.BinOp) -> None:
        """Visit a BinOp node and suggest optimizations."""
        # Check for string concatenation with +
        if isinstance(node.op, ast.Add):
            if isinstance(node.left, ast.Str) or isinstance(node.right, ast.Str):
                self.suggestions.append({
                    'type': 'string_concat',
                    'message': "Consider using f-strings or str.format() for string formatting",
                    'line': getattr(node, 'lineno', '?')
                })
                
        self.generic_visit(node)
        
    def _check_loop_invariants(self, node: ast.For) -> None:
        """
        Check for loop invariant computations.
        
        Args:
            node: For loop node
        """
        # This is a complex analysis that would require data flow tracking
        # For a simple heuristic, look for len() calls inside the loop body
        class LenCallFinder(ast.NodeVisitor):
            def __init__(self):
                self.len_calls = []
                
            def visit_Call(self, node):
                if isinstance(node.func, ast.Name) and node.func.id == 'len':
                    self.len_calls.append(node)
                self.generic_visit(node)
                
        len_finder = LenCallFinder()
        len_finder.visit(node.body)
        
        if len_finder.len_calls:
            self.suggestions.append({
                'type': 'loop_invariant',
                'message': "Consider moving len() calls outside the loop for better performance",
                'line': node.lineno
            })
