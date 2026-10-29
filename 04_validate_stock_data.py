
import csv
from collections import Counter
from pathlib import Path


project_dir = Path(__file__).resolve().parent
input_file = (
    project_dir / "data" / "processed" / "daily_stock_analysis.csv"
)

if not input_file.exists():
    raise FileNotFoundError(f"Input file not found: {input_file}")

with input_file.open("r", encoding="utf-8-sig", newline="") as file:
    reader = csv.DictReader(file)
    rows = list(reader)

if not rows:
    raise ValueError("The input CSV contains no data rows.")

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
    if field not in (reader.fieldnames or [])
]

if missing_columns:
    raise ValueError(f"Missing columns: {missing_columns}")

issues = Counter()
details = []

def report_issue(issue_type, ticker, date, message):
    issues[issue_type] += 1
    details.append(f"{issue_type}: {ticker} {date} - {message}")


seen_keys = set()
previous_rows = {}

for row in rows:
    ticker = row["ticker"].strip()
    date = row["date"].strip()
    key = (ticker, date)

    if not ticker or not date:
        report_issue(
            "missing_identity",
            ticker or "UNKNOWN",
            date or "UNKNOWN",
            "Ticker or date is empty.",
        )
        continue

    if key in seen_keys:
        report_issue(
            "duplicate",
            ticker,
            date,
            "Duplicate ticker-date combination.",
        )
    seen_keys.add(key)

    numeric_fields = [
        "open", "high", "low", "close", "volume",
        "body", "body_pct", "range", "range_pct",
        "upper_wick", "lower_wick", "close_position",
    ]

    for field in numeric_fields:
        value = row.get(field, "").strip()

        if not value:
            report_issue(
                "missing_value", ticker, date,
                f"{field} is empty.",
            )
            continue

        try:
            number = float(value)
        except ValueError:
            report_issue(
                "invalid_number", ticker, date,
                f"{field} is not numeric.",
            )
            continue

        if field in ["open", "high", "low", "close"] and number <= 0:
            report_issue(
                "invalid_price", ticker, date,
                f"{field} must be greater than zero.",
            )

        if field == "volume" and number < 0:
            report_issue(
                "invalid_volume", ticker, date,
                "Volume cannot be negative.",
            )

    try:
        open_price = float(row["open"])
        high_price = float(row["high"])
        low_price = float(row["low"])
        close_price = float(row["close"])
        volume = float(row["volume"])
    except (ValueError, TypeError):
        continue

    if high_price < max(open_price, close_price):
        report_issue(
            "price_consistency", ticker, date,
            "High is below open or close.",
        )

    if low_price > min(open_price, close_price):
        report_issue(
            "price_consistency", ticker, date,
            "Low is above open or close.",
        )

    if high_price < low_price:
        report_issue(
            "price_consistency", ticker, date,
            "High is below low.",
        )

    if volume < 0:
        report_issue(
            "invalid_volume", ticker, date,
            "Volume cannot be negative.",
        )

    expected_bullish = close_price > open_price
    actual_bullish = row["is_bullish"].strip().lower()

    if actual_bullish not in ["true", "false"]:
        report_issue(
            "invalid_boolean", ticker, date,
            "is_bullish must be True or False.",
        )
    elif (actual_bullish == "true") != expected_bullish:
        report_issue(
            "metric_mismatch", ticker, date,
            "is_bullish does not match open and close.",
        )

    candle_range = high_price - low_price

    try:
        stored_range = float(row["range"])
        stored_body_pct = float(row["body_pct"])
        stored_range_pct = float(row["range_pct"])
        stored_close_position = float(row["close_position"])
    except (ValueError, TypeError):
        continue

    if abs(stored_range - candle_range) > 0.01:
        report_issue(
            "metric_mismatch", ticker, date,
            "range does not match high minus low.",
        )

    expected_body_pct = (close_price - open_price) / open_price * 100

    if abs(stored_body_pct - expected_body_pct) > 0.01:
        report_issue(
            "metric_mismatch", ticker, date,
            "body_pct does not match open and close.",
        )

    expected_range_pct = candle_range / open_price * 100

    if abs(stored_range_pct - expected_range_pct) > 0.01:
        report_issue(
            "metric_mismatch", ticker, date,
            "range_pct does not match high, low, and open.",
        )

    if candle_range > 0:
        expected_close_position = (
            (close_price - low_price) / candle_range
        )

        if abs(stored_close_position - expected_close_position) > 0.01:
            report_issue(
                "metric_mismatch", ticker, date,
                "close_position is inconsistent.",
            )

    if not 0 <= stored_close_position <= 1:
        report_issue(
            "invalid_metric", ticker, date,
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
                stored_return = float(row["close_return_pct"])
                stored_gap = float(row["gap_pct"])
            except (ValueError, TypeError):
                report_issue(
                    "missing_metric", ticker, date,
                    "Return or gap is missing or invalid.",
                )
            else:
                if abs(stored_return - expected_return) > 0.02:
                    report_issue(
                        "metric_mismatch", ticker, date,
                        "close_return_pct is inconsistent.",
                    )

                if abs(stored_gap - expected_gap) > 0.02:
                    report_issue(
                        "metric_mismatch", ticker, date,
                        "gap_pct is inconsistent.",
                    )

    previous_rows[ticker] = {
        "close": close_price,
        "date": date,
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

print(f"\nInput file: {input_file}")
