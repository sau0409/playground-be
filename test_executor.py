#!/usr/bin/env python3
"""
Quick test script to verify the codeexecutor logic works correctly.
"""

import sys
import os

# Add codeexecutor to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'codeexecutor'))

from main import is_simple_expression, prepare_code_for_execution, execute_python_code

def test_simple_expression():
    """Test that simple expressions are detected and executed correctly."""
    test_cases = [
        ("5+1", True, "6"),
        ("'hello'", True, "hello"),
        ("[1, 2, 3]", True, "[1, 2, 3]"),
        ("print('test')", False, None),  # Has print, shouldn't wrap
        ("x = 5", False, None),  # Assignment, shouldn't wrap
    ]
    
    print("Testing simple expression detection and execution...")
    print("-" * 60)
    
    for code, should_wrap, expected_output in test_cases:
        is_simple = is_simple_expression(code)
        prepared = prepare_code_for_execution(code)
        
        print(f"\nCode: {repr(code)}")
        print(f"  Is simple: {is_simple} (expected: {should_wrap})")
        print(f"  Prepared code:\n{prepared}")
        
        if should_wrap:
            # Execute and check output
            output, error, exec_time = execute_python_code(code)
            print(f"  Output: {repr(output)}")
            print(f"  Error: {error}")
            print(f"  Expected: {repr(expected_output)}")
            
            if expected_output and expected_output in output:
                print(f"  ✓ PASS")
            else:
                print(f"  ✗ FAIL")
        else:
            print(f"  (Not wrapped, as expected)")

if __name__ == "__main__":
    test_simple_expression()

