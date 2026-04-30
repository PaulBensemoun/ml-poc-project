from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

SRC_DIR = PROJECT_ROOT / "src"
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = PROJECT_ROOT / "logs"
MODELS_DIR = PROJECT_ROOT / "models"
NOTEBOOKS_DIR = PROJECT_ROOT / "notebooks"
PLOTS_DIR = PROJECT_ROOT / "plots"
RESULTS_DIR = PROJECT_ROOT / "results"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
TESTS_DIR = PROJECT_ROOT / "tests"

COVEO_RAW_DIR = DATA_DIR / "coveo" / "raw"
COVEO_PROCESSED_DIR = DATA_DIR / "coveo" / "processed"

BROWSING_RAW = COVEO_RAW_DIR / "browsing_train.csv"
SEARCH_RAW = COVEO_RAW_DIR / "search_train.csv"
CONTENT_RAW = COVEO_RAW_DIR / "sku_to_content.csv"

SESSION_SAMPLE_PATH = COVEO_PROCESSED_DIR / "session_sample.parquet"

for _dir in [
    DATA_DIR,
    COVEO_PROCESSED_DIR,
    LOGS_DIR,
    MODELS_DIR,
    NOTEBOOKS_DIR,
    PLOTS_DIR,
    RESULTS_DIR,
    SCRIPTS_DIR,
    TESTS_DIR,
]:
    _dir.mkdir(parents=True, exist_ok=True)
