import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd  # type: ignore[import-untyped]
import requests  # type: ignore[import-untyped]

logger = logging.getLogger(__name__)

# Путь к файлу с транзакциями
DEFAULT_DATA_PATH = Path("data") / "operations.xlsx"

# Путь к файлу с пользовательскими настройками
USER_SETTINGS_PATH = Path("user_settings.json")


def load_transactions(file_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Загружает таблицу транзакций из Excel-файла и возвращает DataFrame.
    """
    path = file_path or DEFAULT_DATA_PATH

    logger.info("Загрузка транзакций из файла: %s", path)

    df = pd.read_excel(path)

    # Пробуем привести текстовые даты к типу datetime
    for col in ("Дата операции", "Дата платежа"):
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce", dayfirst=True)

    logger.debug("Загружено %d транзакций.", len(df))

    return df


def parse_datetime(datetime_str: str) -> datetime:
    """
    Разбирает строку с датой и временем в формате 'YYYY-MM-DD HH:MM:SS'.

    Возвращает объект datetime или поднимает ValueError при некорректном формате.
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


def load_user_settings(path: Path = USER_SETTINGS_PATH) -> Dict[str, Any]:
    """
    Загружает пользовательские настройки из JSON-файла.

    Ожидаемая структура:
    {
      "user_currencies": [...],
      "user_stocks": [...]
    }
    """
    if not path.exists():
        logger.warning(
            "Файл настроек %s не найден, используются значения по умолчанию.", path
        )
        return {"user_currencies": [], "user_stocks": []}

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    user_currencies = data.get("user_currencies") or []
    user_stocks = data.get("user_stocks") or []

    return {"user_currencies": user_currencies, "user_stocks": user_stocks}


def fetch_currency_rates(currencies: List[str]) -> List[Dict[str, Any]]:
    """
    Получает курсы валют для указанных кодов с использованием внешнего API.

    В качестве примера используется API ЦБ РФ.
    В случае ошибки возвращает список с rate=None.
    """
    if not currencies:
        return []

    url = "https://www.cbr-xml-daily.ru/daily_json.js"

    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
    except Exception:
        logger.exception("Не удалось получить курсы валют с %s", url)
        return [{"currency": code, "rate": None} for code in currencies]

    result: List[Dict[str, Any]] = []
    valute = data.get("Valute", {})

    for code in currencies:
        rate: Optional[float] = None
        info = valute.get(code)
        if info is not None:
            try:
                rate = float(info.get("Value"))
            except (TypeError, ValueError):
                rate = None
        result.append({"currency": code, "rate": rate})

    return result


def fetch_stock_prices(stocks: List[str]) -> List[Dict[str, Any]]:
    """
    Получает цены акций для указанных тикеров с помощью внешнего API.

    В качестве примера используется публичный demo-ключ Alpha Vantage.
    В случае ошибки возвращает price=None.
    """
    if not stocks:
        return []

    result: List[Dict[str, Any]] = []
    base_url = "https://www.alphavantage.co/query"
    api_key = "demo"

    for ticker in stocks:
        params = {"function": "GLOBAL_QUOTE", "symbol": ticker, "apikey": api_key}
        price: Optional[float] = None
        try:
            response = requests.get(base_url, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()
            quote = data.get("Global Quote") or data.get("GlobalQuote") or {}
            price_str = quote.get("05. price") or quote.get("05. Price")
            if price_str is not None:
                price = float(price_str)
        except Exception:
            logger.exception("Не удалось получить цену акции %s", ticker)

        result.append({"stock": ticker, "price": price})

    return result
