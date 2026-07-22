"""Central configuration for the Prescription Cost Analysis ETL pipeline.

All values can be overridden with environment variables so the same code runs
locally (against a docker Postgres) and in CI/production (against Supabase).
"""
from __future__ import annotations

import os
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
# A standard SQLAlchemy/psycopg2 URL, e.g.
#   postgresql+psycopg2://user:pass@host:5432/dbname
# Supabase gives you this under Project Settings -> Database -> Connection string.
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://pca:pca@localhost:5432/pca",
)

# ---------------------------------------------------------------------------
# NHSBSA Open Data Portal (CKAN)
# ---------------------------------------------------------------------------
NHSBSA_API_BASE = "https://opendata.nhsbsa.net/api/3/action"
# The dataset (package) that contains one CSV resource per month.
PCA_MONTHLY_DATASET = "prescription-cost-analysis-pca-monthly-data"

# How many months of history to back-fill on a full run. Each monthly CSV is
# ~230 MB, so keep this sensible for CI. Newest N months are loaded.
BACKFILL_MONTHS = int(os.getenv("PCA_BACKFILL_MONTHS", "24"))

# Rows per pandas chunk while streaming the CSV. Larger = faster but more RAM.
CHUNK_SIZE = int(os.getenv("PCA_CHUNK_SIZE", "250000"))

# ---------------------------------------------------------------------------
# Reference data / label mappings
# ---------------------------------------------------------------------------
# Preparation class codes, verbatim from the NHSBSA PCA Background Information
# & Methodology document (section 1.2.2):
#   1 - drugs prescribed and available generically
#   2 - drugs prescribed generically but only available as a proprietary
#   3 - drugs prescribed and dispensed by proprietary brand name
#   4 - dressings, appliances, and medical devices
#   5 - drugs prescribed generically with a named supplier
PREP_CLASS_LABELS = {
    "01": "Generic",
    "02": "Generic (proprietary only)",
    "03": "Branded",
    "04": "Appliances & devices",
    "05": "Generic (named supplier)",
}

# Coarser grouping used by the dashboard's generic-vs-branded view. Classes
# 1, 2 and 5 are all prescribed generically; 3 is branded; 4 is appliances.
PREP_GROUP = {
    "01": "Generic",
    "02": "Generic",
    "03": "Branded",
    "04": "Appliances & devices",
    "05": "Generic",
}

# The measure columns we actually need from the raw CSV. Restricting the read
# to these keeps memory and parse time down dramatically.
USE_COLUMNS = [
    "YEAR_MONTH",
    "REGION_NAME",
    "REGION_CODE",
    "ICB_NAME",
    "ICB_CODE",
    "BNF_CHEMICAL_SUBSTANCE_CODE",
    "BNF_CHEMICAL_SUBSTANCE",
    "BNF_SECTION_CODE",
    "BNF_SECTION",
    "BNF_CHAPTER_CODE",
    "BNF_CHAPTER",
    "PREP_CLASS",
    "ITEMS",
    "TOTAL_QUANTITY",
    "NIC",
]

# Force dtypes so codes keep their leading zeros and measures stay numeric.
DTYPES = {
    "YEAR_MONTH": "int32",
    "REGION_NAME": "string",
    "REGION_CODE": "string",
    "ICB_NAME": "string",
    "ICB_CODE": "string",
    "BNF_CHEMICAL_SUBSTANCE_CODE": "string",
    "BNF_CHEMICAL_SUBSTANCE": "string",
    "BNF_SECTION_CODE": "string",
    "BNF_SECTION": "string",
    "BNF_CHAPTER_CODE": "string",
    "BNF_CHAPTER": "string",
    "PREP_CLASS": "string",
}
