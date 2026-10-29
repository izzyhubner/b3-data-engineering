# B3 Stock Market Data Pipeline

A Python-based data engineering project that collects, transforms, validates, and maintains daily stock market data from the Brazilian stock exchange (B3).

The project currently focuses on building a reliable local data pipeline, with plans to evolve into a cloud-based Lakehouse and Data Warehouse architecture.

## Project Goals

- Collect stock quotes and historical market data.
- Store raw API responses for traceability.
- Transform daily stock data into analytical features.
- Validate data quality and consistency.
- Maintain a persistent historical dataset through idempotent upserts.
- Automate pipeline execution and raw data retention.

## Architecture

The pipeline follows a layered data organization:

```text
API (brapi)
    |
    v
data/raw/
    |
    v
data/processed/
    |
    |  Upsert by ticker and date
    v
data/silver/
```

### Data Layers

| Layer | Purpose |
|---|---|
| Raw | Timestamped JSON snapshots from the API |
| Processed | Transformed daily stock analysis |
| Silver | Persistent historical dataset, updated through upserts |

## Technologies

- Python
- REST API
- JSON
- CSV
- Logging
- Data validation
- Automated pipeline execution

## Supported Stocks

The current pipeline collects data for:

- PETR4
- VALE3
- ITUB4
- MGLU3

## Pipeline Workflow

Run the complete pipeline using:

```powershell
python .\05_run_pipeline.py
```

The pipeline executes the following stages:

| Script | Responsibility |
|---|---|
| `01_fetch_stock_quote.py` | Collects current stock quotes |
| `02_fetch_stock_history.py` | Collects daily historical data |
| `03_transform_stock_history.py` | Transforms raw data into analytical features |
| `04_validate_stock_data.py` | Validates the processed dataset |
| `06_update_stock_history.py` | Upserts data into persistent Silver storage |
| `08_validate_persistent_history.py` | Validates the persistent historical dataset |
| `10_cleanup_raw_data.py` | Removes older raw snapshots according to retention rules |

Additional utility scripts:

- `07_test_stock_history.py`: tests the historical upsert logic.
- `09_inventory_raw_data.py`: inventories raw files without modifying them.

## Analytical Features

The transformed dataset includes standard OHLCV fields:

- Open
- High
- Low
- Close
- Volume

It also derives analytical features useful for market analysis:

| Feature | Description |
|---|---|
| `body` | Difference between closing and opening prices |
| `body_pct` | Candle body as a percentage of opening price |
| `range` | Difference between high and low prices |
| `range_pct` | Daily range as a percentage of opening price |
| `upper_wick` | Upper candle shadow |
| `lower_wick` | Lower candle shadow |
| `close_position` | Closing price position within the daily range |
| `is_bullish` | Indicates whether the close was above the open |
| `daily_return_pct` | Percentage change from the previous close |
| `overnight_gap_pct` | Percentage difference between the current open and previous close |
| `volume_avg_5d` | Average volume of up to the five previous available trading sessions, excluding the current session |

These features provide a foundation for studying price action, volatility, trading volume, and candlestick behavior.

## Data Quality and Reliability

The project includes validation at both the processed and persistent data stages.

Current checks include:

- Required fields and data types.
- Unique stock and date combinations.
- Positive price values.
- OHLC consistency.
- Formula consistency for derived features.
- Presence of source records in persistent storage.

The historical update process uses `(ticker, date)` as its business key.

Repeated pipeline executions do not create duplicate records. Existing records are updated when their values change.

### Latest Validation Results

The latest successful pipeline execution reported:

- 88 processed records.
- 88 unique ticker-date keys.
- 0 validation issues.
- 0 missing source records in persistent storage.

These figures describe the latest recorded run and may change as historical data grows.

## Raw Data Retention

Raw API snapshots are retained according to configurable rules:

- Latest quote snapshot per ticker.
- Latest three historical snapshots per ticker.

Older files are removed by the cleanup stage. The cleanup script also supports manual execution with confirmation.

## Project Structure

```text
b3-data-engineering/
|
|-- 01_fetch_stock_quote.py
|-- 02_fetch_stock_history.py
|-- 03_transform_stock_history.py
|-- 04_validate_stock_data.py
|-- 05_run_pipeline.py
|-- 06_update_stock_history.py
|-- 07_test_stock_history.py
|-- 08_validate_persistent_history.py
|-- 09_inventory_raw_data.py
|-- 10_cleanup_raw_data.py
|
|-- data/
|   |-- raw/
|   |-- processed/
|   |-- silver/
|
|-- logs/
|
|-- .gitignore
|-- README.md
```

## Current Status

The local pipeline is operational and has successfully completed all seven stages, including data collection, transformation, validation, persistent upsert, and raw data cleanup.

The current implementation is a foundation for future development.

## Future Improvements

- Expand historical coverage.
- Add more B3 tickers.
- Implement automated scheduling.
- Introduce automated tests for additional pipeline components.
- Build a Delta Lake-based Lakehouse.
- Develop a dimensional Data Warehouse.
- Extend the architecture to AWS cloud services.

---

**Disclaimer:** This project is intended for data engineering practice and market data analysis. It does not provide investment recommendations.