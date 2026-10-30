
import importlib.util
import logging
import math
import statistics
from datetime import date, timedelta
from pathlib import Path
from unittest import TestCase


PROJECT_DIR = Path(__file__).resolve().parent
MODULE_FILE = PROJECT_DIR / "11_build_gold_indicators.py"


def load_calculation_function():
    spec = importlib.util.spec_from_file_location(
        "gold_indicators_module",
        MODULE_FILE,
    )

    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load Gold indicators module.")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module.calculate_indicators


def create_stock_rows(ticker="TESTX", count=20):
    rows = []

    for index in range(count):
        rows.append({
            "ticker": ticker,
            "date": date(2099, 1, 1) + timedelta(days=index),
            "close": str(100 + index),
            "volume": str(1000 + (index * 100)),
        })

    return rows


def assert_optional_almost_equal(test_case, actual, expected):
    if expected is None:
        test_case.assertIsNone(actual)
    else:
        test_case.assertIsNotNone(actual)
        test_case.assertTrue(
            math.isclose(
                actual,
                expected,
                rel_tol=1e-9,
                abs_tol=1e-9,
            ),
            f"Expected {expected}, got {actual}",
        )


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s | %(message)s",
    )

    test_case = TestCase()

    try:
        calculate_indicators = load_calculation_function()

        # Test 1: moving averages require enough historical closes.
        rows = create_stock_rows(count=20)
        result = calculate_indicators(rows)

        assert len(result) == 20
        assert result[3]["sma_5"] is None

        assert_optional_almost_equal(
            test_case,
            result[4]["sma_5"],
            102,
        )

        assert result[18]["sma_20"] is None

        assert_optional_almost_equal(
            test_case,
            result[19]["sma_20"],
            109.5,
        )

        logging.info("Test 1 PASSED: SMA calculation windows.")

        # Test 2: daily return compares consecutive closing prices.
        expected_return = ((101 / 100) - 1) * 100

        assert_optional_almost_equal(
            test_case,
            result[1]["daily_return_pct"],
            expected_return,
        )

        assert result[0]["daily_return_pct"] is None

        logging.info("Test 2 PASSED: daily return calculation.")

        # Test 3: volatility requires five valid daily returns.
        expected_returns = [
            ((101 / 100) - 1) * 100,
            ((102 / 101) - 1) * 100,
            ((103 / 102) - 1) * 100,
            ((104 / 103) - 1) * 100,
            ((105 / 104) - 1) * 100,
        ]

        expected_volatility = statistics.stdev(expected_returns)

        assert result[4]["volatility_5d"] is None

        assert_optional_almost_equal(
            test_case,
            result[5]["volatility_5d"],
            expected_volatility,
        )

        logging.info("Test 3 PASSED: five-day volatility calculation.")

        # Test 4: volume ratio uses the five previous trading days.
        expected_volume_ratio = 1500 / 1200

        assert result[4]["volume_ratio"] is None

        assert_optional_almost_equal(
            test_case,
            result[5]["volume_ratio"],
            expected_volume_ratio,
        )

        logging.info("Test 4 PASSED: volume ratio calculation.")

        # Test 5: tickers are calculated independently.
        first_ticker = create_stock_rows("TESTX", 5)
        second_ticker = create_stock_rows("TESTY", 5)

        for row in second_ticker:
            row["close"] = str(float(row["close"]) * 2)

        combined_rows = first_ticker + second_ticker
        result = calculate_indicators(combined_rows)

        testx_rows = [
            row for row in result
            if row["ticker"] == "TESTX"
        ]

        testy_rows = [
            row for row in result
            if row["ticker"] == "TESTY"
        ]

        assert len(testx_rows) == 5
        assert len(testy_rows) == 5
        assert testx_rows[4]["sma_5"] == 102
        assert testy_rows[4]["sma_5"] == 204

        logging.info("Test 5 PASSED: ticker calculations are independent.")

        # Test 6: records are sorted chronologically.
        unsorted_rows = [
            {
                "ticker": "TESTX",
                "date": date(2099, 1, 3),
                "close": "102",
                "volume": "1200",
            },
            {
                "ticker": "TESTX",
                "date": date(2099, 1, 1),
                "close": "100",
                "volume": "1000",
            },
            {
                "ticker": "TESTX",
                "date": date(2099, 1, 2),
                "close": "101",
                "volume": "1100",
            },
        ]

        result = calculate_indicators(unsorted_rows)
        dates = [row["date"] for row in result]

        assert dates == [
            date(2099, 1, 1),
            date(2099, 1, 2),
            date(2099, 1, 3),
        ]

        logging.info("Test 6 PASSED: records sorted by date.")

        # Test 7: repeated calculations produce identical results.
        first_result = calculate_indicators(rows)
        second_result = calculate_indicators(rows)

        assert first_result == second_result

        logging.info("Test 7 PASSED: calculations are consistent.")

        # Test 8: empty input returns an empty result.
        result = calculate_indicators([])

        assert result == []

        logging.info("Test 8 PASSED: empty input handled correctly.")

        logging.info("All Gold indicator tests passed.")
        return 0

    except (OSError, RuntimeError, AssertionError, ValueError, KeyError, TypeError) as error:
        logging.error("Gold indicator test failed: %s", error)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
