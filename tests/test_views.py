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
    data = {
        "Категория": ["Еда", "Транспорт", "Еда"],
        "Сумма платежа": [100.0, 50.0, 300.0],
        "Дата операции": ["2024-01-10", "2024-01-15", "2024-01-20"],
    }
    df = pd.DataFrame(data)
    df["Дата операции"] = pd.to_datetime(df["Дата операции"])
    return df


def test_build_main_page_context_basic(sample_df: pd.DataFrame) -> None:
    """Проверяем, что главная страница корректно считает статистику."""
    generated_at = datetime(2024, 1, 25, 12, 0, 0)

    context = build_main_page_context(sample_df, generated_at=generated_at)

    # Проверяем базовые ключи
    assert context["title"] == "Transactions dashboard"
    assert context["total_transactions"] == 3
    assert context["total_amount"] == 450.0  # 100 + 50 + 300

    # Проверяем топ категорий
    top = context["top_categories"]
    assert len(top) == 2

    # Категория "Еда" должна быть на первом месте
    assert top[0]["category"] == "Еда"
    assert top[0]["amount"] == 400.0

    # Есть generated_at
    assert context["generated_at"] == "2024-01-25 12:00:00"


def test_build_main_page_context_no_amount_column() -> None:
    """Если суммы нет — total_amount=None, топ категорий пустой."""
    df = pd.DataFrame({"Категория": ["A", "B", "A"]})

    context = build_main_page_context(df)

    assert context["total_amount"] is None
    assert context["top_categories"] == []


def test_main_page_returns_valid_json(sample_df: pd.DataFrame) -> None:
    """patch load_transactions → main_page не должен падать."""
    with patch("src.views.load_transactions", return_value=sample_df):
        response_json = main_page("2024-01-25 12:00:00")
        data = json.loads(response_json)

        assert "total_transactions" in data
        assert data["total_transactions"] == 3


def test_main_page_invalid_datetime() -> None:
    """Неверный формат даты — ValueError."""
    with pytest.raises(ValueError):
        main_page("2024/01/25 12-00-00")


def test_main_page_logs_info(sample_df: pd.DataFrame) -> None:
    """patch логгера — проверяем, что логгер вызывается."""
    with patch("src.views.load_transactions", return_value=sample_df):
        with patch("src.views.logger") as mock_logger:
            main_page("2024-01-25 12:00:00")
            assert mock_logger.info.called
