"""Load aggregated month tables into Postgres with idempotent upserts.

Re-running the same month is safe: each month's rows are deleted and re-inserted
inside one transaction (a simple, robust "delete + insert" upsert by year_month).
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from .config import DATABASE_URL

_SCHEMA_PATH = Path(__file__).with_name("schema.sql")

# Only these tables are written by the pipeline (plus etl_runs bookkeeping).
_FACT_TABLES = [
    "fact_national_month",
    "fact_chapter_month",
    "fact_section_month",
    "fact_region_month",
    "fact_icb_month",
    "fact_chemical_month",
    "fact_prepclass_month",
]


def get_engine() -> Engine:
    return create_engine(DATABASE_URL, pool_pre_ping=True)


def init_schema(engine: Engine) -> None:
    """Create all tables/indexes if they do not exist."""
    raw = _SCHEMA_PATH.read_text()
    # Strip line comments first (they can contain ';', which would break split).
    no_comments = "\n".join(line.split("--", 1)[0] for line in raw.splitlines())
    with engine.begin() as conn:
        for statement in no_comments.split(";"):
            if statement.strip():
                conn.execute(text(statement))


def load_month(engine: Engine, tables: dict[str, pd.DataFrame]) -> None:
    """Delete + insert every fact table for one month in a single transaction."""
    meta = tables["_meta"]
    year_month = meta["year_month"]

    with engine.begin() as conn:
        for name in _FACT_TABLES:
            df = tables[name]
            conn.execute(
                text(f"DELETE FROM {name} WHERE year_month = :ym"),
                {"ym": year_month},
            )
            df.to_sql(name, conn, if_exists="append", index=False, method="multi", chunksize=1000)

        conn.execute(text("DELETE FROM etl_runs WHERE year_month = :ym"), {"ym": year_month})
        conn.execute(
            text(
                "INSERT INTO etl_runs (year_month, rows_processed, seconds, source_url) "
                "VALUES (:ym, :rows, :secs, :url)"
            ),
            {
                "ym": year_month,
                "rows": meta["rows_processed"],
                "secs": meta["seconds"],
                "url": meta["source_url"],
            },
        )


def loaded_months(engine: Engine) -> set[int]:
    """Which months are already in the warehouse."""
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT year_month FROM etl_runs")).fetchall()
    return {r[0] for r in rows}
