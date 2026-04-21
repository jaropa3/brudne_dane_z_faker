from sqlalchemy.engine import Engine
from src.logger_app import setup_logger

logger = setup_logger("copy_io")

def copy_from_file(engine: Engine, file_path: str, table: str):
    """
    COPY FROM CSV → staging / target table
    """

    with engine.raw_connection() as conn:
        with conn.cursor() as cur:
            with open(file_path, "r", encoding="utf-8") as f:
                cur.copy_expert(
                    f"""
                    COPY {table}
                    FROM STDIN
                    WITH (FORMAT csv, HEADER true)
                    """,
                    f,
                )
                logger.info(f"COPY from {file_path} INTO {table}")
        conn.commit()