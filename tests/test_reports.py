import json
from unittest.mock import patch

import pandas as pd
import pytest

from src.reports import (
    build_spending_by_category_report,
    get_stub_report,
    spending_by_category,
)


def test_get_stub_report_has_status() -> None:
    """Базовый тест-заглушка для отчётов (изначальный)."""
    report = get_stub_report()
    assert report.get("status") == "ok"


@pytest.fixture
def sample_transactions_df() -> pd.DataFrame:
    """Фикстура с небольшим набором транзакций для тестов отчётов."""
    data = {
        "Дата операции": [
            "2024-01-10",
            "2024-02-05",
            "2024-03-15",
            "2024-04-20",
        ],
        "Категория": ["Еда", "Еда", "Транспорт", "Еда"],
        "Сумма платежа": [100.0, 200.0, 50.0, 300.0],
    }
    df = pd.DataFrame(data)
    df["Дата операции"] = pd.to_datetime(df["Дата операции"])
    return df


@pytest.mark.parametrize(
    "category,expected_total,expected_items",
    [
        ("Еда", 300.0, 1),   # только категория "Еда" в окне 3 месяцев
        (None, 350.0, 2),    # все категории в окне 3 месяцев
    ],
)
def test_build_spending_by_category_report_basic(
    sample_transactions_df: pd.DataFrame,
    category: str | None,
    expected_total: float,
    expected_items: int,
) -> None:
    """
    Проверяем, что отчёт по тратам формируется корректно
    для конкретной категории и для всех категорий.
    """
    # Период: с 2024-01-01 на 90 дней → захватывает 10.01, 05.02, 15.03
    report_json = build_spending_by_category_report(
        sample_transactions_df,
        category=category,
        start_date_str="2024-01-01",
    )

    data = json.loads(report_json)

    assert data["start_date"] == "2024-01-01"
    assert data["total_amount"] == expected_total
    assert len(data["items"]) == expected_items


def test_build_spending_by_category_report_invalid_date_format(
    sample_transactions_df: pd.DataFrame,
) -> None:
    """Некорректный формат даты должен приводить к ValueError."""
    with pytest.raises(ValueError):
        build_spending_by_category_report(
            sample_transactions_df,
            category=None,
            start_date_str="01-01-2024",  # неверный формат
        )


def test_spending_by_category_groups_correctly(
    sample_transactions_df: pd.DataFrame,
) -> None:
    """Проверяем корректность группировки по категориям."""
    grouped = spending_by_category(sample_transactions_df, amount_column="Сумма платежа")

    # Ожидаем, что в отчёте будут две категории: "Еда" и "Транспорт"
    categories = set(grouped["Категория"].tolist())
    assert categories == {"Еда", "Транспорт"}

    # Проверяем суммы по категориям
    amounts = dict(zip(grouped["Категория"], grouped["Сумма платежа"]))
    assert amounts["Еда"] == 100.0 + 200.0 + 300.0
    assert amounts["Транспорт"] == 50.0


def test_build_spending_by_category_report_logs_info(
    sample_transactions_df: pd.DataFrame,
) -> None:
    """
    Используем patch, чтобы проверить, что строящий отчёт код
    пишет информацию в логгер.
    """
    with patch("src.reports.logger") as mock_logger:
        build_spending_by_category_report(
            sample_transactions_df,
            category=None,
            start_date_str="2024-01-01",
        )
        assert mock_logger.info.called
