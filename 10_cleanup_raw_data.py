
import argparse
import logging
from collections import defaultdict
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent
RAW_DIR = PROJECT_DIR / "data" / "raw"

TICKERS = {"PETR4", "VALE3", "ITUB4", "MGLU3"}

KEEP_LATEST = {
    "quote": 1,
    "history": 3,
}

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s | %(message)s",
)


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Clean up old raw stock data files."
    )
    parser.add_argument(
        "--auto",
        action="store_true",
        help="Run cleanup without manual confirmation.",
    )
    return parser.parse_args()


def classify_file(file_path):
    name = file_path.name.lower()

    for ticker in TICKERS:
        prefix = ticker.lower()

        if name.startswith(f"{prefix}_history_") and name.endswith(".json"):
            return ticker, "history"

        if name.startswith(f"{prefix}_") and name.endswith(".json"):
            return ticker, "quote"

    return None, None


def main():
    args = parse_arguments()

    if not RAW_DIR.is_dir():
        logging.error("Raw data directory not found: %s", RAW_DIR)
        return 1

    grouped_files = defaultdict(list)
    unclassified_files = []

    for file_path in RAW_DIR.iterdir():
        if not file_path.is_file() or file_path.suffix.lower() != ".json":
            continue

        ticker, file_type = classify_file(file_path)

        if ticker is None:
            unclassified_files.append(file_path)
            continue

        grouped_files[(ticker, file_type)].append(file_path)

    candidates = []

    for key, files in sorted(grouped_files.items()):
        _, file_type = key

        ordered_files = sorted(
            files,
            key=lambda path: path.name,
            reverse=True,
        )

        keep_count = KEEP_LATEST[file_type]
        candidates.extend(ordered_files[keep_count:])

    if unclassified_files:
        logging.warning(
            "Unclassified files found: %s. They will not be deleted.",
            len(unclassified_files),
        )

    if not candidates:
        logging.info("No files need to be deleted.")
        return 0

    total_size = sum(path.stat().st_size for path in candidates)

    logging.info("RAW DATA CLEANUP")
    logging.info("Files to delete: %s", len(candidates))
    logging.info("Potential space recovery: %.2f KB", total_size / 1024)

    for file_path in candidates:
        logging.info("DELETE: %s", file_path.name)

    if not args.auto:
        confirmation = input(
            "\nType DELETE to permanently remove these files: "
        )

        if confirmation != "DELETE":
            logging.info("Cleanup cancelled. No files were deleted.")
            return 0
    else:
        logging.info("Automatic cleanup enabled.")

    deleted_count = 0
    deleted_size = 0
    failed_count = 0

    for file_path in candidates:
        try:
            file_size = file_path.stat().st_size
            file_path.unlink()
            deleted_count += 1
            deleted_size += file_size
        except OSError:
            logging.exception("Could not delete file: %s", file_path.name)
            failed_count += 1

    logging.info("")
    logging.info("CLEANUP SUMMARY")
    logging.info("Files deleted: %s", deleted_count)
    logging.info("Space recovered: %.2f KB", deleted_size / 1024)
    logging.info("Deletion failures: %s", failed_count)
    logging.info("Unclassified files preserved: %s", len(unclassified_files))

    return 1 if failed_count else 0


if __name__ == "__main__":
    raise SystemExit(main())