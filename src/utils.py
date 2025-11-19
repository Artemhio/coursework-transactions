from pathlib import Path
from typing import Optional

import pandas as pd

# Стандартный путь к Excel-файлу с транзакциями
# (лежит в папке data/operations.xlsx)
DEFAULT_DATA_PATH = Path("data") / "operations.xlsx"


def load_transactions(file_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Загружает таблицу транзакций из Excel-файла и возвращает DataFrame.

    Параметры:
    ----------
    file_path : Path | None
        Необязательный путь к Excel-файлу.
        Если путь не передан — используется DEFAULT_DATA_PATH.

    Возвращает:
    -----------
    pd.DataFrame
        Таблица всех транзакций.
    """
    # Если путь не указан — берём путь по умолчанию
    path = file_path or DEFAULT_DATA_PATH

    # Чтение Excel-файла
    df = pd.read_excel(path)

    # Пробуем привести текстовые даты к типу datetime
    for col in ("Дата операции", "Дата платежа"):
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    return df
