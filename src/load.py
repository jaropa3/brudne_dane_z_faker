import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os
from sqlalchemy.engine import URL
from pathlib import Path
from psycopg2 import sql
import yaml
from datetime import datetime, timezone
import hashlib

def load_config():

    with open("src/config.yaml") as f:
        return yaml.safe_load(f)
    
config = load_config()    

def _compute_hash(file_path: Path) -> str:
    content = file_path.read_bytes()
    return hashlib.sha256(content).hexdigest()

def save_qarantine(df, name: str):
    base_dir = Path(__file__).resolve().parents[1]
    today_str = datetime.today().strftime("%Y%m%d_%H_%M_%S")
    output_dir = base_dir / config["paths"]["quarantine"]
    file_name = f"{config['output']['raport_name']}_{name}_{today_str}.xlsx"
    df.to_excel(output_dir / file_name, index=False)

def insert_raw_file(engine, path: str) -> None:
    file_path = Path(path)
    file_hash = _compute_hash(file_path)
    content = file_path.read_text(encoding="utf-8")
    with engine.begin() as conn:  # begin() = autocommit po wyjściu z bloku, rollback przy wyjątku
        conn.execute(
            text("""
                INSERT INTO raw_products_files (file_name, file_hash, file_content, ingested_at)
                VALUES (:file_name, :file_hash, :file_content, NOW())
                ON CONFLICT (file_hash) DO NOTHING
            """),
            {"file_name": file_path.name, "file_hash":file_hash , "file_content": content},
        )

def truncat_stag(engine):
    with engine.connect() as conn:
        conn.execute(text("TRUNCATE stag_customers"))
        conn.commit()
        conn.execute(text("TRUNCATE stag_products"))
        conn.commit()
        conn.execute(text("TRUNCATE stag_orders"))
        conn.commit()

def insert_from_stagging_to_core(engine):
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO customers (customer_id, customer_name, email, city, created_at)
            SELECT * FROM stag_customers
            ORDER BY customer_id
            ON CONFLICT DO NOTHING
        """))
        conn.execute(text("""
            INSERT INTO products (product_id, product_name, category, price)
            SELECT * FROM stag_products
            ORDER BY product_id
            ON CONFLICT DO NOTHING
        """))
        conn.execute(text("""
            INSERT INTO rejected_orders
            SELECT
                s.*,
                CASE
                    WHEN NOT EXISTS (
                        SELECT 1 FROM products p WHERE p.product_id = s.product_id
                    ) THEN 'PRODUCT_NOT_FOUND'
                    WHEN NOT EXISTS (
                        SELECT 1 FROM customers c WHERE c.customer_id = s.customer_id
                    ) THEN 'CUSTOMER_NOT_FOUND'
                    ELSE 'UNKNOWN'
                END
            FROM stag_orders s
            WHERE
                NOT EXISTS (
                    SELECT 1 FROM products p WHERE p.product_id = s.product_id
                )
                OR NOT EXISTS (
                    SELECT 1 FROM customers c WHERE c.customer_id = s.customer_id
                )
                """))
        conn.execute(text("""
            INSERT INTO orders
            SELECT s.*
            FROM stag_orders s
            WHERE
                EXISTS (
                    SELECT 1 FROM products p WHERE p.product_id = s.product_id
                )
                AND EXISTS (
                    SELECT 1 FROM customers c WHERE c.customer_id = s.customer_id
                )
            ON CONFLICT (order_id) DO NOTHING;
        """))