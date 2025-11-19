import json
import logging
from typing import Any, Dict, List

import pandas as pd  # type: ignore[import-untyped]

logger = logging.getLogger(__name__)


def get_stub_service_result() -> dict:
    """
    Простейший "заглушка"-сервис.

    Нужен для того, чтобы базовый тест на сервисы проходил.
    Основная логика сервисов реализуется в других функциях этого модуля.
    """
    return {"service": "stub", "result": "not implemented yet"}


def _search_dataframe(df: pd.DataFrame, query: str) -> pd.DataFrame:
    """
    Вспомогательная функция для поиска по DataFrame.

    Поиск идёт по подстроке (без учёта регистра) в столбцах:
    - "Описание"
    - "Категория" (если такой столбец есть).
    """
    if not query:
        return df.copy()

    mask = pd.Series(False, index=df.index)
    lower_query = query.lower()

    if "Описание" in df.columns:
        desc_mask = df["Описание"].astype(str).str.lower().str.contains(lower_query)
        mask |= desc_mask

    if "Категория" in df.columns:
        cat_mask = df["Категория"].astype(str).str.lower().str.contains(lower_query)
        mask |= cat_mask

    return df[mask].copy()


def simple_search(query: str, transactions: List[Dict[str, Any]]) -> str:
    """
    Реализует сервис «Простой поиск» по транзакциям.

    Функция принимает строку-запрос и список транзакций (каждая транзакция —
    словарь), выполняет поиск по подстроке в полях «Описание» и «Категория»,
    а затем возвращает результат в виде JSON-строки.

    Параметры:
    ----------
    query : str
        Строка-запрос для поиска (без учёта регистра).
    transactions : list[dict]
        Список транзакций в формате списка словарей.

    Возвращает:
    -----------
    str
        JSON-строка с результатами поиска вида:
        {
            "query": "...",
            "total": <количество найденных>,
            "items": [ {...}, {...}, ... ]
        }
    """
    logger.info("Запуск сервиса 'Простой поиск' с запросом: %s", query)

    # Преобразуем входные данные в DataFrame для удобной фильтрации
    if transactions:
        df = pd.DataFrame(transactions)
    else:
        df = pd.DataFrame()

    logger.debug("Получено транзакций для поиска: %d", len(df))

    filtered_df = _search_dataframe(df, query)
    logger.debug("Найдено транзакций по запросу '%s': %d", query, len(filtered_df))

    items: List[Dict[str, Any]] = filtered_df.to_dict(orient="records")

    result = {
        "query": query,
        "total": len(items),
        "items": items,
    }

    logger.info(
        "Сервис 'Простой поиск' завершён: найдено %d результатов.",
        len(items),
    )

    # Возвращаем JSON-строку (как в ТЗ: корректный JSON-ответ)
    return json.dumps(result, ensure_ascii=False)
