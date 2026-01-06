"""
Example usage of the Python Playground API.

This script demonstrates how to interact with the playground API.
Run this after starting the services with docker-compose.
"""

import requests
import json

# Base URL - adjust if your services are running on different ports
BASE_URL = "http://localhost:5000/api"  # Via Nginx
# Alternative: BASE_URL = "http://localhost:5001"  # Direct FastAPI access

def execute_code(code: str, language: str = "python", input_data: str = None):
    """Execute code through the playground API."""
    url = f"{BASE_URL}/execute"
    payload = {
        "code": code,
        "language": language,
        "input_data": input_data
    }
    
    response = requests.post(url, json=payload)
    return response.json()


def save_code(code: str, filename: str):
    """Save code to persistent storage."""
    url = f"{BASE_URL}/save"
    params = {
        "code": code,
        "filename": filename
    }
    
    response = requests.post(url, params=params)
    return response.json()


def load_code(filename: str):
    """Load code from persistent storage."""
    url = f"{BASE_URL}/load/{filename}"
    
    response = requests.get(url)
    return response.json()


def list_files():
    """List all saved files."""
    url = f"{BASE_URL}/files"
    
    response = requests.get(url)
    return response.json()


def delete_file(filename: str):
    """Delete a saved file."""
    url = f"{BASE_URL}/delete/{filename}"
    
    response = requests.delete(url)
    return response.json()


if __name__ == "__main__":
    # Example 1: Simple code execution
    print("Example 1: Simple code execution")
    result = execute_code("print('Hello, World!')")
    print(json.dumps(result, indent=2))
    print()
    
    # Example 2: Code with calculations
    print("Example 2: Code with calculations")
    code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

for i in range(10):
    print(f"fib({i}) = {fibonacci(i)}")
"""
    result = execute_code(code)
    print(json.dumps(result, indent=2))
    print()
    
    # Example 3: Code with input
    print("Example 3: Code with input (simulated)")
    code = """
import sys
data = sys.stdin.read().strip()
print(f"Received: {data}")
print(f"Length: {len(data)}")
"""
    result = execute_code(code, input_data="Hello from input!")
    print(json.dumps(result, indent=2))
    print()
    
    # Example 4: Save and load code
    print("Example 4: Save and load code")
    test_code = "print('This is saved code!')"
    save_result = save_code(test_code, "test_file.py")
    print(f"Save result: {save_result}")
    
    load_result = load_code("test_file.py")
    print(f"Load result: {load_result}")
    print()
    
    # Example 5: List all saved files
    print("Example 5: List all saved files")
    files_result = list_files()
    print(json.dumps(files_result, indent=2))
    print()
    
    # Example 6: Delete a file
    print("Example 6: Delete a file")
    delete_result = delete_file("test_file.py")
    print(f"Delete result: {delete_result}")
    
    # List files again to confirm deletion
    files_result = list_files()
    print(f"Files after deletion: {files_result['count']} files")
    print()

