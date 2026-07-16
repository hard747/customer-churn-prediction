"""
Entrena y compara 3 modelos de clasificacion para predecir churn de
clientes: Regresion Logistica, Random Forest y XGBoost.

Decisiones clave (documentadas aqui para que queden junto al codigo
que las implementa; tambien se resumen en el README):

1. Split estratificado (train_test_split(..., stratify=y)):
   el churn esta desbalanceado (~26.5% Yes / 73.5% No). Un split
   aleatorio simple puede, por azar, dejar una proporcion distinta
   de positivos en train y en test, lo que sesga tanto el
   entrenamiento como la evaluacion. Estratificar por `y` garantiza
   que train y test conserven la misma proporcion de churn que el
   dataset completo, haciendo la comparacion de metricas confiable.

2. ROC-AUC como metrica principal de seleccion (scoring en
   GridSearchCV y CV):
   con clases desbalanceadas, accuracy es enganosa: un modelo que
   siempre predice "No churn" ya obtiene ~73.5% de accuracy sin
   aprender nada util. ROC-AUC mide la capacidad del modelo para
   *ordenar* clientes por riesgo (probabilidad de churn) a traves de
   todos los umbrales posibles, independientemente del balance de
   clases, lo que la hace mas robusta aqui y ademas es la metrica
   relevante para el caso de uso real: priorizar una lista de
   clientes en riesgo (deciles), no solo clasificar Yes/No con un
   umbral fijo de 0.5.

3. Pipeline (ColumnTransformer + modelo) en vez de preprocesar por
   separado: evita fugas de informacion (el scaler/encoder se ajusta
   solo con datos de entrenamiento dentro de cada fold de CV) y hace
   que el mismo objeto se pueda usar despues para inferencia sobre
   datos nuevos sin repetir el preprocesamiento a mano.

4. Busqueda de hiperparametros "ligera" (grids pequenos, 5-fold CV):
   el objetivo es mostrar el flujo completo (CV + tuning) sin
   incurrir en tiempos de ejecucion largos, adecuado para un
   proyecto de portafolio que debe poder re-ejecutarse rapido.
"""

from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    RocCurveDisplay,
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import GridSearchCV, StratifiedKFold, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from xgboost import XGBClassifier

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "churn.db"
OUTPUT_DIR = BASE_DIR / "outputs"
FIGURES_DIR = BASE_DIR / "reports" / "figures"
MODEL_PATH = OUTPUT_DIR / "best_model.joblib"

RANDOM_STATE = 42
TEST_SIZE = 0.20
CV_FOLDS = 5

NUMERIC_FEATURES = ["tenure", "MonthlyCharges", "TotalCharges"]
CATEGORICAL_FEATURES = [
    "gender", "SeniorCitizen", "Partner", "Dependents", "PhoneService",
    "MultipleLines", "InternetService", "OnlineSecurity", "OnlineBackup",
    "DeviceProtection", "TechSupport", "StreamingTV", "StreamingMovies",
    "Contract", "PaperlessBilling", "PaymentMethod",
]


def load_and_clean_data() -> pd.DataFrame:
    import sqlite3

    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql_query("SELECT * FROM customers", conn)

    # Los 11 clientes con TotalCharges nulo tienen tenure = 0 (recien
    # dados de alta, sin facturacion acumulada todavia) -> 0 es el
    # valor logico, no una imputacion estadistica arbitraria.
    df["TotalCharges"] = df["TotalCharges"].fillna(0.0)

    # SeniorCitizen viene como 0/1 pero es semanticamente una bandera
    # categorica (igual que Partner/Dependents); se homogeniza a
    # Yes/No para que el OneHotEncoder la trate de forma consistente
    # con el resto de columnas binarias.
    df["SeniorCitizen"] = df["SeniorCitizen"].map({0: "No", 1: "Yes"})

    df["Churn"] = df["Churn"].map({"Yes": 1, "No": 0})
    return df


def build_preprocessor() -> ColumnTransformer:
    return ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), NUMERIC_FEATURES),
            ("cat", OneHotEncoder(handle_unknown="ignore", drop="if_binary"), CATEGORICAL_FEATURES),
        ]
    )


def get_model_grids(preprocessor: ColumnTransformer) -> dict:
    """Devuelve, por modelo, el Pipeline base y un grid de hiperparametros
    pequeno (busqueda "ligera" segun se explica en el docstring del modulo)."""
    return {
        "LogisticRegression": {
            "pipeline": Pipeline([
                ("preprocessor", preprocessor),
                ("classifier", LogisticRegression(max_iter=2000, random_state=RANDOM_STATE)),
            ]),
            "param_grid": {
                "classifier__C": [0.01, 0.1, 1, 10],
                "classifier__class_weight": [None, "balanced"],
            },
        },
        "RandomForest": {
            "pipeline": Pipeline([
                ("preprocessor", preprocessor),
                ("classifier", RandomForestClassifier(random_state=RANDOM_STATE, n_jobs=-1)),
            ]),
            "param_grid": {
                "classifier__n_estimators": [200, 400],
                "classifier__max_depth": [6, 10, None],
                "classifier__min_samples_leaf": [1, 2],
            },
        },
        "XGBoost": {
            "pipeline": Pipeline([
                ("preprocessor", preprocessor),
                ("classifier", XGBClassifier(
                    random_state=RANDOM_STATE, eval_metric="logloss", n_jobs=-1
                )),
            ]),
            "param_grid": {
                "classifier__n_estimators": [200, 400],
                "classifier__max_depth": [3, 5],
                "classifier__learning_rate": [0.05, 0.1],
            },
        },
    }


