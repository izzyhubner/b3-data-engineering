
import logging
import sys
from datetime import date, datetime
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq


PROJECT_DIR = Path(__file__).resolve().parent

SOURCE_FILE = (
    PROJECT_DIR
    / "data"
    / "parquet"
    / "processed"
    / "daily_stock_analysis.parquet"
)

HISTORY_FILE = (
    PROJECT_DIR
    / "data"
    / "parquet"
    / "silver"
    / "daily_stock_history.parquet"
)

KEY_FIELDS = ["ticker", "date"]
PRICE_FIELDS = ["open", "high", "low", "close"]


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def read_parquet(file_path):
    table = pq.read_table(file_path)

    if table.num_rows == 0:
        return table.column_names, []

    return table.column_names, table.to_pylist()


def normalize_date(value):
    if isinstance(value, (date, datetime)):
        return value.isoformat()

    return str(value).strip() if value is not None else ""


def validate_rows(rows, file_label):
    issues = []
    seen_keys = set()

    for row_number, row in enumerate(rows, start=1):
        ticker = row.get("ticker")
        ticker = ticker.strip() if ticker is not None else ""
        record_date = normalize_date(row.get("date"))

        if not ticker or not record_date:
            issues.append(
                f"{file_label}, row {row_number}: empty ticker or date."
            )
            continue

        key = (ticker, record_date)

        if key in seen_keys:
            issues.append(
                f"{file_label}, row {row_number}: duplicate key {key}."
            )
        else:
            seen_keys.add(key)

        prices = {}

        for field in PRICE_FIELDS:
            value = row.get(field)

            if value is None:
                issues.append(
                    f"{file_label}, row {row_number}: empty {field}."
                )
                continue

            try:
                prices[field] = float(value)
            except (ValueError, TypeError):
                issues.append(
                    f"{file_label}, row {row_number}: invalid {field}={value!r}."
                )

        if len(prices) == len(PRICE_FIELDS):
            if min(prices.values()) < 0:
                issues.append(
                    f"{file_label}, row {row_number}: negative price."
                )

            if prices["high"] < max(prices["open"], prices["close"]):
                issues.append(
                    f"{file_label}, row {row_number}: high is below open or close."
                )

            if prices["low"] > min(prices["open"], prices["close"]):
                issues.append(
                    f"{file_label}, row {row_number}: low is above open or close."
                )

            if prices["high"] < prices["low"]:
                issues.append(
                    f"{file_label}, row {row_number}: high is below low."
                )

    return issues, seen_keys


def main():
    try:
        for file_path in (SOURCE_FILE, HISTORY_FILE):
            if not file_path.is_file():
                logging.error("Required file not found: %s", file_path)
                return 1

        source_fields, source_rows = read_parquet(SOURCE_FILE)
        history_fields, history_rows = read_parquet(HISTORY_FILE)

        for required_field in KEY_FIELDS + PRICE_FIELDS:
            if required_field not in source_fields:
                logging.error(
                    "Source Parquet is missing required field: %s",
                    required_field,
                )
                return 1

            if required_field not in history_fields:
                logging.error(
                    "History Parquet is missing required field: %s",
                    required_field,
                )
                return 1

        if not history_rows:
            logging.error("Persistent history contains no records.")
            return 1

        source_issues, source_keys = validate_rows(
            source_rows, "Source Parquet"
        )

        history_issues, history_keys = validate_rows(
            history_rows, "Persistent history"
        )

        missing_keys = source_keys - history_keys
        issues = source_issues + history_issues

        for key in sorted(missing_keys):
            issues.append(
                f"Current source candle is missing from history: {key}."
            )

        if len(history_rows) < len(source_rows):
            issues.append(
                "Persistent history has fewer rows than the current source."
            )

        logging.info("Current source rows: %s", len(source_rows))
        logging.info("Persistent history rows: %s", len(history_rows))
        logging.info("Unique history ticker-date keys: %s", len(history_keys))
        logging.info(
            "Current source keys missing from history: %s",
            len(missing_keys),
        )
        logging.info("Total issues found: %s", len(issues))

        if issues:
            for issue in issues[:50]:
                logging.error("%s", issue)

            if len(issues) > 50:
                logging.error(
                    "Additional issues omitted from log: %s",
                    len(issues) - 50,
                )

            logging.error("Validation status: FAILED")
            return 1

        logging.info("Validation status: PASSED")
        return 0

    except (OSError, ValueError, pa.ArrowException) as error:
        logging.exception(
            "Persistent history validation failed: %s",
            error,
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
