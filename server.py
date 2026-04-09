"""
Server entry point - imports FastAPI app from app.py
For running with: uvicorn server.app:app
"""

from app import app

if __name__ == "__main__":
    import uvicorn
    import os
    
    port = int(os.getenv("PORT", "7860"))
    host = os.getenv("HOST", "0.0.0.0")
    
    uvicorn.run(app, host=host, port=port)
    uvicorn.run("server:app", host="0.0.0.0", port=port, log_level="info")