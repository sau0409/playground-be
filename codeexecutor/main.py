import subprocess
import tempfile
import os
import time
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import resource
import signal

app = FastAPI(title="Code Executor Service", version="1.0.0")

# Execution limits
MAX_EXECUTION_TIME = 10  # seconds
MAX_MEMORY_MB = 128  # MB
MAX_OUTPUT_SIZE = 1024 * 1024  # 1MB


class ExecuteRequest(BaseModel):
    code: str
    language: str = "python"
    input_data: Optional[str] = None


class ExecuteResponse(BaseModel):
    output: str
    error: Optional[str] = None
    execution_time: Optional[float] = None


def set_resource_limits():
    """Set resource limits for subprocess execution."""
    # Limit memory (in KB)
    max_memory_kb = MAX_MEMORY_MB * 1024
    resource.setrlimit(resource.RLIMIT_AS, (max_memory_kb * 1024, max_memory_kb * 1024))
    
    # Limit CPU time
    resource.setrlimit(resource.RLIMIT_CPU, (MAX_EXECUTION_TIME, MAX_EXECUTION_TIME))


def is_simple_expression(code: str) -> bool:
    """
    Check if code is a simple expression that should auto-print its result.
    Returns True if code is a single-line expression without print/assignment/import.
    """
    lines = [line.strip() for line in code.strip().split('\n') if line.strip()]
    
    # Must be single line
    if len(lines) != 1:
        return False
    
    line = lines[0]
    
    # Skip if already has print
    if 'print(' in line.lower():
        return False
    
    # Skip if it's an assignment
    if '=' in line and not line.strip().startswith('='):
        # Check if it's a simple assignment (not == or !=)
        if ' == ' not in line and ' != ' not in line and ' <= ' not in line and ' >= ' not in line:
            return False
    
    # Skip if it's an import
    if line.startswith('import ') or line.startswith('from '):
        return False
    
    # Skip if it's a function/class definition
    if line.startswith('def ') or line.startswith('class '):
        return False
    
    # Skip if it's a control flow statement
    if any(line.startswith(keyword) for keyword in ['if ', 'for ', 'while ', 'try:', 'except', 'with ']):
        return False
    
    # Skip if it's a return/yield/break/continue
    if any(line.startswith(keyword) for keyword in ['return', 'yield', 'break', 'continue', 'pass', 'raise']):
        return False
    
    # It's likely a simple expression
    return True


def is_expression_line(line: str) -> bool:
    """
    Check if a line is an expression that should have its result printed.
    Returns True if the line is a function call, arithmetic operation, or other expression.
    """
    line = line.strip()
    
    # Skip empty lines
    if not line:
        return False
    
    # Skip if already has print
    if 'print(' in line.lower():
        return False
    
    # Skip if it's an assignment (but allow ==, !=, etc. and keyword arguments in function calls)
    # Check for assignment pattern: identifier = (not ==, !=, <=, >=, and not inside function call)
    if '=' in line:
        # Check for comparison operators first
        if any(op in line for op in [' == ', ' != ', ' <= ', ' >= ', '==', '!=', '<=', '>=']):
            pass  # It's a comparison, not an assignment
        else:
            # Check if it looks like an assignment (variable = value)
            # Simple heuristic: if there's a space before = and it's not inside parentheses (function call)
            import re
            # Pattern: word characters, then optional spaces, then = (but not ==)
            assignment_pattern = r'\w+\s*='
            if re.search(assignment_pattern, line) and '(' not in line.split('=')[0]:
                return False
    
    # Skip if it's an import
    if line.startswith('import ') or line.startswith('from '):
        return False
    
    # Skip if it's a function/class definition
    if line.startswith('def ') or line.startswith('class '):
        return False
    
    # Skip if it's a control flow statement
    if any(line.startswith(keyword) for keyword in ['if ', 'for ', 'while ', 'try:', 'except', 'with ', 'else:', 'elif ']):
        return False
    
    # Skip if it's a return/yield/break/continue
    if any(line.startswith(keyword) for keyword in ['return', 'yield', 'break', 'continue', 'pass', 'raise']):
        return False
    
    # It's likely an expression (function call, arithmetic, etc.)
    return True


