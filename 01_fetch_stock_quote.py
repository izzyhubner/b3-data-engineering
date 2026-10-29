
import json
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from stock_config import TICKERS


PROJECT_DIR = Path(__file__).resolve().parent
RAW_DIR = PROJECT_DIR / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

API_URL = "https://brapi.dev/api/quote/{}"


def fetch_quote(ticker):
    url = API_URL.format(ticker)
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "B3DataEngineeringPortfolio/1.0"},
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def main():
    successful_tickers = 0
    failed_tickers = 0

    for ticker in TICKERS:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        output_file = RAW_DIR / f"{ticker.lower()}_{timestamp}.json"

        try:
            payload = fetch_quote(ticker)

            results = payload.get("results", [])

            if not results:
                raise ValueError("API response contains no quote results.")

            with output_file.open("w", encoding="utf-8") as file:
                json.dump(payload, file, ensure_ascii=False, indent=2)

            print(f"File saved successfully: {output_file}")
            successful_tickers += 1

        except (
            urllib.error.URLError,
            TimeoutError,
            json.JSONDecodeError,
            ValueError,
            OSError,
        ) as error:
            print(
                f"Collection failed for {ticker}: "
                f"{type(error).__name__}: {error}"
            )
            failed_tickers += 1

    print()
    print("Collection summary")
    print(f"Successful tickers: {successful_tickers}")
    print(f"Failed tickers: {failed_tickers}")
    print(f"Total tickers: {len(TICKERS)}")

    if failed_tickers > 0:
        print("Collection status: FAILED")
        sys.exit(1)

    print("Collection status: PASSED")


if __name__ == "__main__":
    main()
