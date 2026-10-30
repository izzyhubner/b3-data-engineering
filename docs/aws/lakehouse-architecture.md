# AWS Lakehouse Architecture

## 1. Overview

This project implements an AWS-based Lakehouse architecture for collecting, processing, validating, and analyzing Brazilian stock market data.

Stock market data is collected from the Brapi API, processed through a local Python pipeline, and stored in Amazon S3 using a layered data architecture.

AWS Glue Data Catalog manages table definitions and partition metadata, while Amazon Athena provides serverless SQL access to the datasets.

The architecture currently uses four data layers:

- Raw
- Processed
- Silver
- Gold

## 2. AWS Infrastructure

| Resource | Configuration |
|---|---|
| AWS Region | `us-east-1` |
| S3 Bucket | `izzy-b3-lakehouse` |
| Glue Database | `b3_lakehouse` |
| Athena Results Location | `s3://izzy-b3-lakehouse/athena-results/` |
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
                 | JSON Snapshots
                 +-------------+
                        |
                        v
                 +-------------+
                 |  Processed  |
                 |  CSV Dataset|
                 +-------------+
                        |
                        v
                 +-------------+
                 |    Silver   |
                 | Persistent  |
                 | Historical  |
                 |    Data     |
                 +-------------+
                        |
                        v
                 +-------------+
                 |     Gold    |
                 | Analytical  |
                 | Indicators  |
                 +-------------+
                        |
                        v
                  Amazon S3
                        |
              +---------+---------+
              |                   |
              v                   v
         AWS Glue              Athena
       Data Catalog          SQL Queries
```

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

### 3.2 Processed Layer

Stores transformed historical stock data as CSV.

Main dataset:

`daily_stock_analysis.csv`

S3 organization:

```text
processed/
└── ingestion_date=YYYY-MM-DD/
    └── daily_stock_analysis.csv
```

This layer contains structured OHLCV data and calculated candle-related metrics.

### 3.3 Silver Layer

Stores the persistent historical stock dataset.

Main dataset:

`daily_stock_history.csv`

S3 organization:

```text
silver/
└── ingestion_date=YYYY-MM-DD/
    └── daily_stock_history.csv
```

The local Python pipeline maintains this dataset using an upsert strategy based on:

`(ticker, date)`

Existing records are updated when necessary, and new trading sessions are inserted.

The process is designed to be idempotent and avoid duplicate historical records.

### 3.4 Gold Layer

Stores analytical stock indicators generated from Silver.

Main dataset:

`daily_stock_indicators.csv`

S3 organization:

```text
gold/
└── ingestion_date=YYYY-MM-DD/
    └── daily_stock_indicators.csv
```

Calculated indicators include:

- SMA 5.
- SMA 20.
- Daily return percentage.
- Five-day volatility.
- Volume ratio.

Indicator calculations are performed independently for each ticker.

## 4. S3 Upload Strategy

The local Python pipeline uploads the four data layers to S3.

| Script | Responsibility |
|---|---|
| `14_upload_raw_to_s3.py` | Uploads original API JSON snapshots. |
| `16_upload_processed_to_s3.py` | Uploads Processed CSV data. |
| `17_upload_silver_to_s3.py` | Uploads persistent Silver data. |
| `18_upload_gold_to_s3.py` | Uploads Gold analytical data. |

Uploads use SHA-256 checksums to avoid unnecessary transfers when file contents have not changed.

For Processed, Silver, and Gold, files are organized by ingestion date.

When the same S3 key is overwritten, S3 versioning preserves previous object versions.

The project currently uses CSV for structured datasets and JSON for Raw API responses.

## 5. AWS Glue Data Catalog

AWS Glue Data Catalog stores metadata about the datasets available in S3.

Database:

`b3_lakehouse`

Registered external tables:

| Table | S3 Location | Partition Column |
|---|---|---|
| `silver_daily_stock_history` | `s3://izzy-b3-lakehouse/silver/` | `ingestion_date` |
| `gold_daily_stock_indicators` | `s3://izzy-b3-lakehouse/gold/` | `ingestion_date` |

The tables use external definitions, meaning the underlying CSV files remain stored in S3.

Glue stores:

- Database metadata.
- Table schemas.
- S3 locations.
- Partition metadata.

The actual stock market records are not stored in Glue.

### Partition Registration

S3 partition folders follow Hive-style partition naming:

`ingestion_date=YYYY-MM-DD`

After new partition folders are uploaded, the partitions can be discovered and registered using:

```sql
MSCK REPAIR TABLE b3_lakehouse.silver_daily_stock_history;

MSCK REPAIR TABLE b3_lakehouse.gold_daily_stock_indicators;
```

This operation synchronizes the partitions discovered in S3 with the Glue Data Catalog.

It does not move or modify the underlying CSV files.

## 6. Amazon Athena

Amazon Athena provides serverless SQL queries directly over the CSV files stored in S3.

Athena uses the external table definitions registered in Glue Data Catalog.

Query results are stored in:

`s3://izzy-b3-lakehouse/athena-results/`

Example:

```sql
SELECT
    ticker,
    trade_date,
    close,
    sma_5,
    sma_20,
    daily_return_pct,
    volatility_5d
FROM b3_lakehouse.gold_daily_stock_indicators
WHERE ticker = 'ABEV3'
ORDER BY trade_date DESC
LIMIT 10;
```

The complete SQL setup and validation queries are available in:

`docs/aws/athena-queries.sql`

## 7. Data Quality Validation

The AWS datasets were validated through SQL queries executed in Amazon Athena.

Validation covered:

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

All validation queries executed successfully, with no data quality issues identified in the validation run.

Detailed validation documentation:

`docs/aws/data-quality-validation.md`

## 8. Infrastructure as Code

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

## 9. Current Architecture Limitations

The current implementation has the following characteristics:

- Data ingestion and transformation run locally.
- CSV is used for structured datasets.
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

## 10. Future Improvements

Potential architecture improvements include:

- Convert structured datasets from CSV to Parquet.
- Evaluate Apache Spark and PySpark for distributed processing.
- Introduce Delta Lake for transactional data management.
- Implement cloud-native pipeline orchestration.
- Explore Databricks integration.
- Improve automated data quality monitoring.

The current implementation establishes the initial AWS Lakehouse foundation for future development.