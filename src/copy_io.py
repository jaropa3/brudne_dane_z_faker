import io
from pathlib import Path
import pandas as pd
from sqlalchemy.engine import Engine
from psycopg2 import sql
import chardet
from src.logger_app import setup_logger

logger = setup_logger("copy_io")


def _detect_encoding(file_path: Path) -> str:
    with open(file_path, "rb") as f:
        detected = chardet.detect(f.read(10_000))
    return detected["encoding"] or "utf-8"


def _copy_buffer(engine: Engine, buf, table: str) -> None:
    raw_conn = engine.raw_connection()
    try:
        with raw_conn.cursor() as cur:
            cur.copy_expert(
                sql.SQL("COPY {} FROM STDIN WITH (FORMAT csv, HEADER true)")
                    .format(sql.Identifier(table)),
                buf,
            )
        raw_conn.commit()
    except Exception:
        raw_conn.rollback()
        raise
    finally:
        raw_conn.close()


def copy_from_file(engine: Engine, file_path: Path | str, table: str) -> None:
    file_path = Path(file_path)
    encoding = _detect_encoding(file_path)

    with open(file_path, "r", encoding=encoding, errors="replace") as f:
        _copy_buffer(engine, f, table)
    logger.info(f"COPY from {file_path} INTO {table}")


def copy_from_df(engine: Engine, df: pd.DataFrame, table: str) -> None:
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    buf.seek(0)

    _copy_buffer(engine, buf, table)
    logger.info(f"COPY dataframe ({len(df)} rows) INTO {table}")
