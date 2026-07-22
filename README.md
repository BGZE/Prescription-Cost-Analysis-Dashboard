# NHS Prescription Cost Analysis Dashboard

A full, live data product built on the **NHSBSA Prescription Cost Analysis (PCA)**
open dataset. It runs the whole pipeline end to end:

**NHSBSA open data → Python ETL → Postgres warehouse → FastAPI → React dashboard**, deployed free on Render + Supabase, and refreshed automatically every month.

The dashboard answers: *what is the NHS in England spending on prescriptions,
on which drugs, in which regions, and how much of it is generic vs branded?*

![pipeline](https://img.shields.io/badge/pipeline-ETL%20%E2%86%92%20Postgres%20%E2%86%92%20API%20%E2%86%92%20React-005eb8)

---

## Why it's built this way

Each monthly PCA file is ~500,000 rows / ~230 MB. That is far too much to ship to
a browser, and the portal's SQL endpoint is disabled. So the ETL **streams** each
CSV and aggregates it in chunks with pandas into small summary tables (national,
BNF chapter/section, region, ICB, chemical substance, prep class). Those tables —
a few thousand rows each — live in Postgres and are what the API serves. One month
goes from 500k raw rows to a fast dashboard in ~12 seconds of processing.

```
┌──────────────┐   stream+chunk   ┌───────────────┐   upsert   ┌────────────┐
│ NHSBSA CSV   │ ───────────────► │ pandas aggreg. │ ─────────► │ Postgres   │
│ ~230 MB/mo   │                  │ (etl/)         │            │ (Supabase) │
└──────────────┘                  └───────────────┘            └─────┬──────┘
                                                                      │ SQL
                                    ┌───────────────┐   REST     ┌────▼──────┐
                                    │ React + Vite  │ ◄───────── │ FastAPI   │
                                    │ dashboard     │   /api/*   │ (backend/)│
                                    └───────────────┘            └───────────┘
```

## Repository layout

```
etl/                 Data pipeline (extract → transform → load)
  nhsbsa.py          Portal client: list monthly resources + CSV URLs
  transform.py       Stream + chunked aggregation into summary tables
  load.py            Idempotent upserts into Postgres
  pipeline.py        Orchestrator (backfill / incremental / single month)
  schema.sql         Warehouse DDL
backend/             FastAPI app (read-only API + serves the built SPA)
  app/queries.py     All analytical SQL
  app/main.py        Routes, CORS, static hosting
frontend/            React + Vite + TypeScript dashboard (Recharts)
Dockerfile           Multi-stage: build SPA + run API in one image
render.yaml          Render Blueprint (free web service)
docker-compose.yml   Local Postgres for development
.github/workflows/   Monthly scheduled refresh
```

## Data model

| Table | Grain | Purpose |
|-------|-------|---------|
| `fact_national_month` | month | Headline KPIs + trend |
| `fact_chapter_month` | month × BNF chapter | Therapeutic breakdown |
| `fact_section_month` | month × BNF section | Deeper therapeutic breakdown |
| `fact_region_month` | month × NHS region | Geography |
| `fact_icb_month` | month × ICB | Geography (Integrated Care Boards) |
| `fact_chemical_month` | month × chemical substance | Top drugs |
| `fact_prepclass_month` | month × prep class | Generic vs branded |
| `etl_runs` | month | Load bookkeeping |

*NIC = Net Ingredient Cost (list price before discounts, excluding dispensing
fees). Preparation classes follow the NHSBSA methodology: 1 generic, 2 generic
(proprietary only), 3 branded, 4 appliances & devices, 5 generic (named supplier).*

---

## Run it locally

Prerequisites: Python 3.11+, Node 18+, and a Postgres (via `docker compose` or local).

```bash
# 1. Config
cp .env.example .env            # defaults point at the local Postgres below

# 2. Database
docker compose up -d            # starts Postgres on localhost:5432

# 3. ETL — load the most recent months (each is ~230 MB to download)
python -m venv .venv && source .venv/bin/activate
pip install -r etl/requirements.txt
python -m etl.pipeline --backfill 12     # or --month 202605 for a single month
python -m etl.pipeline --list            # see available vs loaded months

# 4. Backend
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload --port 8000

# 5. Frontend (new terminal)
cd frontend && npm install && npm run dev   # http://localhost:5173
```

The Vite dev server proxies `/api` to the backend, so the app is same-origin.
For a production-style run, `npm run build` then just open the backend on `:8000`
— FastAPI serves the built SPA and the API together.

## Deploy it free

**Database — Supabase (free, persistent):**
1. Create a project at [supabase.com](https://supabase.com).
2. Project Settings → Database → Connection string → **URI** (use the *pooler*
   host, port `6543`). Prefix the driver: `postgresql+psycopg2://...`.

**Backend + dashboard — Render (free):**
1. Push this repo to GitHub.
2. Render → **New → Blueprint** → pick the repo (it reads `render.yaml`).
3. Set the `DATABASE_URL` env var to your Supabase URI.
4. Deploy. The Docker image builds the React app and serves everything from
   one URL. Health check: `/api/health`.

**Seed the warehouse** (once), from your machine or the GitHub Action:
```bash
DATABASE_URL="<your supabase uri>" python -m etl.pipeline --backfill 24
```

**Automatic monthly refresh — GitHub Actions:**
Add a repo secret `DATABASE_URL` (Settings → Secrets → Actions). The workflow in
`.github/workflows/etl.yml` runs on the 20th of each month and loads any new
month incrementally. You can also trigger it manually (with an optional backfill).

## API

| Endpoint | Description |
|----------|-------------|
| `GET /api/meta` | Available months, latest, last-updated |
| `GET /api/overview?month=latest` | KPIs with MoM / YoY deltas |
| `GET /api/trend` | National monthly cost & cost-per-item series |
| `GET /api/therapeutic?level=chapter\|section` | Spend by BNF area |
| `GET /api/geography?level=region\|icb` | Spend by geography |
| `GET /api/drugs?limit=20` | Top chemical substances by cost |
| `GET /api/drugs/{code}/trend` | One substance over time |
| `GET /api/prepclass` | Generic vs branded split |

## Data source & licence

Data: [NHSBSA Prescription Cost Analysis (monthly)](https://opendata.nhsbsa.net/dataset/prescription-cost-analysis-pca-monthly-data),
published under the Open Government Licence v3.0. This project is not affiliated
with or endorsed by the NHS or NHSBSA.
