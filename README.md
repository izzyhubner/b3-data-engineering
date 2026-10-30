# B3 Data Engineering

A data engineering portfolio project focused on collecting, transforming, validating, and maintaining Brazilian stock market data, with an AWS-based Lakehouse architecture.

The project uses the [Brapi API](https://brapi.dev/) to collect B3 stock market data and processes it through a layered data pipeline using Python and AWS services.

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
                      |
                      v
                 AWS S3 Lakehouse
                      |
              +-------+-------+
              |               |
              v               v
          AWS Glue          Athena
        Data Catalog      SQL Queries
```

### Data Layers

| Layer | Description |
|---|---|
| Raw | Original API responses stored as JSON snapshots. |
| Processed | Transformed daily stock data enriched with price-related metrics. |
| Silver | Persistent historical dataset maintained through an idempotent upsert process. |
| Gold | Analytical dataset containing calculated technical indicators. |

The local Python pipeline handles ingestion, transformation, validation, and uploads to AWS S3.

AWS Glue Data Catalog manages table metadata and partitions, while Amazon Athena provides serverless SQL access to the Lakehouse datasets.

## Current Status

The local pipeline is operational and has successfully processed 10 stock tickers.

The initial AWS Lakehouse implementation is also operational.

| Component | Current Status |
|---|---|
| Stock quote ingestion | Implemented |
| Historical data ingestion | Implemented |
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
| Automated Raw data cleanup | Implemented |
| Local pipeline orchestration | Implemented |
| Structured logging | Implemented |
| AWS S3 Lakehouse storage | Implemented |
| S3 versioning and encryption | Implemented |
| Terraform infrastructure | Implemented |
| Raw, Processed, Silver and Gold uploads | Implemented |
| AWS Glue database and external tables | Implemented |
| Glue partition registration | Implemented |
| Amazon Athena SQL queries | Implemented |
| Cloud-native orchestration | Planned |
| Parquet conversion | Planned |
| Distributed processing with Spark | Planned |
| Delta Lake | Planned |

### Latest Validated AWS Architecture

- S3 bucket: `izzy-b3-lakehouse`
- AWS Region: `us-east-1`
- Glue database: `b3_lakehouse`
- Silver table: `silver_daily_stock_history`
- Gold table: `gold_daily_stock_indicators`
- Athena query results: `s3://izzy-b3-lakehouse/athena-results/`

## Technologies

- Python 3.14
- Brapi API
- AWS S3
- AWS Glue Data Catalog
- Amazon Athena
- Terraform
- Boto3
- JSON
- CSV
- Git and GitHub
- PowerShell

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
├── docs/
│   └── aws/
│       ├── lakehouse-architecture.md
│       └── athena-queries.sql
│
├── infrastructure/
│   └── terraform/
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
├── 14_upload_raw_to_s3.py
├── 15_cleanup_legacy_s3.py
├── 16_upload_processed_to_s3.py
├── 17_upload_silver_to_s3.py
├── 18_upload_gold_to_s3.py
│
├── stock_config.py
├── requirements.txt
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

Collects current stock quote information from the Brapi API and saves original responses as JSON files in the Raw layer.

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

## AWS Lakehouse

### Amazon S3

The project uses Amazon S3 as its cloud data lake storage layer.

Bucket:

`izzy-b3-lakehouse`

Region:

`us-east-1`

The bucket configuration includes:

- Versioning enabled.
- Server-side encryption using SSE-S3 (AES256).
- Block Public Access enabled.
- Bucket ownership enforced.

### S3 Data Organization

```text
s3://izzy-b3-lakehouse/
│
├── raw/
│   ├── quotes/
│   │   └── ticker=.../ingestion_date=.../
│   └── historical/
│       └── ticker=.../ingestion_date=.../
│
├── processed/
│   └── ingestion_date=.../
│
├── silver/
│   └── ingestion_date=.../
│
├── gold/
│   └── ingestion_date=.../
│
└── athena-results/
```

Raw data is organized by ticker and ingestion date.

Processed, Silver, and Gold datasets are partitioned by ingestion date.

The historical Raw JSON files contain multiple trading dates, so their partitions represent ingestion dates rather than individual trading dates.

### S3 Upload Scripts

| Script | Responsibility |
|---|---|
| `14_upload_raw_to_s3.py` | Uploads original API JSON snapshots to S3. |
| `15_cleanup_legacy_s3.py` | Removes objects and versions from the previous Raw layout. |
| `16_upload_processed_to_s3.py` | Uploads the Processed CSV dataset. |
| `17_upload_silver_to_s3.py` | Uploads the persistent Silver dataset. |
| `18_upload_gold_to_s3.py` | Uploads the Gold analytical dataset. |

Uploads use SHA-256 checksums to avoid unnecessary transfers when file content has not changed.

S3 versioning preserves previous object versions when an existing key is overwritten.

### Infrastructure as Code

Terraform manages the S3 infrastructure under:

`infrastructure/terraform/`

Managed resources include:

- S3 bucket.
- Bucket versioning.
- Server-side encryption.
- Public access block.
- Object ownership controls.

### AWS Glue Data Catalog

The project uses AWS Glue Data Catalog to manage metadata for the Lakehouse datasets.

Database:

`b3_lakehouse`

Registered external tables:

- `silver_daily_stock_history`
- `gold_daily_stock_indicators`

Both tables use `ingestion_date` as a partition column.

The Glue Data Catalog stores table definitions, schemas, and partition metadata. The actual datasets remain stored in S3.

### Amazon Athena

Amazon Athena provides serverless SQL queries over the CSV files stored in S3.

Athena uses the external table definitions registered in Glue Data Catalog.

The query results location is:

`s3://izzy-b3-lakehouse/athena-results/`

Partition discovery is performed using:

`MSCK REPAIR TABLE`

This command discovers existing partition folders in S3 and registers them in the Glue Data Catalog.

SQL table definitions and validation queries are documented in:

`docs/aws/athena-queries.sql`

Additional architecture details are available in:

`docs/aws/lakehouse-architecture.md`

## Pipeline Orchestration

`05_run_pipeline.py`

Coordinates the complete local data workflow through sequential execution of the project scripts.

The current pipeline contains 14 steps:

1. Fetch current stock quotes.
2. Fetch historical stock data.
3. Transform historical data.
4. Validate processed data.
5. Upload Processed data to S3.
6. Update persistent Silver history.
7. Validate persistent Silver history.
8. Upload Silver data to S3.
9. Generate Gold indicators.
10. Validate Gold data.
11. Run Gold automated tests.
12. Upload Gold data to S3.
13. Upload Raw data to S3.
14. Clean up obsolete local Raw snapshots.

Each step runs using the same Python interpreter as the orchestrator.

The pipeline stops when a step fails and records execution details in timestamped log files under `logs/`.

Raw data cleanup runs only after the preceding ingestion, transformation, validation, testing, and upload steps complete successfully.

The current orchestration runs locally. Cloud-native scheduling and orchestration have not yet been implemented.

## Raw Data Management

`09_inventory_raw_data.py`

Provides a read-only inventory of Raw JSON snapshots, grouped by ticker and data type.

`10_cleanup_raw_data.py`

Removes obsolete local Raw snapshots while retaining a configurable number of recent files.

The cleanup process supports manual confirmation and automatic execution through the pipeline.

Unclassified files are preserved.

`15_cleanup_legacy_s3.py` was used to clean up the previous S3 object layout.

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

### Lakehouse Improvements

- Convert CSV datasets to Parquet.
- Implement Apache Spark and PySpark for distributed processing.
- Introduce Delta Lake for transactional data management.
- Explore Databricks for Lakehouse development.
- Implement cloud-native pipeline orchestration and scheduling.

### Data Warehouse

- Dimensional modeling.
- Fact and dimension tables.
- dbt for transformation and data modeling.
- Amazon Redshift for analytical workloads.

The long-term objective is to maintain a reusable stock market data source that can serve both Lakehouse and Data Warehouse architectures.

### AWS Documentation

- [Lakehouse Architecture](docs/aws/lakehouse-architecture.md)
- [Athena SQL Queries](docs/aws/athena-queries.sql)
- [Data Quality Validation](docs/aws/data-quality-validation.md)

## Project Goals

This project is designed to demonstrate practical data engineering skills through a real-world financial data use case, emphasizing:

- Data ingestion and API integration.
- Layered data architecture.
- Data transformation and analytical modeling.
- Data quality and automated testing.
- Idempotent data processing.
- Pipeline orchestration.
- Logging and error handling.
- Infrastructure as Code.
- Cloud storage and metadata management.
- Serverless SQL analytics.