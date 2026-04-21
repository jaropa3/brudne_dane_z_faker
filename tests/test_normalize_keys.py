import sys
from pathlib import Path

# Dodaj src do ścieżki zanim zaimportujesz cokolwiek z src
sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd
import pytest
from transform import normalize_keys  # teraz już działa bez 'src.'
# from src.transform import normalize_keys  # <-- nie używamy tego, bo dodaliśmy src do sys.path

def test_normalize_keys():

    df = pd.DataFrame({
        "Product ID": [1],
        "Price Value": [100]
    })

    result = normalize_keys(df)

    assert "product_id" in result.columns
    assert "price_value" in result.columns