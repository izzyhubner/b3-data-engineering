
import hashlib
import logging
from datetime import datetime, timezone
from pathlib import Path

import boto3
from botocore.exceptions import ClientError


PROJECT_DIR = Path(__file__).resolve().parent
SOURCE_FILE = (
    PROJECT_DIR
    / "data"
    / "parquet"
    / "processed"
    / "daily_stock_analysis.parquet"
)

BUCKET = "izzy-b3-lakehouse"
AWS_PROFILE = "b3-data-engineering"


def calculate_sha256(file_path):
    sha256 = hashlib.sha256()

    with file_path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            sha256.update(chunk)

    return sha256.hexdigest()


def get_existing_hash(s3, key):
    try:
        response = s3.head_object(Bucket=BUCKET, Key=key)
        return response.get("Metadata", {}).get("sha256")

    except ClientError as error:
        status_code = error.response.get(
            "ResponseMetadata", {}
        ).get("HTTPStatusCode")

        if status_code == 404:
            return None

        raise


def upload_processed_data():
    logging.info("Starting Processed Parquet upload.")

    if not SOURCE_FILE.is_file():
        raise FileNotFoundError(
            f"Processed Parquet file not found: {SOURCE_FILE}"
        )

    if SOURCE_FILE.stat().st_size == 0:
        raise ValueError("Processed Parquet file is empty.")

    ingestion_date = datetime.now(
        timezone.utc
    ).strftime("%Y-%m-%d")

    s3_key = (
        f"processed/ingestion_date={ingestion_date}/"
        "daily_stock_analysis.parquet"
    )

    file_hash = calculate_sha256(SOURCE_FILE)

    session = boto3.Session(profile_name=AWS_PROFILE)
    s3 = session.client("s3")

    existing_hash = get_existing_hash(s3, s3_key)

    if existing_hash == file_hash:
        logging.info("Processed Parquet unchanged. Upload skipped.")
        return

    s3.upload_file(
        str(SOURCE_FILE),
        BUCKET,
        s3_key,
        ExtraArgs={
            "ContentType": "application/vnd.apache.parquet",
            "Metadata": {"sha256": file_hash},
        },
    )

    logging.info(
        "Processed Parquet uploaded: s3://%s/%s",
        BUCKET,
        s3_key,
    )


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )

    upload_processed_data()


if __name__ == "__main__":
    main()
