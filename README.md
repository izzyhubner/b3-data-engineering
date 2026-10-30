# B3 Data Engineering

A data engineering portfolio project focused on collecting, transforming, validating, and maintaining Brazilian stock market data.

The project uses B3 stock market data from the [Brapi API](https://brapi.dev/) to build a local data pipeline, with a future roadmap toward a cloud-based Lakehouse and Data Warehouse architecture.

## Project Overview

The pipeline collects daily stock quotes and historical OHLCV data for a configurable list of Brazilian stocks.

Data flows through three layers:

```text
Brapi API
    |
    v
   Raw
    |
    v
 Processed
    |
    v
  Silver
```

- **Raw:** Original API responses stored as JSON snapshots.
- **Processed:** Transformed daily stock data enriched with technical and price-related metrics.
- **Silver:** Persistent historical dataset maintained through an idempotent upsert process.

## Current Status

The local pipeline is operational and has successfully processed 10 stock tickers.

| Component | Current Status |
|---|---|
| Stock quote ingestion | Operational |
| Historical data ingestion | Operational |
| Configurable ticker list | Implemented |
| Data transformation | Implemented |
| Data quality validation | Implemented |
| Persistent Silver layer | Implemented |
| Idempotent upsert | Implemented |
| Automated raw data cleanup | Implemented |
| Pipeline orchestration | Implemented |
| Structured logging | Implemented |
| Python version | 3.14 |

Latest successful execution:

- 10 tickers collected.
- 220 historical records transformed.
- 220 unique ticker-date combinations validated.
- 0 data quality issues.
- 0 missing historical keys.
- 7 pipeline steps completed successfully.

## Technologies

- Python 3.14
- Brapi API
- JSON
- CSV
- Git and GitHub
- PowerShell

The current implementation relies primarily on Python's standard library.

## Project Structure

```text
b3-data-engineering/
│
├── config/
│   └── stocks.json
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── silver/
│
├── logs/
│
├── 01_fetch_stock_quote.py
├── 02_fetch_stock_history.py
├── 03_transform_stock_history.py
├── 04_validate_stock_data.py
├── 05_run_pipeline.py
├── 06_update_stock_history.py
├── 07_test_stock_history.py
├── 08_validate_persistent_history.py
├── 09_inventory_raw_data.py
├── 10_cleanup_raw_data.py
│
├── stock_config.py
├── .gitignore
└── README.md
```

## Stock Configuration

The ticker list is centralized in `config/stocks.json`.

Current tracked assets:

- PETR4
- VALE3
- ITUB4
- MGLU3
- BBDC4
- BBAS3
- WEGE3
- ABEV3
- RENT3
- B3SA3

New assets can be added by updating the configuration file without modifying the ingestion, transformation, or validation scripts.

## Data Ingestion

### Current Quotes

`01_fetch_stock_quote.py`

Collects current stock quote information from the Brapi API and saves the original responses as JSON files in the Raw layer.

### Historical Prices

`02_fetch_stock_history.py`

Collects daily historical OHLCV data using:

- Range: 1 month
- Interval: 1 day
- Sorting: Ascending

Historical records include:

- Open
- High
- Low
- Close
- Volume

Both ingestion scripts authenticate through the `BRAPI_TOKEN` environment variable.

## Data Transformation

`03_transform_stock_history.py`

Reads historical JSON snapshots and transforms them into a structured CSV dataset.

Output:

`data/processed/daily_stock_analysis.csv`

### Calculated Metrics

| Metric | Description |
|---|---|
| Body |