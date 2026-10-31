# Data Warehouse Architecture

## 1. Overview

The B3 Data Warehouse is a relational analytical database implemented using PostgreSQL.

It consumes the existing Silver and Gold Parquet datasets produced by the Lakehouse pipeline and consolidates them into a dimensional model.

The objective is to provide a structured analytical environment using a traditional Data Warehouse architecture, enabling comparison with the project's Lakehouse implementations.

**Database:** `b3_warehouse`  
**Schema:** `dw`  
**Database engine:** PostgreSQL

## 2. Architecture

```text
             B3 Stock Data
                   |
                   v
          Existing Lakehouse
                   |
             +-----+-----+
             |           |
             v           v
           Silver       Gold
          Parquet      Parquet
             |           |
             +-----+-----+
                   |
                   v
             Python ETL
                   |
          Data Integration
          and Transformation
                   |
                   v
          PostgreSQL Warehouse
                   |
             +-----+-----+
             |           |
             v           v
          Dimensions   Fact Table
             |           |
             +-----+-----+
                   |
                   v
            Analytical SQL
```

The Warehouse uses the same underlying stock market data as the Lakehouse.

Silver provides historical prices and derived candle metrics. Gold provides analytical indicators.

The Python loading process combines both datasets using `(ticker, date)` as the business key.

## 3. Dimensional Model

The Warehouse uses a Star Schema with one central fact table and two dimensions.

### 3.1 dim_stock

Stores the stock identifiers used by the fact table.

| Column | Description |
|---|---|
| stock_key | Surrogate primary key |
| ticker | Stock ticker, unique business identifier |

Each ticker has one record in the dimension.

### 3.2 dim_date

Stores calendar attributes for analytical queries.

| Column | Description |
|---|---|
| date_key | Integer date key in YYYYMMDD format |
| full_date | Actual calendar date |
| year | Calendar year |
| quarter | Calendar quarter |
| month | Month number |
| day | Day of month |
| day_of_week | ISO weekday number |
| day_name | Weekday name |
| month_name | Month name |
| is_weekend | Weekend indicator |

The current implementation contains the distinct trading dates available in the source datasets.

### 3.3 fact_daily_stock

Stores one record per stock and trading date.

**Composite primary key:** `(stock_key, date_key)`

The table contains:

- OHLC prices: open, high, low and close.
- Trading volume.
- Candle metrics: body, range, wicks, shadows and close position.
- Bullish candle indicator.
- Daily returns and overnight gaps.
- Five-day average volume.
- Gold indicators: SMA 5, SMA 20, five-day volatility and volume ratio.

The fact table uses foreign keys to both dimensions.

## 4. Data Integration

The loading process reads:

- `data/parquet/silver/daily_stock_history.parquet`
- `data/parquet/gold/daily_stock_indicators.parquet`

Both datasets are validated before loading.

The integration process:

1. Checks that Silver and Gold contain unique `(ticker, date)` keys.
2. Checks that both datasets contain matching business keys.
3. Loads distinct tickers into `dim_stock`.
4. Loads distinct trading dates into `dim_date`.
5. Resolves surrogate keys.
6. Combines Silver and Gold attributes.
7. Loads the resulting records into `fact_daily_stock`.

Metrics shared by Silver and Gold, such as closing price, daily return and volume, are stored only once.

## 5. Incremental Loading and Idempotency

The loading process uses PostgreSQL `INSERT ... ON CONFLICT`.

Dimension records are inserted without duplicating existing stock identifiers. Date attributes are updated when a matching date key already exists.

Fact records use the composite key `(stock_key, date_key)`.

When a record already exists, its attributes are updated. Otherwise, a new record is inserted.

This allows the loading script to be executed repeatedly without creating duplicate fact records.

## 6. Data Validation

The project includes an automated validation script:

`src/warehouse/validate_warehouse.py`

It validates:

- Stock dimension record count.
- Date dimension record count.
- Fact table record count.
- Unique fact keys.
- Referential integrity.
- Source-to-Warehouse ticker/date key consistency.

The validation compares the Warehouse against the current Silver and Gold Parquet datasets.

## 7. Implementation

Main scripts:

| Script | Responsibility |
|---|---|
| `src/warehouse/load_warehouse.py` | Loads dimensions and fact records |
| `src/warehouse/validate_warehouse.py` | Validates Warehouse consistency |

The PostgreSQL connection is configured through environment variables.

The database password is not stored in the source code.

## 8. Current Validation Results

Latest successful execution:

| Metric | Result |
|---|---:|
| Distinct stocks | 10 |
| Distinct trading dates | 23 |
| Fact records | 230 |
| Unique fact keys | 230 |
| Referential integrity violations | 0 |

The loading process was executed more than once, and the record counts remained unchanged.

The automated validation completed successfully.

## 9. Current Limitations

- PostgreSQL is running locally rather than on managed cloud infrastructure.
- The date dimension currently contains source trading dates rather than a complete calendar.
- The current dataset is relatively small and does not support meaningful large-scale performance conclusions.
- Performance benchmarks and numerical cost comparisons have not yet been performed.
- The current model represents daily stock observations and does not yet include additional business dimensions or historical stock master data.

## 10. Future Considerations

The current implementation is sufficient for the project's architectural comparison.

Potential future extensions include a complete calendar dimension, additional analytical dimensions, and larger historical datasets.