def prepare_code_for_execution(code: str) -> str:
    """
    Prepare code for execution. If the last line is an expression, wrap it to print the result.
    Handles both single-line and multi-line code.
    """
    lines = [line.rstrip() for line in code.rstrip().split('\n')]
    non_empty_lines = [line.strip() for line in lines if line.strip()]
    
    if not non_empty_lines:
        return code
    
    # Check if it's a single simple expression
    if is_simple_expression(code):
        return f"_result = {code}\nprint(_result)"
    
    # Check if the last non-empty line is an expression that should be printed
    last_line_stripped = non_empty_lines[-1]
    
    # Find the index of the last non-empty line in the original lines
    last_non_empty_idx = None
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].strip():
            last_non_empty_idx = i
            break
    
    if last_non_empty_idx is None:
        return code
    
    original_last_line = lines[last_non_empty_idx]
    
    if is_expression_line(last_line_stripped):
        # Find the indentation of the last line
        indent = len(original_last_line) - len(original_last_line.lstrip())
        indent_str = ' ' * indent
        
        # Replace the last non-empty line with wrapped version
        # Keep everything before it, then add the wrapped expression
        code_before_last = '\n'.join(lines[:last_non_empty_idx])
        wrapped_expression = f"{indent_str}_result = {last_line_stripped}\n{indent_str}print(_result)"
        
        if code_before_last.strip():
            return f"{code_before_last}\n{wrapped_expression}"
        else:
            return wrapped_expression
    
    return code


def execute_python_code(code: str, input_data: Optional[str] = None) -> tuple[str, Optional[str], float]:
    """
    Execute Python code safely with resource limits.
    Returns: (output, error, execution_time)
    """
    start_time = time.time()
    
    # Prepare code (auto-print simple expressions)
    prepared_code = prepare_code_for_execution(code)
    
    # Create temporary file for code
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(prepared_code)
        temp_file = f.name
    
    try:
        # Prepare input
        stdin_data = input_data.encode() if input_data else None
        
        # Execute with timeout and resource limits
        process = subprocess.Popen(
            ["python3", temp_file],
            stdin=subprocess.PIPE if input_data else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=set_resource_limits,
            text=True,
            cwd=tempfile.gettempdir(),
        )
        
        try:
            stdout, stderr = process.communicate(input=stdin_data, timeout=MAX_EXECUTION_TIME)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
            execution_time = time.time() - start_time
            return "", "Execution timeout: Code exceeded maximum execution time", execution_time
        
        execution_time = time.time() - start_time
        
        # Normalize stdout (ensure it's a string, strip trailing newlines but preserve content)
        stdout = stdout if stdout else ""
        stdout = stdout.rstrip('\n') if stdout.endswith('\n') and len(stdout) > 1 else stdout
        
        # Limit output size
        if stdout and len(stdout) > MAX_OUTPUT_SIZE:
            stdout = stdout[:MAX_OUTPUT_SIZE] + "\n... (output truncated)"
        
        if stderr:
            return stdout, stderr, execution_time
        
        return stdout, None, execution_time
        
    except Exception as e:
        execution_time = time.time() - start_time
        return "", f"Execution error: {str(e)}", execution_time
    finally:
        # Clean up temporary file
        try:
            os.unlink(temp_file)
        except:
            pass


@app.get("/")
async def root():
    return {"message": "Code Executor Service", "status": "running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.post("/execute", response_model=ExecuteResponse)
async def execute_code(request: ExecuteRequest):
    """
    Execute code in the specified language.
    Currently supports Python only.
    """
    if request.language != "python":
        raise HTTPException(
            status_code=400,
            detail=f"Language '{request.language}' is not supported yet. Only 'python' is supported."
        )
    
    # Basic security checks
    dangerous_patterns = [
        "__import__",
        "eval(",
        "exec(",
        "compile(",
        "open(",
        "file(",
        "input(",
        "raw_input(",
        "subprocess",
        "os.system",
        "os.popen",
        "import os",
        "import subprocess",
        "import sys",
    ]
    
    code_lower = request.code.lower()
    for pattern in dangerous_patterns:
        if pattern in code_lower:
            raise HTTPException(
                status_code=400,
                detail=f"Code contains restricted operations: {pattern}"
            )
    
    output, error, execution_time = execute_python_code(request.code, request.input_data)
    
    return ExecuteResponse(
        output=output,
        error=error,
        execution_time=execution_time
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

