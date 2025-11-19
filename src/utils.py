import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd  # type: ignore[import-untyped]

logger = logging.getLogger(__name__)


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
    path = file_path or DEFAULT_DATA_PATH

    logger.info("Загрузка транзакций из файла: %s", path)

    df = pd.read_excel(path)

    # Пробуем привести текстовые даты к типу datetime
    for col in ("Дата операции", "Дата платежа"):
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    logger.debug("Загружено %d транзакций.", len(df))

    return df


def parse_datetime(datetime_str: str) -> datetime:
    """
    Разбирает строку с датой и временем в формате 'YYYY-MM-DD HH:MM:SS'.

    Параметры:
    ----------
    datetime_str : str
        Строка с датой и временем.

    Возвращает:
    -----------
    datetime
        Объект datetime, соответствующий переданной строке.

    Исключения:
    -----------
    ValueError
        Если формат строки некорректен.
    """
    logger.info("Разбор строки даты/времени: %s", datetime_str)

    try:
        dt = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
    except ValueError as exc:
        logger.error("Некорректный формат даты/времени: %s", datetime_str)
        raise ValueError(
            "Дата и время должны быть в формате 'YYYY-MM-DD HH:MM:SS'."
        ) from exc

    logger.debug("Строка даты/времени разобрана успешно: %s", dt.isoformat())
    return dt
