
import csv
import logging
import statistics
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent
SOURCE_FILE = PROJECT_DIR / "data" / "silver" / "daily_stock_history.csv"
OUTPUT_DIR = PROJECT_DIR / "data" / "gold"
OUTPUT_FILE = OUTPUT_DIR / "daily_stock_indicators.csv"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def load_silver_data():
    if not SOURCE_FILE.exists():
        raise FileNotFoundError(
            f"Silver dataset not found: {SOURCE_FILE}"
        )

    with SOURCE_FILE.open("r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        rows = list(reader)

    if not rows:
        raise ValueError("Silver dataset is empty.")

    return rows


def calculate_indicators(rows):
    grouped_data = {}

    for row in rows:
        ticker = row["ticker"]

        grouped_data.setdefault(ticker, []).append(row)

    output_rows = []

    for ticker, ticker_rows in grouped_data.items():
        ticker_rows.sort(key=lambda row: row["date"])

        closes = []
        returns = []
        volumes = []

        for row in ticker_rows:
            close = float(row["close"])
            volume = float(row["volume"])

            closes.append(close)
            volumes.append(volume)

            sma_5 = (
                sum(closes[-5:]) / 5
                if len(closes) >= 5
                else None
            )

            sma_20 = (
                sum(closes[-20:]) / 20
                if len(closes) >= 20
                else None
            )

            if len(closes) >= 2:
                daily_return = (
                    (closes[-1] / closes[-2]) - 1
                ) * 100
            else:
                daily_return = None

            returns.append(daily_return)

            valid_returns = [
                value for value in returns[-5:]
                if value is not None
            ]

            volatility_5d = (
                statistics.stdev(valid_returns)
                if len(valid_returns) == 5
                else None
            )

            previous_volumes = volumes[-6:-1]

            volume_ratio = (
                volume / (sum(previous_volumes) / 5)
                if len(previous_volumes) == 5
                and sum(previous_volumes) > 0
                else None
            )

            output_rows.append({
                "ticker": ticker,
                "date": row["date"],
                "close": close,
                "daily_return_pct": daily_return,
                "sma_5": sma_5,
                "sma_20": sma_20,
                "volatility_5d": volatility_5d,
                "volume": volume,
                "volume_ratio": volume_ratio,
            })

    return output_rows


def save_gold_data(rows):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "ticker",
        "date",
        "close",
        "daily_return_pct",
        "sma_5",
        "sma_20",
        "volatility_5d",
        "volume",
        "volume_ratio",
    ]

    with OUTPUT_FILE.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        for row in rows:
            writer.writerow({
                key: (
                    round(value, 6)
                    if isinstance(value, float)
                    else value
                )
                for key, value in row.items()
            })

    logging.info("Gold dataset saved: %s", OUTPUT_FILE)
    logging.info("Records generated: %s", len(rows))


def main():
    logging.info("Starting Gold indicators generation.")

    silver_rows = load_silver_data()
    logging.info("Silver records loaded: %s", len(silver_rows))

    gold_rows = calculate_indicators(silver_rows)
    save_gold_data(gold_rows)

    logging.info("Gold indicators generation completed successfully.")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        logging.exception("Gold indicators generation failed.")
        raise
