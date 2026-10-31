# B3 Data Engineering

A data engineering portfolio project focused on collecting, transforming, validating, and maintaining Brazilian stock market data through cloud-based Lakehouse architectures.

The project uses the [Brapi API](https://brapi.dev/) to collect B3 stock market data and processes it through a layered data pipeline using Python and AWS services.

It implements two Lakehouse representations using the same underlying datasets:

1. **AWS Lakehouse:** Amazon S3, Apache Parquet, AWS Glue Data Catalog, and Amazon Athena.
2. **Delta Lakehouse:** Amazon S3, Databricks, Apache Spark, Delta Lake, and Unity Catalog.

The original Parquet implementation remains operational. Delta tables are stored separately, allowing both representations to be maintained and evaluated without modifying the original datasets.

## Project Overview

The pipeline collects daily stock quotes and historical OHLCV data for a configurable list of Brazilian stocks.

Data flows through four layers:

```text
                         Brapi API
                             |
                             v
                      Python Pipeline
                             |
                             v
                            Raw
                           (JSON)
                             |
                             v
                         Processed
                         (Parquet)
                             |
                             v
                           Silver
                         (Parquet)
                             |
                             v
                            Gold
                         (Parquet)
                             |
                             v
                       AWS S3 Lakehouse
                             |
                   +---------+---------+
                   |                   |
                   v                   v
                AWS Glue            Athena
              Data Catalog       SQL Queries
                                      

                 AWS S3 - Original Parquet
                             |
                             v
                         Databricks
                       Apache Spark
                             |
                             v
                         Delta Lake
                             |
                             v
                       Unity Catalog
```

### Data Layers

| Layer | Description | Original Format | Delta Representation |
|---|---|---|---|
| Raw | Original API responses stored as immutable ingestion snapshots. | JSON | — |
| Processed | Transformed daily stock data enriched with price-related metrics. | Parquet | — |
| Silver | Persistent historical dataset maintained through an idempotent upsert process. | Parquet | Delta |
| Gold | Analytical dataset containing calculated technical indicators. | Parquet | Delta |

The local Python pipeline handles ingestion, transformation, validation, historical maintenance, and uploads to AWS S3.

AWS Glue Data Catalog manages metadata for the original Parquet datasets, while Amazon Athena provides serverless SQL access.

Databricks is used to create a separate Delta Lake representation of the Silver and Gold datasets. Unity Catalog manages the metadata of these Delta tables.

Structured datasets in the original AWS implementation are written directly to Parquet using Snappy compression. No intermediate CSV conversion is required.

## Current Status

The local Python pipeline and the initial AWS Lakehouse implementation are operational.

The Silver and Gold datasets have also been successfully migrated to Delta Lake using Databricks Serverless Spark.

| Component | Current Status |
|---|---|
| Stock quote ingestion | Implemented |
| Historical data ingestion | Implemented |
| Configurable ticker list | Implemented |
| Raw JSON snapshots | Implemented |
| Data transformation to Parquet | Implemented |
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
| Databricks S3 integration | Implemented |
| Unity Catalog | Implemented |
| Silver Parquet-to-Delta migration | Implemented |
| Gold Parquet-to-Delta migration | Implemented |
| Delta transaction history inspection | Validated |
| Production Delta incremental updates | Planned |
| Cloud-native orchestration | Planned |
| Data Warehouse architecture | Planned |
| Lakehouse and Data Warehouse comparison | Planned |

### Latest Validated AWS Architecture

- S3 bucket: `izzy-b3-lakehouse`
- AWS Region: `us-east-1`
- Glue database: `b3_lakehouse`
- Processed table: `processed_daily_stock_analysis_parquet`
- Silver table: `silver_daily_stock_history_parquet`
- Gold table: `gold_daily_stock_indicators_parquet`
- Athena query results: `s3://izzy-b3-lakehouse/athena-results/`

Latest Athena validation results:

| Layer | Records | Tickers | First Date | Last Date |
|---|---:|---:|---|---|
| Processed | 220 | 10 | 2026-09-30 | 2026-10-30 |
| Silver | 230 | 10 | 2026-09-29 | 2026-10-30 |
| Gold | 230 | 10 | 2026-09-29 | 2026-10-30 |

Silver and Gold contain the accumulated historical dataset, while Processed represents the latest transformed ingestion.

### Latest Validated Delta Tables

The original Silver and Gold Parquet datasets were migrated to Delta Lake and registered in Unity Catalog.

| Layer | Unity Catalog Table | Records | Columns | Delta Version |
|---|---|---:|---:|---:|
| Silver | `b3_lakehouse.silver.daily_stock_history` | 230 | 25 | 0 |
| Gold | `b3_lakehouse.gold.daily_stock_indicators` | 230 | 9 | 0 |

Both migrations were validated against their original Parquet sources. Record counts and schemas matched.

Gold data quality validation also confirmed:

- 230 records.
- 230 unique `(ticker, date)` combinations.
- No null ticker values.
- No null dates.
- No null closing prices.

## Technologies

- Python 3.14
- Brapi API
- AWS S3
- AWS Glue Data Catalog
- Amazon Athena
- Terraform
- Boto3
- Databricks
- Apache Spark
- Delta Lake
- Unity Catalog
- JSON
- Apache Parquet
- PyArrow
- Snappy compression
- SQL
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
│   ├── gold/
│   └── parquet/
│       ├── processed/
│       ├── silver/
│       └── gold/
│
├── docs/
│   └── aws/
│       ├── lakehouse-architecture.md
│       ├── athena-queries.sql
│       └── data-quality-validation.md
│
├── infrastructure/
│   └── terraform/
│       ├── main.tf
│       ├── outputs.tf
│       ├── providers.tf
│       └── variables.tf
│
├── logs/
│
├── src/
│   └── databricks/
│       ├── 01_migrate_silver_to_delta.py
│       └── 02_migrate_gold_to_delta.py
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

Generated datasets, execution logs, Python cache files, and Terraform working files are not intended to be versioned in Git.

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

Collects current stock quote information from the Brapi API and saves original responses as JSON snapshots in the local Raw layer.

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

Original API responses are preserved in JSON format, allowing the structured datasets to be rebuilt from the source snapshots.

## Data Transformation

`03_transform_stock_history.py`

Reads historical JSON snapshots, transforms the data, calculates price-related metrics, and writes the Processed dataset directly to Parquet.

Output:

`data/parquet/processed/daily_stock_analysis.parquet`

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

The output uses Apache Parquet with Snappy compression.

## Data Validation

`04_validate_stock_data.py`

Validates the transformed Processed dataset before it is incorporated into the persistent historical layer.

Validation includes:

- Required fields.
- Unique ticker-date combinations.
- Numeric and valid price values.
- OHLC consistency.
- Calculated metric consistency.

## Silver Layer

`06_update_stock_history.py`

Maintains the persistent historical dataset:

`data/parquet/silver/daily_stock_history.parquet`

The process reads the Processed Parquet dataset and applies an upsert strategy based on the composite key:

`(ticker, date)`

Existing records are updated when new source data is available, while new trading sessions are inserted.

The operation is designed to be idempotent, preventing duplicate historical records when the same input is processed repeatedly.

### Persistent History Validation

`08_validate_persistent_history.py`

Validates the persistent Silver dataset against the latest Processed source data.

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

`data/parquet/gold/daily_stock_indicators.parquet`

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
├── databricks/
│   ├── silver/
│   │   └── daily_stock_history/
│   │       ├── _delta_log/
│   │       └── *.parquet
│   │
│   └── gold/
│       └── daily_stock_indicators/
│           ├── _delta_log/
│           └── *.parquet
│
└── athena-results/
```

Raw data is organized by ticker and ingestion date.

Processed, Silver, and Gold datasets are partitioned by ingestion date.

The historical Raw JSON files contain multiple trading dates, so their partitions represent ingestion dates rather than individual trading dates.

Structured datasets in the original AWS implementation are stored as Parquet files with Snappy compression.

Delta datasets are stored separately under the `databricks/` prefix.

### S3 Upload Scripts

| Script | Responsibility |
|---|---|
| `14_upload_raw_to_s3.py` | Uploads original API JSON snapshots to S3. |
| `15_cleanup_legacy_s3.py` | Removes objects and versions from the previous Raw layout. |
| `16_upload_processed_to_s3.py` | Uploads the Processed Parquet dataset. |
| `17_upload_silver_to_s3.py` | Uploads the persistent Silver Parquet dataset. |
| `18_upload_gold_to_s3.py` | Uploads the Gold Parquet dataset. |

Structured dataset uploads use SHA-256 checksums to avoid unnecessary transfers when file content has not changed.

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

The project uses AWS Glue Data Catalog to manage metadata for the original Parquet Lakehouse datasets.

Database:

`b3_lakehouse`

Registered external tables:

- `processed_daily_stock_analysis_parquet`
- `silver_daily_stock_history_parquet`
- `gold_daily_stock_indicators_parquet`

All three tables use `ingestion_date` as a partition column and reference Parquet datasets stored in S3.

The Glue Data Catalog stores table definitions, schemas, and partition metadata. The actual datasets remain stored in S3.

### Amazon Athena

Amazon Athena provides serverless SQL queries over the Parquet files stored in S3.

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

## Databricks and Delta Lake

Databricks is used to implement a separate Delta Lake representation of the existing AWS Lakehouse datasets.

The integration uses an AWS IAM role and a Databricks Unity Catalog Storage Credential to access the S3 bucket.

The original Parquet datasets remain unchanged.

### Storage Credential and External Locations

The Databricks integration uses a Unity Catalog Storage Credential backed by an AWS IAM role.

External Locations provide controlled access to the relevant S3 prefixes:

| External Location | S3 Prefix | Purpose |
|---|---|---|
| `b3_silver_source` | `s3://izzy-b3-lakehouse/silver/` | Read original Silver Parquet data. |
| `b3_gold_source` | `s3://izzy-b3-lakehouse/gold/` | Read original Gold Parquet data. |
| `b3_delta_storage` | `s3://izzy-b3-lakehouse/databricks/` | Store Delta datasets. |

The Delta datasets are stored under a dedicated prefix, preserving the original Parquet sources.

### Unity Catalog

The Databricks catalog is named:

`b3_lakehouse`

The following schemas and tables are registered:

| Schema | Table | Format |
|---|---|---|
| silver | `daily_stock_history` | Delta |
| gold | `daily_stock_indicators` | Delta |

Unity Catalog manages table metadata and access to the Delta datasets stored in S3.

### Delta Migration

The migration scripts are located under:

`src/databricks/`

| Script | Responsibility |
|---|---|
| `01_migrate_silver_to_delta.py` | Migrates the Silver Parquet dataset into Delta Lake. |
| `02_migrate_gold_to_delta.py` | Migrates the Gold Parquet dataset into Delta Lake. |

Each migration:

- Reads the existing Parquet source.
- Checks whether the Delta destination already exists.
- Writes the data to a separate S3 prefix.
- Registers the resulting table in Unity Catalog.
- Validates source and destination record counts.
- Validates schema consistency.

The migration process does not modify the original Parquet datasets.

### Delta Transaction History

Delta transaction history was inspected using:

`DESCRIBE HISTORY`

Both production tables currently have an initial version (version 0) representing their successful initial write.

A separate test table was also used to validate Delta version history, time travel, and controlled updates through `MERGE`.

The production Silver and Gold tables currently contain their initial migrated snapshots. Incremental Delta maintenance is part of the future roadmap.

## Pipeline Orchestration

`05_run_pipeline.py`

Coordinates the complete local data workflow through sequential execution of the project scripts.

The current pipeline contains 15 steps:

1. Fetch current stock quotes.
2. Fetch historical stock data.
3. Transform historical data to Parquet.
4. Validate Processed data.
5. Run Silver automated tests.
6. Upload Processed data to S3.
7. Update persistent Silver history.
8. Validate persistent Silver history.
9. Upload Silver data to S3.
10. Generate Gold indicators.
11. Validate Gold data.
12. Run Gold automated tests.
13. Upload Gold data to S3.
14. Upload Raw data to S3.
15. Clean up obsolete local Raw snapshots.

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

`15_cleanup_legacy_s3.py` was used to clean up the previous S3 object layout. It is a legacy maintenance script and is not part of the regular pipeline.

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

- Implement incremental Delta updates and MERGE operations for production tables.
- Evaluate Delta time travel and historical recovery for production datasets.
- Improve automated validation between Parquet and Delta representations.
- Evaluate cloud-native pipeline orchestration and scheduling.
- Compare query performance and storage characteristics across the two Lakehouse implementations.

### Data Warehouse

- Design dimensional models using facts and dimensions.
- Implement a Data Warehouse using the same stock market dataset.
- Introduce dbt for transformation and data modeling.
- Evaluate PostgreSQL and Amazon Redshift as analytical storage options.

### Architecture Comparison

The long-term objective is to compare Lakehouse and Data Warehouse architectures using the same source data.

The comparison will consider:

- Data modeling and transformation approaches.
- Storage formats and organization.
- Query performance.
- Data maintenance and incremental processing.
- Data quality and governance.
- Operational complexity.
- Infrastructure and operational costs.

### AWS Documentation

- [Lakehouse Architecture](docs/aws/lakehouse-architecture.md)
- [Athena SQL Queries](docs/aws/athena-queries.sql)
- [Data Quality Validation](docs/aws/data-quality-validation.md)

## Project Goals

This project is designed to demonstrate practical data engineering skills through a real-world financial data use case, emphasizing:

- Data ingestion and API integration.
- Layered data architecture.
- Data transformation and analytical modeling.
- Apache Parquet and columnar storage.
- Delta Lake and transactional data management.
- Data quality and automated testing.
- Idempotent data processing.
- Pipeline orchestration.
- Logging and error handling.
- Infrastructure as Code.
- Cloud storage and metadata management.
- Serverless SQL analytics.
- Lakehouse architecture implementation.
- Comparative evaluation of analytical data architectures.
