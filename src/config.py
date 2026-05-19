from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
SRC_DIR = PROJECT_ROOT / "src"
DATA_DIR = PROJECT_ROOT / "data"
DATA_RAW_DIR = DATA_DIR / "raw"
DATA_PROCESSED_DIR = DATA_DIR / "processed"
APP_DIR = PROJECT_ROOT / "app"
LOGS_DIR = PROJECT_ROOT / "logs"
MODELS_DIR = PROJECT_ROOT / "models"
NOTEBOOKS_DIR = PROJECT_ROOT / "notebooks"
PLOTS_DIR = PROJECT_ROOT / "plots"
RESULTS_DIR = PROJECT_ROOT / "results"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
TESTS_DIR = PROJECT_ROOT / "tests"

# Expected local TMDB files (place under ``data/raw/``; not committed by default).
TMDB_MOVIES_CSV = DATA_RAW_DIR / "tmdb_5000_movies.csv"
TMDB_CREDITS_CSV = DATA_RAW_DIR / "tmdb_5000_credits.csv"

for dir in [
    DATA_DIR,
    DATA_RAW_DIR,
    DATA_PROCESSED_DIR,
    APP_DIR,
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

STREAMLIT_HOST = "localhost"
STREAMLIT_PORT = 8501

# Replace with trained models after the modeling phase.
MODELS = {
    "model_a": {
        "name": "Model A",
        "description": "Baseline placeholder until models are trained.",
        "path": MODELS_DIR / "model_a.pkl",
    },
}
