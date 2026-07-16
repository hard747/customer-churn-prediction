"""
Genera outputs/customer_risk_scores.csv: para cada cliente, su
probabilidad de churn segun el mejor modelo entrenado y el decil de
riesgo correspondiente (10 = mayor riesgo, 1 = menor riesgo).

Nota de diseno: el modelo se entrena en train_models.py solo con el
80% de train (para que la evaluacion en outputs/model_comparison.csv
sea honesta, sin fuga de datos). Aqui se reutiliza ese mismo modelo
ya entrenado (outputs/best_model.joblib) para puntuar a *todos* los
clientes, incluyendo los que participaron en el entrenamiento. Esto
es intencional: el objetivo de este archivo no es medir performance
(eso ya se hizo), sino producir una lista operativa de riesgo para
todo el universo de clientes, lista para priorizar acciones de
retencion en Power BI. En un despliegue productivo real, el modelo
final se reentrenaria con el 100% de los datos historicos antes de
puntuar la base completa.
"""

import sqlite3
from pathlib import Path

import joblib
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "churn.db"
MODEL_PATH = BASE_DIR / "outputs" / "best_model.joblib"
OUTPUT_PATH = BASE_DIR / "outputs" / "customer_risk_scores.csv"


def main() -> None:
    bundle = joblib.load(MODEL_PATH)
    model = bundle["model"]
    feature_cols = bundle["feature_cols"]

    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql_query("SELECT * FROM customers", conn)

    df["TotalCharges"] = df["TotalCharges"].fillna(0.0)
    df["SeniorCitizen"] = df["SeniorCitizen"].map({0: "No", 1: "Yes"})

    churn_proba = model.predict_proba(df[feature_cols])[:, 1]

    result = pd.DataFrame({
        "customerID": df["customerID"],
        "churn_probability": churn_proba.round(4),
        "actual_churn": df["Churn"],
    })

    # qcut asigna deciles por cuantiles de probabilidad: decil 10 =
    # 10% de clientes con mayor probabilidad de churn (mayor riesgo).
    result["risk_decile"] = (
        pd.qcut(result["churn_probability"], 10, labels=False, duplicates="drop") + 1
    )

    result = result.sort_values("churn_probability", ascending=False).reset_index(drop=True)
    result.to_csv(OUTPUT_PATH, index=False)

    print(f"Modelo usado: {bundle['model_name']}")
    print(f"Scores generados para {len(result)} clientes -> {OUTPUT_PATH}")
    print(result.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
