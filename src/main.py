from pathlib import Path

from src.reports import build_spending_by_category_report
from src.services import simple_search
from src.utils import load_transactions
from src.views import build_main_page_context


def main() -> None:
    """
    Entry point for the coursework application.

    Выполняет:
    1. Загрузку транзакций из Excel.
    2. Формирование контекста для главной страницы.
    3. Формирование отчёта "Траты по категориям".
    4. Демонстрацию работы сервиса "Простой поиск".
    """
    data_path = Path("data") / "operations.xlsx"
    df = load_transactions(data_path)

    # 1. Краткая информация
    print("=== Transactions summary ===")
    print(f"Total transactions: {len(df)}")

    # 2. Главная страница (контекст)
    main_context = build_main_page_context(df)
    print("\n=== Main page context ===")
    print(main_context)

    # 3. Отчёт "Траты по категориям" (по всем категориям за период)
    report_json = build_spending_by_category_report(
        df=df,
        category=None,
        start_date_str="2024-01-01",
    )
    print("\n=== Spending by category report (JSON) ===")
    print(report_json)

    # 4. Сервис "Простой поиск"
    transactions_list = df.to_dict(orient="records")
    search_json = simple_search("еда", transactions_list)
    print("\n=== Simple search for 'еда' (JSON) ===")
    print(search_json)


if __name__ == "__main__":
    main()
