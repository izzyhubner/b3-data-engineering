
import hashlib
import logging
import os
from pathlib import Path

import boto3
from botocore.exceptions import BotoCoreError, ClientError


PROJECT_DIR = Path(__file__).resolve().parent
RAW_DIR = PROJECT_DIR / "data" / "raw"

BUCKET_NAME = "izzy-b3-lakehouse"
AWS_REGION = "us-east-1"
AWS_PROFILE = os.getenv("AWS_PROFILE", "b3-data-engineering")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)


def create_s3_client():
    session = boto3.Session(
        profile_name=AWS_PROFILE,
        region_name=AWS_REGION,
    )

    return session.client("s3")


def calculate_sha256(file_path):
    sha256 = hashlib.sha256()

    with file_path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            sha256.update(chunk)

    return sha256.hexdigest()


def get_s3_object_hash(s3_client, s3_key):
    try:
        response = s3_client.head_object(
            Bucket=BUCKET_NAME,
            Key=s3_key,
        )

        return response.get("Metadata", {}).get("sha256")

    except ClientError as error:
        error_code = error.response.get("Error", {}).get("Code")
        status_code = error.response.get(
            "ResponseMetadata", {}
        ).get("HTTPStatusCode")

        if error_code in ("404", "NoSuchKey", "NotFound") or status_code == 404:
            return None

        raise


def upload_raw_files():
    if not RAW_DIR.exists():
        raise FileNotFoundError(f"Raw directory not found: {RAW_DIR}")

    raw_files = sorted(RAW_DIR.glob("*.json"))

    if not raw_files:
        logging.warning("No Raw JSON files found.")
        return

    s3_client = create_s3_client()

    uploaded_files = 0
    skipped_files = 0

    for file_path in raw_files:
        ticker = file_path.name.split("_")[0].lower()
        s3_key = f"raw/{ticker}/{file_path.name}"

        try:
            local_hash = calculate_sha256(file_path)
            s3_hash = get_s3_object_hash(s3_client, s3_key)

            if local_hash == s3_hash:
                skipped_files += 1

                logging.info(
                    "Skipped unchanged file: %s",
                    file_path.name,
                )
                continue

            s3_client.upload_file(
                str(file_path),
                BUCKET_NAME,
                s3_key,
                ExtraArgs={
                    "Metadata": {
                        "sha256": local_hash,
                    }
                },
            )

            uploaded_files += 1

            logging.info(
                "Uploaded %s to s3://%s/%s",
                file_path.name,
                BUCKET_NAME,
                s3_key,
            )

        except (BotoCoreError, ClientError):
            logging.exception(
                "Failed to process file: %s",
                file_path.name,
            )
            raise

    logging.info(
        "Raw upload completed | Uploaded: %s | Skipped: %s",
        uploaded_files,
        skipped_files,
    )


def main():
    logging.info("Starting Raw upload to S3.")

    upload_raw_files()


if __name__ == "__main__":
    main()
