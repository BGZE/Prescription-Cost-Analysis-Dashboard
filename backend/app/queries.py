"""Analytical queries over the pre-aggregated warehouse tables.

Every function returns plain dicts/lists ready to be serialised to JSON.
`year_month` is an integer like 202605; we expose it as an int plus a friendly
"YYYY-MM" label for the frontend.
"""
from __future__ import annotations

from .db import fetch_all, fetch_one


def _label(ym: int) -> str:
    s = str(ym)
    return f"{s[:4]}-{s[4:]}"


# ---------------------------------------------------------------------------
# Metadata
# ---------------------------------------------------------------------------
def available_months() -> list[int]:
    rows = fetch_all("SELECT year_month FROM fact_national_month ORDER BY year_month")
    return [r["year_month"] for r in rows]


def latest_month() -> int | None:
    row = fetch_one("SELECT max(year_month) AS m FROM fact_national_month")
    return row["m"] if row else None


def resolve_month(month: str | int | None) -> int | None:
    """Accept 'latest', an int, or None -> concrete year_month that exists."""
    months = available_months()
    if not months:
        return None
    if month in (None, "latest", ""):
        return months[-1]
    ym = int(month)
    return ym if ym in months else months[-1]


def meta() -> dict:
    months = available_months()
    run = fetch_one("SELECT max(loaded_at) AS updated FROM etl_runs")
    return {
        "months": [{"year_month": m, "label": _label(m)} for m in months],
        "latest_month": months[-1] if months else None,
        "earliest_month": months[0] if months else None,
        "month_count": len(months),
        "last_updated": run["updated"].isoformat() if run and run["updated"] else None,
    }


# ---------------------------------------------------------------------------
# Overview KPIs + national trend
# ---------------------------------------------------------------------------
def _national(ym: int) -> dict | None:
    return fetch_one(
        "SELECT year_month, nic, items, quantity, cost_per_item "
        "FROM fact_national_month WHERE year_month = :ym",
        ym=ym,
    )


def _pct(cur: float, prev: float | None) -> float | None:
    if prev in (None, 0):
        return None
    return round((float(cur) - float(prev)) / float(prev) * 100, 2)


def overview(ym: int) -> dict:
    cur = _national(ym)
    if not cur:
        return {}
    months = available_months()
    idx = months.index(ym)
    prev = _national(months[idx - 1]) if idx > 0 else None
    year_ago_ym = ym - 100  # same month, previous year
    year_ago = _national(year_ago_ym) if year_ago_ym in months else None

    def kpi(field):
        return {
            "value": float(cur[field]),
            "mom_pct": _pct(cur[field], prev[field]) if prev else None,
            "yoy_pct": _pct(cur[field], year_ago[field]) if year_ago else None,
        }

    return {
        "year_month": ym,
        "label": _label(ym),
        "nic": kpi("nic"),
        "items": kpi("items"),
        "cost_per_item": kpi("cost_per_item"),
        "quantity": kpi("quantity"),
    }


def national_trend() -> list[dict]:
    rows = fetch_all(
        "SELECT year_month, nic, items, quantity, cost_per_item "
        "FROM fact_national_month ORDER BY year_month"
    )
    for r in rows:
        r["label"] = _label(r["year_month"])
        r["nic"] = float(r["nic"])
        r["cost_per_item"] = float(r["cost_per_item"])
    return rows


# ---------------------------------------------------------------------------
# Therapeutic breakdown (BNF chapter / section)
# ---------------------------------------------------------------------------
def therapeutic(ym: int, level: str, limit: int = 25) -> list[dict]:
    if level == "section":
        sql = (
            "SELECT bnf_section_code AS code, bnf_section AS name, "
            "bnf_chapter AS parent, nic, items, quantity "
            "FROM fact_section_month WHERE year_month = :ym "
            "ORDER BY nic DESC LIMIT :limit"
        )
    else:  # chapter
        sql = (
            "SELECT bnf_chapter_code AS code, bnf_chapter AS name, "
            "NULL AS parent, nic, items, quantity "
            "FROM fact_chapter_month WHERE year_month = :ym "
            "ORDER BY nic DESC LIMIT :limit"
        )
    rows = fetch_all(sql, ym=ym, limit=limit)
    for r in rows:
        r["nic"] = float(r["nic"])
    return rows


# ---------------------------------------------------------------------------
# Geography (region / ICB)
# ---------------------------------------------------------------------------
def geography(ym: int, level: str) -> list[dict]:
    if level == "icb":
        sql = (
            "SELECT icb_code AS code, icb_name AS name, region_name AS parent, "
            "nic, items, quantity FROM fact_icb_month WHERE year_month = :ym "
            "ORDER BY nic DESC"
        )
    else:  # region
        sql = (
            "SELECT region_code AS code, region_name AS name, NULL AS parent, "
            "nic, items, quantity FROM fact_region_month WHERE year_month = :ym "
            "ORDER BY nic DESC"
        )
    rows = fetch_all(sql, ym=ym)
    for r in rows:
        r["nic"] = float(r["nic"])
        r["cost_per_item"] = round(r["nic"] / r["items"], 4) if r["items"] else 0
    return rows


# ---------------------------------------------------------------------------
# Top drugs (BNF chemical substance)
# ---------------------------------------------------------------------------
def top_drugs(ym: int, limit: int = 20) -> list[dict]:
    rows = fetch_all(
        "SELECT bnf_chemical_substance_code AS code, bnf_chemical_substance AS name, "
        "bnf_chapter AS chapter, nic, items, quantity "
        "FROM fact_chemical_month WHERE year_month = :ym "
        "ORDER BY nic DESC LIMIT :limit",
        ym=ym,
        limit=limit,
    )
    for r in rows:
        r["nic"] = float(r["nic"])
        r["cost_per_item"] = round(r["nic"] / r["items"], 4) if r["items"] else 0
    return rows


def drug_trend(code: str) -> list[dict]:
    rows = fetch_all(
        "SELECT year_month, bnf_chemical_substance AS name, nic, items "
        "FROM fact_chemical_month WHERE bnf_chemical_substance_code = :code "
        "ORDER BY year_month",
        code=code,
    )
    for r in rows:
        r["label"] = _label(r["year_month"])
        r["nic"] = float(r["nic"])
        r["cost_per_item"] = round(r["nic"] / r["items"], 4) if r["items"] else 0
    return rows


def substances() -> list[dict]:
    """Distinct chemical substances across all months, for the search box."""
    return fetch_all(
        "SELECT bnf_chemical_substance_code AS code, bnf_chemical_substance AS name "
        "FROM fact_chemical_month WHERE bnf_chemical_substance IS NOT NULL "
        "GROUP BY bnf_chemical_substance_code, bnf_chemical_substance "
        "ORDER BY bnf_chemical_substance"
    )


# ---------------------------------------------------------------------------
# Generic vs branded (prep class)
# ---------------------------------------------------------------------------
def prep_breakdown(ym: int) -> dict:
    detail = fetch_all(
        "SELECT prep_class, prep_class_label, prep_group, nic, items, quantity "
        "FROM fact_prepclass_month WHERE year_month = :ym ORDER BY prep_class",
        ym=ym,
    )
    groups: dict[str, dict] = {}
    for r in detail:
        r["nic"] = float(r["nic"])
        g = groups.setdefault(r["prep_group"], {"prep_group": r["prep_group"], "nic": 0.0, "items": 0})
        g["nic"] += r["nic"]
        g["items"] += r["items"]
    grouped = sorted(groups.values(), key=lambda x: x["nic"], reverse=True)
    return {"groups": grouped, "classes": detail}
