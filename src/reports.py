import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List

import pandas as pd  # type: ignore[import-untyped]

logger = logging.getLogger(__name__)


def get_stub_report() -> dict:
    """
    Простейший "заглушка"-отчёт.

    Нужен для того, чтобы базовый тест на отчёты проходил.
    Основная логика отчётов реализуется в других функциях этого модуля.
    """
    return {"status": "ok", "details": []}


def spending_by_category(
    df: pd.DataFrame,
    amount_column: str = "Сумма платежа",
) -> pd.DataFrame:
    """
    Строит табличный отчёт по тратам в разрезе категорий.

    Это вспомогательная функция: она возвращает DataFrame,
    который потом может использоваться другими функциями (например,
    для построения JSON-ответа или сохранения в Excel).

    Параметры:
    ----------
    df : pd.DataFrame
        Таблица исходных транзакций.
    amount_column : str
        Название столбца с суммой.
        Обычно это "Сумма платежа" или "Сумма операции".

    Возвращает:
    -----------
    pd.DataFrame
        Таблица с двумя колонками:
        - "Категория"
        - amount_column (сумма по каждой категории),
        отсортированная по убыванию суммы.
    """
    if "Категория" not in df.columns:
        raise ValueError("В данных отсутствует столбец 'Категория'.")

    if amount_column not in df.columns:
        raise ValueError(f"В данных отсутствует столбец '{amount_column}'.")

    grouped = (
        df.groupby("Категория", dropna=False)[amount_column]
        .sum()
        .reset_index()
        .sort_values(by=amount_column, ascending=False)
        .reset_index(drop=True)
    )

    return grouped


def build_spending_by_category_report(
    df: pd.DataFrame,
    category: str | None,
    start_date_str: str,
    amount_column: str = "Сумма платежа",
    date_column: str = "Дата операции",
) -> str:
    """
    Строит JSON-отчёт "Траты по категории" за трёхмесячный период.

    Параметры:
    ----------
    df : pd.DataFrame
        Таблица исходных транзакций.
    category : str | None
        Название категории, по которой нужно построить отчёт.
        Если None — считаем по всем категориям.
    start_date_str : str
        Строка с датой начала периода в формате "YYYY-MM-DD".
        Период считается как [start_date, start_date + 3 месяца).
    amount_column : str
        Название столбца с суммой платежа (по умолчанию "Сумма платежа").
    date_column : str
        Название столбца с датой операции (по умолчанию "Дата операции").

    Возвращает:
    -----------
    str
        JSON-строка с отчётом.
    """
    logger.info(
        "Построение отчёта по тратам: category=%s, start_date=%s",
        category,
        start_date_str,
    )

    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    except ValueError as exc:
        logger.error("Некорректный формат даты: %s", start_date_str)
        raise ValueError("Дата должна быть в формате 'YYYY-MM-DD'.") from exc

    end_date = start_date + timedelta(days=90)

    if date_column not in df.columns:
        raise ValueError(f"В данных отсутствует столбец '{date_column}'.")

    filtered = df.copy()
    filtered[date_column] = pd.to_datetime(filtered[date_column], errors="coerce")

    date_mask = (filtered[date_column] >= start_date) & (
        filtered[date_column] < end_date
    )
    filtered = filtered[date_mask]

    logger.debug(
        "После фильтрации по датам осталось %d транзакций.",
        len(filtered),
    )

    if category is not None:
        if "Категория" not in filtered.columns:
            raise ValueError("В данных отсутствует столбец 'Категория'.")

        cat_mask = filtered["Категория"] == category
        filtered = filtered[cat_mask]

        logger.debug(
            "После фильтрации по категории '%s' осталось %d транзакций.",
            category,
            len(filtered),
        )

    if filtered.empty:
        logger.warning("Нет транзакций для указанного периода и категории.")
        result: Dict[str, Any] = {
            "category": category,
            "start_date": start_date_str,
            "end_date": end_date.strftime("%Y-%m-%d"),
            "total_amount": 0.0,
            "items": [],
        }
        return json.dumps(result, ensure_ascii=False)

    grouped = spending_by_category(filtered, amount_column=amount_column)

    total_amount = float(grouped[amount_column].sum())

    items: List[Dict[str, Any]] = []
    for _, row in grouped.iterrows():
        items.append(
            {
                "category": row["Категория"],
                "amount": float(row[amount_column]),
            },
        )

    result: Dict[str, Any] = {
        "category": category,
        "start_date": start_date_str,
        "end_date": end_date.strftime("%Y-%m-%d"),
        "total_amount": total_amount,
        "items": items,
    }

    logger.info(
        "Отчёт сформирован: total_amount=%.2f, categories=%d",
        total_amount,
        len(items),
    )

    return json.dumps(result, ensure_ascii=False)
