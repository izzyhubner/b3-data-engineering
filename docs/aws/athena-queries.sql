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
--   silver_daily_stock_history
--   gold_daily_stock_indicators
--
-- Partition column:
--   ingestion_date
--
-- Data format:
--   CSV
--
-- ============================================================


-- ============================================================
-- 1. CREATE GLUE DATABASE
-- ============================================================

CREATE DATABASE IF NOT EXISTS b3_lakehouse;


-- ============================================================
-- 2. CREATE SILVER EXTERNAL TABLE
-- ============================================================

CREATE EXTERNAL TABLE IF NOT EXISTS b3_lakehouse.silver_daily_stock_history (
    ticker STRING,
    trade_date DATE,
    open DOUBLE,
    high DOUBLE,
    low DOUBLE,
    close DOUBLE,
    volume DOUBLE,
    body DOUBLE,
    body_pct DOUBLE,
    price_range DOUBLE,
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
ROW FORMAT SERDE
    'org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe'
WITH SERDEPROPERTIES (
    'field.delim' = ',',
    'serialization.format' = ','
)
STORED AS TEXTFILE
LOCATION 's3://izzy-b3-lakehouse/silver/'
TBLPROPERTIES (
    'skip.header.line.count' = '1'
);


-- ============================================================
-- 3. CREATE GOLD EXTERNAL TABLE
-- ============================================================

CREATE EXTERNAL TABLE IF NOT EXISTS b3_lakehouse.gold_daily_stock_indicators (
    ticker STRING,
    trade_date DATE,
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
ROW FORMAT SERDE
    'org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe'
WITH SERDEPROPERTIES (
    'field.delim' = ',',
    'serialization.format' = ','
)
STORED AS TEXTFILE
LOCATION 's3://izzy-b3-lakehouse/gold/'
TBLPROPERTIES (
    'skip.header.line.count' = '1'
);


-- ============================================================
-- 4. REGISTER S3 PARTITIONS
-- ============================================================
--
-- Run after uploading new ingestion_date folders.
-- These commands discover partition folders in S3 and register
-- their metadata in the Glue Data Catalog.
--
-- They do not modify the underlying CSV files.
--
-- ============================================================

MSCK REPAIR TABLE b3_lakehouse.silver_daily_stock_history;

MSCK REPAIR TABLE b3_lakehouse.gold_daily_stock_indicators;


-- ============================================================
-- 5. INSPECT REGISTERED PARTITIONS
-- ============================================================

SHOW PARTITIONS b3_lakehouse.silver_daily_stock_history;

SHOW PARTITIONS b3_lakehouse.gold_daily_stock_indicators;


-- ============================================================
-- 6. BASIC GOLD DATA QUERY
-- ============================================================

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


-- ============================================================
-- 7. DATA QUALITY VALIDATION
-- ============================================================


-- 7.1 SILVER: RECORD COUNT AND DATE RANGE

SELECT
    'SILVER' AS layer,
    ticker,
    COUNT(*) AS total_records,
    MIN(trade_date) AS first_trade_date,
    MAX(trade_date) AS last_trade_date,
    COUNT(DISTINCT trade_date) AS distinct_trading_days
FROM b3_lakehouse.silver_daily_stock_history
GROUP BY ticker
ORDER BY ticker;


-- 7.2 GOLD: RECORD COUNT AND DATE RANGE

SELECT
    'GOLD' AS layer,
    ticker,
    COUNT(*) AS total_records,
    MIN(trade_date) AS first_trade_date,
    MAX(trade_date) AS last_trade_date,
    COUNT(DISTINCT trade_date) AS distinct_trading_days
FROM b3_lakehouse.gold_daily_stock_indicators
GROUP BY ticker
ORDER BY ticker;


-- 7.3 SILVER: DUPLICATE TICKER-DATE KEYS
-- Expected result: no rows.

SELECT
    ticker,
    trade_date,
    COUNT(*) AS occurrences
FROM b3_lakehouse.silver_daily_stock_history
GROUP BY ticker, trade_date
HAVING COUNT(*) > 1
ORDER BY ticker, trade_date;


-- 7.4 GOLD: DUPLICATE TICKER-DATE KEYS
-- Expected result: no rows.

SELECT
    ticker,
    trade_date,
    COUNT(*) AS occurrences
FROM b3_lakehouse.gold_daily_stock_indicators
GROUP BY ticker, trade_date
HAVING COUNT(*) > 1
ORDER BY ticker, trade_date;


-- 7.5 SILVER: NULL VALUES IN CRITICAL FIELDS

SELECT
    ticker,
    COUNT(*) AS total_records,
    COUNT_IF(trade_date IS NULL) AS null_dates,
    COUNT_IF(open IS NULL) AS null_open,
    COUNT_IF(high IS NULL) AS null_high,
    COUNT_IF(low IS NULL) AS null_low,
    COUNT_IF(close IS NULL) AS null_close,
    COUNT_IF(volume IS NULL) AS null_volume
FROM b3_lakehouse.silver_daily_stock_history
GROUP BY ticker
ORDER BY ticker;


-- 7.6 GOLD: NULL VALUES IN CRITICAL FIELDS

SELECT
    ticker,
    COUNT(*) AS total_records,
    COUNT_IF(trade_date IS NULL) AS null_dates,
    COUNT_IF(close IS NULL) AS null_close,
    COUNT_IF(volume IS NULL) AS null_volume
FROM b3_lakehouse.gold_daily_stock_indicators
GROUP BY ticker
ORDER BY ticker;


-- 7.7 SILVER: OHLC VALIDATION
-- Expected result: no rows.

SELECT
    ticker,
    trade_date,
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
FROM b3_lakehouse.silver_daily_stock_history
WHERE
    high < low
    OR high < GREATEST(open, close)
    OR low > LEAST(open, close)
    OR open <= 0
    OR high <= 0
    OR low <= 0
    OR close <= 0
    OR volume < 0
ORDER BY ticker, trade_date;


-- 7.8 SILVER VS GOLD: RECORD COUNT COMPARISON

WITH silver_counts AS (
    SELECT
        ticker,
        COUNT(*) AS silver_records
    FROM b3_lakehouse.silver_daily_stock_history
    GROUP BY ticker
),
gold_counts AS (
    SELECT
        ticker,
        COUNT(*) AS gold_records
    FROM b3_lakehouse.gold_daily_stock_indicators
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


-- 7.9 SILVER VS GOLD: MISSING OR EXTRA TICKER-DATE KEYS
-- Expected result: no rows.

SELECT
    COALESCE(s.ticker, g.ticker) AS ticker,
    COALESCE(s.trade_date, g.trade_date) AS trade_date,
    CASE
        WHEN s.ticker IS NULL THEN 'MISSING IN SILVER'
        WHEN g.ticker IS NULL THEN 'MISSING IN GOLD'
    END AS discrepancy
FROM (
    SELECT DISTINCT ticker, trade_date
    FROM b3_lakehouse.silver_daily_stock_history
) s
FULL OUTER JOIN (
    SELECT DISTINCT ticker, trade_date
    FROM b3_lakehouse.gold_daily_stock_indicators
) g
    ON s.ticker = g.ticker
    AND s.trade_date = g.trade_date
WHERE s.ticker IS NULL OR g.ticker IS NULL
ORDER BY ticker, trade_date;


-- 7.10 GOLD: INDICATOR COVERAGE

SELECT
    ticker,
    COUNT(*) AS total_records,
    COUNT_IF(sma_5 IS NOT NULL) AS records_with_sma_5,
    COUNT_IF(sma_20 IS NOT NULL) AS records_with_sma_20,
    COUNT_IF(volatility_5d IS NOT NULL)
        AS records_with_volatility,
    COUNT_IF(volume_ratio IS NOT NULL)
        AS records_with_volume_ratio
FROM b3_lakehouse.gold_daily_stock_indicators
GROUP BY ticker
ORDER BY ticker;


-- 7.11 GOLD: INDICATOR SANITY CHECK
-- Expected result: no rows.

SELECT
    ticker,
    trade_date,
    close,
    sma_5,
    sma_20,
    daily_return_pct,
    volatility_5d,
    volume,
    volume_ratio
FROM b3_lakehouse.gold_daily_stock_indicators
WHERE
    close <= 0
    OR volume < 0
    OR volatility_5d < 0
    OR volume_ratio < 0
ORDER BY ticker, trade_date;


-- ============================================================
-- 8. PARTITION INSPECTION
-- ============================================================

SHOW PARTITIONS b3_lakehouse.silver_daily_stock_history;

SHOW PARTITIONS b3_lakehouse.gold_daily_stock_indicators;


-- ============================================================
-- END OF ATHENA SQL DOCUMENTATION
-- ============================================================