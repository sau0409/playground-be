# Python Playground - Backend

Backend repository for the Python Playground application - a web-based code execution platform for interviews and coding practice.

## Overview

This is a Python playground where users can write and run code on the web. The editor is simple (notepad-like) with no code completion, designed for:
- Users testing themselves for interviews
- Interviewers using the platform to test candidates

Initially supports Python only, with plans to add support for other languages.

## Architecture

The backend consists of multiple Docker containers:

- **FastAPI**: Main API service that communicates with the frontend playground
- **CodeExecutor**: Separate service responsible for safely executing user code
- **Nginx**: Reverse proxy for routing requests
- **Volume**: Persistent storage for user files

## Project Structure

```
playground-be/
├── fastapi_app/          # FastAPI main application
│   ├── main.py          # API endpoints
│   ├── Dockerfile       # FastAPI container definition
│   └── requirements.txt # Python dependencies
├── codeexecutor/        # Code execution service
│   ├── main.py          # Code execution logic
│   ├── Dockerfile       # CodeExecutor container definition
│   └── requirements.txt # Python dependencies
├── nginx/               # Nginx configuration
│   └── nginx.conf       # Reverse proxy setup
├── docker-compose.yml   # Container orchestration
└── README.md           # This file
```

## Features

- **Code Execution**: Execute Python code with resource limits (time, memory)
- **File Persistence**: Save and load user code files
- **Security**: Restricted operations to prevent malicious code execution
- **Resource Limits**: 
  - Maximum execution time: 10 seconds
  - Maximum memory: 128 MB
  - Maximum output size: 1 MB

## Getting Started

### Prerequisites

- Docker and Docker Compose installed
- Git (for cloning the repository)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd playground-be
```

2. Build and start all services:
```bash
docker-compose up --build
```

3. The services will be available at:
   - **Nginx (Main Entry Point)**: http://localhost:5000
   - **FastAPI**: http://localhost:5001
   - **CodeExecutor**: http://localhost:5002

### API Endpoints

#### FastAPI Endpoints (via Nginx at `/api/`)

- `GET /api/` - API information
- `GET /api/health` - Health check
- `POST /api/execute` - Execute code
  ```json
  {
    "code": "print('Hello, World!')",
    "language": "python",
    "input_data": null
  }
  ```
- `GET /api/files` - List all saved files
  - Returns: List of files with metadata (filename, size, modified time)
  ```json
  {
    "files": [
      {
        "filename": "my_script.py",
        "size": 1234,
        "modified": "2024-01-15T10:30:00"
      }
    ],
    "count": 1
  }
  ```
- `POST /api/save` - Save code to file
  - Parameters: `code` (string), `filename` (string)
- `GET /api/load/{filename}` - Load code from file
- `DELETE /api/delete/{filename}` - Delete a saved file

#### CodeExecutor Endpoints (via Nginx at `/executor/`)

- `GET /executor/` - Service information
- `GET /executor/health` - Health check
- `POST /executor/execute` - Execute code (internal use)

## Development

### Running Services Individually

#### FastAPI
```bash
cd fastapi_app
pip install -r requirements.txt
python main.py
# Runs on http://localhost:8000 (internal port)
```

#### CodeExecutor
```bash
cd codeexecutor
pip install -r requirements.txt
python main.py
# Runs on http://localhost:8001 (internal port)
```

### Environment Variables

- `CODE_EXECUTOR_URL`: URL of the CodeExecutor service (default: `http://codeexecutor:8001`)
- `USER_FILES_VOLUME`: Path to user files volume (default: `/app/user_files`)

## Security Considerations

The CodeExecutor service implements several security measures:

- **Restricted Operations**: Blocks dangerous operations like:
  - File I/O (`open`, `file`)
  - System calls (`os.system`, `subprocess`)
  - Code evaluation (`eval`, `exec`, `compile`)
  - Dynamic imports (`__import__`)

- **Resource Limits**:
  - CPU time limits
  - Memory limits
  - Output size limits
  - Execution timeout

- **Container Isolation**: CodeExecutor runs in a separate container with limited privileges

## Future Enhancements

- Support for additional languages (JavaScript, Java, C++, etc.)
- Enhanced security with sandboxing
- Code execution history
- User authentication and session management
- Real-time collaboration features
- Code templates and examples

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]
