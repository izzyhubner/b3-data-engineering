# AWS Lakehouse - Data Quality Validation

## Overview

After implementing the AWS Lakehouse storage and metadata layers, a validation process was performed using Amazon Athena.

The objective was to verify data integrity, completeness, consistency, and partition availability across the Processed, Silver, and Gold layers.

All validations were executed using read-only SQL queries against the AWS Glue Data Catalog tables.

## Validation Environment

| Property | Value |
|---|---|
| AWS Region | us-east-1 |
| S3 Bucket | izzy-b3-lakehouse |
| Glue Database | b3_lakehouse |
| Processed Table | processed_daily_stock_analysis_parquet |
| Silver Table | silver_daily_stock_history_parquet |
| Gold Table | gold_daily_stock_indicators_parquet |
| Query Engine | Amazon Athena |
| Structured Data Format | Apache Parquet with Snappy compression |

## Validation Scope

The validation process covered the following areas.

### 1. Record Counts and Date Ranges

Verified total record counts, distinct tickers, and first and last trading dates across Processed, Silver, and Gold.

Latest validated results:

| Layer | Total Records | Tickers | First Trading Date | Last Trading Date |
|---|---:|---:|---|---|
| Processed | 220 | 10 | 2026-09-30 | 2026-10-30 |
| Silver | 230 | 10 | 2026-09-29 | 2026-10-30 |
| Gold | 230 | 10 | 2026-09-29 | 2026-10-30 |

Processed contains the latest transformed dataset, while Silver and Gold retain the accumulated historical records.

### 2. Duplicate Detection

Checked the composite key `(ticker, date)` in the structured datasets to identify duplicated records.

Expected result: no duplicated ticker-date keys.

### 3. Null Value Checks

Verified null values in critical fields.

**Processed and Silver:**

- Trading date (`date`)
- Open
- High
- Low
- Close
- Volume

**Gold:**

- Trading date (`date`)
- Close
- Volume

Indicator fields were evaluated separately because moving averages and other rolling calculations require sufficient historical data.

### 4. OHLC Data Integrity

Validated price relationships in the Processed and Silver datasets:

- High must be greater than or equal to Low.
- High must be greater than or equal to Open and Close.
- Low must be lower than or equal to Open and Close.
- Prices must be positive.
- Volume must not be negative.

Expected result: no invalid records.

### 5. Silver and Gold Record Consistency

Compared record counts per ticker between Silver and Gold.

Also compared distinct `(ticker, date)` keys to identify missing or unexpected records.

Expected result:

- Matching record counts per ticker.
- No missing or unexpected ticker-date keys.

### 6. Gold Indicator Coverage

Evaluated the availability of:

- SMA 5
- SMA 20
- Five-day volatility
- Volume ratio

Null values are expected when insufficient historical observations are available for the corresponding calculation.

### 7. Gold Indicator Sanity Checks

Checked for:

- Non-positive closing prices.
- Negative trading volume.
- Negative volatility.
- Negative volume ratios.

Expected result: no invalid records.

### 8. Partition Availability

Verified registered partitions using Athena's `SHOW PARTITIONS` command.

The Processed, Silver, and Gold tables use `ingestion_date` as their partition key.

Partition discovery is performed using `MSCK REPAIR TABLE` when required.

## Validation Results

All validation queries in the latest validation run completed successfully.

| Validation | Result |
|---|---|
| Record counts and date ranges across all three layers | Passed |
| Duplicate detection | Passed |
| Critical field null checks | Passed |
| OHLC integrity | Passed |
| Silver vs. Gold record counts | Passed |
| Silver vs. Gold key consistency | Passed |
| Gold indicator coverage | Passed |
| Gold indicator sanity checks | Passed |
| Processed partition availability | Passed |
| Silver partition availability | Passed |
| Gold partition availability | Passed |

No data quality issues were identified in the validation run.

## Conclusion

The initial AWS Lakehouse implementation successfully passed the documented SQL validation checks.

The results confirm that:

- Processed, Silver, and Gold datasets are accessible through Athena.
- Structured datasets are stored and queried in Parquet format.
- Silver and Gold contain consistent historical records.
- No duplicate ticker-date keys were identified.
- OHLC relationships are valid.
- Gold indicators follow their expected historical availability requirements.
- Glue partition metadata is available for querying.

The latest validation confirmed 220 Processed records and 230 records in both Silver and Gold, covering 10 tickers.

This validation establishes an initial data quality baseline for the AWS Lakehouse.

Future pipeline executions should repeat these checks to monitor data quality as new ingestion dates are added.

## SQL Validation Queries

The complete SQL validation script is maintained in:

`docs/aws/athena-queries.sql`

It includes queries for record counts, date ranges, duplicates, null checks, OHLC integrity, Silver-to-Gold consistency, indicator coverage, sanity checks, and partition discovery.