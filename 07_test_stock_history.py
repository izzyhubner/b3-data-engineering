
import csv
import importlib.util
import logging
import tempfile
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent
SOURCE_FILE = PROJECT_DIR / "data" / "processed" / "daily_stock_analysis.csv"
MODULE_FILE = PROJECT_DIR / "06_update_stock_history.py"


def load_update_function():
    spec = importlib.util.spec_from_file_location(
        "stock_history_module",
        MODULE_FILE,
    )

    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load stock history module.")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.update_history


def write_csv(file_path, fieldnames, rows):
    with file_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")

    if not SOURCE_FILE.is_file():
        logging.error("Source CSV not found: %s", SOURCE_FILE)
        return 1

    try:
        update_history = load_update_function()

        with SOURCE_FILE.open(
            "r", newline="", encoding="utf-8-sig"
        ) as file:
            reader = csv.DictReader(file)
            fieldnames = reader.fieldnames
            sample_row = next(reader, None)

        if not fieldnames or sample_row is None:
            raise ValueError("Source CSV has no data rows.")

        # Use synthetic records so production data is never modified.
        first_row = dict(sample_row)
        first_row["ticker"] = "TESTX"
        first_row["date"] = "2099-01-01"

        second_row = dict(first_row)
        second_row["date"] = "2099-01-02"

        with tempfile.TemporaryDirectory(prefix="stock_history_test_") as temp_dir:
            temp_path = Path(temp_dir)
            test_source = temp_path / "source.csv"
            test_target = temp_path / "history.csv"

            # Test 1: a new candle is inserted.
            write_csv(test_source, fieldnames, [first_row])
            result = update_history(test_source, test_target)

            assert result["inserted"] == 1
            assert result["updated"] == 0
            assert result["total"] == 1
            logging.info("Test 1 PASSED: new candle inserted.")

            # Test 2: a changed existing candle is updated.
            changed_row = dict(first_row)
            changed_row["close"] = str(float(first_row["close"]) + 1)

            write_csv(test_source, fieldnames, [changed_row])
            result = update_history(test_source, test_target)

            assert result["inserted"] == 0
            assert result["updated"] == 1
            assert result["total"] == 1
            logging.info("Test 2 PASSED: existing candle updated.")

            # Test 3: repeating the same input creates no duplicates.
            result = update_history(test_source, test_target)

            assert result["inserted"] == 0
            assert result["updated"] == 0
            assert result["total"] == 1
            logging.info("Test 3 PASSED: repeated run is idempotent.")

            # Test 4: another date is added without duplicating the first.
            write_csv(test_source, fieldnames, [changed_row, second_row])
            result = update_history(test_source, test_target)

            assert result["inserted"] == 1
            assert result["updated"] == 0
            assert result["total"] == 2
            logging.info("Test 4 PASSED: second date added.")

            with test_target.open(
                "r", newline="", encoding="utf-8-sig"
            ) as file:
                stored_rows = list(csv.DictReader(file))

            keys = {(row["ticker"], row["date"]) for row in stored_rows}
            assert len(keys) == 2
            assert len(stored_rows) == 2

        logging.info("All tests passed. Temporary test data removed.")
        return 0

    except (OSError, csv.Error, ValueError, RuntimeError, AssertionError) as error:
        logging.error("Test failed: %s", error)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
