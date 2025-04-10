"""
Tests for the code analyzer component of PyPerfOptimizer.
"""

import unittest
import os
import tempfile
import ast

from pyperfoptimizer.optimizer.code_analyzer import CodeAnalyzer, CodeVisitor

class TestCodeAnalyzer(unittest.TestCase):
    """Test cases for the CodeAnalyzer class."""

    def setUp(self):
        """Set up test fixtures."""
        self.analyzer = CodeAnalyzer()
        
    def tearDown(self):
        """Tear down test fixtures."""
        self.analyzer = None
        
    def test_analyze_code(self):
        """Test analyzing code for optimization opportunities."""
        # A code snippet with various potential optimizations
        code = """
def inefficient_function(data, threshold=0):
    results = []
    for i in range(len(data)):
        item = data[i]
        if item > threshold:
            results.append(item)
            
    # String concatenation in a loop
    report = ""
    for result in results:
        report += str(result) + ", "
        
    # Unnecessary list conversion
    numbers = list(range(10))
    
    # Call len inside a loop
    total = 0
    for _ in range(10):
        total += len(data)
        
    return report, numbers, total
"""
        
        results = self.analyzer.analyze_code(code)
        
        # Check that the basic structure is correct
        self.assertIsInstance(results, dict)
        self.assertIn('issues', results)
        self.assertIn('issue_counts', results)
        self.assertIn('construct_counts', results)
        self.assertIn('imported_modules', results)
        self.assertIn('defined_functions', results)
        self.assertIn('loops', results)
        
        # Check that it found the function
        self.assertEqual(len(results['defined_functions']), 1)
        self.assertIn('inefficient_function', results['defined_functions'])
        
        # Check that it found some loops
        self.assertGreater(len(results['loops']), 0)
        
        # Check that it found some issues
        self.assertGreater(len(results['issues']), 0)
        
    def test_analyze_function(self):
        """Test analyzing a function for optimization opportunities."""
        # Define a function to analyze
        def test_function(data, limit=100):
            result = []
            for i in range(len(data)):
                if i < limit:
                    result.append(data[i] * 2)
            return result
        
        results = self.analyzer.analyze_function(test_function)
        
        # Check that the basic structure is correct
        self.assertIsInstance(results, dict)
        self.assertIn('issues', results)
        self.assertIn('issue_counts', results)
        self.assertIn('construct_counts', results)
        self.assertIn('imported_modules', results)
        self.assertIn('defined_functions', results)
        self.assertIn('loops', results)
        
        # It should find the range(len()) pattern
        found_range_len = False
        for issue in results['issues']:
            if 'range(len(' in issue.get('message', ''):
                found_range_len = True
                break
                
        self.assertTrue(found_range_len, "Should detect the range(len()) pattern")
        
    def test_analyze_file(self):
        """Test analyzing a Python file for optimization opportunities."""
        # Create a temporary file with some code
        with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as tmp:
            tmp.write(b"""
def inefficient_file_function(items):
    # Inefficient list creation
    total = 0
    for item in items:
        total += len(item)
        
    # List comprehension that could be a generator
    squares = [x**2 for x in range(1000)]
    
    return total, sum(squares)
""")
            file_path = tmp.name
            
        try:
            results = self.analyzer.analyze_file(file_path)
            
            # Check that the basic structure is correct
            self.assertIsInstance(results, dict)
            self.assertIn('issues', results)
            self.assertIn('issue_counts', results)
            self.assertIn('construct_counts', results)
            self.assertIn('imported_modules', results)
            self.assertIn('defined_functions', results)
            self.assertIn('loops', results)
            self.assertIn('comprehensions', results)
            
            # Check that it found the function
            self.assertEqual(len(results['defined_functions']), 1)
            self.assertIn('inefficient_file_function', results['defined_functions'])
            
            # Check that it found a comprehension
            self.assertGreater(len(results['comprehensions']), 0)
            
            # Check that it found the len() in loop issue
            found_len_in_loop = False
            for issue in results['issues']:
                if 'len() inside a loop' in issue.get('message', ''):
                    found_len_in_loop = True
                    break
                    
            self.assertTrue(found_len_in_loop, "Should detect len() calls inside a loop")
        finally:
            # Clean up
            if os.path.exists(file_path):
                os.unlink(file_path)
                
    def test_get_optimization_opportunities(self):
        """Test getting optimization opportunities."""
        # Analyze code with opportunities
        code = """
def nested_loops_example(data):
    result = []
    # Nested loop
    for i in range(len(data)):
        for j in range(len(data[i])):
            result.append(data[i][j])
    return result

def unused_function():
    # This function is defined but never called
    pass
"""
        self.analyzer.analyze_code(code)
        opportunities = self.analyzer.get_optimization_opportunities()
        
        # Check that it found opportunities
        self.assertIsInstance(opportunities, list)
        self.assertGreater(len(opportunities), 0)
        
        # Check for nested loop opportunity
        found_nested_loop = False
        for opp in opportunities:
            if opp['type'] == 'loop' and 'Nested loop' in opp['message']:
                found_nested_loop = True
                break
                
        self.assertTrue(found_nested_loop, "Should detect nested loop optimization opportunity")
        
        # Check for unused function opportunity
        found_unused_func = False
        for opp in opportunities:
            if opp['type'] == 'function' and 'unused_function' in opp['message']:
                found_unused_func = True
                break
                
        self.assertTrue(found_unused_func, "Should detect unused function optimization opportunity")
        
    def test_reset(self):
        """Test resetting the analyzer state."""
        # Analyze some code
        code = "def example(): return [x for x in range(100)]"
        self.analyzer.analyze_code(code)
        
        # Check that it has results
        self.assertGreater(len(self.analyzer.issues), 0)
        self.assertGreater(len(self.analyzer.loops), 0)
        
        # Reset the analyzer
        self.analyzer.reset()
        
        # Check that everything was reset
        self.assertEqual(len(self.analyzer.issues), 0)
        self.assertEqual(len(self.analyzer.loops), 0)
        self.assertEqual(len(self.analyzer.defined_functions), 0)

