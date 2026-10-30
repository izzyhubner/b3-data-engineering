# AWS Lakehouse Architecture

## 1. Overview

This project implements an AWS-based Lakehouse architecture for collecting, processing, validating, and analyzing Brazilian stock market data.

Stock market data is collected from the Brapi API, processed through a local Python pipeline, and stored in Amazon S3 using a layered data architecture.

AWS Glue Data Catalog manages table definitions and partition metadata, while Amazon Athena provides serverless SQL access to the datasets.

The architecture uses four data layers:

- Raw
- Processed
- Silver
- Gold

Structured datasets are stored directly as Parquet files. No intermediate CSV conversion is required.

## 2. AWS Infrastructure

| Resource | Configuration |
|---|---|
| AWS Region | `us-east-1` |
| S3 Bucket | `izzy-b3-lakehouse` |
| Glue Database | `b3_lakehouse` |
| Athena Results Location | `s3://izzy-b3-lakehouse/athena-results/` |
| Structured Data Format | Parquet |
| Parquet Compression | Snappy |
| Raw Data Format | JSON |
| Infrastructure as Code | Terraform |

### S3 Bucket Security

The S3 bucket is configured with:

- Versioning enabled.
- Server-side encryption using SSE-S3 (AES256).
- Block Public Access enabled.
- Bucket ownership enforced through BucketOwnerEnforced.

Terraform manages the bucket and its security-related configurations.

## 3. Data Lake Architecture

The project follows a layered architecture in which each layer has a specific responsibility.

```text
                         Brapi API
                             |
                             v
                      +-------------+
                      |     Raw     |
                      |     JSON    |
                      |  Snapshots  |
                      +-------------+
                             |
                             v
                      +-------------+
                      |  Processed  |
                      |   Parquet   |
                      |  Transformed|
                      |    Data     |
                      +-------------+
                             |
                             v
                      +-------------+
                      |    Silver   |
                      |   Parquet   |
                      |  Persistent |
                      |  Historical |
                      |    Data     |
                      +-------------+
                             |
                             v
                      +-------------+
                      |     Gold    |
                      |   Parquet   |
                      |  Analytical |
                      |  Indicators |
                      +-------------+
                             |
                             v
                         Amazon S3
                             |
                   +---------+---------+
                   |                   |
                   v                   v
              AWS Glue              Athena
           Data Catalog           SQL Queries
```

The local Python pipeline performs ingestion, transformation, validation, and orchestration. Amazon S3 stores the resulting datasets, while Glue and Athena provide metadata management and analytical access.

### 3.1 Raw Layer

Stores original API responses as JSON snapshots.

Data types:

- Current stock quotes.
- Historical stock prices.

S3 organization:

```text
raw/
├── quotes/
│   └── ticker=ABEV3/
│       └── ingestion_date=YYYY-MM-DD/
└── historical/
    └── ticker=ABEV3/
        └── ingestion_date=YYYY-MM-DD/
```

Historical API responses can contain multiple trading dates. Therefore, Raw historical files are partitioned by ingestion date rather than individual trading dates.

Raw preserves the original API responses and acts as the source for downstream transformations.

### 3.2 Processed Layer

Stores transformed historical stock data directly as Parquet.

Main dataset:

`daily_stock_analysis.parquet`

Local output:

`data/parquet/processed/daily_stock_analysis.parquet`

S3 organization:

```text
processed/
└── ingestion_date=YYYY-MM-DD/
    └── daily_stock_analysis.parquet
```

This layer contains structured OHLCV data and calculated candle-related metrics.

The transformation reads Raw JSON files and writes the structured dataset directly to Parquet using PyArrow and Snappy compression.

### 3.3 Silver Layer

Stores the persistent historical stock dataset directly as Parquet.

Main dataset:

`daily_stock_history.parquet`

Local output:

`data/parquet/silver/daily_stock_history.parquet`

S3 organization:

