from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
SRC_DIR = PROJECT_ROOT / "src"

# --- Paths (aligned with notebook / repo layout) ---
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
# Backward-compatible aliases used elsewhere in the template
DATA_RAW_DIR = RAW_DATA_DIR
DATA_PROCESSED_DIR = PROCESSED_DATA_DIR

PROCESSED_MOVIES_CSV = PROCESSED_DATA_DIR / "movies_cleaned_with_target.csv"
TMDB_CREDITS_CSV = RAW_DATA_DIR / "tmdb_5000_credits.csv"

LOGS_DIR = PROJECT_ROOT / "logs"
MODELS_DIR = PROJECT_ROOT / "models"
NOTEBOOKS_DIR = PROJECT_ROOT / "notebooks"
PLOTS_DIR = PROJECT_ROOT / "plots"
RESULTS_DIR = PROJECT_ROOT / "results"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
TESTS_DIR = PROJECT_ROOT / "tests"

for dir in [
    DATA_DIR,
    RAW_DATA_DIR,
    PROCESSED_DATA_DIR,
    LOGS_DIR,
    MODELS_DIR,
    NOTEBOOKS_DIR,
    PLOTS_DIR,
    RESULTS_DIR,
    SCRIPTS_DIR,
    TESTS_DIR,
]:
    dir.mkdir(parents=True, exist_ok=True)

ENV_FILE = PROJECT_ROOT / ".env"
APP_ENTRYPOINT = PROJECT_ROOT / "src" / "app.py"
MODEL_METRICS_FILE = RESULTS_DIR / "model_metrics.csv"
TRAIN_ARTIFACTS_FILE = MODELS_DIR / "train_artifacts.joblib"
REGIME_COMPARISON_FILE = RESULTS_DIR / "regime_comparison.csv"
ERROR_ANALYSIS_FULL_FILE = RESULTS_DIR / "error_analysis_full.csv"
CASE_STUDIES_FILE = RESULTS_DIR / "case_studies.csv"
APP_KPIS_FILE = RESULTS_DIR / "app_kpis.json"

STREAMLIT_HOST = "localhost"
STREAMLIT_PORT = 8501

# --- Modeling contract (notebooks 05 / 06) ---
TARGET_COLUMN = "movie_success_class"
RANDOM_STATE = 42
TEST_SIZE = 0.2
FORBIDDEN_IN_X = ["revenue", "roi", "log_roi", TARGET_COLUMN]

# Registered serialized models (paths relative to repo root via Path)
MODELS = {
    "credits_logistic_regression": {
        "name": "Credits-enriched Logistic Regression",
        "description": (
            "Multinomial logistic regression on leakage-safe tabular features plus "
            "train-only talent/credits signals (director frequency, cast footprint, franchise heuristic). "
            "Aligned with notebook 05 champion."
        ),
        "path": MODELS_DIR / "credits_logistic_regression.joblib",
    },
}
