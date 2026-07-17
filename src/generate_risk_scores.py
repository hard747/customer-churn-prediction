"""
Gera outputs/customer_risk_scores.csv: para cada cliente, sua
probabilidade de churn segundo o melhor modelo treinado e o decil de
risco correspondente (10 = maior risco, 1 = menor risco).

Nota de design: o modelo e treinado em train_models.py usando apenas os
80% de treino (para que a avaliacao em outputs/model_comparison.csv
seja honesta, sem vazamento de dados). Aqui esse mesmo modelo ja
treinado (outputs/best_model.joblib) e reutilizado para pontuar
*todos* os clientes, incluindo os que participaram do treinamento.
Isso e intencional: o objetivo deste arquivo nao e medir performance
(isso ja foi feito), e sim produzir uma lista operacional de risco
para todo o universo de clientes, pronta para priorizar acoes de
retencao no Power BI. Em um deploy produtivo real, o modelo final
seria retreinado com 100% dos dados historicos antes de pontuar a base
completa.
"""

from pathlib import Path

import joblib
import pandas as pd

from db import get_engine

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = BASE_DIR / "outputs" / "best_model.joblib"
OUTPUT_PATH = BASE_DIR / "outputs" / "customer_risk_scores.csv"


def main() -> None:
    bundle = joblib.load(MODEL_PATH)
    model = bundle["model"]
    feature_cols = bundle["feature_cols"]

    engine = get_engine()
    with engine.connect() as conn:
        df = pd.read_sql_query("SELECT * FROM customers", conn)

    df["TotalCharges"] = df["TotalCharges"].fillna(0.0)
    df["SeniorCitizen"] = df["SeniorCitizen"].map({0: "No", 1: "Yes"})

    churn_proba = model.predict_proba(df[feature_cols])[:, 1]

    result = pd.DataFrame({
        "customerID": df["customerID"],
        "churn_probability": churn_proba.round(4),
        "actual_churn": df["Churn"],
    })

    # qcut atribui decis por quantis de probabilidade: decil 10 =
    # 10% dos clientes com maior probabilidade de churn (maior risco).
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
