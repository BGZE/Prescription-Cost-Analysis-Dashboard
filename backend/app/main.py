"""FastAPI application entrypoint.

Exposes a small read-only REST API over the aggregated PCA warehouse and, in
production, serves the built React frontend from ../frontend/dist.
"""
from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from . import queries

app = FastAPI(
    title="Prescription Cost Analysis API",
    description="Live NHS England prescription cost & volume data, aggregated from NHSBSA open data.",
    version="1.0.0",
)

_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _origins if o.strip()] or ["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# API routes
# ---------------------------------------------------------------------------
@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/meta")
def get_meta():
    return queries.meta()


def _require_month(month: str | None) -> int:
    ym = queries.resolve_month(month)
    if ym is None:
        raise HTTPException(status_code=503, detail="No data loaded yet. Run the ETL pipeline.")
    return ym


@app.get("/api/overview")
def get_overview(month: str | None = Query(None, description="'latest' or YYYYMM")):
    return queries.overview(_require_month(month))


@app.get("/api/trend")
def get_trend():
    return queries.national_trend()


@app.get("/api/therapeutic")
def get_therapeutic(
    month: str | None = None,
    level: str = Query("chapter", pattern="^(chapter|section)$"),
    limit: int = Query(25, ge=1, le=200),
):
    return queries.therapeutic(_require_month(month), level, limit)


@app.get("/api/geography")
def get_geography(
    month: str | None = None,
    level: str = Query("region", pattern="^(region|icb)$"),
):
    return queries.geography(_require_month(month), level)


@app.get("/api/drugs")
def get_drugs(month: str | None = None, limit: int = Query(20, ge=1, le=100)):
    return queries.top_drugs(_require_month(month), limit)


@app.get("/api/drugs/{code}/trend")
def get_drug_trend(code: str):
    rows = queries.drug_trend(code)
    if not rows:
        raise HTTPException(status_code=404, detail="Unknown chemical substance code")
    return rows


@app.get("/api/prepclass")
def get_prepclass(month: str | None = None):
    return queries.prep_breakdown(_require_month(month))


# ---------------------------------------------------------------------------
# Serve the built frontend (production). In dev, Vite serves it on :5173.
# ---------------------------------------------------------------------------
_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if _DIST.is_dir():
    app.mount("/assets", StaticFiles(directory=_DIST / "assets"), name="assets")

    @app.get("/")
    def index():
        return FileResponse(_DIST / "index.html")

    @app.get("/{full_path:path}")
    def spa_fallback(full_path: str):
        # Let the SPA router handle unknown non-API paths.
        candidate = _DIST / full_path
        if candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(_DIST / "index.html")
