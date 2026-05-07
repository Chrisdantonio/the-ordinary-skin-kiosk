"""
PyInstaller entry point — runs the FastAPI app via uvicorn on localhost:8000.
We import `app` directly (not as a string) so PyInstaller can trace the dependency
and so uvicorn does not try to dynamically resolve the module at runtime.
"""
import uvicorn
from main import app  # noqa: F401 — explicit import pulls main into the bundle

if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=8000, log_level='info')
