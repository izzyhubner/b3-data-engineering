# Lakehouse vs. Data Warehouse: Architecture Comparison

## 1. Objective

This document compares the Lakehouse and Data Warehouse implementations developed in the B3 Data Engineering project.

Both architectures use the same underlying Brazilian stock market dataset, allowing their design choices, data organization, processing approaches and operational characteristics to be evaluated in a consistent context.

The project includes three analytical implementations:

1. AWS-based Parquet Lakehouse.
2. Databricks-based Delta Lakehouse.
3. PostgreSQL Data Warehouse.

The comparison focuses on architectural characteristics rather than assuming that one approach is universally superior.

## 2. Implemented Architectures

### 2.1 AWS Parquet Lakehouse

**Technologies:**
- Amazon S3
- Apache Parquet
- Snappy compression
- AWS Glue Data Catalog
- Amazon Athena
- Python and Boto3
- Terraform

Data is stored in S3 and organized into Raw, Processed, Silver and Gold layers.

Glue manages table metadata, while Athena provides serverless SQL access to the Parquet datasets.

### 2.2 Databricks Delta Lakehouse

**Technologies:**
- Databricks
- Apache Spark
- Delta Lake
- Unity Catalog
- Amazon S3

The existing Silver and Gold Parquet datasets are migrated into separate Delta Lake locations.

Unity Catalog manages the resulting tables, while Delta transaction logs provide transactional metadata and version history.

The original Parquet datasets remain unchanged.

### 2.3 PostgreSQL Data Warehouse

**Technologies:**
- PostgreSQL
- Python
- psycopg2
- Apache Parquet
- Dimensional modeling
- SQL

Silver and Gold datasets are integrated into a relational Star Schema.

The model contains:
- `dim_stock`
- `dim_date`
- `fact_daily_stock`

The fact table stores daily stock observations and analytical indicators.

## 3. Architectural Comparison

| Characteristic | AWS Parquet Lakehouse | Databricks Delta Lakehouse | PostgreSQL Data Warehouse |
|---|---|---|---|
| Storage | S3 | S3 | PostgreSQL tables |
| Primary format | Parquet | Delta Lake | Relational |
| Data organization | Layered datasets | Layered Delta tables | Star Schema |
| Metadata management | Glue Data Catalog | Unity Catalog | PostgreSQL catalog |
| Query engine | Athena | Spark SQL | PostgreSQL SQL |
| Transaction management | Object storage operations | Delta transaction log | Database transactions |
| Schema organization | File/table schemas | Delta schemas and tables | Relational tables |
| Processing | Python | Spark | Python and SQL |
| Data modeling | Layer-oriented | Layer-oriented | Dimensional |
| Main analytical structure | Silver and Gold datasets | Silver and Gold Delta tables | Fact and dimensions |

## 4. Data Modeling

### Lakehouse

The Lakehouse organizes data into layers according to processing and refinement stages.

Raw preserves source data, Processed contains structured transformations, Silver maintains historical records, and Gold provides analytical datasets.

This approach supports multiple data consumers and different analytical workloads.

### Data Warehouse

The Data Warehouse organizes data according to analytical entities and business processes.

The Star Schema centralizes daily stock observations in a fact table and uses dimensions to describe stocks and dates.

This makes analytical relationships explicit and provides a structured interface for SQL queries.

## 5. Data Processing and Maintenance

| Aspect | Lakehouse | Data Warehouse |
|---|---|---|
| Source ingestion | Python pipeline | Reuses existing Parquet datasets |
| Historical maintenance | Persistent Silver dataset | Fact table upsert |
| Analytical indicators | Gold transformation | Loaded from Gold |
| Incremental behavior | Existing pipeline and Delta capabilities | PostgreSQL conflict handling |
| Data validation | Pipeline validation scripts | Warehouse validation script |
| Data integration | File-based transformations | Relational joins and key resolution |

The Warehouse currently depends on the Lakehouse's Silver and Gold outputs.

