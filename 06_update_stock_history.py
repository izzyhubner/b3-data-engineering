
import logging
import os
import sys
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

TARGET_FILE = (
    PROJECT_DIR
    / "data"
    / "parquet"
    / "silver"
    / "daily_stock_history.parquet"
)

KEY_FIELDS = ["ticker", "date"]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def read_parquet(file_path):
    table = pq.read_table(file_path)

    if table.num_rows == 0:
        raise ValueError(f"Parquet file contains no rows: {file_path}")

    if not all(field in table.column_names for field in KEY_FIELDS):
        raise ValueError(
            f"Parquet must contain these key fields: {KEY_FIELDS}"
        )

    return table


def update_history(source_file, target_file):
    if not source_file.exists():
        raise FileNotFoundError(f"Source file not found: {source_file}")

    source_table = read_parquet(source_file)
    source_rows = source_table.to_pylist()

    target_file.parent.mkdir(parents=True, exist_ok=True)

    if target_file.exists():
        target_table = read_parquet(target_file)

        if not target_table.schema.equals(
            source_table.schema,
            check_metadata=False,
        ):
            raise ValueError(
                "Source and target Parquet schemas do not match. "
                "No data was changed."
            )

        target_rows = target_table.to_pylist()
    else:
        target_rows = []

    history = {}

    for row in target_rows:
        key = (row["ticker"], row["date"])

        if key in history:
            raise ValueError(
                f"Duplicate key already exists in target: {key}"
            )

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

    result_table = pa.Table.from_pylist(
        sorted_rows,
        schema=source_table.schema,
    )

    temporary_file = target_file.with_suffix(".tmp.parquet")

    try:
        pq.write_table(
            result_table,
            temporary_file,
            compression="snappy",
            use_dictionary=["ticker"],
            write_statistics=True,
        )

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

    except (OSError, ValueError, pa.ArrowException) as error:
        logging.exception("History update failed: %s", error)
        return 1


if __name__ == "__main__":
    sys.exit(main())
