"""
Treina o modelo contra fct_customer_features (a feature table que o
dbt monta), em vez da tabela `customers` crua do pipeline simples
(src/train_models.py).

Nao duplica a logica de modelagem: importa e reutiliza diretamente
build_preprocessor, get_model_grids, evaluate_model e os plots de
src/train_models.py (ja parametrizados para aceitar nomes de coluna
diferentes). A unica coisa que muda e de onde vem os dados e os nomes
de coluna (snake_case, convencao dbt, em vez do PascalCase do CSV
original -- porque a limpeza/renomeacao ja foi feita pelo dbt em
warehouse_demo/dbt/churn_analytics/models/staging/).
"""

import sys
from pathlib import Path

WAREHOUSE_DIR = Path(__file__).resolve().parent.parent
BASE_DIR = WAREHOUSE_DIR.parent
sys.path.insert(0, str(BASE_DIR / "src"))

import joblib  # noqa: E402
import pandas as pd  # noqa: E402
from sklearn.model_selection import GridSearchCV, StratifiedKFold, train_test_split  # noqa: E402

import train_models as tm  # noqa: E402
from db import get_engine  # noqa: E402

FEATURE_TABLE = "fct_customer_features"
OUTPUT_DIR = WAREHOUSE_DIR / "outputs"
FIGURES_DIR = WAREHOUSE_DIR / "reports" / "figures"
MODEL_PATH = OUTPUT_DIR / "best_model.joblib"

NUMERIC_FEATURES = ["tenure", "monthly_charges", "total_charges"]
CATEGORICAL_FEATURES = [
    "gender", "senior_citizen", "partner", "dependents", "phone_service",
    "multiple_lines", "internet_service", "online_security", "online_backup",
    "device_protection", "tech_support", "streaming_tv", "streaming_movies",
    "contract", "paperless_billing", "payment_method",
]


def load_feature_table() -> pd.DataFrame:
    engine = get_engine()
    with engine.connect() as conn:
        df = pd.read_sql_query(f"SELECT * FROM {FEATURE_TABLE}", conn)
    # A limpeza estrutural (nulos, tipos, join) ja foi feita pelo dbt.
    # A unica coisa que sobra do lado do Python e a codificacao binaria
    # do target, que e uma decisao de modelagem (nao de limpeza de dados).
    df["churn"] = df["churn"].map({"Yes": 1, "No": 0})
    return df


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    df = load_feature_table()
    feature_cols = NUMERIC_FEATURES + CATEGORICAL_FEATURES
    X = df[feature_cols]
    y = df["churn"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=tm.TEST_SIZE, stratify=y, random_state=tm.RANDOM_STATE
    )
    print(f"Feature table: {FEATURE_TABLE} | Treino: {X_train.shape[0]} | Teste: {X_test.shape[0]}")

    preprocessor = tm.build_preprocessor(NUMERIC_FEATURES, CATEGORICAL_FEATURES)
    model_grids = tm.get_model_grids(preprocessor)
    cv = StratifiedKFold(n_splits=tm.CV_FOLDS, shuffle=True, random_state=tm.RANDOM_STATE)

    fitted_models = {}
    comparison_rows = []

    for name, spec in model_grids.items():
        print(f"\nTreinando {name} (GridSearchCV, {tm.CV_FOLDS}-fold, scoring=roc_auc)...")
        search = GridSearchCV(
            spec["pipeline"], spec["param_grid"], scoring="roc_auc", cv=cv, n_jobs=-1, refit=True
        )
        search.fit(X_train, y_train)
        best_estimator = search.best_estimator_
        fitted_models[name] = best_estimator

        metrics = tm.evaluate_model(best_estimator, X_test, y_test)
        metrics["model"] = name
        metrics["best_params"] = search.best_params_
        metrics["cv_best_roc_auc"] = search.best_score_
        comparison_rows.append(metrics)
        print(f"  Teste ROC-AUC: {metrics['roc_auc']:.4f}")

    comparison_df = pd.DataFrame(comparison_rows)[
        ["model", "accuracy", "precision", "recall", "f1", "roc_auc", "cv_best_roc_auc", "best_params"]
    ].sort_values("roc_auc", ascending=False)
    comparison_df.to_csv(OUTPUT_DIR / "model_comparison.csv", index=False)
    print(f"\nTabela comparativa salva em {OUTPUT_DIR / 'model_comparison.csv'}")
    print(comparison_df.to_string(index=False))

    tm.plot_roc_curves(fitted_models, X_test, y_test, FIGURES_DIR / "roc_curves.png")
    tm.plot_confusion_matrices(fitted_models, X_test, y_test, FIGURES_DIR / "confusion_matrices.png")

    best_name = comparison_df.iloc[0]["model"]
    best_model = fitted_models[best_name]
    tm.plot_feature_importance(best_name, best_model, FIGURES_DIR / "feature_importance.png")

    joblib.dump(
        {"model": best_model, "model_name": best_name, "feature_cols": feature_cols},
        MODEL_PATH,
    )
    print(f"\nMelhor modelo: {best_name} (ROC-AUC teste = {comparison_df.iloc[0]['roc_auc']:.4f})")
    print(f"Modelo salvo em {MODEL_PATH}")


if __name__ == "__main__":
    main()
