import pandas as pd
import chardet
from src.logger_app import setup_logger

logger = setup_logger("load")

def load_csv(path: str) -> pd.DataFrame:
    """
    Wczytuje CSV jako raw strings.
    Wykrywa encoding i separator automatycznie, ale pozwala je nadpisać.
    """
    # Najpierw wykryj encoding
  
    with open(path, "rb") as f:
        detected = chardet.detect(f.read(10_000))  # pierwsze 10KB wystarczy
    encoding = detected["encoding"] or "utf-8"

    # Wczytaj pierwszą linię żeby wykryć separator
    with open(path, "r", encoding=encoding, errors="replace") as f:
        first_line = f.readline()
    sep = max([",", ";", "\t", "|"], key=first_line.count)

    df = pd.read_csv(
        path,
        header=0,
        sep=sep,
        encoding=encoding,
        encoding_errors="replace",   # nie crashuj na złym znaku
        dtype=str,                   # wszystko jako string — typy castujepi później
        keep_default_na=False,       # nie zamieniaj "NA", "NULL", "" na NaN automatycznie
        skipinitialspace=True,       # usuń spacje po separatorze
        on_bad_lines="warn",         # nie crashuj na złej linii, tylko zaloguj
    )

    # Wyczyść nazwy kolumn — spacje, wielkie litery
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
    logger.info("-------START PIPELINE-------")
    #print(f"Loaded: {len(df)} rows | encoding: {encoding} | sep: repr({sep!r})")
    return df