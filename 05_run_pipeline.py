
import logging
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent
LOG_DIR = PROJECT_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

RUN_TIMESTAMP = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
LOG_FILE = LOG_DIR / f"pipeline_{RUN_TIMESTAMP}.log"

PIPELINE_STEPS = [
    "01_fetch_stock_quote.py",
    "02_fetch_stock_history.py",
    "03_transform_stock_history.py",
    "04_validate_stock_data.py",
    "06_update_stock_history.py",
    "08_validate_persistent_history.py",
    "10_cleanup_raw_data.py",
]


def configure_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def run_step(script_name):
    script_path = PROJECT_DIR / script_name

    if not script_path.is_file():
        logging.error("Script not found: %s", script_path)
        raise FileNotFoundError(f"Script not found: {script_path}")

    logging.info("Starting step: %s", script_name)

    command = [sys.executable, str(script_path)]

    if script_name == "10_cleanup_raw_data.py":
        command.append("--auto")

    try:
        result = subprocess.run(
            command,
            cwd=PROJECT_DIR,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except OSError:
        logging.exception("Could not start script: %s", script_name)
        raise

    if result.stdout:
        for line in result.stdout.rstrip().splitlines():
            logging.info("[%s] %s", script_name, line)

    if result.stderr:
        for line in result.stderr.rstrip().splitlines():
            logging.warning("[%s] %s", script_name, line)

    if result.returncode != 0:
        logging.error(
            "Step failed: %s | Exit code: %s",
            script_name,
            result.returncode,
        )
        raise RuntimeError(
            f"Pipeline stopped at {script_name} "
            f"with exit code {result.returncode}"
        )

    logging.info(
        "Step completed successfully: %s | Exit code: 0",
        script_name,
    )


def main():
    configure_logging()

    logging.info("Pipeline started.")
    logging.info("Project directory: %s", PROJECT_DIR)
    logging.info("Python executable: %s", sys.executable)
    logging.info("Log file: %s", LOG_FILE)

    completed_steps = 0

    try:
        for script_name in PIPELINE_STEPS:
            run_step(script_name)
            completed_steps += 1

    except (FileNotFoundError, RuntimeError, OSError):
        logging.exception(
            "Pipeline failed after %s completed step(s).",
            completed_steps,
        )
        logging.error("Pipeline status: FAILED")
        sys.exit(1)

    logging.info(
        "Pipeline completed successfully. Steps completed: %s",
        completed_steps,
    )
    logging.info("Pipeline status: PASSED")


if __name__ == "__main__":
    main()