class TestCodeVisitor(unittest.TestCase):
    """Test cases for the CodeVisitor class."""

    def test_visit_import(self):
        """Test the Import node visitor."""
        code = "import os, sys"
        tree = ast.parse(code)
        visitor = CodeVisitor()
        visitor.visit(tree)
        
        self.assertIn('os', visitor.imported_modules)
        self.assertIn('sys', visitor.imported_modules)
        
    def test_visit_import_from(self):
        """Test the ImportFrom node visitor."""
        code = "from os import path, environ"
        tree = ast.parse(code)
        visitor = CodeVisitor()
        visitor.visit(tree)
        
        self.assertIn('os', visitor.imported_modules)
        
    def test_visit_function_def(self):
        """Test the FunctionDef node visitor."""
        code = "def test_func(a, b=10): return a + b"
        tree = ast.parse(code)
        visitor = CodeVisitor()
        visitor.visit(tree)
        
        self.assertIn('test_func', visitor.defined_functions)
        func_info = visitor.defined_functions['test_func']
        self.assertEqual(func_info['args'], ['a', 'b'])
        self.assertEqual(func_info['defaults'], 1)
        
    def test_visit_call(self):
        """Test the Call node visitor."""
        code = "len([1, 2, 3])"
        tree = ast.parse(code)
        visitor = CodeVisitor()
        visitor.visit(tree)
        
        self.assertIn('len', visitor.called_functions)
        self.assertIn('len', visitor.used_builtins)
        
    def test_visit_for(self):
        """Test the For node visitor."""
        code = "for i in range(10): print(i)"
        tree = ast.parse(code)
        visitor = CodeVisitor()
        visitor.visit(tree)
        
        self.assertEqual(len(visitor.loops), 1)
        loop_info = visitor.loops[0]
        self.assertEqual(loop_info['nested'], False)
        
    def test_visit_nested_for(self):
        """Test the For node visitor with nested loops."""
        code = "for i in range(5):\n  for j in range(5): print(i, j)"
        tree = ast.parse(code)
        visitor = CodeVisitor()
        visitor.visit(tree)
        
        self.assertEqual(len(visitor.loops), 2)
        # Second loop should be nested
        self.assertEqual(visitor.loops[1]['nested'], True)
        
    def test_visit_while(self):
        """Test the While node visitor."""
        code = "i = 0\nwhile i < 10: i += 1"
        tree = ast.parse(code)
        visitor = CodeVisitor()
        visitor.visit(tree)
        
        self.assertEqual(len(visitor.loops), 1)
        loop_info = visitor.loops[0]
        self.assertEqual(loop_info['nested'], False)
        
    def test_visit_if(self):
        """Test the If node visitor."""
        code = "if x > 0: y = 1\nelse: y = 2"
        tree = ast.parse(code)
        visitor = CodeVisitor()
        visitor.visit(tree)
        
        self.assertEqual(len(visitor.conditionals), 1)
        cond_info = visitor.conditionals[0]
        self.assertEqual(cond_info['has_else'], True)
        
    def test_visit_try(self):
        """Test the Try node visitor."""
        code = "try: x = 1/0\nexcept ZeroDivisionError: x = 0\nfinally: print('done')"
        tree = ast.parse(code)
        visitor = CodeVisitor()
        visitor.visit(tree)
        
        self.assertEqual(len(visitor.exception_handling), 1)
        ex_info = visitor.exception_handling[0]
        self.assertEqual(ex_info['num_handlers'], 1)
        self.assertEqual(ex_info['has_finally'], True)
        
    def test_visit_list_comp(self):
        """Test the ListComp node visitor."""
        code = "[x**2 for x in range(10)]"
        tree = ast.parse(code)
        visitor = CodeVisitor()
        visitor.visit(tree)
        
        self.assertEqual(len(visitor.comprehensions), 1)
        self.assertEqual(len(visitor.data_structures['lists']), 1)
        comp_info = visitor.comprehensions[0]
        self.assertEqual(comp_info['type'], 'list')
        
    def test_visit_dict_comp(self):
        """Test the DictComp node visitor."""
        code = "{x: x**2 for x in range(10)}"
        tree = ast.parse(code)
        visitor = CodeVisitor()
        visitor.visit(tree)
        
        self.assertEqual(len(visitor.comprehensions), 1)
        self.assertEqual(len(visitor.data_structures['dicts']), 1)
        comp_info = visitor.comprehensions[0]
        self.assertEqual(comp_info['type'], 'dict')
        
    def test_visit_set_comp(self):
        """Test the SetComp node visitor."""
        code = "{x**2 for x in range(10)}"
        tree = ast.parse(code)
        visitor = CodeVisitor()
        visitor.visit(tree)
        
        self.assertEqual(len(visitor.comprehensions), 1)
        self.assertEqual(len(visitor.data_structures['sets']), 1)
        comp_info = visitor.comprehensions[0]
        self.assertEqual(comp_info['type'], 'set')
        
    def test_visit_generator_exp(self):
        """Test the GeneratorExp node visitor."""
        code = "sum(x**2 for x in range(10))"
        tree = ast.parse(code)
        visitor = CodeVisitor()
        visitor.visit(tree)
        
        self.assertEqual(len(visitor.comprehensions), 1)
        comp_info = visitor.comprehensions[0]
        self.assertEqual(comp_info['type'], 'generator')
        
    def test_visit_list(self):
        """Test the List node visitor."""
        code = "[1, 2, 3, 4, 5]"
        tree = ast.parse(code)
        visitor = CodeVisitor()
        visitor.visit(tree)
        
        self.assertEqual(len(visitor.data_structures['lists']), 1)
        list_info = visitor.data_structures['lists'][0]
        self.assertEqual(list_info['size'], 5)
        self.assertEqual(list_info['comprehension'], False)
        
    def test_visit_dict(self):
        """Test the Dict node visitor."""
        code = "{1: 'one', 2: 'two', 3: 'three'}"
        tree = ast.parse(code)
        visitor = CodeVisitor()
        visitor.visit(tree)
        
        self.assertEqual(len(visitor.data_structures['dicts']), 1)
        dict_info = visitor.data_structures['dicts'][0]
        self.assertEqual(dict_info['size'], 3)
        self.assertEqual(dict_info['comprehension'], False)
        
    def test_visit_set(self):
        """Test the Set node visitor."""
        code = "{1, 2, 3, 4}"
        tree = ast.parse(code)
        visitor = CodeVisitor()
        visitor.visit(tree)
        
        self.assertEqual(len(visitor.data_structures['sets']), 1)
        set_info = visitor.data_structures['sets'][0]
        self.assertEqual(set_info['size'], 4)
        self.assertEqual(set_info['comprehension'], False)
        
    def test_visit_tuple(self):
        """Test the Tuple node visitor."""
        code = "(1, 2, 3)"
        tree = ast.parse(code)
        visitor = CodeVisitor()
        visitor.visit(tree)
        
        self.assertEqual(len(visitor.data_structures['tuples']), 1)
        tuple_info = visitor.data_structures['tuples'][0]
        self.assertEqual(tuple_info['size'], 3)

if __name__ == '__main__':
    unittest.main()
