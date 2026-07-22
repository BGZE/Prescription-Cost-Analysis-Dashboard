"""Database engine + a tiny query helper.

The API is read-only over the pre-aggregated warehouse tables, so we use
SQLAlchemy Core with parameterised text queries rather than an ORM.
"""
from __future__ import annotations

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://pca:pca@localhost:5432/pca",
)

# pool_pre_ping avoids stale connections after Render/Supabase idle timeouts.
_engine: Engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_size=5, max_overflow=5)


def fetch_all(sql: str, **params) -> list[dict]:
    """Run a query and return a list of plain dicts (JSON-serialisable)."""
    with _engine.connect() as conn:
        rows = conn.execute(text(sql), params).mappings().all()
    return [dict(r) for r in rows]


def fetch_one(sql: str, **params) -> dict | None:
    with _engine.connect() as conn:
        row = conn.execute(text(sql), params).mappings().first()
    return dict(row) if row else None
