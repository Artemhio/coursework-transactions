import json
import logging
from datetime import datetime
from typing import Any, Dict, List

import pandas as pd  # type: ignore[import-untyped]

from src.utils import (
    fetch_currency_rates,
    fetch_stock_prices,
    load_transactions,
    load_user_settings,
    parse_datetime,
)

logger = logging.getLogger(__name__)


def get_index_context() -> dict:
    """
    Простейший контекст для заглушки главной страницы.

    Используется в базовом тесте.
    """
    return {"title": "Transactions dashboard"}


def _get_month_period(current_time: datetime) -> tuple[datetime, datetime]:
    """
    Возвращает начало и конец периода:
    с первого дня месяца по указанную дату (включительно).
    """
    start = current_time.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    end = current_time
    return start, end


def _get_greeting(current_time: datetime) -> str:
    """
    Возвращает приветствие в зависимости от времени суток.
    """
    hour = current_time.hour
    if 5 <= hour < 12:
        return "Доброе утро"
    if 12 <= hour < 18:
        return "Добрый день"
    if 18 <= hour < 23:
        return "Добрый вечер"
    return "Доброй ночи"


def _build_cards(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Формирует список карт с суммой трат и кешбэком.

    Использует столбцы:
    - "Номер карты"
    - "Сумма платежа"
    """
    if "Номер карты" not in df.columns or "Сумма платежа" not in df.columns:
        return []

    grouped = (
        df.groupby("Номер карты", dropna=False)["Сумма платежа"]
        .sum()
        .reset_index()
        .sort_values(by="Сумма платежа", ascending=False)
    )

    cards: List[Dict[str, Any]] = []
    for _, row in grouped.iterrows():
        last_digits = str(row["Номер карты"])
        total_spent = float(row["Сумма платежа"])
        cashback = round(total_spent / 100, 2)  # 1 рубль на каждые 100 рублей

        cards.append(
            {
                "last_digits": last_digits,
                "total_spent": total_spent,
                "cashback": cashback,
            }
        )
    return cards


def _build_top_transactions(df: pd.DataFrame, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Формирует топ-N транзакций по сумме платежа.
    """
    if "Сумма платежа" not in df.columns:
        return []

    work_df = df.copy()
    if "Дата операции" in work_df.columns:
        work_df["Дата операции"] = pd.to_datetime(
            work_df["Дата операции"],
            errors="coerce",
            dayfirst=True,
        )

    work_df = work_df.sort_values(by="Сумма платежа", ascending=False).head(limit)

    result: List[Dict[str, Any]] = []
    for _, row in work_df.iterrows():
        date_val = row.get("Дата операции")
        if isinstance(date_val, datetime):
            date_str = date_val.strftime("%d.%m.%Y")
        else:
            date_str = str(date_val) if date_val is not None else ""

        result.append(
            {
                "date": date_str,
                "amount": float(row["Сумма платежа"]),
                "category": str(row.get("Категория", "")),
                "description": str(row.get("Описание", "")),
            }
        )
    return result


def build_main_page_context(df: pd.DataFrame, current_time: datetime) -> Dict[str, Any]:
    """
    Формирует базовый контекст для главной страницы без курсов и акций.

    Содержит:
    - greeting
    - cards
    - top_transactions
    """
    greeting = _get_greeting(current_time)
    cards = _build_cards(df)
    top_transactions = _build_top_transactions(df)

    return {
        "greeting": greeting,
        "cards": cards,
        "top_transactions": top_transactions,
    }


def main_page(current_time_str: str) -> str:
    """
    Функция для страницы «Главная».

    Принимает строку с датой и временем в формате "YYYY-MM-DD HH:MM:SS",
    фильтрует транзакции по периоду с начала месяца по указанную дату,
    строит контекст и добавляет курсы валют и цены акций.

    Возвращает JSON-строку с ключами:
    - greeting
    - cards
    - top_transactions
    - currency_rates
    - stock_prices
    """
    logger.info("Запрос главной страницы. current_time=%s", current_time_str)

    current_time = parse_datetime(current_time_str)

    df = load_transactions()
    logger.debug("Всего загружено транзакций: %d", len(df))

    # Фильтрация по периоду
    start_date, end_date = _get_month_period(current_time)

    if "Дата операции" in df.columns:
        df["Дата операции"] = pd.to_datetime(
            df["Дата операции"],
            errors="coerce",
            dayfirst=True,
        )
        mask = (df["Дата операции"] >= start_date) & (df["Дата операции"] <= end_date)
        period_df = df[mask].copy()
    else:
        period_df = df.copy()

    logger.debug("Транзакций в выбранном периоде: %d", len(period_df))

    # Базовый контекст (greeting, cards, top_transactions)
    context = build_main_page_context(period_df, current_time)

    # Пользовательские настройки (валюты и акции)
    settings = load_user_settings()
    currencies = settings.get("user_currencies", [])
    stocks = settings.get("user_stocks", [])

    currency_rates = fetch_currency_rates(currencies)
    stock_prices = fetch_stock_prices(stocks)

    context["currency_rates"] = currency_rates
    context["stock_prices"] = stock_prices

    response_json = json.dumps(context, ensure_ascii=False)

    logger.info("Контекст главной страницы сформирован успешно.")
    return response_json