```text
silver/
└── ingestion_date=YYYY-MM-DD/
    └── daily_stock_history.parquet
```

The local Python pipeline maintains this dataset using an upsert strategy based on:

`(ticker, date)`

Existing records are updated when necessary, and new trading sessions are inserted.

The process is designed to be idempotent and avoid duplicate historical records.

Silver preserves the accumulated historical dataset across pipeline executions.

### 3.4 Gold Layer

Stores analytical stock indicators generated from Silver, directly as Parquet.

Main dataset:

`daily_stock_indicators.parquet`

Local output:

`data/parquet/gold/daily_stock_indicators.parquet`

S3 organization:

```text
gold/
└── ingestion_date=YYYY-MM-DD/
    └── daily_stock_indicators.parquet
```

Calculated indicators include:

- SMA 5.
- SMA 20.
- Daily return percentage.
- Five-day volatility.
- Volume ratio.

Indicator calculations are performed independently for each ticker.

Gold provides an analysis-ready dataset for SQL queries and downstream analytical use cases.

## 4. Data Format and Storage Strategy

The project uses JSON for Raw data and Parquet for all structured layers.

| Layer | Format | Compression | Purpose |
|---|---|---|---|
| Raw | JSON | API response format | Preserve original source data |
| Processed | Parquet | Snappy | Store transformed stock data |
| Silver | Parquet | Snappy | Maintain persistent historical data |
| Gold | Parquet | Snappy | Store analytical indicators |

Parquet was selected for structured datasets because it is a columnar storage format suitable for analytical workloads.

Benefits include:

- Column-oriented data access.
- Efficient compression.
- Typed schema representation.
- Reduced data scanning for queries that access selected columns.
- Native compatibility with Amazon Athena.

The pipeline writes Parquet directly. There is no CSV intermediate layer or separate CSV-to-Parquet conversion step.

## 5. S3 Upload Strategy

The local Python pipeline uploads the four data layers to S3.

| Script | Responsibility |
|---|---|
| `14_upload_raw_to_s3.py` | Uploads original API JSON snapshots. |
| `16_upload_processed_to_s3.py` | Uploads Processed Parquet data. |
| `17_upload_silver_to_s3.py` | Uploads persistent Silver Parquet data. |
| `18_upload_gold_to_s3.py` | Uploads Gold analytical Parquet data. |

Uploads use SHA-256 checksums to avoid unnecessary transfers when file contents have not changed.

For Processed, Silver, and Gold, files are organized by ingestion date using Hive-style partition folders.

When the same S3 key is overwritten, S3 versioning preserves previous object versions.

The upload scripts use the configured AWS profile and do not store AWS credentials in source code.

## 6. AWS Glue Data Catalog

AWS Glue Data Catalog stores metadata about the datasets available in S3.

Database:

`b3_lakehouse`

Registered external tables:

| Table | S3 Location | Format | Partition Column |
|---|---|---|---|
| `processed_daily_stock_analysis_parquet` | `s3://izzy-b3-lakehouse/processed/` | Parquet | `ingestion_date` |
| `silver_daily_stock_history_parquet` | `s3://izzy-b3-lakehouse/silver/` | Parquet | `ingestion_date` |
| `gold_daily_stock_indicators_parquet` | `s3://izzy-b3-lakehouse/gold/` | Parquet | `ingestion_date` |

The tables use external definitions, meaning the underlying Parquet files remain stored in S3.

Glue stores:

- Database metadata.
- Table schemas.
- S3 locations.
- Partition metadata.

The actual stock market records are not stored in Glue.

### Partition Registration

S3 partition folders follow Hive-style partition naming:

`ingestion_date=YYYY-MM-DD`

After new partition folders are uploaded, partitions can be discovered and registered using:

