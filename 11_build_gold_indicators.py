
import logging
import os
import statistics
from datetime import date, datetime
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq


PROJECT_DIR = Path(__file__).resolve().parent

SOURCE_FILE = (
    PROJECT_DIR
    / "data"
    / "parquet"
    / "silver"
    / "daily_stock_history.parquet"
)

OUTPUT_DIR = PROJECT_DIR / "data" / "parquet" / "gold"
OUTPUT_FILE = OUTPUT_DIR / "daily_stock_indicators.parquet"

SCHEMA = pa.schema([
    ("ticker", pa.string()),
    ("date", pa.date32()),
    ("close", pa.float64()),
    ("daily_return_pct", pa.float64()),
    ("sma_5", pa.float64()),
    ("sma_20", pa.float64()),
    ("volatility_5d", pa.float64()),
    ("volume", pa.float64()),
    ("volume_ratio", pa.float64()),
])

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

    table = pq.read_table(SOURCE_FILE)

    if table.num_rows == 0:
        raise ValueError("Silver dataset is empty.")

    required_fields = ["ticker", "date", "close", "volume"]
    missing_fields = [
        field for field in required_fields
        if field not in table.column_names
    ]

    if missing_fields:
        raise ValueError(
            f"Silver dataset is missing fields: {missing_fields}"
        )

    return table.to_pylist()


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

    rounded_rows = []

    for row in rows:
        rounded_rows.append({
            key: (
                round(value, 6)
                if isinstance(value, float)
                else value
            )
            for key, value in row.items()
        })

    table = pa.Table.from_pylist(
        rounded_rows,
        schema=SCHEMA,
    )

    temporary_file = OUTPUT_FILE.with_suffix(".tmp.parquet")

    try:
        pq.write_table(
            table,
            temporary_file,
            compression="snappy",
            use_dictionary=["ticker"],
            write_statistics=True,
        )

        os.replace(temporary_file, OUTPUT_FILE)

    finally:
        if temporary_file.exists():
            temporary_file.unlink()

    logging.info("Gold dataset saved: %s", OUTPUT_FILE)
    logging.info("Records generated: %s", table.num_rows)


def main():
    logging.info("Starting Gold indicators generation.")

    silver_rows = load_silver_data()
    logging.info("Silver records loaded: %s", len(silver_rows))

    gold_rows = calculate_indicators(silver_rows)
    save_gold_data(gold_rows)

    logging.info(
        "Gold indicators generation completed successfully."
    )


if __name__ == "__main__":
    try:
        main()
    except Exception:
        logging.exception("Gold indicators generation failed.")
        raise
