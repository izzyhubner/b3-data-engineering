
import logging
import math
import statistics
from collections import Counter
from pathlib import Path

import pyarrow.parquet as pq


PROJECT_DIR = Path(__file__).resolve().parent

SOURCE_FILE = (
    PROJECT_DIR
    / "data"
    / "parquet"
    / "silver"
    / "daily_stock_history.parquet"
)

GOLD_FILE = (
    PROJECT_DIR
    / "data"
    / "parquet"
    / "gold"
    / "daily_stock_indicators.parquet"
)

SILVER_FIELDS = {
    "ticker",
    "date",
    "close",
    "volume",
}

GOLD_FIELDS = {
    "ticker",
    "date",
    "close",
    "daily_return_pct",
    "sma_5",
    "sma_20",
    "volatility_5d",
    "volume",
    "volume_ratio",
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def load_parquet(file_path, required_fields):
    if not file_path.exists():
        raise FileNotFoundError(
            f"Dataset not found: {file_path}"
        )

    table = pq.read_table(file_path)

    missing_fields = required_fields - set(table.column_names)

    if missing_fields:
        raise ValueError(
            f"Missing required fields in {file_path.name}: "
            f"{sorted(missing_fields)}"
        )

    return table.to_pylist()


def validate_gold(source_rows, gold_rows):
    issues = []

    source_keys = {
        (row["ticker"], row["date"])
        for row in source_rows
    }

    gold_keys = [
        (row["ticker"], row["date"])
        for row in gold_rows
    ]

    duplicate_keys = [
        key
        for key, count in Counter(gold_keys).items()
        if count > 1
    ]

    if duplicate_keys:
        issues.append(
            f"Duplicate ticker-date keys: {len(duplicate_keys)}"
        )

    gold_key_set = set(gold_keys)

    missing_keys = source_keys - gold_key_set
    unexpected_keys = gold_key_set - source_keys

    if missing_keys:
        issues.append(
            f"Missing source records: {len(missing_keys)}"
        )

    if unexpected_keys:
        issues.append(
            f"Unexpected Gold records: {len(unexpected_keys)}"
        )

    grouped_rows = {}

    for row in gold_rows:
        grouped_rows.setdefault(row["ticker"], []).append(row)

    for ticker, rows in grouped_rows.items():
        rows.sort(key=lambda row: row["date"])

        closes = []
        returns = []
        volumes = []

        for row in rows:
            try:
                close = float(row["close"])
                volume = float(row["volume"])

                if not math.isfinite(close) or close <= 0:
                    issues.append(
                        f"{ticker} {row['date']}: invalid close"
                    )

                if not math.isfinite(volume) or volume < 0:
                    issues.append(
                        f"{ticker} {row['date']}: invalid volume"
                    )

                closes.append(close)
                volumes.append(volume)

                expected_sma_5 = (
                    sum(closes[-5:]) / 5
                    if len(closes) >= 5
                    else None
                )

                expected_sma_20 = (
                    sum(closes[-20:]) / 20
                    if len(closes) >= 20
                    else None
                )

                expected_return = (
                    (closes[-1] / closes[-2] - 1) * 100
                    if len(closes) >= 2
                    else None
                )

                returns.append(expected_return)

                valid_returns = [
                    value for value in returns[-5:]
                    if value is not None
                ]

                expected_volatility = (
                    statistics.stdev(valid_returns)
                    if len(valid_returns) == 5
                    else None
                )

                previous_volumes = volumes[-6:-1]

                expected_volume_ratio = (
                    volume / (sum(previous_volumes) / 5)
                    if len(previous_volumes) == 5
                    and sum(previous_volumes) > 0
                    else None
                )

                expected_values = {
                    "daily_return_pct": expected_return,
                    "sma_5": expected_sma_5,
                    "sma_20": expected_sma_20,
                    "volatility_5d": expected_volatility,
                    "volume_ratio": expected_volume_ratio,
                }

                for field, expected in expected_values.items():
                    actual_value = row[field]

                    if expected is None:
                        if actual_value is not None:
                            issues.append(
                                f"{ticker} {row['date']}: "
                                f"{field} should be null"
                            )
                        continue

                    if actual_value is None:
                        issues.append(
                            f"{ticker} {row['date']}: "
                            f"{field} is unexpectedly null"
                        )
                        continue

                    actual = float(actual_value)

                    if not math.isfinite(actual):
                        issues.append(
                            f"{ticker} {row['date']}: "
                            f"{field} is not finite"
                        )
                        continue

                    if not math.isclose(
                        actual,
                        expected,
                        rel_tol=1e-5,
                        abs_tol=1e-5,
                    ):
                        issues.append(
                            f"{ticker} {row['date']}: "
                            f"{field} calculation mismatch"
                        )

            except (ValueError, TypeError, ZeroDivisionError) as error:
                issues.append(
                    f"{ticker} {row['date']}: invalid data - {error}"
                )

    return issues, len(source_keys), len(gold_keys), len(duplicate_keys)


def main():
    logging.info("Starting Gold data validation.")

    source_rows = load_parquet(SOURCE_FILE, SILVER_FIELDS)
    gold_rows = load_parquet(GOLD_FILE, GOLD_FIELDS)

    logging.info("Silver records loaded: %s", len(source_rows))
    logging.info("Gold records loaded: %s", len(gold_rows))

    issues, source_count, gold_count, duplicate_count = (
        validate_gold(source_rows, gold_rows)
    )

    logging.info("Unique Silver keys: %s", source_count)
    logging.info("Gold records: %s", gold_count)
    logging.info("Duplicate Gold keys: %s", duplicate_count)
    logging.info("Validation issues: %s", len(issues))

    for issue in issues:
        logging.error(issue)

    if issues:
        raise ValueError(
            f"Gold validation failed with {len(issues)} issue(s)."
        )

    logging.info("Gold data validation completed successfully.")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        logging.exception("Gold data validation failed.")
        raise
