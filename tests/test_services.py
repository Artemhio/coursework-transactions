import json
from typing import Any, Dict, List
from unittest.mock import patch

import pytest

from src.services import get_stub_service_result, simple_search


def test_get_stub_service_result_has_service_key() -> None:
    """Базовый тест-заглушка для сервиса (изначальный)."""
    result = get_stub_service_result()
    assert "service" in result


@pytest.fixture
def sample_transactions_list() -> List[Dict[str, Any]]:
    """
    Фикстура со списком транзакций в формате списка словарей.

    Используется для тестирования сервиса «Простой поиск».
    """
    return [
        {
            "Описание": "Покупка продуктов в магазине",
            "Категория": "Еда",
            "Сумма платежа": 150.0,
        },
        {
            "Описание": "Оплата проезда в метро",
            "Категория": "Транспорт",
            "Сумма платежа": 50.0,
        },
        {
            "Описание": "Заказ еды в доставке",
            "Категория": "Еда",
            "Сумма платежа": 800.0,
        },
    ]


def test_simple_search_empty_query_returns_all(
    sample_transactions_list: List[Dict[str, Any]],
) -> None:
    """Пустой запрос должен возвращать все транзакции без фильтрации."""
    response_json = simple_search("", sample_transactions_list)
    data = json.loads(response_json)

    assert data["query"] == ""
    assert data["total"] == len(sample_transactions_list)
    assert len(data["items"]) == len(sample_transactions_list)


@pytest.mark.parametrize(
    "query,expected_total",
    [
        ("еда", 2),          # найдём по "еда" в описании/категории
        ("транспорт", 1),    # найдём только одну транзакцию по категории
        ("магазин", 1),      # найдём по слову из описания
    ],
)
def test_simple_search_filters_by_query(
    sample_transactions_list: List[Dict[str, Any]],
    query: str,
    expected_total: int,
) -> None:
    """
    Проверяем, что поиск по подстроке корректно фильтрует транзакции
    по полям «Описание» и «Категория».
    """
    response_json = simple_search(query, sample_transactions_list)
    data = json.loads(response_json)

    assert data["query"] == query
    assert data["total"] == expected_total
    assert len(data["items"]) == expected_total

    # Дополнительно убедимся, что все найденные элементы содержат подстроку
    lower_query = query.lower()
    for item in data["items"]:
        text = (
            str(item.get("Описание", "")).lower()
            + " "
            + str(item.get("Категория", "")).lower()
        )
        assert lower_query in text


def test_simple_search_no_matches_returns_empty(
    sample_transactions_list: List[Dict[str, Any]],
) -> None:
    """Если совпадений нет, сервис должен вернуть пустой список items."""
    response_json = simple_search("несуществующий запрос", sample_transactions_list)
    data = json.loads(response_json)

    assert data["total"] == 0
    assert data["items"] == []


def test_simple_search_logs_info(
    sample_transactions_list: List[Dict[str, Any]],
) -> None:
    """Через patch проверяем, что сервис пишет информацию в логгер."""
    with patch("src.services.logger") as mock_logger:
        simple_search("еда", sample_transactions_list)
        assert mock_logger.info.called
