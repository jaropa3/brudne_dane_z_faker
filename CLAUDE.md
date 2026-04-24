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

Python ETL pipeline: CSV files → validate → PostgreSQL (staging → core tables).

**Flow:**
```
CSV files (data/raw_data/)
  → src/extract.py   load_csv()                      — encoding/separator detection
  → src/validate.py  validate()                       — returns (valid_df, quarantine_df, duplicates_df)
  → src/copy_io.py   copy_from_file()                — COPY FROM STDIN → staging
  → src/load.py      insert_from_stagging_to_core()  — staging → core with FK checks
```

**Key modules:**
- `src/load.py` — config loading, quarantine saves (Excel), DB insert functions, staging truncate
- `src/extract.py` — CSV ingestion with auto-encoding/separator detection via `chardet`
- `src/validate.py` — validates orders: type casting, null checks, date parsing (5 formats), status whitelist, future-date check, duplicate detection
- `src/connection.py` — SQLAlchemy engine via env vars (`DB_USER`, `DB_PASSWORD`) + `src/config.yaml` (host/port/dbname)
- `src/copy_io.py` — bulk PostgreSQL COPY using raw psycopg2 cursor
- `src/logger_app.py` — JSON-structured logger, writes to `logs/etl_YYYYMMDD.log`
- `src/transform.py` — stub module, not connected to pipeline (incomplete)

**Database tables:**
- Staging: `stag_orders`, `stag_customers`, `stag_products` — truncated at the start of each run
- Core: `orders`, `customers`, `products` — inserted with `ON CONFLICT DO NOTHING`
- `rejected_orders` — orders that fail FK checks (missing product or customer)
- `raw_products_files` — raw text backup of products CSV, deduplicated by SHA-256

**validate() details:**
- Raises `ValueError` if any required column is missing (`order_id`, `customer_id`, `product_id`, `quantity`, `amount`, `order_date`, `status`)
- Accepts 5 date formats: `%Y-%m-%d`, `%d/%m/%Y`, `%m/%d/%Y`, `%d.%m.%Y`, `%Y%m%d`
- Valid statuses: `pending`, `paid`, `refunded`, `cancelled`
- Duplicate `order_id`: keeps last by `order_date`; earlier copies go to `duplicates_df`
- Quarantined rows get `fail_*` boolean columns explaining the reason (e.g. `fail_positive_qty`, `fail_valid_status`, `fail_not_future_date`)

**Config & credentials:**
- `src/config.yaml` — DB host/port/dbname, file paths, quarantine output dir
- `.env` must provide `DB_USER` and `DB_PASSWORD`
- `config.yaml` contains a hardcoded `password` field — it is ignored at runtime; credentials come only from `.env`
- `sslmode` is in `config.yaml` but not wired to the SQLAlchemy engine

**Testing:**
- `pytest.ini` sets `pythonpath = src`, so tests import directly: `from validate import validate` (not `from src.validate import validate`)

**Known issues:**
- `src/transform.py` only exports `data_cleaning` — it has no `validate` or `normalize_keys`; old test files that imported those from `transform` will fail with `ImportError`
- Table name in `copy_io.py` is interpolated via f-string into the COPY statement (SQL injection risk if `table` comes from untrusted input)
- `truncat_stag()` commits each TRUNCATE in a separate transaction instead of one atomic block
