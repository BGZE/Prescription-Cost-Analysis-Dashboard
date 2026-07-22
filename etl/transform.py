"""Stream one monthly PCA CSV and aggregate it into compact summary tables.

The raw monthly file is ~500k rows / ~230 MB. We never hold it all in memory:
pandas reads it in chunks, we group each chunk to a handful of grains, and the
partial group results (a few thousand rows each) are combined at the end.

`aggregate_month` returns a dict of {table_name: DataFrame} ready to be loaded.
"""
from __future__ import annotations

import time
from typing import Iterator

import pandas as pd
import requests

from .config import CHUNK_SIZE, DTYPES, PREP_CLASS_LABELS, PREP_GROUP, USE_COLUMNS

# Each grain: (output table, dimension columns kept alongside the codes).
# The tuple is (group keys, extra descriptive columns carried through).
_GRAINS = {
    "fact_chapter_month": (["BNF_CHAPTER_CODE"], ["BNF_CHAPTER"]),
    "fact_section_month": (
        ["BNF_SECTION_CODE"],
        ["BNF_SECTION", "BNF_CHAPTER_CODE", "BNF_CHAPTER"],
    ),
    "fact_region_month": (["REGION_CODE"], ["REGION_NAME"]),
    "fact_icb_month": (["ICB_CODE"], ["ICB_NAME", "REGION_CODE", "REGION_NAME"]),
    "fact_chemical_month": (
        ["BNF_CHEMICAL_SUBSTANCE_CODE"],
        ["BNF_CHEMICAL_SUBSTANCE", "BNF_CHAPTER_CODE", "BNF_CHAPTER"],
    ),
    "fact_prepclass_month": (["PREP_CLASS"], []),
}

_MEASURES = {"ITEMS": "items", "TOTAL_QUANTITY": "quantity", "NIC": "nic"}


def _iter_chunks(csv_url: str) -> Iterator[pd.DataFrame]:
    resp = requests.get(csv_url, stream=True, timeout=180)
    resp.raise_for_status()
    resp.raw.decode_content = True
    yield from pd.read_csv(
        resp.raw,
        chunksize=CHUNK_SIZE,
        usecols=USE_COLUMNS,
        dtype=DTYPES,
    )
    resp.close()


def _group_chunk(chunk: pd.DataFrame, keys: list[str], extras: list[str]) -> pd.DataFrame:
    cols = keys + extras
    agg = (
        chunk.groupby(keys, dropna=False, observed=True)
        .agg(items=("ITEMS", "sum"), quantity=("TOTAL_QUANTITY", "sum"), nic=("NIC", "sum"))
        .reset_index()
    )
    # Carry the descriptive columns (they are functionally dependent on the code).
    if extras:
        lookup = chunk[cols].drop_duplicates(subset=keys)
        agg = agg.merge(lookup, on=keys, how="left")
    return agg


def _combine(parts: list[pd.DataFrame], keys: list[str], extras: list[str]) -> pd.DataFrame:
    combined = pd.concat(parts, ignore_index=True)
    grouped = (
        combined.groupby(keys, dropna=False, observed=True)
        .agg(items=("items", "sum"), quantity=("quantity", "sum"), nic=("nic", "sum"))
        .reset_index()
    )
    if extras:
        lookup = combined[keys + extras].drop_duplicates(subset=keys)
        grouped = grouped.merge(lookup, on=keys, how="left")
    return grouped


def aggregate_month(year_month: int, csv_url: str) -> dict[str, pd.DataFrame]:
    """Return all summary DataFrames for one month, plus row/timing metadata."""
    started = time.time()
    partials: dict[str, list[pd.DataFrame]] = {name: [] for name in _GRAINS}
    national = {"items": 0, "quantity": 0, "nic": 0.0}
    total_rows = 0

    for chunk in _iter_chunks(csv_url):
        total_rows += len(chunk)
        national["items"] += int(chunk["ITEMS"].sum())
        national["quantity"] += int(chunk["TOTAL_QUANTITY"].sum())
        national["nic"] += float(chunk["NIC"].sum())
        for name, (keys, extras) in _GRAINS.items():
            partials[name].append(_group_chunk(chunk, keys, extras))

    tables: dict[str, pd.DataFrame] = {}
    for name, (keys, extras) in _GRAINS.items():
        df = _combine(partials[name], keys, extras)
        df.insert(0, "year_month", year_month)
        tables[name] = _finalise(name, df)

    tables["fact_national_month"] = pd.DataFrame(
        [
            {
                "year_month": year_month,
                "nic": round(national["nic"], 2),
                "items": national["items"],
                "quantity": national["quantity"],
                "cost_per_item": round(national["nic"] / national["items"], 4)
                if national["items"]
                else 0.0,
            }
        ]
    )

    tables["_meta"] = {
        "year_month": year_month,
        "rows_processed": total_rows,
        "seconds": round(time.time() - started, 1),
        "source_url": csv_url,
    }
    return tables


def _finalise(name: str, df: pd.DataFrame) -> pd.DataFrame:
    """Rename columns to snake_case DB names and add derived fields."""
    rename = {
        "BNF_CHAPTER_CODE": "bnf_chapter_code",
        "BNF_CHAPTER": "bnf_chapter",
        "BNF_SECTION_CODE": "bnf_section_code",
        "BNF_SECTION": "bnf_section",
        "REGION_CODE": "region_code",
        "REGION_NAME": "region_name",
        "ICB_CODE": "icb_code",
        "ICB_NAME": "icb_name",
        "BNF_CHEMICAL_SUBSTANCE_CODE": "bnf_chemical_substance_code",
        "BNF_CHEMICAL_SUBSTANCE": "bnf_chemical_substance",
        "PREP_CLASS": "prep_class",
    }
    df = df.rename(columns=rename)
    df["nic"] = df["nic"].round(2)

    if name == "fact_prepclass_month":
        df["prep_class"] = df["prep_class"].fillna("00")
        df["prep_class_label"] = df["prep_class"].map(PREP_CLASS_LABELS).fillna("Unknown")
        df["prep_group"] = df["prep_class"].map(PREP_GROUP).fillna("Other")

    # Tidy up NaN text so Postgres gets clean values.
    for col in df.select_dtypes(include=["string", "object"]).columns:
        df[col] = df[col].where(df[col].notna(), None)
    return df
