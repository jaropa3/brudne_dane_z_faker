from pathlib import Path
from sqlalchemy.engine import Engine
from psycopg2 import sql
import chardet
from src.logger_app import setup_logger

logger = setup_logger("copy_io")


def _detect_encoding(file_path: Path) -> str:
    with open(file_path, "rb") as f:
        detected = chardet.detect(f.read(10_000))
    return detected["encoding"] or "utf-8"


def copy_from_file(engine: Engine, file_path: Path | str, table: str) -> None:
    file_path = Path(file_path)
    encoding = _detect_encoding(file_path)

    raw_conn = engine.raw_connection()
    try:
        with raw_conn.cursor() as cur:
            with open(file_path, "r", encoding=encoding, errors="replace") as f:
                cur.copy_expert(
                    sql.SQL("COPY {} FROM STDIN WITH (FORMAT csv, HEADER true)")
                        .format(sql.Identifier(table)),
                    f,
                )
        raw_conn.commit()
        logger.info(f"COPY from {file_path} INTO {table}")
    except Exception:
        raw_conn.rollback()
        raise
    finally:
        raw_conn.close()
