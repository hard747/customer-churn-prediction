"""
Equivalente a src/generate_risk_scores.py, mas lendo de
fct_customer_features (dbt) e usando warehouse_demo/outputs/best_model.joblib.
"""

import sys
from pathlib import Path

WAREHOUSE_DIR = Path(__file__).resolve().parent.parent
BASE_DIR = WAREHOUSE_DIR.parent
sys.path.insert(0, str(BASE_DIR / "src"))

import joblib  # noqa: E402
import pandas as pd  # noqa: E402

from db import get_engine  # noqa: E402

FEATURE_TABLE = "fct_customer_features"
MODEL_PATH = WAREHOUSE_DIR / "outputs" / "best_model.joblib"
OUTPUT_PATH = WAREHOUSE_DIR / "outputs" / "customer_risk_scores.csv"


def main() -> None:
    bundle = joblib.load(MODEL_PATH)
    model = bundle["model"]
    feature_cols = bundle["feature_cols"]

    engine = get_engine()
    with engine.connect() as conn:
        df = pd.read_sql_query(f"SELECT * FROM {FEATURE_TABLE}", conn)

    churn_proba = model.predict_proba(df[feature_cols])[:, 1]

    result = pd.DataFrame({
        "customer_id": df["customer_id"],
        "churn_probability": churn_proba.round(4),
        "actual_churn": df["churn"],
    })
    result["risk_decile"] = (
        pd.qcut(result["churn_probability"], 10, labels=False, duplicates="drop") + 1
    )
    result = result.sort_values("churn_probability", ascending=False).reset_index(drop=True)
    result.to_csv(OUTPUT_PATH, index=False)

    print(f"Modelo usado: {bundle['model_name']}")
    print(f"Scores gerados para {len(result)} clientes -> {OUTPUT_PATH}")
    print(result.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
