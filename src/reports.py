import json
import logging
from datetime import datetime, timedelta

import pandas as pd

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

    # Парсим дату начала периода
    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    except ValueError as exc:
        logger.error("Некорректный формат даты: %s", start_date_str)
        raise ValueError("Дата должна быть в формате 'YYYY-MM-DD'.") from exc

    # Конец трёхмесячного периода (условно: 90 дней)
    end_date = start_date + timedelta(days=90)

    # Убеждаемся, что дата-колонка в datetime
    if date_column not in df.columns:
        raise ValueError(f"В данных отсутствует столбец '{date_column}'.")

    df = df.copy()
    df[date_column] = pd.to_datetime(df[date_column], errors="coerce")

    # Фильтрация по дате
    date_mask = (df[date_column] >= start_date) & (df[date_column] < end_date)
    filtered = df[date_mask]

    logger.debug(
        "После фильтрации по датам осталось %d транзакций.",
        len(filtered),
    )

    # Фильтрация по категории (если указана)
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

    # Если данных нет — возвращаем пустой отчёт
    if filtered.empty:
        logger.warning("Нет транзакций для указанного периода и категории.")
        result = {
            "category": category,
            "start_date": start_date_str,
            "end_date": end_date.strftime("%Y-%m-%d"),
            "total_amount": 0.0,
            "items": [],
        }
        return json.dumps(result, ensure_ascii=False)

    # Считаем по категориям (на случай category=None берём все)
    grouped = spending_by_category(filtered, amount_column=amount_column)

    total_amount = float(grouped[amount_column].sum())

    items: list[dict] = []
    for _, row in grouped.iterrows():
        items.append(
            {
                "category": row["Категория"],
                "amount": float(row[amount_column]),
            },
        )

    result = {
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

    # Возвращаем JSON-строку, как требует ТЗ (JSON-ответ)
    return json.dumps(result, ensure_ascii=False)
