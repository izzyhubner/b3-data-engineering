
import json
import logging
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from stock_config import TICKERS


PROJECT_DIR = Path(__file__).resolve().parent
RAW_DIR = PROJECT_DIR / "data" / "raw"
PROCESSED_DIR = PROJECT_DIR / "data" / "parquet" / "processed"
OUTPUT_FILE = PROCESSED_DIR / "daily_stock_analysis.parquet"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

SCHEMA = pa.schema([
    ("ticker", pa.string()),
    ("date", pa.date32()),
    ("open", pa.float64()),
    ("high", pa.float64()),
    ("low", pa.float64()),
    ("close", pa.float64()),
    ("volume", pa.float64()),
    ("body", pa.float64()),
    ("body_pct", pa.float64()),
    ("range", pa.float64()),
    ("range_pct", pa.float64()),
    ("upper_wick", pa.float64()),
    ("lower_wick", pa.float64()),
    ("close_position", pa.float64()),
    ("is_bullish", pa.bool_()),
    ("close_return_pct", pa.float64()),
    ("gap_pct", pa.float64()),
    ("candle_body", pa.float64()),
    ("candle_range", pa.float64()),
    ("upper_shadow", pa.float64()),
    ("lower_shadow", pa.float64()),
    ("daily_return_pct", pa.float64()),
    ("overnight_gap_pct", pa.float64()),
    ("volume_avg_5d", pa.float64()),
])


def load_latest_history(ticker):
    files = list(RAW_DIR.glob(f"{ticker.lower()}_history_*.json"))

    if not files:
        raise FileNotFoundError(f"No history JSON found for {ticker}.")

    latest_file = max(files, key=lambda path: path.stat().st_mtime)

    with latest_file.open("r", encoding="utf-8") as file:
        payload = json.load(file)

    results = payload.get("results", [])
    result = next(
        (
            item for item in results
            if item.get("symbol", "").upper() == ticker
        ),
        None,
    )

    if result is None:
        raise ValueError(f"No matching API result for {ticker}.")

    history = result.get("data", {}).get("historicalDataPrice", [])

    if not history:
        raise ValueError(f"No historical records found for {ticker}.")

    return latest_file, history


def transform_history(ticker, history):
    records = []

    for item in history:
        timestamp = item.get("date")

        if timestamp is None:
            continue

        date_value = datetime.fromtimestamp(
            int(timestamp), timezone.utc
        ).date()

        records.append({
            "ticker": ticker,
            "date": date_value,
            "open": item.get("open"),
            "high": item.get("high"),
            "low": item.get("low"),
            "close": item.get("close"),
            "volume": item.get("volume"),
        })

    records.sort(key=lambda row: row["date"])

    output = []
    previous_close = None
    recent_volumes = []

    for row in records:
        if any(
            row[field] is None
            for field in ("open", "high", "low", "close", "volume")
        ):
            logging.warning(
                "Skipping incomplete record: %s %s",
                ticker, row["date"],
            )
            continue

        open_price, high_price, low_price, close_price = (
            float(row[field])
            for field in ("open", "high", "low", "close")
        )
        volume = float(row["volume"])

        if open_price <= 0:
            logging.warning(
                "Skipping non-positive open: %s %s",
                ticker, row["date"],
            )
            continue

        body = close_price - open_price
        candle_range = high_price - low_price
        upper_wick = high_price - max(open_price, close_price)
        lower_wick = min(open_price, close_price) - low_price

        body_pct = body / open_price * 100
        range_pct = candle_range / open_price * 100
        close_position = (
            (close_price - low_price) / candle_range
            if candle_range > 0 else 0.0
        )
        is_bullish = close_price > open_price

        close_return_pct = None
        gap_pct = None

        if previous_close is not None and previous_close > 0:
            close_return_pct = (
                close_price / previous_close - 1
            ) * 100
            gap_pct = (
                open_price / previous_close - 1
            ) * 100

        volume_avg_5d = (
            sum(recent_volumes) / len(recent_volumes)
            if recent_volumes else None
        )

        output.append({
            "ticker": ticker,
            "date": row["date"],
            "open": open_price,
            "high": high_price,
            "low": low_price,
            "close": close_price,
            "volume": volume,
            "body": body,
            "body_pct": body_pct,
            "range": candle_range,
            "range_pct": range_pct,
            "upper_wick": upper_wick,
            "lower_wick": lower_wick,
            "close_position": close_position,
            "is_bullish": is_bullish,
            "close_return_pct": close_return_pct,
            "gap_pct": gap_pct,
            "candle_body": body,
            "candle_range": candle_range,
            "upper_shadow": upper_wick,
            "lower_shadow": lower_wick,
            "daily_return_pct": close_return_pct,
            "overnight_gap_pct": gap_pct,
            "volume_avg_5d": volume_avg_5d,
        })

        recent_volumes.append(volume)
        recent_volumes = recent_volumes[-5:]
        previous_close = close_price

    if not output:
        raise ValueError(f"No valid records transformed for {ticker}.")

    return output


def write_parquet(records):
    table = pa.Table.from_pylist(records, schema=SCHEMA)

    temporary_file = OUTPUT_FILE.with_suffix(".tmp.parquet")

    pq.write_table(
        table,
        temporary_file,
        compression="snappy",
        use_dictionary=["ticker"],
        write_statistics=True,
    )

    temporary_file.replace(OUTPUT_FILE)

    return table.num_rows


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s | %(message)s",
    )

    all_rows = []
    failed_tickers = []

    for ticker in TICKERS:
        try:
            source_file, history = load_latest_history(ticker)
            rows = transform_history(ticker, history)
            all_rows.extend(rows)

            logging.info(
                "%s: transformed %s records from %s",
                ticker, len(rows), source_file.name,
            )

        except (
            FileNotFoundError,
            json.JSONDecodeError,
            ValueError,
            OSError,
            TypeError,
        ) as error:
            logging.error(
                "%s: transformation failed: %s: %s",
                ticker, type(error).__name__, error,
            )
            failed_tickers.append(ticker)

    if failed_tickers:
        logging.error(
            "Transformation status: FAILED | Tickers: %s",
            ", ".join(failed_tickers),
        )
        sys.exit(1)

    unique_rows = {
        (row["ticker"], row["date"]): row
        for row in all_rows
    }

    final_rows = sorted(
        unique_rows.values(),
        key=lambda row: (row["ticker"], row["date"]),
    )

    rows_written = write_parquet(final_rows)

    logging.info("Transformation status: PASSED")
    logging.info("Tickers processed: %s", len(TICKERS))
    logging.info("Rows written: %s", rows_written)
    logging.info("Output file: %s", OUTPUT_FILE)


if __name__ == "__main__":
    main()
