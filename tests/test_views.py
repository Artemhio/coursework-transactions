import json
from datetime import datetime
from typing import Any, Dict, List
from unittest.mock import patch

import pandas as pd
import pytest

from src.views import (
    get_index_context,
    build_main_page_context,
    main_page,
)


def test_get_index_context_returns_title() -> None:
    """Базовый тест-заглушка (изначальный)."""
    context = get_index_context()
    assert context["title"] == "Transactions dashboard"


@pytest.fixture
def sample_df() -> pd.DataFrame:
    """Фикстура с тестовыми транзакциями для views."""
    data: Dict[str, List[Any]] = {
        "Номер карты": ["1111", "1111", "2222"],
        "Категория": ["Еда", "Транспорт", "Еда"],
        "Сумма платежа": [100.0, 50.0, 300.0],
        "Дата операции": ["2024-01-10", "2024-01-15", "2024-01-20"],
        "Описание": ["Покупка 1", "Проезд", "Покупка 2"],
    }
    df = pd.DataFrame(data)
    df["Дата операции"] = pd.to_datetime(df["Дата операции"])
    return df


def test_build_main_page_context_basic(sample_df: pd.DataFrame) -> None:
    """Проверяем, что главная страница формирует контекст по ТЗ."""
    current_time = datetime(2024, 1, 25, 12, 0, 0)

    context = build_main_page_context(sample_df, current_time=current_time)

    # Приветствие
    assert context["greeting"] == "Добрый день"

    # Карты: две карты с номерами 1111 и 2222
    cards = context["cards"]
    assert isinstance(cards, list)
    assert len(cards) == 2

    first_card = cards[0]
    assert first_card["last_digits"] == "1111"
    assert first_card["total_spent"] == 400.0
    assert first_card["cashback"] == 4.0

    # Топ транзакций: 3 штуки, отсортированы по сумме
    top_tx = context["top_transactions"]
    assert isinstance(top_tx, list)
    assert len(top_tx) == 3
    assert top_tx[0]["amount"] == 300.0
    assert top_tx[0]["category"] == "Еда"
    assert top_tx[0]["description"] == "Покупка 2"


def test_build_main_page_context_no_amount_column() -> None:
    """
    Если нет столбца 'Сумма платежа', то список карт и топ транзакций
    должны быть пустыми.
    """
    df = pd.DataFrame(
        {
            "Номер карты": ["1111", "2222"],
            "Категория": ["A", "B"],
        }
    )
    current_time = datetime(2024, 1, 25, 12, 0, 0)

    context = build_main_page_context(df, current_time=current_time)

    assert context["cards"] == []
    assert context["top_transactions"] == []


def test_main_page_returns_valid_json(sample_df: pd.DataFrame) -> None:
    """main_page должен возвращать корректный JSON с нужными ключами."""
    with patch("src.views.load_transactions", return_value=sample_df), patch(
        "src.views.fetch_currency_rates", return_value=[{"currency": "USD", "rate": 73.21}]
    ), patch(
        "src.views.fetch_stock_prices", return_value=[{"stock": "AAPL", "price": 150.12}]
    ):
        response_json = main_page("2024-01-25 12:00:00")
        data = json.loads(response_json)

        assert data["greeting"] == "Добрый день"
        assert "cards" in data
        assert "top_transactions" in data
        assert "currency_rates" in data
        assert "stock_prices" in data

        assert data["currency_rates"] == [{"currency": "USD", "rate": 73.21}]
        assert data["stock_prices"] == [{"stock": "AAPL", "price": 150.12}]


def test_main_page_invalid_datetime() -> None:
    """Неверный формат даты — ValueError."""
    with pytest.raises(ValueError):
        main_page("2024/01/25 12-00-00")


def test_main_page_logs_info(sample_df: pd.DataFrame) -> None:
    """Через patch проверяем, что логгер главной страницы вызывается."""
    with patch("src.views.load_transactions", return_value=sample_df), patch(
        "src.views.fetch_currency_rates", return_value=[]
    ), patch("src.views.fetch_stock_prices", return_value=[]), patch(
        "src.views.logger"
    ) as mock_logger:
        main_page("2024-01-25 12:00:00")
        assert mock_logger.info.called
