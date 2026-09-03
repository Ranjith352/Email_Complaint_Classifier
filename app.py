"""
Main application launcher for the Enterprise Complaint Classifier.
Starts the modern FastAPI enterprise backend server.
"""
import uvicorn

if __name__ == "__main__":
    print("Starting Enterprise Complaint Classifier Backend (FastAPI)...")
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
