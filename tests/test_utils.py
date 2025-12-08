from pathlib import Path

from src.utils import load_transactions


def test_load_transactions_returns_dataframe():
    data_path = Path("data") / "operations.xlsx"
    df = load_transactions(data_path)
    assert not df.empty
