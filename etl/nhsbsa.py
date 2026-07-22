"""Thin client for the NHSBSA Open Data Portal (CKAN API).

We only need two things from the portal:
  1. The list of monthly PCA resources (each is one CSV file for one month).
  2. The direct CSV download URL for a given month.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

import requests

from .config import NHSBSA_API_BASE, PCA_MONTHLY_DATASET


@dataclass(frozen=True)
class MonthlyResource:
    """One month of PCA data available on the portal."""

    year_month: int  # e.g. 202605
    name: str  # e.g. "PCA_202605"
    csv_url: str
    size_bytes: int | None = None


_YM_RE = re.compile(r"PCA_(\d{6})$")


def _get(path: str, **params) -> dict:
    resp = requests.get(f"{NHSBSA_API_BASE}/{path}", params=params, timeout=60)
    resp.raise_for_status()
    payload = resp.json()
    if not payload.get("success"):
        raise RuntimeError(f"NHSBSA API error for {path}: {payload}")
    return payload["result"]


def list_monthly_resources() -> list[MonthlyResource]:
    """Return every monthly PCA resource that has a real CSV, newest first."""
    result = _get("package_show", id=PCA_MONTHLY_DATASET)
    resources: list[MonthlyResource] = []
    for res in result.get("resources", []):
        match = _YM_RE.match(res.get("name", ""))
        if not match:
            continue
        if (res.get("format") or "").upper() != "CSV":
            continue
        url = res.get("url")
        if not url:
            continue
        resources.append(
            MonthlyResource(
                year_month=int(match.group(1)),
                name=res["name"],
                csv_url=url,
                size_bytes=res.get("size"),
            )
        )
    resources.sort(key=lambda r: r.year_month, reverse=True)
    return resources


def latest_available_months(limit: int) -> list[MonthlyResource]:
    """Newest `limit` monthly resources, oldest-first for stable load order."""
    newest = list_monthly_resources()[:limit]
    return sorted(newest, key=lambda r: r.year_month)
