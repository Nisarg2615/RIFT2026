"""
PharmaGuard — FastAPI application entrypoint.

Run with:
    uvicorn src.main:app --reload --port 8000

Routes
──────
POST /api/analyze   → VCF upload + drug list → PharmaGuardResult[]
GET  /api/health    → liveness probe
GET  /               → serves frontend/index.html
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from src.api.routes.analyze import router as analyze_router
from src.core.config import get_settings

# ── Logging ──────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("pharmaguard")

# ── Settings ─────────────────────────────────────────────────────────────
settings = get_settings()

# ── App ──────────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.app_name,
    description="Pharmacogenomic Risk Prediction System",
    version=settings.app_version,
)

# ── CORS ─────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ──────────────────────────────────────────────────────────────
app.include_router(analyze_router)

# ── Health check ─────────────────────────────────────────────────────────

@app.get("/api/health", tags=["infra"])
async def health():
    """Liveness probe + configuration summary."""
    return {
        "status": "ok",
        "gemini_configured": bool(settings.gemini_api_key),
        "supported_drugs": settings.supported_drugs,
        "supported_genes": settings.supported_genes,
    }


# ── Serve frontend ──────────────────────────────────────────────────────
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
FRONTEND_BUILD_DIR = FRONTEND_DIR / "build"


@app.get("/", include_in_schema=False)
async def serve_index():
    """Serve the React SPA index.html."""
    # Try React build first
    if FRONTEND_BUILD_DIR.exists():
        index = FRONTEND_BUILD_DIR / "index.html"
        if index.exists():
            return FileResponse(str(index))
    
    # Fallback to static frontend
    index = FRONTEND_DIR / "index.html"
    if index.exists():
        return FileResponse(str(index))
    
    return JSONResponse(
        {"detail": "Frontend not found. Run 'npm run build' in /frontend."},
        status_code=404,
    )


# Mount static files from React build
if FRONTEND_BUILD_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_BUILD_DIR / "static")), name="static")
elif FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


# SPA fallback: serve index.html for all unmatched routes
@app.get("/{full_path:path}", include_in_schema=False)
async def serve_spa(full_path: str):
    """SPA fallback - serve index.html for all unmatched routes."""
    if full_path.startswith("api/"):
        return JSONResponse({"detail": "Not found"}, status_code=404)
    
    if FRONTEND_BUILD_DIR.exists():
        index = FRONTEND_BUILD_DIR / "index.html"
        if index.exists():
            return FileResponse(str(index))
    
    return JSONResponse({"detail": "Frontend not found"}, status_code=404)
