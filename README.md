# Coursework Transactions

Учебный проект по анализу банковских транзакций из Excel-файла.  
Проект реализует веб-страницу с общей статистикой, сервис простого поиска и отчёт по тратам.

## Функциональность проекта

### Главная страница (views.py)

Функция `main_page(current_time_str: str)` формирует JSON-ответ со следующими данными:

- общее количество транзакций;
- общая сумма трат;
- топ-3 категорий по сумме трат;
- дата и время генерации отчёта.

Функция использует модули:
- `datetime`
- `json`
- `pandas`
- `logging`.

### Простой поиск (services.py)

Функция `simple_search(query: str, transactions: list[dict])` выполняет поиск по подстроке в полях:

- "Описание";
- "Категория".

Возвращаемый JSON содержит:
- запрос;
- количество найденных транзакций;
- список найденных элементов.

Функция использует:
- `json`
- `logging`
- `pandas`.

### Отчёт "Траты по категориям" (reports.py)

Функция `build_spending_by_category_report(df, category, start_date_str)`:

- фильтрует операции по трёхмесячному периоду;
- группирует траты по категориям;
- вычисляет суммы;
- возвращает JSON-отчёт.

Использует:
- `datetime`
- `json`
- `pandas`
- `logging`.

## Установка и запуск

### Установка зависимостей

poetry install

### Создание файла окружения

cp .env_template .env

### Запуск приложения

poetry run python -m src.main

## Тестирование

Запуск тестов:        poetry run pytest -v

Покрытие тестами:       poetry run pytest --cov=src

HTML-отчёт покрытия:        poetry run pytest --cov=src --cov-report=html

Тесты используют:
- фикстуры;
- параметризацию;
- unittest.mock.patch;
- проверку JSON;
- проверку логирования.

## Стиль и анализ кода

Форматирование:    

poetry run black src tests

poetry run isort src tests

Линтер: poetry run flake8

Статический анализ типов: poetry run mypy src

Настройки инструментов находятся в файлах:
- `.flake8`
- `pyproject.toml`.

## Переменные окружения

### Шаблон `.env_template`

EXTERNAL_API_BASE_URL=https://api.example.com

EXTERNAL_API_TOKEN=your_api_token_here
APP_LOG_LEVEL=INFO

## Точка входа (main.py)

```python
from src.utils import load_transactions
from src.views import build_main_page_context
from src.reports import build_spending_by_category_report
from src.services import simple_search

def main() -> None:
    df = load_transactions()

    print("=== Main page ===")
    print(build_main_page_context(df))

    print("=== Spending report ===")
    print(build_spending_by_category_report(df, None, "2024-01-01"))

    print("=== Simple search ===")
    print(simple_search("еда", df.to_dict(orient="records")))

if __name__ == "__main__":
    main()
```

## Команда проекта:

`Чунаев Артем - student ` 

## Контакт для связи с командой разработки:

`artemiy9999@gmail.com` 

`Discord - artemhio`

## Источники

Материалы для изучения SKYPRO [skypro@skyeng.ru](https://sky.pro/#giftpopup)

Проект выполнен в рамках обучения на курсе SkyPro.