from sqlalchemy import text
from pathlib import Path
import yaml
from datetime import datetime
import hashlib

def load_config():
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)


def _compute_hash(file_path: Path) -> str:
    content = file_path.read_bytes()
    return hashlib.sha256(content).hexdigest()

def save_quarantine(df, name: str):
    config = load_config()
    base_dir = Path(__file__).resolve().parents[1]
    today_str = datetime.today().strftime("%Y%m%d_%H_%M_%S")
    output_dir = base_dir / config["paths"]["quarantine"]
    output_dir.mkdir(parents=True, exist_ok=True)
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
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE stag_customers, stag_products, stag_orders"))

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
            WHERE (
                NOT EXISTS (
                    SELECT 1 FROM products p WHERE p.product_id = s.product_id
                )
                OR NOT EXISTS (
                    SELECT 1 FROM customers c WHERE c.customer_id = s.customer_id
                )
            )
            AND NOT EXISTS (
                SELECT 1 FROM rejected_orders r WHERE r.order_id = s.order_id
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