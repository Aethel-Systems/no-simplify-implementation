#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Hardcore Dynamic/Static Structural Analyzer.
Engineered to detect "Mock Implementations" where an AI outputs structurally valid
but functionally empty code (e.g., a function just printing "success").
Calculates Cyclomatic Complexity and Branch Depth.
"""

import ast
import re
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

# ==============================================================================
# Cross-Language Structural Models
# ==============================================================================

@dataclass
class FunctionMetrics:
    name: str
    start_line: int
    end_line: int
    cyclomatic_complexity: int
    statement_count: int
    has_loops: bool
    has_try_catch: bool
    is_empty: bool
    returns_constant: bool
    only_prints: bool

# ==============================================================================
# Mock Implementation Detection Heuristics
# ==============================================================================

class MockDetector:
    """
    Evaluates FunctionMetrics to determine if the implementation is a "Mock".
    """
    # Verbs usually associated with complex business logic
    COMPLEX_VERBS = {
        'make', 'build', 'generate', 'process', 'calculate', 'parse', 'compile',
        'sync', 'execute', 'connect', 'initialize', 'setup', 'fetch', 'download'
    }

    @classmethod
    def evaluate(cls, metrics: FunctionMetrics, file_path: str) -> Optional[str]:
        # Ignore strictly structural or standard magic methods in Python
        if metrics.name.startswith('__') and metrics.name.endswith('__'):
            return None
        if metrics.name in ['main', 'run']:
            return None

        # Check verb
        name_parts = metrics.name.lower().split('_')
        is_complex_action = any(verb in name_parts for verb in cls.COMPLEX_VERBS)

        # Rule 1: The "Print & Pass" Mock
        if is_complex_action and metrics.only_prints and metrics.statement_count <= 2:
            return f"Function '{metrics.name}' implies complex action but only prints/logs. Mock implementation detected."

        # Rule 2: The "Blind Constant Return" Mock
        if is_complex_action and metrics.returns_constant and metrics.statement_count == 1:
            return f"Function '{metrics.name}' blindly returns a constant without computing anything. Mock implementation detected."

        # Rule 3: Extreme Simplicity in Domain Logic
        # E.g., generate_fat_table() but cyclomatic complexity is 1 and no loops.
        if "generate" in name_parts or "process" in name_parts:
            if metrics.cyclomatic_complexity == 1 and not metrics.has_loops and metrics.statement_count <= 3:
                return f"Function '{metrics.name}' requires loops or branches based on its name, but implementation is linear and trivial."

        # Rule 4: Completely Empty
        if metrics.is_empty:
            return f"Function '{metrics.name}' is completely empty."

        return None


# ==============================================================================
# Python AST Analyzer
# ==============================================================================

class PythonAnalyzer(ast.NodeVisitor):
    def __init__(self):
        self.violations: List[Dict[str, Any]] = []
        self.current_function: Optional[str] = None
    
    def analyze_source(self, file_path: str, source_code: str) -> List[Dict[str, Any]]:
        try:
            tree = ast.parse(source_code, filename=file_path)
            self.file_path = file_path
            self.visit(tree)
        except SyntaxError as e:
            self.violations.append({
                "file_path": file_path,
                "line_number": e.lineno or 1,
                "rule_name": "PYTHON_SYNTAX_ERROR",
                "snippet": f"{e.msg} at offset {e.offset}",
                "suggestion": "The code cannot even be parsed. Fix syntax errors.",
                "severity": "CRITICAL"
            })
        return self.violations

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._analyze_function(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self._analyze_function(node)
        self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler):
        # Empty except blocks
        functional_stmts = [s for s in node.body if not (isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant))]
        if not functional_stmts or (len(functional_stmts) == 1 and isinstance(functional_stmts[0], ast.Pass)):
            self.violations.append({
                "file_path": getattr(self, 'file_path', 'unknown'),
                "line_number": node.lineno,
                "rule_name": "EMPTY_EXCEPTION_HANDLER",
                "snippet": "except [Exception]: pass",
                "suggestion": "Swallowing exceptions is forbidden. Log the error properly and handle degradation.",
                "severity": "ERROR"
            })
        self.generic_visit(node)

    def _analyze_function(self, node: ast.AST):
        statements = [s for s in node.body if not (isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant))]
        
        metrics = FunctionMetrics(
            name=getattr(node, 'name', 'anonymous'),
            start_line=node.lineno,
            end_line=getattr(node, 'end_lineno', node.lineno),
            cyclomatic_complexity=1,
            statement_count=len(statements),
            has_loops=False,
            has_try_catch=False,
            is_empty=len(statements) == 0,
            returns_constant=False,
            only_prints=False
        )

        if metrics.is_empty:
            metrics.is_empty = True
            
        else:
            print_count = 0
            for stmt in ast.walk(node):
                # Complexity calculation (Branches)
                if isinstance(stmt, (ast.If, ast.IfExp, ast.For, ast.While, ast.And, ast.Or, ast.ExceptHandler)):
                    metrics.cyclomatic_complexity += 1
                
                if isinstance(stmt, (ast.For, ast.While)):
                    metrics.has_loops = True
                    
                if isinstance(stmt, ast.Try):
                    metrics.has_try_catch = True

                # Check returns
                if isinstance(stmt, ast.Return):
                    if isinstance(stmt.value, ast.Constant):
                        metrics.returns_constant = True

                # Check pass / Ellipsis / NotImplemented
                if isinstance(stmt, ast.Pass):
                    self.violations.append({
                        "file_path": getattr(self, 'file_path', 'unknown'),
                        "line_number": stmt.lineno,
                        "rule_name": "EXPLICIT_PASS_DETECTED",
                        "snippet": "pass",
                        "suggestion": "Remove 'pass' and implement concrete logic.",
                        "severity": "ERROR"
                    })
                elif isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant) and stmt.value.value is Ellipsis:
                    self.violations.append({
                        "file_path": getattr(self, 'file_path', 'unknown'),
                        "line_number": stmt.lineno,
                        "rule_name": "ELLIPSIS_DETECTED",
                        "snippet": "...",
                        "suggestion": "Ellipsis is forbidden. Write the actual code.",
                        "severity": "ERROR"
                    })
                elif isinstance(stmt, ast.Raise):
                    if isinstance(stmt.exc, ast.Call) and getattr(stmt.exc.func, 'id', '') == 'NotImplementedError':
                        self.violations.append({
                            "file_path": getattr(self, 'file_path', 'unknown'),
                            "line_number": stmt.lineno,
                            "rule_name": "NOT_IMPLEMENTED_ERROR",
                            "snippet": "raise NotImplementedError",
                            "suggestion": "Implement the function instead of raising NotImplementedError.",
                            "severity": "ERROR"
                        })

                # Check if it's just printing
                if isinstance(stmt, ast.Call):
                    if isinstance(stmt.func, ast.Name) and stmt.func.id in ['print', 'Logger', 'logging']:
                        print_count += 1
                    elif isinstance(stmt.func, ast.Attribute) and stmt.func.attr in ['info', 'log', 'debug', 'error', 'warn']:
                        print_count += 1

            if len(statements) > 0 and (print_count == len(statements) or (print_count == len(statements)-1 and metrics.returns_constant)):
                metrics.only_prints = True

        # Run Mock Heuristics
        mock_reason = MockDetector.evaluate(metrics, getattr(self, 'file_path', 'unknown'))
        if mock_reason:
            self.violations.append({
                "file_path": getattr(self, 'file_path', 'unknown'),
                "line_number": node.lineno,
                "rule_name": "MOCK_IMPLEMENTATION_DETECTED",
                "snippet": f"def {metrics.name}(...): [Trivial Body]",
                "suggestion": mock_reason,
                "severity": "ERROR"
            })

# ==============================================================================
# C-Family Generic Structural Analyzer (Lexer + Block Scope)
# Supports C, C++, Java, JS, TS, Go
# ==============================================================================

class GenericCAnalyzer:
    """
    A structural parser that understands curly braces `{}` and basic control flow
    to detect mock implementations in non-Python languages.
    """
    
    def __init__(self):
        self.violations: List[Dict[str, Any]] = []

    def analyze_source(self, file_path: str, source_code: str) -> List[Dict[str, Any]]:
        # Remove comments and strings for structural analysis using simple regex
        # This is a safe approximation for block counting
        code = re.sub(r'//.*', '', source_code)
        code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
        code = re.sub(r'"(?:\\.|[^"\\])*"', '""', code)
        code = re.sub(r"'(?:\\.|[^'\\])*'", "''", code)

        lines = code.splitlines()
        
        # State machine for block tracking
        brace_depth = 0
        current_func_name = ""
        current_func_start = 0
        statement_count = 0
        complexity = 1
        has_loops = False
        print_count = 0
        
        # Regexes for structure
        func_def_pattern = re.compile(r'([a-zA-Z_]\w*)\s*\([^)]*\)\s*\{')
        branch_pattern = re.compile(r'\b(if|else if|case|catch)\b')
        loop_pattern = re.compile(r'\b(for|while|do)\b')
        print_pattern = re.compile(r'\b(printf|console\.log|fmt\.Print|fmt\.Println|System\.out\.println)\b')

        for i, line in enumerate(lines):
            line_num = i + 1
            
            # Detect function entry
            if brace_depth == 0:
                match = func_def_pattern.search(line)
                if match:
                    current_func_name = match.group(1)
                    current_func_start = line_num
                    statement_count = 0
                    complexity = 1
                    has_loops = False
                    print_count = 0

            # Count braces
            for char in line:
                if char == '{':
                    brace_depth += 1
                elif char == '}':
                    brace_depth -= 1
                    
                    # Function exit
                    if brace_depth == 0 and current_func_name:
                        # Evaluate collected metrics
                        metrics = FunctionMetrics(
                            name=current_func_name,
                            start_line=current_func_start,
                            end_line=line_num,
                            cyclomatic_complexity=complexity,
                            statement_count=statement_count,
                            has_loops=has_loops,
                            has_try_catch=False,
                            is_empty=statement_count == 0,
                            returns_constant=False, # Hard to perfectly statically analyze in raw text, assume false
                            only_prints=(print_count >= statement_count and statement_count > 0)
                        )
                        
                        mock_reason = MockDetector.evaluate(metrics, file_path)
                        if mock_reason:
                            self.violations.append({
                                "file_path": file_path,
                                "line_number": current_func_start,
                                "rule_name": "MOCK_IMPLEMENTATION_DETECTED",
                                "snippet": f"{current_func_name}() {{ ... }}",
                                "suggestion": mock_reason + " Expand into complete production logic.",
                                "severity": "ERROR"
                            })
                            
                        current_func_name = ""

            # If inside a function block, count statements and complexity
            if brace_depth > 0:
                if ';' in line:
                    statement_count += line.count(';')
                if branch_pattern.search(line):
                    complexity += 1
                if loop_pattern.search(line):
                    complexity += 1
                    has_loops = True
                if print_pattern.search(line):
                    print_count += 1

                # Go specific empty error handler: if err != nil {}
                if 'if err != nil' in line and '{' in line and '}' in line:
                    if re.search(r'\{\s*\}', line):
                        self.violations.append({
                            "file_path": file_path,
                            "line_number": line_num,
                            "rule_name": "EMPTY_ERROR_HANDLER_GO",
                            "snippet": line.strip(),
                            "suggestion": "Go error handler 'if err != nil' is empty. Handle the error.",
                            "severity": "ERROR"
                        })

                # Empty Catch blocks
                if re.search(r'catch\s*\([^)]*\)\s*\{\s*\}', line):
                    self.violations.append({
                        "file_path": file_path,
                        "line_number": line_num,
                        "rule_name": "EMPTY_CATCH_BLOCK",
                        "snippet": line.strip(),
                        "suggestion": "Empty catch block detected. Handle exceptions explicitly.",
                        "severity": "ERROR"
                    })

        return self.violations

# ==============================================================================
# Analyzer Gateway
# ==============================================================================

class HardcoreAnalyzer:
    def analyze(self, file_path: str, source_code: str, file_suffix: str) -> List[Dict[str, Any]]:
        violations = []
        
        # 1. Python specific deep AST parsing
        if file_suffix == '.py':
            py_analyzer = PythonAnalyzer()
            violations.extend(py_analyzer.analyze_source(file_path, source_code))
            
        # 2. C-Family structural parsing (C, C++, Java, JS, TS, Go)
        elif file_suffix in ['.c', '.cpp', '.h', '.hpp', '.java', '.js', '.ts', '.go', '.cs', '.php']:
            c_analyzer = GenericCAnalyzer()
            violations.extend(c_analyzer.analyze_source(file_path, source_code))
            
        return violations
