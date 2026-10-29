
import json
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent
CONFIG_FILE = PROJECT_DIR / "config" / "stocks.json"


def load_tickers():
    if not CONFIG_FILE.exists():
        raise FileNotFoundError(
            f"Stock configuration file not found: {CONFIG_FILE}"
        )

    with CONFIG_FILE.open("r", encoding="utf-8") as file:
        config = json.load(file)

    tickers = config.get("tickers")

    if not isinstance(tickers, list) or not tickers:
        raise ValueError(
            "The 'tickers' configuration must be a non-empty list."
        )

    normalized_tickers = []

    for ticker in tickers:
        if not isinstance(ticker, str) or not ticker.strip():
            raise ValueError(
                "Every ticker must be a non-empty string."
            )

        normalized_tickers.append(ticker.strip().upper())

    if len(normalized_tickers) != len(set(normalized_tickers)):
        raise ValueError("Duplicate tickers found in configuration.")

    return normalized_tickers


TICKERS = load_tickers()
