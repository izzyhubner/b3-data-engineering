
import logging
from collections import defaultdict
from pathlib import Path

from stock_config import TICKERS


PROJECT_DIR = Path(__file__).resolve().parent
RAW_DIR = PROJECT_DIR / "data" / "raw"

TICKERS = set(TICKERS)

KEEP_LATEST = {
    "quote": 1,
    "history": 3,
}

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s | %(message)s",
)


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

    kept_files = []
    candidate_files = []

    for key, files in sorted(grouped_files.items()):
        ticker, file_type = key

        # Filenames contain sortable timestamps: YYYYMMDD_HHMMSS.
        ordered_files = sorted(
            files,
            key=lambda path: path.name,
            reverse=True,
        )

        keep_count = KEEP_LATEST[file_type]

        kept = ordered_files[:keep_count]
        candidates = ordered_files[keep_count:]

        kept_files.extend(kept)
        candidate_files.extend(candidates)

        logging.info(
            "%s | %s | Found: %s | Keep: %s | Candidates: %s",
            ticker,
            file_type,
            len(files),
            len(kept),
            len(candidates),
        )

        for file_path in candidates:
            logging.info("  CANDIDATE: %s", file_path.name)

    kept_size = sum(path.stat().st_size for path in kept_files)
    candidate_size = sum(path.stat().st_size for path in candidate_files)

    logging.info("")
    logging.info("RETENTION PREVIEW SUMMARY")
    logging.info("Files to keep: %s", len(kept_files))
    logging.info("Files to keep size: %.2f KB", kept_size / 1024)
    logging.info("Deletion candidates: %s", len(candidate_files))
    logging.info("Candidate size: %.2f KB", candidate_size / 1024)
    logging.info("Unclassified files: %s", len(unclassified_files))
    logging.info("")

    if unclassified_files:
        logging.warning("Unclassified files will not be considered for deletion:")
        for file_path in unclassified_files:
            logging.warning("  %s", file_path.name)

    logging.info("PREVIEW ONLY: no files were modified or deleted.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
