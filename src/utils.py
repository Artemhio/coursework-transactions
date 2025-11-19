from pathlib import Path
from typing import Any

import pandas as pd


def load_transactions(file_path: Path) -> pd.DataFrame:
    """Load transactions data from Excel file and return DataFrame."""
    return pd.read_excel(file_path)
