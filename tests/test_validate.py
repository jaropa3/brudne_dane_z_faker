import sys
from pathlib import Path

# Dodaj src do ścieżki zanim zaimportujesz cokolwiek z src
sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd
import pytest
from transform import validate  # teraz już działa bez 'src.'
# from src.transform import normalize_keys  # <-- nie używamy tego, bo dodaliśmy src do sys.path


def test_validate_negative_price():

    df = pd.DataFrame({
        "qty": [1],
        "unit_price": [-10]
    })

    with pytest.raises(ValueError):
        validate(df)