def evaluate_model(model, X_test, y_test) -> dict:
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]
    return {
        "accuracy": accuracy_score(y_test, y_pred),
        "precision": precision_score(y_test, y_pred),
        "recall": recall_score(y_test, y_pred),
        "f1": f1_score(y_test, y_pred),
        "roc_auc": roc_auc_score(y_test, y_proba),
    }


def plot_roc_curves(fitted_models: dict, X_test, y_test, out_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(7, 6))
    for name, model in fitted_models.items():
        RocCurveDisplay.from_estimator(model, X_test, y_test, ax=ax, name=name)
    ax.plot([0, 1], [0, 1], linestyle="--", color="gray", label="Azar (AUC = 0.50)")
    ax.set_title("Curvas ROC - Comparacion de modelos")
    ax.legend(loc="lower right")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_confusion_matrices(fitted_models: dict, X_test, y_test, out_path: Path) -> None:
    fig, axes = plt.subplots(1, len(fitted_models), figsize=(5 * len(fitted_models), 4.5))
    for ax, (name, model) in zip(axes, fitted_models.items()):
        cm = confusion_matrix(y_test, model.predict(X_test))
        ConfusionMatrixDisplay(cm, display_labels=["No churn", "Churn"]).plot(
            ax=ax, colorbar=False, cmap="Blues"
        )
        ax.set_title(name)
    fig.suptitle("Matrices de confusion (umbral = 0.5)")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_feature_importance(best_name: str, best_model: Pipeline, out_path: Path) -> None:
    preprocessor = best_model.named_steps["preprocessor"]
    feature_names = preprocessor.get_feature_names_out()
    classifier = best_model.named_steps["classifier"]

    if hasattr(classifier, "feature_importances_"):
        importances = classifier.feature_importances_
        xlabel = "Importancia (impureza / ganancia)"
    elif hasattr(classifier, "coef_"):
        importances = np.abs(classifier.coef_[0])
        xlabel = "Importancia (|coeficiente|)"
    else:
        return

    importance_df = (
        pd.DataFrame({"feature": feature_names, "importance": importances})
        .sort_values("importance", ascending=False)
        .head(15)
    )

    fig, ax = plt.subplots(figsize=(8, 7))
    sns.barplot(data=importance_df, x="importance", y="feature", ax=ax, color="#3b6fa0")
    ax.set_title(f"Top 15 variables mas importantes - {best_name}")
    ax.set_xlabel(xlabel)
    ax.set_ylabel("")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    df = load_and_clean_data()
    feature_cols = NUMERIC_FEATURES + CATEGORICAL_FEATURES
    X = df[feature_cols]
    y = df["Churn"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, stratify=y, random_state=RANDOM_STATE
    )
    print(f"Train: {X_train.shape[0]} filas | Test: {X_test.shape[0]} filas")
    print(f"Tasa de churn train: {y_train.mean():.3f} | test: {y_test.mean():.3f}")

    preprocessor = build_preprocessor()
    model_grids = get_model_grids(preprocessor)
    cv = StratifiedKFold(n_splits=CV_FOLDS, shuffle=True, random_state=RANDOM_STATE)

    fitted_models = {}
    comparison_rows = []

    for name, spec in model_grids.items():
        print(f"\nEntrenando {name} (GridSearchCV, {CV_FOLDS}-fold, scoring=roc_auc)...")
        search = GridSearchCV(
            spec["pipeline"],
            spec["param_grid"],
            scoring="roc_auc",
            cv=cv,
            n_jobs=-1,
            refit=True,
        )
        search.fit(X_train, y_train)
        best_estimator = search.best_estimator_
        fitted_models[name] = best_estimator

        metrics = evaluate_model(best_estimator, X_test, y_test)
        metrics["model"] = name
        metrics["best_params"] = search.best_params_
        metrics["cv_best_roc_auc"] = search.best_score_
        comparison_rows.append(metrics)

        print(f"  Mejor CV ROC-AUC: {search.best_score_:.4f} | params: {search.best_params_}")
        print(f"  Test -> " + " | ".join(f"{k}: {v:.4f}" for k, v in metrics.items() if k not in ("model", "best_params", "cv_best_roc_auc")))

    comparison_df = pd.DataFrame(comparison_rows)[
        ["model", "accuracy", "precision", "recall", "f1", "roc_auc", "cv_best_roc_auc", "best_params"]
    ].sort_values("roc_auc", ascending=False)
    comparison_path = OUTPUT_DIR / "model_comparison.csv"
    comparison_df.to_csv(comparison_path, index=False)
    print(f"\nTabla comparativa guardada en {comparison_path}")
    print(comparison_df.to_string(index=False))

    plot_roc_curves(fitted_models, X_test, y_test, FIGURES_DIR / "roc_curves.png")
    plot_confusion_matrices(fitted_models, X_test, y_test, FIGURES_DIR / "confusion_matrices.png")

    best_name = comparison_df.iloc[0]["model"]
    best_model = fitted_models[best_name]
    plot_feature_importance(best_name, best_model, FIGURES_DIR / "feature_importance.png")

    joblib.dump({"model": best_model, "model_name": best_name, "feature_cols": feature_cols}, MODEL_PATH)
    print(f"\nMejor modelo: {best_name} (ROC-AUC test = {comparison_df.iloc[0]['roc_auc']:.4f})")
    print(f"Modelo guardado en {MODEL_PATH}")


if __name__ == "__main__":
    main()
