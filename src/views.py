import json
import logging
from datetime import datetime
from typing import Any, Dict, List

import pandas as pd

from src.reports import spending_by_category
from src.utils import load_transactions, parse_datetime

logger = logging.getLogger(__name__)


def get_index_context() -> dict:
    """
    Простейший контекст для главной страницы.

    Нужен для базового теста.
    Основной "умный" контекст строится функцией build_main_page_context.
    """
    return {"title": "Transactions dashboard"}


def build_main_page_context(
    df: pd.DataFrame,
    generated_at: datetime | None = None,
) -> Dict[str, Any]:
    """
    Собирает контекст для главной страницы с общей статистикой.

    В контекст включаем:
    - заголовок страницы,
    - общее количество транзакций,
    - общую сумму трат,
    - топ-3 категорий по сумме трат,
    - время генерации отчёта (если передано).

    Параметры:
    ----------
    df : pd.DataFrame
        Таблица исходных транзакций.
    generated_at : datetime | None
        Момент времени, когда формируется контекст (может быть None).

    Возвращает:
    -----------
    dict
        Словарь, который удобно отдавать как JSON.
    """
    total_transactions = len(df)

    # Определяем, есть ли в данных столбец "Сумма платежа"
    amount_column = "Сумма платежа" if "Сумма платежа" in df.columns else None

    total_amount = None
    top_categories: List[Dict[str, Any]] = []

    if amount_column:
        total_amount = float(df[amount_column].sum())

        by_category_df = spending_by_category(df, amount_column=amount_column)

        for _, row in by_category_df.head(3).iterrows():
            top_categories.append(
                {
                    "category": row["Категория"],
                    "amount": float(row[amount_column]),
                }
            )

    context: Dict[str, Any] = {
        "title": "Transactions dashboard",
        "total_transactions": total_transactions,
        "total_amount": total_amount,
        "top_categories": top_categories,
    }

    if generated_at is not None:
        # Сохраняем время генерации в ISO-формате
        context["generated_at"] = generated_at.isoformat(sep=" ")

    return context


def main_page(current_time_str: str) -> str:
    """
    Функция для страницы «Главная».

    Принимает строку с датой и временем в формате "YYYY-MM-DD HH:MM:SS",
    загружает транзакции из Excel, формирует общую статистику
    и возвращает JSON-строку с контекстом.

    Параметры:
    ----------
    current_time_str : str
        Строка с датой и временем в формате "YYYY-MM-DD HH:MM:SS".

    Возвращает:
    -----------
    str
        JSON-строка с контекстом главной страницы.
    """
    logger.info("Запрос главной страницы. current_time=%s", current_time_str)

    # Разбираем строку даты/времени
    current_time = parse_datetime(current_time_str)

    # Загружаем все транзакции
    df = load_transactions()
    logger.debug("Для главной страницы загружено %d транзакций.", len(df))

    # Собираем словарь-контекст
    context = build_main_page_context(df, generated_at=current_time)

    # Преобразуем в JSON-строку (готовый JSON-ответ)
    response_json = json.dumps(context, ensure_ascii=False)

    logger.info("Контекст главной страницы сформирован успешно.")
    return response_json
