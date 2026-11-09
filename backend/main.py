"""
Main FastAPI server application for Brigade Harmony Engine.
Serves REST API and compiled SPA static assets.
"""

from __future__ import annotations

from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from backend.api import router as api_router

app = FastAPI(
    title="Brigade Harmony Engine Web API",
    description="REST API Gateway for Classical Four-Part Harmony and Voice-Leading Validation",
    version="1.0.0",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes
app.include_router(api_router)


@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "brigade-harmony-web", "version": "1.0.0"}


# Static files setup (serving frontend/dist)
DIST_DIR = Path(__file__).resolve().parents[1] / "frontend" / "dist"

if DIST_DIR.exists():
    assets_dir = DIST_DIR / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Don't intercept API routes
        if full_path.startswith("api/"):
            return HTMLResponse(status_code=404, content="API route not found")
        
        file_path = DIST_DIR / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        
        index_file = DIST_DIR / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        
        return HTMLResponse("<h1>Frontend dist not found. Please build frontend first.</h1>")
else:
    @app.get("/")
    def serve_placeholder():
        return HTMLResponse("<h1>Brigade Harmony Backend is Running! Frontend will be served once built.</h1>")
