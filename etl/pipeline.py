"""Orchestrate the Prescription Cost Analysis ETL.

Usage:
    python -m etl.pipeline                 # incremental: load any new months
    python -m etl.pipeline --backfill 24   # (re)load the newest 24 months
    python -m etl.pipeline --month 202605  # load one specific month
    python -m etl.pipeline --list          # show available vs loaded months

The pipeline is safe to re-run; each month is upserted atomically.
"""
from __future__ import annotations

import argparse
import sys

from .config import BACKFILL_MONTHS
from .load import get_engine, init_schema, load_month, loaded_months
from .nhsbsa import latest_available_months, list_monthly_resources
from .transform import aggregate_month


def _log(msg: str) -> None:
    print(f"[etl] {msg}", flush=True)


def run(months_to_load, engine) -> None:
    total = len(months_to_load)
    for i, res in enumerate(months_to_load, 1):
        _log(f"({i}/{total}) {res.name}: downloading + aggregating "
             f"(~{(res.size_bytes or 0) / 1e6:.0f} MB)...")
        tables = aggregate_month(res.year_month, res.csv_url)
        meta = tables["_meta"]
        _log(f"    aggregated {meta['rows_processed']:,} rows in {meta['seconds']}s; loading...")
        load_month(engine, tables)
        _log(f"    ✓ {res.name} loaded")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="NHSBSA Prescription Cost Analysis ETL")
    parser.add_argument("--backfill", type=int, metavar="N",
                        help="reload the newest N months (default from config)")
    parser.add_argument("--month", type=int, metavar="YYYYMM",
                        help="load one specific month")
    parser.add_argument("--list", action="store_true",
                        help="list available vs already-loaded months and exit")
    args = parser.parse_args(argv)

    engine = get_engine()
    init_schema(engine)

    available = list_monthly_resources()
    if args.list:
        done = loaded_months(engine)
        _log(f"{len(available)} months available on the portal:")
        for res in available[:36]:
            mark = "✓ loaded" if res.year_month in done else "  new"
            _log(f"   {res.year_month}  {mark}")
        return 0

    if args.month:
        chosen = [r for r in available if r.year_month == args.month]
        if not chosen:
            _log(f"month {args.month} not found on the portal")
            return 1
        run(chosen, engine)
        return 0

    if args.backfill is not None:
        run(latest_available_months(args.backfill), engine)
        return 0

    # Default: incremental. Load newest BACKFILL_MONTHS window, skipping done ones.
    done = loaded_months(engine)
    window = latest_available_months(BACKFILL_MONTHS)
    todo = [r for r in window if r.year_month not in done]
    if not todo:
        _log("nothing to do — warehouse is up to date")
        return 0
    _log(f"{len(todo)} new month(s) to load: {[r.year_month for r in todo]}")
    run(todo, engine)
    return 0


if __name__ == "__main__":
    sys.exit(main())