```sql
MSCK REPAIR TABLE b3_lakehouse.processed_daily_stock_analysis_parquet;

MSCK REPAIR TABLE b3_lakehouse.silver_daily_stock_history_parquet;

MSCK REPAIR TABLE b3_lakehouse.gold_daily_stock_indicators_parquet;
```

Execute each statement separately in Athena.

This operation synchronizes partitions discovered in S3 with the Glue Data Catalog.

It does not move or modify the underlying Parquet files.

## 7. Amazon Athena

Amazon Athena provides serverless SQL queries directly over the Parquet files stored in S3.

Athena uses the external table definitions registered in Glue Data Catalog.

Query results are stored in:

`s3://izzy-b3-lakehouse/athena-results/`

Example:

```sql
SELECT
    ticker,
    date,
    close,
    sma_5,
    sma_20,
    daily_return_pct,
    volatility_5d
FROM b3_lakehouse.gold_daily_stock_indicators_parquet
WHERE ticker = 'ABEV3'
ORDER BY date DESC
LIMIT 10;
```

The complete SQL setup, partition management, and validation queries are available in:

`docs/aws/athena-queries.sql`

## 8. Data Quality Validation

The project validates datasets locally and through SQL queries executed in Amazon Athena.

Local validation includes:

- Processed dataset validation.
- Persistent Silver history validation.
- Duplicate ticker-date key checks.
- OHLC price consistency.
- Gold indicator recalculation and comparison.
- Synthetic tests for history updates and indicator calculations.

Athena validation covers:

- Record counts by ticker.
- Available trading date ranges.
- Duplicate ticker-date keys.
- Null values in critical fields.
- OHLC price relationships.
- Silver and Gold record count consistency.
- Silver and Gold ticker-date key consistency.
- Gold indicator coverage.
- Invalid indicator values.
- Registered S3 partitions.

### Latest Athena Validation Results

The Parquet tables were successfully queried in Athena.

| Layer | Total Records | Distinct Tickers | First Date | Last Date |
|---|---:|---:|---|---|
| Processed | 220 | 10 | 2026-09-30 | 2026-10-30 |
| Silver | 230 | 10 | 2026-09-29 | 2026-10-30 |
| Gold | 230 | 10 | 2026-09-29 | 2026-10-30 |

Processed contains the current transformed dataset, while Silver and Gold contain the accumulated historical dataset.

The three Parquet tables were successfully registered and queried. The previous CSV Athena tables were removed from the Glue Data Catalog.

Detailed validation queries are available in:

`docs/aws/athena-queries.sql`

## 9. Infrastructure as Code

Terraform configuration is maintained under:

`infrastructure/terraform/`

Managed S3 resources include:

- S3 bucket.
- Bucket versioning.
- Server-side encryption.
- Public access block.
- Object ownership controls.

The project uses AWS CLI profiles for local AWS authentication.

Sensitive credentials and API tokens are not stored in source code.

## 10. Current Architecture Limitations

The current implementation has the following characteristics:

- Data ingestion and transformation run locally.
- Raw source data is stored as JSON.
- Structured datasets are stored as Parquet with Snappy compression.
- S3 stores the Lakehouse datasets.
- Glue Data Catalog manages external table metadata.
- Athena provides serverless SQL queries.
- Pipeline orchestration is local and sequential.

The project does not currently use:

- AWS Glue Crawlers.
- AWS Glue ETL Jobs.
- AWS Lambda.
- Cloud-native orchestration.
- Apache Spark.
- Delta Lake.
- Databricks.

These technologies may be considered in future iterations.

## 11. Future Improvements

Potential architecture improvements include:

- Evaluate Apache Spark and PySpark for distributed processing.
- Introduce Delta Lake for transactional data management.
- Implement cloud-native pipeline orchestration.
- Explore Databricks integration.
- Improve automated data quality monitoring.
- Evaluate automated partition management.

The current implementation establishes an AWS Lakehouse foundation with direct Parquet storage, persistent historical data, and serverless analytical access through Athena.
