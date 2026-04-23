import pandas as pd
from typing import Dict
from src.logger_app import setup_logger
from datetime import datetime, timezone

logger = setup_logger("walidacja")

VALID_STATUSES = {"pending", "paid", "refunded", "cancelled"}

REQUIRED_COLUMNS = [
    "order_id", "customer_id", "product_id",
    "quantity", "amount", "order_date", "status"
]
DATE_FORMATS = ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d.%m.%Y", "%Y%m%d"]

def _parse_date(val) -> datetime | None:
    if pd.isna(val) or not isinstance(val, str):
        return None
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(val.strip(), fmt)
        except ValueError:
            continue
    return None

def validate(df):
    df = df.copy()
     # --- 2. Sprzawdzam kolumny ---
    missing_cols = set(REQUIRED_COLUMNS) - set(df.columns)
    if missing_cols:
        raise ValueError(f"Missing columns: {missing_cols}")
    #3 sprawdzam wymagania
    # RAW backup
    df["order_date_raw"] = df["order_date"]

    # 4--- TYPE CAST ---
    df["order_id"] = pd.to_numeric(df["order_id"], errors="coerce").astype("Int64")
    df["customer_id"] = pd.to_numeric(df["customer_id"], errors="coerce").astype("Int64")
    df["product_id"] = pd.to_numeric(df["product_id"], errors="coerce").astype("Int64")
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").astype("Int64")
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    df["status"] = df["status"].astype(str).str.strip().replace({"": pd.NA, "nan": pd.NA, "<NA>": pd.NA})


    # 4. Data — jedna ścieżka, ze stringa
    df["order_date"] = pd.to_datetime(
        df["order_date_raw"].apply(_parse_date),
        errors="coerce"
    )

    # duplikaty
    rejected_duplicates_mask = df.duplicated(subset=["order_id"],keep="last")  # zostawiasz ostatni → reszta to odrzucone
    duplicates_mask = df.duplicated(subset=["order_id"], keep=False)
    duplicates = df[rejected_duplicates_mask]
    df = df.sort_values("order_date").drop_duplicates(
        subset=["order_id"],
        keep="last"
    )

    # 5. Reguły — osobna kolumna na każdy powód odrzucenia
    now = pd.Timestamp.now()
    rules = {
        "not_null_keys":    df[["order_id", "customer_id", "product_id", "status"]].notna().all(axis=1),
        "valid_date":       df["order_date"].notna(),      # osobna reguła — wiesz czemu odpada
        "not_future_date":  df["order_date"] <= now,
        "positive_qty":     df["quantity"] > 0,
        "positive_amount":  df["amount"] > 0,
        "valid_status":     df["status"].isin(VALID_STATUSES),  
    }
    # 6. Audit DataFrame — buduj przed splittem, na pełnym df
    rule_df = pd.DataFrame({f"fail_{name}": ~mask for name, mask in rules.items()})

    # not_future_date nie ma sensu jeśli data jest NaT — wyczyść podwójne flagowanie
    rule_df.loc[~rules["valid_date"], "fail_not_future_date"] = False

    final_mask = rule_df.eq(False).all(axis=1)  # valid = żaden flag nie jest True

    valid      = df[final_mask].copy()
    quarantine = df[~final_mask].copy()
    
    quarantine = quarantine.join(rule_df[~final_mask])

    # 7. Log summary
    rule_stats = {name: int(col.sum()) for name, col in rule_df.items()}

    logger.info(
        "data_valid_summary",
        extra={
            "extra": {
                "total_rows":       len(df),
                "valid_rows":       len(valid),
                "quarantine_rows":  len(quarantine),
                "duplikates":       len(duplicates),
                "rules_failed":     rule_stats,
            }
        }
    )

    return valid, quarantine, duplicates