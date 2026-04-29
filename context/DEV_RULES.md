# Development Rules

## General
- Do not modify scripts/main.py
- Respect existing project structure
- Do not rename required functions

## data.py
- Must implement load_dataset_split()
- Must return (X_train, X_test, y_train, y_test)

## metrics.py
- Must implement compute_metrics(y_true, y_pred)

## app.py
- Must implement build_app()

## Coding Style
- Keep code simple and readable
- Avoid over-engineering
- Prefer pandas + scikit-learn

## Constraints
- Models must support .predict()
- Output must be compatible with main.py
