-- Prescription Cost Analysis warehouse schema (summary / star-style tables).
-- All grains are pre-aggregated from the raw NHSBSA monthly CSVs. NIC is the
-- Net Ingredient Cost in GBP; items = number of prescription items.

CREATE TABLE IF NOT EXISTS fact_national_month (
    year_month     INTEGER PRIMARY KEY,
    nic            NUMERIC(16, 2) NOT NULL,
    items          BIGINT NOT NULL,
    quantity       BIGINT NOT NULL,
    cost_per_item  NUMERIC(12, 4) NOT NULL
);

CREATE TABLE IF NOT EXISTS fact_chapter_month (
    year_month        INTEGER NOT NULL,
    bnf_chapter_code  TEXT NOT NULL,
    bnf_chapter       TEXT,
    nic               NUMERIC(16, 2) NOT NULL,
    items             BIGINT NOT NULL,
    quantity          BIGINT NOT NULL,
    PRIMARY KEY (year_month, bnf_chapter_code)
);

CREATE TABLE IF NOT EXISTS fact_section_month (
    year_month        INTEGER NOT NULL,
    bnf_section_code  TEXT NOT NULL,
    bnf_section       TEXT,
    bnf_chapter_code  TEXT,
    bnf_chapter       TEXT,
    nic               NUMERIC(16, 2) NOT NULL,
    items             BIGINT NOT NULL,
    quantity          BIGINT NOT NULL,
    PRIMARY KEY (year_month, bnf_section_code)
);

CREATE TABLE IF NOT EXISTS fact_region_month (
    year_month   INTEGER NOT NULL,
    region_code  TEXT NOT NULL,
    region_name  TEXT,
    nic          NUMERIC(16, 2) NOT NULL,
    items        BIGINT NOT NULL,
    quantity     BIGINT NOT NULL,
    PRIMARY KEY (year_month, region_code)
);

CREATE TABLE IF NOT EXISTS fact_icb_month (
    year_month   INTEGER NOT NULL,
    icb_code     TEXT NOT NULL,
    icb_name     TEXT,
    region_code  TEXT,
    region_name  TEXT,
    nic          NUMERIC(16, 2) NOT NULL,
    items        BIGINT NOT NULL,
    quantity     BIGINT NOT NULL,
    PRIMARY KEY (year_month, icb_code)
);

CREATE TABLE IF NOT EXISTS fact_chemical_month (
    year_month                   INTEGER NOT NULL,
    bnf_chemical_substance_code  TEXT NOT NULL,
    bnf_chemical_substance       TEXT,
    bnf_chapter_code             TEXT,
    bnf_chapter                  TEXT,
    nic                          NUMERIC(16, 2) NOT NULL,
    items                        BIGINT NOT NULL,
    quantity                     BIGINT NOT NULL,
    PRIMARY KEY (year_month, bnf_chemical_substance_code)
);

CREATE TABLE IF NOT EXISTS fact_prepclass_month (
    year_month        INTEGER NOT NULL,
    prep_class        TEXT NOT NULL,
    prep_class_label  TEXT,
    prep_group        TEXT,
    nic               NUMERIC(16, 2) NOT NULL,
    items             BIGINT NOT NULL,
    quantity          BIGINT NOT NULL,
    PRIMARY KEY (year_month, prep_class)
);

-- Bookkeeping: what has been loaded, when, and how big.
CREATE TABLE IF NOT EXISTS etl_runs (
    year_month      INTEGER PRIMARY KEY,
    rows_processed  BIGINT,
    seconds         NUMERIC(10, 1),
    source_url      TEXT,
    loaded_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Helpful indexes for the API's common access patterns.
CREATE INDEX IF NOT EXISTS idx_chemical_ym_nic ON fact_chemical_month (year_month, nic DESC);
CREATE INDEX IF NOT EXISTS idx_section_ym_nic ON fact_section_month (year_month, nic DESC);
CREATE INDEX IF NOT EXISTS idx_icb_ym_nic ON fact_icb_month (year_month, nic DESC);
