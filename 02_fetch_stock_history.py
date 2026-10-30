
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from stock_config import TICKERS


PROJECT_DIR = Path(__file__).resolve().parent
RAW_DIR = PROJECT_DIR / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

API_URL = "https://brapi.dev/api/v2/stocks/historical"


def fetch_history(ticker, token):
    params = urlencode(
        {
            "symbols": ticker,
            "range": "1mo",
            "interval": "1d",
            "sortOrder": "asc",
        }
    )
    url = f"{API_URL}?{params}"

    request = Request(
        url,
        headers={
            "User-Agent": "b3-data-engineering/1.0",
            "Authorization": f"Bearer {token}",
        },
    )

    with urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))

    results = payload.get("results", [])
    matching_result = next(
        (
            item
            for item in results
            if item.get("symbol", "").upper() == ticker.upper()
        ),
        None,
    )

    if matching_result is None:
        raise ValueError(f"No historical result returned for {ticker}.")

    history = matching_result.get("data", {}).get(
        "historicalDataPrice", []
    )

    if not history:
        raise ValueError(
            f"No historical price records returned for {ticker}."
        )

    return payload


def save_history(ticker, payload):
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    output_file = RAW_DIR / f"{ticker.lower()}_history_{timestamp}.json"

    with output_file.open("w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)

    return output_file


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s | %(message)s",
    )

    token = os.getenv("BRAPI_TOKEN")

    if not token or not token.strip():
        logging.error(
            "BRAPI_TOKEN environment variable is not configured."
        )
        sys.exit(1)

    successful = 0
    failed = 0

    for ticker in TICKERS:
        try:
            payload = fetch_history(ticker, token)
            output_file = save_history(ticker, payload)

            logging.info(
                "%s: historical data saved to %s",
                ticker,
                output_file,
            )
            successful += 1

        except (
            HTTPError,
            URLError,
            TimeoutError,
            OSError,
            ValueError,
            json.JSONDecodeError,
        ) as error:
            logging.error(
                "%s: collection failed: %s: %s",
                ticker,
                type(error).__name__,
                error,
            )
            failed += 1

    logging.info("Historical collection summary")
    logging.info("Successful tickers: %s", successful)
    logging.info("Failed tickers: %s", failed)
    logging.info("Total tickers: %s", len(TICKERS))

    if failed:
        logging.error("Historical collection status: FAILED")
        sys.exit(1)

    logging.info("Historical collection status: PASSED")


if __name__ == "__main__":
    main()
