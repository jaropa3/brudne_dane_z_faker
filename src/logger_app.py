import logging
import sys
from datetime import datetime, timezone
import json
from pathlib import Path

class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log = {
            "time": datetime.now(timezone.utc).isoformat(),  # ISO8601
            "level": record.levelname,
            "msg": record.getMessage(),
            "logger": record.name,
        }

        # dodatkowe pola (extra=...)
        if hasattr(record, "extra"):
            log.update(record.extra)

        return json.dumps(log, ensure_ascii=False)

def setup_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    logger.propagate = False
    
    # upewnij się że katalog istnieje
    Path("logs").mkdir(exist_ok=True)

    formatter = JsonFormatter()
    
    # konsola
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    
    # plik
    file_handler = logging.FileHandler(f"logs/etl_{datetime.now():%Y%m%d}.log")
    
    file_handler.setFormatter(formatter)

    logger.addHandler(handler)
    logger.addHandler(file_handler)
    
    return logger