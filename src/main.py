from pathlib import Path

from src.utils import load_transactions


def main() -> None:
    """Entry point for the coursework application."""
    data_path = Path("data") / "operations.xlsx"
    df = load_transactions(data_path)
    print(f"Loaded {len(df)} transactions.")


if __name__ == "__main__":
    main()
