# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run the main ETL pipeline
python main.py

# Run all tests
pytest tests/

# Run a single test file
pytest tests/test_validate.py

# Install dependencies
pip install -r requirements.txt

# Run SQL query scripts
python skrypt_zapytan_sql.py
```

## Architecture

This is a Python ETL pipeline that ingests CSV files, validates them, and loads data into PostgreSQL via staging tables.

**Flow:**
```
CSV files (data/raw_data/)
  → src/extract.py  (load_csv: encoding detection, separator detection)
  → src/validate.py (validate: type casting, rule checks, duplicate handling)
  → src/copy_io.py  (copy_from_file: COPY FROM STDIN → staging tables)
  → src/load.py     (insert_from_staging_to_core: staging → core tables)
```

**Key modules:**
- `src/load.py` — config loading, quarantine saves (Excel), DB insert functions, staging truncate
- `src/extract.py` — CSV ingestion with auto-encoding/separator detection via `chardet`
- `src/validate.py` — validates orders: type casting, null checks, date parsing (5 formats), status whitelist, future-date check, duplicate detection
- `src/connection.py` — SQLAlchemy engine via env vars (`DB_USER`, `DB_PASSWORD`) + `src/config.yaml` (host/port/dbname)
- `src/copy_io.py` — bulk PostgreSQL COPY using raw psycopg2 cursor
- `src/logger_app.py` — JSON-structured logger, writes to `logs/etl_YYYYMMDD.log`
- `src/transform.py` — stub module, not connected to pipeline (incomplete)

**Database pattern:**
1. Truncate staging tables (`stag_orders`, `stag_customers`, `stag_products`)
2. COPY CSVs into staging
3. Insert staging → core tables (`orders`, `customers`, `products`) with `ON CONFLICT DO NOTHING`
4. Rows with referential integrity failures go to `rejected_orders`
5. Products file also backed up as raw text in `raw_products_files` (with SHA-256 dedup)

**Config:** `src/config.yaml` — database host/port/dbname, file paths, quarantine output dir. Credentials must come from `.env` (`DB_USER`, `DB_PASSWORD`).

**Known issues to be aware of:**
- `src/transform.py` exports neither `validate` nor `normalize_keys` — both test files will fail with `ImportError`
- Table name in `copy_io.py` is interpolated via f-string (SQL injection risk)
- `sslmode` in config.yaml is not wired to the engine
