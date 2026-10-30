
from collections import Counter
from datetime import date, datetime
from pathlib import Path

import pyarrow.parquet as pq


PROJECT_DIR = Path(__file__).resolve().parent
INPUT_FILE = (
    PROJECT_DIR
    / "data"
    / "parquet"
    / "processed"
    / "daily_stock_analysis.parquet"
)

if not INPUT_FILE.exists():
    raise FileNotFoundError(f"Input file not found: {INPUT_FILE}")

table = pq.read_table(INPUT_FILE)
rows = table.to_pylist()

if not rows:
    raise ValueError("The input Parquet file contains no data rows.")

required_fields = [
    "ticker",
    "date",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "close_return_pct",
    "gap_pct",
    "body_pct",
    "range_pct",
    "is_bullish",
]

missing_columns = [
    field for field in required_fields
    if field not in table.column_names
]

if missing_columns:
    raise ValueError(f"Missing columns: {missing_columns}")

issues = Counter()
details = []


def report_issue(issue_type, ticker, record_date, message):
    issues[issue_type] += 1
    details.append(
        f"{issue_type}: {ticker} {record_date} - {message}"
    )


def to_float(value):
    if value is None:
        raise ValueError("Value is null.")

    return float(value)


seen_keys = set()
previous_rows = {}

numeric_fields = [
    "open", "high", "low", "close", "volume",
    "body", "body_pct", "range", "range_pct",
    "upper_wick", "lower_wick", "close_position",
]

for row in rows:
    ticker = row["ticker"]
    ticker = ticker.strip() if ticker is not None else ""

    raw_date = row["date"]

    if isinstance(raw_date, (date, datetime)):
        record_date = raw_date.isoformat()
    else:
        record_date = str(raw_date).strip() if raw_date is not None else ""

    key = (ticker, record_date)

    if not ticker or not record_date:
        report_issue(
            "missing_identity",
            ticker or "UNKNOWN",
            record_date or "UNKNOWN",
            "Ticker or date is empty.",
        )
        continue

    if key in seen_keys:
        report_issue(
            "duplicate",
            ticker,
            record_date,
            "Duplicate ticker-date combination.",
        )

    seen_keys.add(key)

    for field in numeric_fields:
        value = row.get(field)

        try:
            number = to_float(value)
        except (ValueError, TypeError):
            report_issue(
                "missing_value",
                ticker,
                record_date,
                f"{field} is empty or invalid.",
            )
            continue

        if field in ["open", "high", "low", "close"] and number <= 0:
            report_issue(
                "invalid_price",
                ticker,
                record_date,
                f"{field} must be greater than zero.",
            )

        if field == "volume" and number < 0:
            report_issue(
                "invalid_volume",
                ticker,
                record_date,
                "Volume cannot be negative.",
            )

    try:
        open_price = to_float(row["open"])
        high_price = to_float(row["high"])
        low_price = to_float(row["low"])
        close_price = to_float(row["close"])
        volume = to_float(row["volume"])
    except (ValueError, TypeError):
        continue

    if high_price < max(open_price, close_price):
        report_issue(
            "price_consistency",
            ticker,
            record_date,
            "High is below open or close.",
        )

    if low_price > min(open_price, close_price):
        report_issue(
            "price_consistency",
            ticker,
            record_date,
            "Low is above open or close.",
        )

    if high_price < low_price:
        report_issue(
            "price_consistency",
            ticker,
            record_date,
            "High is below low.",
        )

    if volume < 0:
        report_issue(
            "invalid_volume",
            ticker,
            record_date,
            "Volume cannot be negative.",
        )

    expected_bullish = close_price > open_price
    actual_bullish = row["is_bullish"]

    if not isinstance(actual_bullish, bool):
        report_issue(
            "invalid_boolean",
            ticker,
            record_date,
            "is_bullish must be a boolean.",
        )
    elif actual_bullish != expected_bullish:
        report_issue(
            "metric_mismatch",
            ticker,
            record_date,
            "is_bullish does not match open and close.",
        )

    candle_range = high_price - low_price

    try:
        stored_range = to_float(row["range"])
        stored_body_pct = to_float(row["body_pct"])
        stored_range_pct = to_float(row["range_pct"])
        stored_close_position = to_float(row["close_position"])
    except (ValueError, TypeError):
        continue

    if abs(stored_range - candle_range) > 0.01:
        report_issue(
            "metric_mismatch",
            ticker,
            record_date,
            "range does not match high minus low.",
        )

    expected_body_pct = (
        (close_price - open_price) / open_price * 100
    )

    if abs(stored_body_pct - expected_body_pct) > 0.01:
        report_issue(
            "metric_mismatch",
            ticker,
            record_date,
            "body_pct does not match open and close.",
        )

    expected_range_pct = candle_range / open_price * 100

    if abs(stored_range_pct - expected_range_pct) > 0.01:
        report_issue(
            "metric_mismatch",
            ticker,
            record_date,
            "range_pct does not match high, low, and open.",
        )

    if candle_range > 0:
        expected_close_position = (
            (close_price - low_price) / candle_range
        )

        if abs(
            stored_close_position - expected_close_position
        ) > 0.01:
            report_issue(
                "metric_mismatch",
                ticker,
                record_date,
                "close_position is inconsistent.",
            )

    if not 0 <= stored_close_position <= 1:
        report_issue(
            "invalid_metric",
            ticker,
            record_date,
            "close_position must be between 0 and 1.",
        )

    previous = previous_rows.get(ticker)

    if previous is not None:
        previous_close = previous["close"]

        if previous_close > 0:
            expected_return = (
                (close_price / previous_close) - 1
            ) * 100

            expected_gap = (
                (open_price / previous_close) - 1
            ) * 100

            try:
                stored_return = to_float(row["close_return_pct"])
                stored_gap = to_float(row["gap_pct"])
            except (ValueError, TypeError):
                report_issue(
                    "missing_metric",
                    ticker,
                    record_date,
                    "Return or gap is missing or invalid.",
                )
            else:
                if abs(stored_return - expected_return) > 0.02:
                    report_issue(
                        "metric_mismatch",
                        ticker,
                        record_date,
                        "close_return_pct is inconsistent.",
                    )

                if abs(stored_gap - expected_gap) > 0.02:
                    report_issue(
                        "metric_mismatch",
                        ticker,
                        record_date,
                        "gap_pct is inconsistent.",
                    )

    previous_rows[ticker] = {
        "close": close_price,
        "date": record_date,
    }


print("STOCK DATA QUALITY REPORT")
print("=" * 40)
print(f"Rows checked: {len(rows)}")
print(f"Unique ticker-date combinations: {len(seen_keys)}")
print(f"Total issues found: {sum(issues.values())}")

if issues:
    print("\nIssues by category:")

    for issue_type, count in sorted(issues.items()):
        print(f"- {issue_type}: {count}")

    print("\nIssue details:")

    for detail in details:
        print(f"- {detail}")
else:
    print("Status: PASSED")
    print("No data quality issues detected.")

print(f"\nInput file: {INPUT_FILE}")
