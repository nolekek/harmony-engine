"""
Main FastAPI server application for Brigade Harmony Engine.
Serves REST API and compiled SPA static assets.
"""

from __future__ import annotations

import logging
import uuid
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.api import router as api_router

# Configure centralized structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("backend.main")

app = FastAPI(
    title="Brigade Harmony Engine Web API",
    description="REST API Gateway for Classical Four-Part Harmony and Voice-Leading Validation",
    version="1.0.0",
)

MAX_REQUEST_BYTES = 2 * 1024 * 1024  # 2 MB body limit (ReDoS / slowloris guard)


@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    """Attaches a request id to every response and rejects oversized bodies."""
    request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
    request.state.request_id = request_id

    content_length = request.headers.get("content-length")
    if content_length is not None:
        try:
            if int(content_length) > MAX_REQUEST_BYTES:
                return JSONResponse(
                    status_code=413,
                    content={
                        "detail": "Тело запроса слишком большое (лимит 2 МБ).",
                        "request_id": request_id,
                    },
                    headers={"X-Request-ID": request_id},
                )
        except ValueError:
            return JSONResponse(
                status_code=400,
                content={"detail": "Неверный заголовок Content-Length.", "request_id": request_id},
                headers={"X-Request-ID": request_id},
            )

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    for err in exc.errors():
        if err.get("type") == "too_short" and err.get("loc") == ("body", "melody"):
            return JSONResponse(
                status_code=400,
                content={"detail": "Мелодия не может быть пустой."},
            )
    return await request_validation_exception_handler(request, exc)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """
    Global unhandled exception handler.
    Logs full traceback with unique error_id and returns structured JSON 500.
    Preserves Starlette / FastAPI HTTPException status codes and payloads.
    """
    if isinstance(exc, StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers=getattr(exc, "headers", None),
        )

    error_id = str(uuid.uuid4())
    request_id = getattr(request.state, "request_id", None) or error_id
    logger.exception(
        "Unhandled exception [error_id=%s][request_id=%s] on %s %s: %s",
        error_id,
        request_id,
        request.method,
        request.url.path,
        exc,
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error", "error_id": error_id},
        headers={"X-Request-ID": request_id},
    )


# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:8000",
        "http://localhost:8000",
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes first
app.include_router(api_router)


@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "brigade-harmony-web", "version": "1.0.0"}


# Fallback for any unknown /api/* endpoints to ensure JSON 404 response
@app.api_route("/api/{full_path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
async def api_unknown_fallback(full_path: str):
    return JSONResponse(status_code=404, content={"detail": "Not Found"})


# Static files setup (serving frontend/dist)
DIST_DIR = Path(__file__).resolve().parents[1] / "frontend" / "dist"

if DIST_DIR.exists():
    assets_dir = DIST_DIR / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Don't intercept API routes: return JSON 404
        if full_path.startswith("api/") or full_path == "api":
            return JSONResponse(status_code=404, content={"detail": "Not Found"})

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
