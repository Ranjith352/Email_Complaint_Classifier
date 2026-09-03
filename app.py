"""
Main application launcher.
Starts the modern FastAPI enterprise backend server by default,
or falls back to legacy Flask app if invoked with --legacy or --flask.
"""
import sys

if __name__ == "__main__":
    if "--legacy" in sys.argv or "--flask" in sys.argv:
        from legacy_app_flask import app
        app.run(debug=True)
    else:
        import uvicorn
        print("Starting Enterprise Complaint Classifier Backend (FastAPI)...")
        uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
