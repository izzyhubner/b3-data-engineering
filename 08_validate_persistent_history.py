

import csv
import logging
import sys
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent
SOURCE_FILE = PROJECT_DIR / "data" / "processed" / "daily_stock_analysis.csv"
HISTORY_FILE = PROJECT_DIR / "data" / "silver" / "daily_stock_history.csv"

KEY_FIELDS = ["ticker", "date"]
PRICE_FIELDS = ["open", "high", "low", "close"]


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def read_csv(file_path):
    with file_path.open("r", newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)

        if not reader.fieldnames:
            raise ValueError(f"CSV has no header: {file_path}")

        return reader.fieldnames, list(reader)


def validate_rows(rows, file_label):
    issues = []
    seen_keys = set()

    for row_number, row in enumerate(rows, start=2):
        ticker = (row.get("ticker") or "").strip()
        date = (row.get("date") or "").strip()

        if not ticker or not date:
            issues.append(
                f"{file_label}, row {row_number}: empty ticker or date."
            )
            continue

        key = (ticker, date)

        if key in seen_keys:
            issues.append(
                f"{file_label}, row {row_number}: duplicate key {key}."
            )
        else:
            seen_keys.add(key)

        prices = {}

        for field in PRICE_FIELDS:
            value = (row.get(field) or "").strip()

            if not value:
                issues.append(
                    f"{file_label}, row {row_number}: empty {field}."
                )
                continue

            try:
                prices[field] = float(value)
            except ValueError:
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

        source_fields, source_rows = read_csv(SOURCE_FILE)
        history_fields, history_rows = read_csv(HISTORY_FILE)

        for required_field in KEY_FIELDS + PRICE_FIELDS:
            if required_field not in source_fields:
                logging.error(
                    "Source CSV is missing required field: %s",
                    required_field,
                )
                return 1

            if required_field not in history_fields:
                logging.error(
                    "History CSV is missing required field: %s",
                    required_field,
                )
                return 1

        if not history_rows:
            logging.error("Persistent history contains no records.")
            return 1

        source_issues, source_keys = validate_rows(
            source_rows, "Source CSV"
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
        logging.info("Current source keys missing from history: %s", len(missing_keys))
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

    except (OSError, csv.Error, ValueError) as error:
        logging.exception("Persistent history validation failed: %s", error)
        return 1


if __name__ == "__main__":
    sys.exit(main())