This means the two architectures share the same upstream data preparation, but use different storage and analytical models.

## 6. Querying and Analytical Workloads

### Lakehouse

Athena and Spark SQL query structured datasets stored in object storage.

This architecture is suitable for exploring large datasets without requiring all data to reside in a traditional relational database.

Delta Lake adds transactional metadata and version history to the object-storage-based datasets.

### Data Warehouse

PostgreSQL provides relational SQL queries over the fact and dimension tables.

The dimensional model allows analytical queries to join daily stock observations with stock and calendar attributes.

Examples include:
- Average closing price by ticker.
- Returns by trading date.
- Moving averages by stock.
- Volume and volatility analysis.
- Comparisons across stocks and time periods.

## 7. Performance

Performance has not yet been evaluated through controlled benchmarks.

The current datasets contain approximately 230 records, which is insufficient for meaningful conclusions about large-scale performance.

A future benchmark should use the same data volume, equivalent analytical questions and comparable execution conditions.

Suggested measurements:

- Query execution time.
- Data scanned.
- Data read from storage.
- Query planning and execution overhead.
- Performance as dataset volume increases.
- Effects of partitioning and file organization.

No performance winner should be declared before these tests are performed.

## 8. Cost and Operational Complexity

### AWS Parquet Lakehouse

Potential costs include:
- S3 storage.
- Athena data scanned.
- Glue catalog usage where applicable.
- Other AWS infrastructure and operational resources.

The architecture separates storage from query execution.

### Databricks Delta Lakehouse

Potential costs in a production deployment include:
- Databricks compute.
- Cloud object storage.
- Supporting cloud infrastructure.

The current project uses Databricks Free Edition, so its observed development environment should not be interpreted as a production cost estimate.

### PostgreSQL Data Warehouse

The current implementation runs on a local PostgreSQL installation.

There is no separate managed database infrastructure cost in the current setup, although local hardware, maintenance, backup and operational effort still represent costs.

A managed production deployment would introduce hosting, storage, backup and maintenance expenses.

A numerical cost comparison has not yet been performed.

## 9. Data Quality and Governance

All three implementations rely on validation and consistent source data.

The original Lakehouse pipeline validates structured datasets before they are uploaded.

The Delta migration validates record counts and schema consistency.

The Warehouse validates record counts, unique keys, referential integrity and source-to-target key consistency.

Unity Catalog, Glue Data Catalog and PostgreSQL's relational constraints provide different metadata and governance mechanisms.

These mechanisms should be evaluated according to the access-control, discoverability and operational requirements of each architecture.

## 10. Current Project Results

The current validated dataset contains:

| Metric | Value |
|---|---:|
| Stock tickers | 10 |
| Trading dates | 23 |
| Silver records | 230 |
| Gold records | 230 |
| Delta Silver records | 230 |
| Delta Gold records | 230 |
| Warehouse fact records | 230 |

All current implementations have passed their respective record-count and structural validations.

The Warehouse loading process was also re-executed successfully without creating duplicate fact records.

## 11. Preliminary Conclusions

The implementations demonstrate different approaches to analytical data management.

The AWS Parquet Lakehouse provides a layered object-storage architecture with serverless SQL access.

The Databricks Delta Lakehouse extends the object-storage model with transactional metadata, version history and Spark-based processing.

The PostgreSQL Data Warehouse provides a relational dimensional model designed for structured analytical queries.

The architectures address overlapping analytical needs but differ in data organization, processing engines, metadata management and operational responsibilities.

The current project validates that all three approaches can represent the same stock market dataset.

However, performance, scalability and numerical cost conclusions require larger datasets and controlled benchmarks.

## 12. Final Assessment

The most appropriate architecture depends on workload characteristics, data volume, analytical requirements, infrastructure constraints and operational capabilities.

This project demonstrates the implementation of multiple analytical architectures using a shared data source and establishes a foundation for a more detailed quantitative comparison.