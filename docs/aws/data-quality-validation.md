# AWS Lakehouse - Data Quality Validation

## Overview

After implementing the AWS Lakehouse storage and metadata layers, a validation process was performed using Amazon Athena.

The objective was to verify data integrity, completeness, consistency, and partition availability across the Silver and Gold layers.

All validations were executed using read-only SQL queries against the Glue Data Catalog tables.

## Validation Environment

| Property | Value |
|---|---|
| AWS Region | us-east-1 |
| S3 Bucket | izzy-b3-lakehouse |
| Glue Database | b3_lakehouse |
| Silver Table | silver_daily_stock_history |
| Gold Table | gold_daily_stock_indicators |
| Query Engine | Amazon Athena |

## Validation Scope

The validation process covered the following areas:

### 1. Record Counts and Date Ranges

Verified the number of records per ticker, first and last trading dates, and distinct trading days in both Silver and Gold.

### 2. Duplicate Detection

Checked the composite key `(ticker, trade_date)` to identify duplicated records.

Expected result: no duplicated keys.

### 3. Null Value Checks

Verified null values in critical fields.

Silver:
- Trading date
- Open
- High
- Low
- Close
- Volume

Gold:
- Trading date
- Close
- Volume

Indicator fields were evaluated separately because moving averages and other rolling calculations require sufficient historical data.

### 4. OHLC Data Integrity

Validated price relationships:

- High must be greater than or equal to Low.
- High must be greater than or equal to Open and Close.
- Low must be lower than or equal to Open and Close.
- Prices must be positive.
- Volume must not be negative.

Expected result: no invalid records.

### 5. Silver and Gold Record Consistency

Compared record counts per ticker between Silver and Gold.

Also compared distinct `(ticker, trade_date)` keys to identify missing or unexpected records.

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

Verified registered partitions for both Silver and Gold using Athena's `SHOW PARTITIONS` command.

The partition key is `ingestion_date`.

## Validation Results

<badge color="success">Passed</badge>

All validation queries executed successfully.

| Validation | Result |
|---|---|
| Record counts and date ranges | Passed |
| Duplicate detection | Passed |
| Critical field null checks | Passed |
| OHLC integrity | Passed |
| Silver vs. Gold record counts | Passed |
| Silver vs. Gold key consistency | Passed |
| Gold indicator coverage | Passed |
| Gold indicator sanity checks | Passed |
| Silver partition availability | Passed |
| Gold partition availability | Passed |

No data quality issues were identified in the validation run.

## Conclusion

The initial AWS Lakehouse implementation successfully passed the SQL validation checks.

The results confirm that:

- Silver and Gold datasets are accessible through Athena.
- Historical records are consistent across both layers.
- No duplicate ticker-date keys were identified.
- OHLC relationships are valid.
- Gold indicators follow their expected historical availability requirements.
- Glue partition metadata is available for querying.

This validation establishes an initial data quality baseline for the AWS Lakehouse.

Future pipeline executions should repeat these checks to monitor data quality as new ingestion dates are added.

## SQL Validation Queries

The complete validation SQL script is maintained in:

`docs/aws/athena-queries.sql`

It includes the queries used for record counts, date ranges, duplicates, null checks, OHLC integrity, Silver-to-Gold consistency, indicator coverage, sanity checks, and partition discovery.