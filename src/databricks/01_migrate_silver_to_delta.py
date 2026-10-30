
from pyspark.sql import SparkSession

# --------------------------------------------------
# Configuration
# --------------------------------------------------

SOURCE_PATH = (
    "s3://izzy-b3-lakehouse/silver/"
)

DELTA_PATH = (
    "s3://izzy-b3-lakehouse/databricks/"
    "silver/daily_stock_history/"
)

CATALOG = "b3_lakehouse"
SCHEMA = "silver"
TABLE = "daily_stock_history"

FULL_TABLE_NAME = f"{CATALOG}.{SCHEMA}.{TABLE}"


# --------------------------------------------------
# Spark session
# --------------------------------------------------

spark = SparkSession.builder.getOrCreate()


# --------------------------------------------------
# Read existing Silver Parquet data
# --------------------------------------------------

print("Reading Silver Parquet data...")

df = spark.read.parquet(SOURCE_PATH)

source_count = df.count()

print(f"Source records: {source_count}")
print(f"Source columns: {df.columns}")

if source_count == 0:
    raise ValueError("Source dataset is empty.")


# --------------------------------------------------
# Write Delta table
# --------------------------------------------------

print("Writing Delta table...")

(
    df.write
    .format("delta")
    .mode("errorifexists")
    .save(DELTA_PATH)
)

print(f"Delta data written to: {DELTA_PATH}")


# --------------------------------------------------
# Register table in Unity Catalog
# --------------------------------------------------

print("Registering table in Unity Catalog...")

spark.sql(f"""
    CREATE TABLE {FULL_TABLE_NAME}
    USING DELTA
    LOCATION '{DELTA_PATH}'
""")

print(f"Table registered: {FULL_TABLE_NAME}")


# --------------------------------------------------
# Validate migration
# --------------------------------------------------

delta_df = spark.table(FULL_TABLE_NAME)

delta_count = delta_df.count()

print("\nMigration validation")
print("--------------------")
print(f"Source records: {source_count}")
print(f"Delta records:  {delta_count}")

if source_count != delta_count:
    raise ValueError("Record count mismatch!")

print("Migration completed successfully!")
