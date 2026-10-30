# B3 Data Engineering

A data engineering portfolio project focused on collecting, transforming, validating, and maintaining Brazilian stock market data.

The project uses B3 stock market data from the [Brapi API](https://brapi.dev/) to build a local data pipeline, with a future roadmap toward a cloud-based Lakehouse and Data Warehouse architecture.

## Project Overview

The pipeline collects daily stock quotes and historical OHLCV data for a configurable list of Brazilian stocks.

Data flows through four layers:

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
    |
    v
   Gold
```

- **Raw:** Original API responses stored as JSON snapshots.
- **Processed:** Transformed daily stock data enriched with technical and price-related metrics.
- **Silver:** Persistent historical dataset maintained through an idempotent upsert process.
- **Gold:** Analytical dataset containing calculated indicators designed to support financial analysis and downstream consumption.

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
| Gold analytical layer | Implemented |
| Technical indicator calculations | Implemented |
| Gold data validation | Implemented |
| Silver automated tests | Implemented |
| Gold automated tests | Implemented |
| Automated raw data cleanup | Implemented |
| Pipeline orchestration | Implemented |
| Structured logging | Implemented |
| Python version | 3.14 |

Latest successful execution:

- 10 stock tickers collected.
- 230 historical records maintained in Silver.
- 230 analytical records generated in Gold.
- 0 duplicate Gold keys.
- 0 Gold validation issues.
- 8 Gold automated tests passed.
- 0 raw data cleanup failures.
- 10 pipeline steps completed successfully.

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
│   ├── silver/
│   └── gold/
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
├── 11_build_gold_indicators.py
├── 12_validate_gold_data.py
├── 13_test_gold_indicators.py
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
| Body | Absolute difference between closing and opening prices. |
| Body percentage | Candle body expressed as a percentage of the opening price. |
| Range | Difference between the daily high and low. |
| Range percentage | Daily range expressed as a percentage of the opening price. |
| Upper wick | Distance between the high and the highest of open and close. |
| Lower wick | Distance between the lowest of open and close and the low. |
| Close position | Closing price position within the daily trading range. |
| Bullish candle | Indicates whether the closing price is higher than the opening price. |
| Daily return | Percentage change between consecutive closing prices. |
| Overnight gap | Percentage difference between the current opening price and previous closing price. |
| Five-day average volume | Average volume of the previous five available trading sessions, excluding the current session. |

## Data Validation

`04_validate_stock_data.py`

Validates the transformed dataset before it is incorporated into the persistent historical layer.

Validation includes:

- Required fields.
- Unique ticker-date combinations.
- Numeric and valid price values.
- OHLC consistency.
- Calculated metric consistency.

## Silver Layer

`06_update_stock_history.py`

Maintains the persistent historical dataset:

`data/silver/daily_stock_history.csv`

The process uses an upsert strategy based on the composite key:

`(ticker, date)`

Existing records are updated when new source data is available, while new trading sessions are inserted.

The operation is designed to be idempotent, preventing duplicate historical records when the same input is processed repeatedly.

### Persistent History Validation

`08_validate_persistent_history.py`

Validates the persistent Silver dataset against the latest processed source data.

Checks include:

- Required fields.
- Duplicate ticker-date keys.
- Valid numeric and OHLC values.
- Missing historical keys.
- Source-to-target consistency.

### Silver Automated Tests

`07_test_stock_history.py`

Runs automated tests using synthetic records and temporary files.

The tests cover:

- Inserting a new historical record.
- Updating an existing record.
- Idempotent execution.
- Adding a second trading date without duplication.

Production datasets are not modified during testing.

## Gold Layer

`11_build_gold_indicators.py`

Reads the persistent Silver dataset and generates analytical indicators for each ticker.

Output:

`data/gold/daily_stock_indicators.csv`

### Calculated Indicators

| Indicator | Description |
|---|---|
| SMA 5 | Simple moving average of the current and previous four closing prices. |
| SMA 20 | Simple moving average of the current and previous nineteen closing prices. |
| Daily return | Percentage change between consecutive closing prices. |
| Volatility 5d | Sample standard deviation of the latest five daily returns. |
| Volume ratio | Current trading volume divided by the average volume of the previous five trading sessions. |

Indicators are calculated independently for each ticker and chronologically ordered by trading date.

Values remain empty when insufficient historical data is available for a calculation.

### Gold Data Validation

`12_validate_gold_data.py`

Validates the generated Gold dataset against Silver and independently recalculates the expected indicators.

Validation includes:

- Required fields.
- Unique ticker-date keys.
- Missing and unexpected historical keys.
- Valid numeric values.
- Indicator calculation consistency.
- Historical data availability requirements.

### Gold Automated Tests

`13_test_gold_indicators.py`

Runs automated tests using synthetic stock records without modifying production datasets.

The eight tests cover:

1. SMA calculation windows.
2. Daily return calculation.
3. Five-day volatility calculation.
4. Volume ratio calculation.
5. Independent ticker calculations.
6. Chronological record ordering.
7. Calculation consistency across repeated executions.
8. Empty input handling.

## Pipeline Orchestration

`05_run_pipeline.py`

Coordinates the complete data workflow through sequential execution of the project scripts.

The pipeline currently contains 10 steps:

1. Fetch current stock quotes.
2. Fetch historical stock data.
3. Transform historical data.
4. Validate processed data.
5. Update persistent Silver history.
6. Validate persistent Silver history.
7. Generate Gold indicators.
8. Validate Gold data.
9. Run Gold automated tests.
10. Clean up obsolete Raw snapshots.

Each step runs using the same Python interpreter as the orchestrator.

The pipeline stops when a step fails and records execution details in timestamped log files under `logs/`.

Raw data cleanup runs only after all ingestion, transformation, validation, and testing steps complete successfully.

## Raw Data Management

`09_inventory_raw_data.py`

Provides a read-only inventory of Raw JSON snapshots, grouped by ticker and data type.

`10_cleanup_raw_data.py`

Removes obsolete Raw snapshots while retaining a configurable number of recent files.

The cleanup process supports manual confirmation and automatic execution through the pipeline.

Unclassified files are preserved.

## Logging and Error Handling

The pipeline uses Python's logging module to provide structured execution logs.

Logs include:

- Pipeline start and completion.
- Individual step execution.
- Script output.
- Warnings and errors.
- Exit codes.
- Final pipeline status.

Timestamped log files are stored in the `logs/` directory.

## Future Roadmap

The next development stages will expand the local implementation toward cloud-based data engineering architectures.

### Lakehouse

- AWS S3 as cloud storage.
- Parquet as a columnar storage format.
- AWS Glue for data cataloging.
- Amazon Athena for serverless SQL queries.
- Apache Spark and PySpark for distributed processing.
- Delta Lake for reliable transactional data management.
- Databricks for Lakehouse development.

### Data Warehouse

- Dimensional modeling.
- Fact and dimension tables.
- dbt for transformation and data modeling.
- Amazon Redshift for analytical workloads.

The long-term objective is to maintain a reusable stock market data source that can serve both Lakehouse and Data Warehouse architectures.

## Project Goals

This project is designed to demonstrate practical data engineering skills through a real-world financial data use case, emphasizing:

- Data ingestion and API integration.
- Layered data architecture.
- Data transformation and analytical modeling.
- Data quality and automated testing.
- Idempotent data processing.
- Pipeline orchestration.
- Logging and error handling.
- Cloud architecture evolution.
