import uvicorn
import os
import sys

# Add the current directory to sys.path to ensure src can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("Starting DB-LLM Server...")
    print("Backend API: http://localhost:8000")
    print("Frontend Web: http://localhost:8000")
    uvicorn.run("src.api:app", host="0.0.0.0", port=8000, reload=True)
