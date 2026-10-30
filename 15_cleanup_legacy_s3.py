
import boto3

BUCKET = "izzy-b3-lakehouse"

TICKERS = [
    "abev3", "b3sa3", "bbas3", "bbdc4", "itub4",
    "mglu3", "petr4", "rent3", "vale3", "wege3"
]


def collect_legacy_versions(s3):
    items = []

    paginator = s3.get_paginator("list_object_versions")

    for ticker in TICKERS:
        prefix = f"raw/{ticker}/"

        for page in paginator.paginate(
            Bucket=BUCKET,
            Prefix=prefix
        ):
            for version in page.get("Versions", []):
                items.append({
                    "Key": version["Key"],
                    "VersionId": version["VersionId"]
                })

            for marker in page.get("DeleteMarkers", []):
                items.append({
                    "Key": marker["Key"],
                    "VersionId": marker["VersionId"]
                })

    return items


def delete_legacy_versions(s3, items):
    deleted = 0

    for start in range(0, len(items), 1000):
        batch = items[start:start + 1000]

        response = s3.delete_objects(
            Bucket=BUCKET,
            Delete={
                "Objects": batch,
                "Quiet": True
            }
        )

        errors = response.get("Errors", [])

        if errors:
            for error in errors:
                print("ERROR:", error)

            raise RuntimeError("Some objects could not be deleted.")

        deleted += len(batch)
        print(f"Deleted: {deleted}/{len(items)}")

    return deleted


def main():
    session = boto3.Session(
        profile_name="b3-data-engineering"
    )
    s3 = session.client("s3")

    print("Collecting legacy S3 versions...")
    items = collect_legacy_versions(s3)

    print(f"\nTotal versions and delete markers: {len(items)}")

    if not items:
        print("Nothing to delete.")
        return

    print("\nPrefixes selected:")
    for ticker in TICKERS:
        print(f"  raw/{ticker}/")

    print("\nNew prefixes will NOT be touched:")
    print("  raw/quotes/")
    print("  raw/historical/")

    confirmation = input(
        "\nType APAGAR to permanently delete these versions: "
    )

    if confirmation != "APAGAR":
        print("Deletion cancelled.")
        return

    deleted = delete_legacy_versions(s3, items)

    print(f"\nCleanup completed. Deleted: {deleted}")


if __name__ == "__main__":
    main()
