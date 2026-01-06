from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import os
from typing import Optional, List
from datetime import datetime

app = FastAPI(title="Python Playground API", version="1.0.0")

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# CodeExecutor service URL
CODE_EXECUTOR_URL = os.getenv("CODE_EXECUTOR_URL", "http://codeexecutor:8001")


class CodeRequest(BaseModel):
    code: str
    language: str = "python"
    input_data: Optional[str] = None


class CodeResponse(BaseModel):
    output: str
    error: Optional[str] = None
    execution_time: Optional[float] = None


class FileInfo(BaseModel):
    filename: str
    size: int
    modified: str


class FileListResponse(BaseModel):
    files: List[FileInfo]
    count: int


@app.get("/")
async def root():
    return {"message": "Python Playground API", "status": "running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.post("/execute", response_model=CodeResponse)
async def execute_code(request: CodeRequest):
    """
    Execute code through the CodeExecutor service.
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{CODE_EXECUTOR_URL}/execute",
                json={
                    "code": request.code,
                    "language": request.language,
                    "input_data": request.input_data,
                },
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=503,
            detail=f"CodeExecutor service unavailable: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@app.post("/save")
async def save_code(code: str, filename: str):
    """
    Save user code to persistent storage.
    """
    try:
        # Save to volume
        volume_path = os.getenv("USER_FILES_VOLUME", "/app/user_files")
        os.makedirs(volume_path, exist_ok=True)
        
        file_path = os.path.join(volume_path, filename)
        with open(file_path, "w") as f:
            f.write(code)
        
        return {"message": "File saved successfully", "filename": filename}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save file: {str(e)}"
        )


@app.get("/files", response_model=FileListResponse)
async def list_files():
    """
    List all saved files with metadata.
    """
    try:
        volume_path = os.getenv("USER_FILES_VOLUME", "/app/user_files")
        os.makedirs(volume_path, exist_ok=True)
        
        files = []
        if os.path.exists(volume_path):
            for filename in os.listdir(volume_path):
                file_path = os.path.join(volume_path, filename)
                if os.path.isfile(file_path):
                    stat = os.stat(file_path)
                    files.append(FileInfo(
                        filename=filename,
                        size=stat.st_size,
                        modified=datetime.fromtimestamp(stat.st_mtime).isoformat()
                    ))
        
        # Sort by modification time (newest first)
        files.sort(key=lambda x: x.modified, reverse=True)
        
        return FileListResponse(files=files, count=len(files))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list files: {str(e)}"
        )


@app.get("/load/{filename}")
async def load_code(filename: str):
    """
    Load user code from persistent storage.
    """
    try:
        volume_path = os.getenv("USER_FILES_VOLUME", "/app/user_files")
        file_path = os.path.join(volume_path, filename)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        with open(file_path, "r") as f:
            code = f.read()
        
        return {"code": code, "filename": filename}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load file: {str(e)}"
        )


@app.delete("/delete/{filename}")
async def delete_file(filename: str):
    """
    Delete a saved file.
    """
    try:
        volume_path = os.getenv("USER_FILES_VOLUME", "/app/user_files")
        file_path = os.path.join(volume_path, filename)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        os.remove(file_path)
        
        return {"message": "File deleted successfully", "filename": filename}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete file: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

