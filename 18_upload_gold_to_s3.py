
import hashlib
from datetime import datetime, timezone
from pathlib import Path

import boto3
from botocore.exceptions import ClientError


AWS_PROFILE = "b3-data-engineering"
BUCKET_NAME = "izzy-b3-lakehouse"

SOURCE_FILE = Path("data/gold/daily_stock_indicators.csv")

INGESTION_DATE = datetime.now(timezone.utc).strftime("%Y-%m-%d")

S3_KEY = (
    f"gold/ingestion_date={INGESTION_DATE}/"
    "daily_stock_indicators.csv"
)


def calculate_sha256(file_path: Path) -> str:
    sha256 = hashlib.sha256()

    with file_path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            sha256.update(chunk)

    return sha256.hexdigest()


def get_existing_hash(s3_client, bucket: str, key: str):
    try:
        response = s3_client.head_object(
            Bucket=bucket,
            Key=key
        )

        return response.get("Metadata", {}).get("sha256")

    except ClientError as error:
        status_code = error.response.get(
            "ResponseMetadata", {}
        ).get("HTTPStatusCode")

        if status_code == 404:
            return None

        raise


def main():
    if not SOURCE_FILE.exists():
        raise FileNotFoundError(
            f"Gold file not found: {SOURCE_FILE}"
        )

    if SOURCE_FILE.stat().st_size == 0:
        raise ValueError(
            f"Gold file is empty: {SOURCE_FILE}"
        )

    file_hash = calculate_sha256(SOURCE_FILE)

    session = boto3.Session(
        profile_name=AWS_PROFILE
    )

    s3_client = session.client("s3")

    existing_hash = get_existing_hash(
        s3_client,
        BUCKET_NAME,
        S3_KEY
    )

    if existing_hash == file_hash:
        print("Gold file is already up to date.")
        print(f"S3 location: s3://{BUCKET_NAME}/{S3_KEY}")
        return

    s3_client.upload_file(
        str(SOURCE_FILE),
        BUCKET_NAME,
        S3_KEY,
        ExtraArgs={
            "Metadata": {
                "sha256": file_hash
            }
        }
    )

    print("Gold file uploaded successfully.")
    print(f"Source: {SOURCE_FILE}")
    print(f"Destination: s3://{BUCKET_NAME}/{S3_KEY}")
    print(f"SHA-256: {file_hash}")


if __name__ == "__main__":
    main()
