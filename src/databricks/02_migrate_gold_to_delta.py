
from delta.tables import DeltaTable

# Source: existing Gold Parquet
SOURCE_PATH = (
    "s3://izzy-b3-lakehouse/gold/"
    "ingestion_date=2026-10-30/daily_stock_indicators.parquet"
)

# Destination: new Delta representation
DELTA_PATH = (
    "s3://izzy-b3-lakehouse/databricks/"
    "gold/daily_stock_indicators/"
)

TABLE_NAME = "b3_lakehouse.gold.daily_stock_indicators"


print("Reading Gold Parquet data...")
gold_df = spark.read.parquet(SOURCE_PATH)

source_count = gold_df.count()

print(f"Source records: {source_count}")
print(f"Source columns: {gold_df.columns}")


print("Checking Delta destination...")

if DeltaTable.isDeltaTable(spark, DELTA_PATH):
    raise RuntimeError(
        f"Delta destination already exists: {DELTA_PATH}"
    )

if spark.catalog.tableExists(TABLE_NAME):
    raise RuntimeError(
        f"Unity Catalog table already exists: {TABLE_NAME}"
    )


print("Writing Delta table...")

gold_df.write \
    .format("delta") \
    .mode("overwrite") \
    .save(DELTA_PATH)

print(f"Delta data written to: {DELTA_PATH}")


print("Registering table in Unity Catalog...")

spark.sql(f"""
    CREATE TABLE {TABLE_NAME}
    USING DELTA
    LOCATION '{DELTA_PATH}'
""")

print(f"Table registered: {TABLE_NAME}")


print("\nMigration validation")
print("--------------------")

delta_df = spark.table(TABLE_NAME)
delta_count = delta_df.count()

print(f"Source records: {source_count}")
print(f"Delta records:  {delta_count}")

if source_count != delta_count:
    raise RuntimeError("Record count mismatch!")

if gold_df.schema != delta_df.schema:
    raise RuntimeError("Schema mismatch!")

print("\nGold migration completed successfully!")
