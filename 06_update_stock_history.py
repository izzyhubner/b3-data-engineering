
import csv
import logging
import os
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
SOURCE_FILE = PROJECT_DIR / "data" / "processed" / "daily_stock_analysis.csv"
TARGET_FILE = PROJECT_DIR / "data" / "silver" / "daily_stock_history.csv"

KEY_FIELDS = ["ticker", "date"]

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

        if not all(field in reader.fieldnames for field in KEY_FIELDS):
            raise ValueError(
                f"CSV must contain these key fields: {KEY_FIELDS}"
            )

        return reader.fieldnames, list(reader)


def update_history(source_file, target_file):
    if not source_file.exists():
        raise FileNotFoundError(f"Source file not found: {source_file}")

    source_fields, source_rows = read_csv(source_file)

    if not source_rows:
        raise ValueError("Source CSV contains no rows.")

    target_file.parent.mkdir(parents=True, exist_ok=True)

    if target_file.exists():
        target_fields, target_rows = read_csv(target_file)

        if target_fields != source_fields:
            raise ValueError(
                "Source and target CSV columns do not match. "
                "No data was changed."
            )
    else:
        target_fields = source_fields
        target_rows = []

    history = {}

    for row in target_rows:
        key = (row["ticker"], row["date"])

        if key in history:
            raise ValueError(f"Duplicate key already exists in target: {key}")

        history[key] = row

    inserted = 0
    updated = 0

    for row in source_rows:
        key = (row["ticker"], row["date"])

        if not all(key):
            raise ValueError(f"Row has an empty key: {key}")

        if key not in history:
            history[key] = row
            inserted += 1
        elif history[key] != row:
            history[key] = row
            updated += 1

    sorted_rows = sorted(
        history.values(),
        key=lambda row: (row["ticker"], row["date"]),
    )

    temporary_file = target_file.with_suffix(".tmp")

    try:
        with temporary_file.open(
            "w",
            newline="",
            encoding="utf-8",
        ) as file:
            writer = csv.DictWriter(file, fieldnames=target_fields)
            writer.writeheader()
            writer.writerows(sorted_rows)

        os.replace(temporary_file, target_file)

    finally:
        if temporary_file.exists():
            temporary_file.unlink()

    return {
        "source_rows": len(source_rows),
        "inserted": inserted,
        "updated": updated,
        "total": len(sorted_rows),
    }


def main():
    try:
        result = update_history(SOURCE_FILE, TARGET_FILE)

        logging.info("Source rows processed: %s", result["source_rows"])
        logging.info("New candles inserted: %s", result["inserted"])
        logging.info("Existing candles updated: %s", result["updated"])
        logging.info("Total historical candles: %s", result["total"])
        logging.info("History file: %s", TARGET_FILE)
        logging.info("Status: PASSED")

        return 0

    except (OSError, csv.Error, ValueError) as error:
        logging.exception("History update failed: %s", error)
        return 1


if __name__ == "__main__":
    sys.exit(main())
