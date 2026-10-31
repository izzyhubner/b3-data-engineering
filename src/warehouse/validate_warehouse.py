
import os
import sys
from pathlib import Path

import psycopg2
import pyarrow.parquet as pq


PROJECT_ROOT = Path(__file__).resolve().parents[2]

SILVER_PATH = (
    PROJECT_ROOT / "data" / "parquet" / "silver"
    / "daily_stock_history.parquet"
)

GOLD_PATH = (
    PROJECT_ROOT / "data" / "parquet" / "gold"
    / "daily_stock_indicators.parquet"
)

DB_CONFIG = {
    "host": os.getenv("B3_WAREHOUSE_HOST", "localhost"),
    "port": os.getenv("B3_WAREHOUSE_PORT", "5432"),
    "dbname": os.getenv("B3_WAREHOUSE_DB", "b3_warehouse"),
    "user": os.getenv("B3_WAREHOUSE_USER", "postgres"),
    "password": os.getenv("B3_WAREHOUSE_PASSWORD"),
}


def validate():
    if not DB_CONFIG["password"]:
        raise RuntimeError("B3_WAREHOUSE_PASSWORD is not configured.")

    silver = pq.read_table(SILVER_PATH).to_pylist()
    gold = pq.read_table(GOLD_PATH).to_pylist()

    source_keys = {
        (row["ticker"], row["date"])
        for row in silver
    }

    gold_keys = {
        (row["ticker"], row["date"])
        for row in gold
    }

    if source_keys != gold_keys:
        raise AssertionError("Silver and Gold source keys differ.")

    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:

            cur.execute("""
                SELECT
                    (SELECT COUNT(*) FROM dw.dim_stock),
                    (SELECT COUNT(*) FROM dw.dim_date),
                    (SELECT COUNT(*) FROM dw.fact_daily_stock),
                    (
                        SELECT COUNT(DISTINCT (stock_key, date_key))
                        FROM dw.fact_daily_stock
                    )
            """)

            stocks, dates, facts, unique_keys = cur.fetchone()

            cur.execute("""
                SELECT COUNT(*)
                FROM dw.fact_daily_stock f
                LEFT JOIN dw.dim_stock s
                    ON s.stock_key = f.stock_key
                LEFT JOIN dw.dim_date d
                    ON d.date_key = f.date_key
                WHERE s.stock_key IS NULL
                   OR d.date_key IS NULL
            """)

            orphan_records = cur.fetchone()[0]

            cur.execute("""
                SELECT s.ticker, d.full_date
                FROM dw.fact_daily_stock f
                JOIN dw.dim_stock s
                    ON s.stock_key = f.stock_key
                JOIN dw.dim_date d
                    ON d.date_key = f.date_key
            """)

            warehouse_keys = set(cur.fetchall())

    expected_stocks = len({row["ticker"] for row in silver})
    expected_dates = len({row["date"] for row in silver})

    expected = {
        "stocks": expected_stocks,
        "dates": expected_dates,
        "facts": len(source_keys),
        "unique_keys": len(source_keys),
    }

    actual = {
        "stocks": stocks,
        "dates": dates,
        "facts": facts,
        "unique_keys": unique_keys,
    }

    print("Warehouse validation")
    print("--------------------")

    for metric, expected_value in expected.items():
        actual_value = actual[metric]
        status = "PASS" if actual_value == expected_value else "FAIL"

        print(
            f"{metric}: {actual_value} "
            f"(expected: {expected_value}) [{status}]"
        )

        if actual_value != expected_value:
            raise AssertionError(f"Mismatch in {metric}.")

    if orphan_records:
        raise AssertionError(
            f"Found {orphan_records} fact records without dimensions."
        )

    if warehouse_keys != source_keys:
        raise AssertionError(
            "Warehouse ticker/date keys do not match source data."
        )

    print("Referential integrity: PASS")
    print("Source-to-Warehouse keys: PASS")
    print("\nAll Warehouse validations passed!")


if __name__ == "__main__":
    try:
        validate()
    except Exception as error:
        print(f"\nVALIDATION FAILED: {error}")
        sys.exit(1)
