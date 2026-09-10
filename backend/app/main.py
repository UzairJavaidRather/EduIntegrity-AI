"""
EduIntegrity AI — FastAPI Application Entry Point

This is the main application file. It:
  - Creates the FastAPI application instance
  - Configures CORS (Cross-Origin Resource Sharing) so the Next.js
    frontend can make requests to this API
  - Registers all API routers (added in later phases)
  - Provides a health-check endpoint

IMPORTANT: This file should remain thin. Business logic belongs in
services/, route handlers belong in api/, database models in models/.
"""

import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables from .env file into os.environ
# This must happen before we read any os.environ values
load_dotenv()

# ─── Application instance ────────────────────────────────────────────────────

app = FastAPI(
    title="EduIntegrity AI API",
    description=(
        "Academic integrity analysis platform. "
        "Provides explainable, evidence-based risk indicators for instructor review. "
        "This system does not automatically accuse students — "
        "the instructor makes the final decision."
    ),
    version="0.1.0",
    docs_url="/docs",       # Interactive Swagger UI at /docs
    redoc_url="/redoc",     # Alternative docs at /redoc
)

# ─── CORS middleware ──────────────────────────────────────────────────────────
# CORS controls which frontend origins are allowed to make requests to this API.
# In development we allow localhost:3000 (Next.js dev server).
# In production this should be locked down to your actual domain.

_cors_origins_raw = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
_cors_origins = [origin.strip() for origin in _cors_origins_raw.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Routes ──────────────────────────────────────────────────────────────────
# Routers are imported and registered here as each phase is completed.
# The prefix /api/v1 is applied to every route in each router.

from app.api import extraction  # Phase 2 — text extraction
from app.api import analysis    # MVP — full pipeline

app.include_router(extraction.router, prefix="/api/v1")
app.include_router(analysis.router,   prefix="/api/v1")


# ─── Health check endpoints ───────────────────────────────────────────────────

@app.get("/", tags=["Health"])
def root():
    """
    Root endpoint. Confirms the API is running.
    Used by load balancers and deployment health checks.
    """
    return {
        "service": "EduIntegrity AI API",
        "status": "running",
        "version": "0.1.0",
        "message": (
            "This system provides advisory integrity indicators only. "
            "The instructor makes the final academic integrity decision."
        ),
    }


@app.get("/health", tags=["Health"])
def health_check():
    """
    Detailed health check. Returns service status.
    In later phases this can check database connectivity and model availability.
    """
    return {
        "status": "healthy",
        "api": "ok",
        # Future phases will add:
        # "database": "ok" | "error",
        # "embedding_model": "loaded" | "not_loaded",
        # "granite": "reachable" | "not_configured",
    }
