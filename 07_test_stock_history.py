
import importlib.util
import logging
import tempfile
from datetime import date, timedelta
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


def write_parquet(file_path, schema, rows):
    table = pa.Table.from_pylist(
        rows,
        schema=schema,
    )

    pq.write_table(
        table,
        file_path,
        compression="snappy",
        use_dictionary=["ticker"],
        write_statistics=True,
    )


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s | %(message)s",
    )

    if not SOURCE_FILE.is_file():
        logging.error("Source Parquet not found: %s", SOURCE_FILE)
        return 1

    try:
        update_history = load_update_function()

        source_table = pq.read_table(SOURCE_FILE)

        if source_table.num_rows == 0:
            raise ValueError("Source Parquet has no data rows.")

        schema = source_table.schema
        sample_row = source_table.slice(0, 1).to_pylist()[0]

        # Use synthetic records so production data is never modified.
        first_row = dict(sample_row)
        first_row["ticker"] = "TESTX"
        first_row["date"] = date(2099, 1, 1)

        second_row = dict(first_row)
        second_row["date"] = date(2099, 1, 2)

        with tempfile.TemporaryDirectory(
            prefix="stock_history_test_"
        ) as temp_dir:
            temp_path = Path(temp_dir)

            test_source = temp_path / "source.parquet"
            test_target = temp_path / "history.parquet"

            # Test 1: a new candle is inserted.
            write_parquet(
                test_source,
                schema,
                [first_row],
            )

            result = update_history(test_source, test_target)

            assert result["inserted"] == 1
            assert result["updated"] == 0
            assert result["total"] == 1

            logging.info("Test 1 PASSED: new candle inserted.")

            # Test 2: a changed existing candle is updated.
            changed_row = dict(first_row)
            changed_row["close"] = float(first_row["close"]) + 1

            write_parquet(
                test_source,
                schema,
                [changed_row],
            )

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
            write_parquet(
                test_source,
                schema,
                [changed_row, second_row],
            )

            result = update_history(test_source, test_target)

            assert result["inserted"] == 1
            assert result["updated"] == 0
            assert result["total"] == 2

            logging.info("Test 4 PASSED: second date added.")

            stored_table = pq.read_table(test_target)
            stored_rows = stored_table.to_pylist()

            keys = {
                (row["ticker"], row["date"])
                for row in stored_rows
            }

            assert len(keys) == 2
            assert len(stored_rows) == 2

        logging.info("All tests passed. Temporary test data removed.")
        return 0

    except (
        OSError,
        ValueError,
        RuntimeError,
        AssertionError,
        TypeError,
        KeyError,
    ) as error:
        logging.error("Test failed: %s", error)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
