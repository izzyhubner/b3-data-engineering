```sql
-- ============================================================
-- B3 DATA ENGINEERING
-- AWS GLUE DATA CATALOG AND AMAZON ATHENA
-- ============================================================
--
-- AWS Region: us-east-1
-- S3 Bucket: izzy-b3-lakehouse
-- Glue Database: b3_lakehouse
--
-- Tables:
--   processed_daily_stock_analysis_parquet
--   silver_daily_stock_history_parquet
--   gold_daily_stock_indicators_parquet
--
-- Partition column:
--   ingestion_date
--
-- Data formats:
--   Raw: JSON
--   Processed, Silver, Gold: Parquet (Snappy compression)
--
-- IMPORTANT:
-- Athena accepts one SQL statement per execution.
-- Execute each DDL, MSCK, SHOW, or SELECT separately.
--
-- ============================================================


-- ============================================================
-- 1. CREATE GLUE DATABASE
-- ============================================================

CREATE DATABASE IF NOT EXISTS b3_lakehouse;


-- ============================================================
-- 2. CREATE PROCESSED EXTERNAL TABLE
-- ============================================================

CREATE EXTERNAL TABLE IF NOT EXISTS b3_lakehouse.processed_daily_stock_analysis_parquet (
    ticker STRING,
    date DATE,
    open DOUBLE,
    high DOUBLE,
    low DOUBLE,
    close DOUBLE,
    volume DOUBLE,
    body DOUBLE,
    body_pct DOUBLE,
    `range` DOUBLE,
    range_pct DOUBLE,
    upper_wick DOUBLE,
    lower_wick DOUBLE,
    close_position DOUBLE,
    is_bullish BOOLEAN,
    close_return_pct DOUBLE,
    gap_pct DOUBLE,
    candle_body DOUBLE,
    candle_range DOUBLE,
    upper_shadow DOUBLE,
    lower_shadow DOUBLE,
    daily_return_pct DOUBLE,
    overnight_gap_pct DOUBLE,
    volume_avg_5d DOUBLE
)
PARTITIONED BY (
    ingestion_date STRING
)
STORED AS PARQUET
LOCATION 's3://izzy-b3-lakehouse/processed/';


-- ============================================================
-- 3. CREATE SILVER EXTERNAL TABLE
-- ============================================================

CREATE EXTERNAL TABLE IF NOT EXISTS b3_lakehouse.silver_daily_stock_history_parquet (
    ticker STRING,
    date DATE,
    open DOUBLE,
    high DOUBLE,
    low DOUBLE,
    close DOUBLE,
    volume DOUBLE,
    body DOUBLE,
    body_pct DOUBLE,
    `range` DOUBLE,
    range_pct DOUBLE,
    upper_wick DOUBLE,
    lower_wick DOUBLE,
    close_position DOUBLE,
    is_bullish BOOLEAN,
    close_return_pct DOUBLE,
    gap_pct DOUBLE,
    candle_body DOUBLE,
    candle_range DOUBLE,
    upper_shadow DOUBLE,
    lower_shadow DOUBLE,
    daily_return_pct DOUBLE,
    overnight_gap_pct DOUBLE,
    volume_avg_5d DOUBLE
)
PARTITIONED BY (
    ingestion_date STRING
)
STORED AS PARQUET
LOCATION 's3://izzy-b3-lakehouse/silver/';


-- ============================================================
-- 4. CREATE GOLD EXTERNAL TABLE
-- ============================================================

CREATE EXTERNAL TABLE IF NOT EXISTS b3_lakehouse.gold_daily_stock_indicators_parquet (
    ticker STRING,
    date DATE,
    close DOUBLE,
    daily_return_pct DOUBLE,
    sma_5 DOUBLE,
    sma_20 DOUBLE,
    volatility_5d DOUBLE,
    volume DOUBLE,
    volume_ratio DOUBLE
)
PARTITIONED BY (
    ingestion_date STRING
)
STORED AS PARQUET
LOCATION 's3://izzy-b3-lakehouse/gold/';


-- ============================================================
-- 5. REGISTER S3 PARTITIONS
-- ============================================================
--
-- Run after uploading new ingestion_date folders.
-- Execute each statement separately.
--
-- These commands discover Hive-style partition folders
-- and register their metadata in the Glue Data Catalog.
--
-- They do not modify the underlying Parquet files.
--
-- ============================================================

MSCK REPAIR TABLE b3_lakehouse.processed_daily_stock_analysis_parquet;

MSCK REPAIR TABLE b3_lakehouse.silver_daily_stock_history_parquet;

MSCK REPAIR TABLE b3_lakehouse.gold_daily_stock_indicators_parquet;


-- ============================================================
-- 6. INSPECT REGISTERED PARTITIONS
-- ============================================================

SHOW PARTITIONS b3_lakehouse.processed_daily_stock_analysis_parquet;

SHOW PARTITIONS b3_lakehouse.silver_daily_stock_history_parquet;

SHOW PARTITIONS b3_lakehouse.gold_daily_stock_indicators_parquet;


-- ============================================================
-- 7. BASIC GOLD DATA QUERY
-- ============================================================

SELECT
    ticker,
    date,
    close,
    sma_5,
    sma_20,
    daily_return_pct,
    volatility_5d,
    volume_ratio
FROM b3_lakehouse.gold_daily_stock_indicators_parquet
WHERE ticker = 'ABEV3'
ORDER BY date DESC
LIMIT 10;


-- ============================================================
-- 8. DATA QUALITY VALIDATION
-- ============================================================


-- 8.1 PROCESSED: RECORD COUNT AND DATE RANGE

SELECT
    'PROCESSED' AS layer,
    ticker,
    COUNT(*) AS total_records,
    MIN(date) AS first_date,
    MAX(date) AS last_date,
    COUNT(DISTINCT date) AS distinct_trading_days
FROM b3_lakehouse.processed_daily_stock_analysis_parquet
GROUP BY ticker
ORDER BY ticker;


-- 8.2 SILVER: RECORD COUNT AND DATE RANGE

SELECT
    'SILVER' AS layer,
    ticker,
    COUNT(*) AS total_records,
    MIN(date) AS first_date,
    MAX(date) AS last_date,
    COUNT(DISTINCT date) AS distinct_trading_days
FROM b3_lakehouse.silver_daily_stock_history_parquet
GROUP BY ticker
ORDER BY ticker;


-- 8.3 GOLD: RECORD COUNT AND DATE RANGE

SELECT
    'GOLD' AS layer,
    ticker,
    COUNT(*) AS total_records,
    MIN(date) AS first_date,
    MAX(date) AS last_date,
    COUNT(DISTINCT date) AS distinct_trading_days
FROM b3_lakehouse.gold_daily_stock_indicators_parquet
GROUP BY ticker
ORDER BY ticker;


-- 8.4 SILVER: DUPLICATE TICKER-DATE KEYS
-- Expected result: no rows.

SELECT
    ticker,
    date,
    COUNT(*) AS occurrences
FROM b3_lakehouse.silver_daily_stock_history_parquet
GROUP BY ticker, date
HAVING COUNT(*) > 1
ORDER BY ticker, date;


-- 8.5 GOLD: DUPLICATE TICKER-DATE KEYS
-- Expected result: no rows.

SELECT
    ticker,
    date,
    COUNT(*) AS occurrences
FROM b3_lakehouse.gold_daily_stock_indicators_parquet
GROUP BY ticker, date
HAVING COUNT(*) > 1
ORDER BY ticker, date;


-- 8.6 SILVER: NULL VALUES IN CRITICAL FIELDS

SELECT
    ticker,
    COUNT(*) AS total_records,
    COUNT_IF(date IS NULL) AS null_dates,
    COUNT_IF(open IS NULL) AS null_open,
    COUNT_IF(high IS NULL) AS null_high,
    COUNT_IF(low IS NULL) AS null_low,
    COUNT_IF(close IS NULL) AS null_close,
    COUNT_IF(volume IS NULL) AS null_volume
FROM b3_lakehouse.silver_daily_stock_history_parquet
GROUP BY ticker
ORDER BY ticker;


-- 8.7 GOLD: NULL VALUES IN CRITICAL FIELDS

SELECT
    ticker,
    COUNT(*) AS total_records,
    COUNT_IF(date IS NULL) AS null_dates,
    COUNT_IF(close IS NULL) AS null_close,
    COUNT_IF(volume IS NULL) AS null_volume
FROM b3_lakehouse.gold_daily_stock_indicators_parquet
GROUP BY ticker
ORDER BY ticker;


-- 8.8 SILVER: OHLC VALIDATION
-- Expected result: no rows.

SELECT
    ticker,
    date,
    open,
    high,
    low,
    close,
    CASE
        WHEN high < low THEN 'INVALID: HIGH BELOW LOW'
        WHEN high < GREATEST(open, close)
            THEN 'INVALID: HIGH BELOW OPEN/CLOSE'
        WHEN low > LEAST(open, close)
            THEN 'INVALID: LOW ABOVE OPEN/CLOSE'
        WHEN open <= 0 OR high <= 0 OR low <= 0 OR close <= 0
            THEN 'INVALID: NON-POSITIVE PRICE'
        WHEN volume < 0 THEN 'INVALID: NEGATIVE VOLUME'
        ELSE 'VALID'
    END AS validation_status
FROM b3_lakehouse.silver_daily_stock_history_parquet
WHERE
    high < low
    OR high < GREATEST(open, close)
    OR low > LEAST(open, close)
    OR open <= 0
    OR high <= 0
    OR low <= 0
    OR close <= 0
    OR volume < 0
ORDER BY ticker, date;


-- 8.9 SILVER VS GOLD: RECORD COUNT COMPARISON

WITH silver_counts AS (
    SELECT
        ticker,
        COUNT(*) AS silver_records
    FROM b3_lakehouse.silver_daily_stock_history_parquet
    GROUP BY ticker
),
gold_counts AS (
    SELECT
        ticker,
        COUNT(*) AS gold_records
    FROM b3_lakehouse.gold_daily_stock_indicators_parquet
    GROUP BY ticker
)
SELECT
    COALESCE(s.ticker, g.ticker) AS ticker,
    COALESCE(s.silver_records, 0) AS silver_records,
    COALESCE(g.gold_records, 0) AS gold_records,
    COALESCE(s.silver_records, 0)
        - COALESCE(g.gold_records, 0) AS record_difference
FROM silver_counts s
FULL OUTER JOIN gold_counts g
    ON s.ticker = g.ticker
ORDER BY ticker;


-- 8.10 SILVER VS GOLD: MISSING OR EXTRA TICKER-DATE KEYS
-- Expected result: no rows.

SELECT
    COALESCE(s.ticker, g.ticker) AS ticker,
    COALESCE(s.date, g.date) AS date,
    CASE
        WHEN s.ticker IS NULL THEN 'MISSING IN SILVER'
        WHEN g.ticker IS NULL THEN 'MISSING IN GOLD'
    END AS discrepancy
FROM (
    SELECT DISTINCT ticker, date
    FROM b3_lakehouse.silver_daily_stock_history_parquet
) s
FULL OUTER JOIN (
    SELECT DISTINCT ticker, date
    FROM b3_lakehouse.gold_daily_stock_indicators_parquet
) g
    ON s.ticker = g.ticker
    AND s.date = g.date
WHERE s.ticker IS NULL OR g.ticker IS NULL
ORDER BY ticker, date;


-- 8.11 GOLD: INDICATOR COVERAGE

SELECT
    ticker,
    COUNT(*) AS total_records,
    COUNT_IF(sma_5 IS NOT NULL) AS records_with_sma_5,
    COUNT_IF(sma_20 IS NOT NULL) AS records_with_sma_20,
    COUNT_IF(volatility_5d IS NOT NULL) AS records_with_volatility,
    COUNT_IF(volume_ratio IS NOT NULL) AS records_with_volume_ratio
FROM b3_lakehouse.gold_daily_stock_indicators_parquet
GROUP BY ticker
ORDER BY ticker;


-- 8.12 GOLD: INDICATOR SANITY CHECK
-- Expected result: no rows.

SELECT
    ticker,
    date,
    close,
    sma_5,
    sma_20,
    daily_return_pct,
    volatility_5d,
    volume,
    volume_ratio
FROM b3_lakehouse.gold_daily_stock_indicators_parquet
WHERE
    close <= 0
    OR volume < 0
    OR volatility_5d < 0
    OR volume_ratio < 0
ORDER BY ticker, date;


-- ============================================================
-- 9. LAYER ROW COUNT SUMMARY
-- ============================================================

SELECT
    'processed' AS layer,
    COUNT(*) AS total_rows,
    COUNT(DISTINCT ticker) AS total_tickers,
    MIN(date) AS first_date,
    MAX(date) AS last_date
FROM b3_lakehouse.processed_daily_stock_analysis_parquet

UNION ALL

SELECT
    'silver',
    COUNT(*),
    COUNT(DISTINCT ticker),
    MIN(date),
    MAX(date)
FROM b3_lakehouse.silver_daily_stock_history_parquet

UNION ALL

SELECT
    'gold',
    COUNT(*),
    COUNT(DISTINCT ticker),
    MIN(date),
    MAX(date)
FROM b3_lakehouse.gold_daily_stock_indicators_parquet;


-- ============================================================
-- END OF ATHENA SQL DOCUMENTATION
-- ============================================================
```