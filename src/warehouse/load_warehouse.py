
import math
import os
from datetime import date
from pathlib import Path

import pyarrow.parquet as pq
import psycopg2
from psycopg2.extras import execute_values


# --------------------------------------------------
# Configuration
# --------------------------------------------------

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

FACT_COLUMNS = [
    "stock_key",
    "date_key",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "body",
    "body_pct",
    "range",
    "range_pct",
    "upper_wick",
    "lower_wick",
    "close_position",
    "is_bullish",
    "close_return_pct",
    "gap_pct",
    "candle_body",
    "candle_range",
    "upper_shadow",
    "lower_shadow",
    "daily_return_pct",
    "overnight_gap_pct",
    "volume_avg_5d",
    "sma_5",
    "sma_20",
    "volatility_5d",
    "volume_ratio",
]

SILVER_COLUMNS = [
    "open",
    "high",
    "low",
    "close",
    "volume",
    "body",
    "body_pct",
    "range",
    "range_pct",
    "upper_wick",
    "lower_wick",
    "close_position",
    "is_bullish",
    "close_return_pct",
    "gap_pct",
    "candle_body",
    "candle_range",
    "upper_shadow",
    "lower_shadow",
    "daily_return_pct",
    "overnight_gap_pct",
    "volume_avg_5d",
]

GOLD_COLUMNS = [
    "sma_5",
    "sma_20",
    "volatility_5d",
    "volume_ratio",
]


# --------------------------------------------------
# Helpers
# --------------------------------------------------

def read_parquet(path):
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")

    return pq.read_table(path).to_pylist()


def validate_source_data(silver_rows, gold_rows):
    silver_keys = [(r["ticker"], r["date"]) for r in silver_rows]
    gold_keys = [(r["ticker"], r["date"]) for r in gold_rows]

    if len(silver_keys) != len(set(silver_keys)):
        raise ValueError("Duplicate keys found in Silver dataset.")

    if len(gold_keys) != len(set(gold_keys)):
        raise ValueError("Duplicate keys found in Gold dataset.")

    if set(silver_keys) != set(gold_keys):
        raise ValueError(
            "Silver and Gold datasets have different ticker/date keys."
        )

    print(f"Silver records: {len(silver_rows)}")
    print(f"Gold records:   {len(gold_rows)}")
    print("Source key validation passed.")


def date_key(value):
    return int(value.strftime("%Y%m%d"))


def clean_value(value):
    if isinstance(value, float) and math.isnan(value):
        return None
    return value


def build_date_dimension(dates):
    rows = []

    for current_date in sorted(dates):
        rows.append((
            date_key(current_date),
            current_date,
            current_date.year,
            (current_date.month - 1) // 3 + 1,
            current_date.month,
            current_date.day,
            current_date.isoweekday(),
            current_date.strftime("%A"),
            current_date.strftime("%B"),
            current_date.isoweekday() >= 6,
        ))

    return rows


# --------------------------------------------------
# Dimension loads
# --------------------------------------------------

def load_stock_dimension(cursor, tickers):
    values = [(ticker,) for ticker in sorted(tickers)]

    execute_values(
        cursor,
        """
        INSERT INTO dw.dim_stock (ticker)
        VALUES %s
        ON CONFLICT (ticker) DO NOTHING
        """,
        values,
    )

    cursor.execute(
        "SELECT ticker, stock_key FROM dw.dim_stock"
    )

    return {
        ticker: stock_key
        for ticker, stock_key in cursor.fetchall()
    }


def load_date_dimension(cursor, dates):
    values = build_date_dimension(dates)

    execute_values(
        cursor,
        """
        INSERT INTO dw.dim_date (
            date_key,
            full_date,
            year,
            quarter,
            month,
            day,
            day_of_week,
            day_name,
            month_name,
            is_weekend
        )
        VALUES %s
        ON CONFLICT (date_key) DO UPDATE SET
            full_date = EXCLUDED.full_date,
            year = EXCLUDED.year,
            quarter = EXCLUDED.quarter,
            month = EXCLUDED.month,
            day = EXCLUDED.day,
            day_of_week = EXCLUDED.day_of_week,
            day_name = EXCLUDED.day_name,
            month_name = EXCLUDED.month_name,
            is_weekend = EXCLUDED.is_weekend
        """,
        values,
    )


# --------------------------------------------------
# Fact load
# --------------------------------------------------

def load_fact_table(cursor, silver_rows, gold_by_key, stock_keys):
    values = []

    for silver in silver_rows:
        key = (silver["ticker"], silver["date"])
        gold = gold_by_key[key]

        row = [
            stock_keys[silver["ticker"]],
            date_key(silver["date"]),
        ]

        row.extend(silver[column] for column in SILVER_COLUMNS)
        row.extend(gold[column] for column in GOLD_COLUMNS)

        values.append(tuple(clean_value(v) for v in row))

    columns_sql = ", ".join(FACT_COLUMNS)
    update_columns = [
        column for column in FACT_COLUMNS
        if column not in ("stock_key", "date_key")
    ]
    update_sql = ", ".join(
        f"{column} = EXCLUDED.{column}"
        for column in update_columns
    )

    execute_values(
        cursor,
        f"""
        INSERT INTO dw.fact_daily_stock ({columns_sql})
        VALUES %s
        ON CONFLICT (stock_key, date_key)
        DO UPDATE SET {update_sql}
        """,
        values,
        page_size=500,
    )

    return len(values)


# --------------------------------------------------
# Main
# --------------------------------------------------

def main():
    if not DB_CONFIG["password"]:
        raise RuntimeError(
            "Missing B3_WAREHOUSE_PASSWORD environment variable."
        )

    print("Reading Silver and Gold datasets...")

    silver_rows = read_parquet(SILVER_PATH)
    gold_rows = read_parquet(GOLD_PATH)

    validate_source_data(silver_rows, gold_rows)

    gold_by_key = {
        (row["ticker"], row["date"]): row
        for row in gold_rows
    }

    tickers = {row["ticker"] for row in silver_rows}
    dates = {row["date"] for row in silver_rows}

    print("\nConnecting to PostgreSQL...")

    with psycopg2.connect(**DB_CONFIG) as connection:
        with connection.cursor() as cursor:
            print("Loading dim_stock...")
            stock_keys = load_stock_dimension(cursor, tickers)

            print("Loading dim_date...")
            load_date_dimension(cursor, dates)

            print("Loading fact_daily_stock...")
            fact_count = load_fact_table(
                cursor,
                silver_rows,
                gold_by_key,
                stock_keys,
            )

        # The connection context commits only if all operations succeed.

    print("\nWarehouse load completed successfully.")
    print(f"Tickers processed: {len(tickers)}")
    print(f"Dates processed:   {len(dates)}")
    print(f"Fact rows loaded:  {fact_count}")


if __name__ == "__main__":
    main()
