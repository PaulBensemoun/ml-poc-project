"""Helpers for saving and loading serialized models."""

from __future__ import annotations

import pickle
from pathlib import Path
from typing import Any


def save_model(model: Any, path: str | Path) -> Path:
    """Serialize ``model`` to ``path`` (creates parent directories). Uses joblib for ``.joblib``."""

    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    suffix = out.suffix.lower()
    if suffix == ".joblib":
        import joblib

        joblib.dump(model, out)
        return out
    if suffix in {".pkl", ".pickle"}:
        with out.open("wb") as fh:
            pickle.dump(model, fh)
        return out
    raise ValueError(f"save_model: unsupported suffix for {out} (use .joblib, .pkl, or .pickle)")


def load_model(model_path: Path | str) -> Any:
    """Load a serialized model from disk.

    Supported formats are ``.joblib``, ``.pkl``, and ``.pickle``.
    """

    model_path = Path(model_path)
    if not model_path.exists():
        raise FileNotFoundError(f"Model file does not exist: {model_path}")

    suffix = model_path.suffix.lower()

    if suffix == ".joblib":
        try:
            import joblib
        except ImportError as exc:
            raise ImportError(
                "Loading `.joblib` files requires the `joblib` package. "
                "Add it to requirements.txt if needed."
            ) from exc

        return joblib.load(model_path)

    if suffix in {".pkl", ".pickle"}:
        with model_path.open("rb") as file_handle:
            return pickle.load(file_handle)

    raise ValueError(
        f"Unsupported model format for {model_path}. Use .joblib, .pkl, or .pickle."
    )
