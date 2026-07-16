"""
Orquesta el pipeline completo de cero, en orden:

1. Construir data/churn.db a partir del CSV crudo.
2. Ejecutar las consultas SQL de analisis (outputs/sql_analysis/*.csv).
3. Ejecutar el notebook de EDA (genera reports/figures/*.png).
4. Entrenar y comparar los 3 modelos (outputs/model_comparison.csv,
   reports/figures/roc_curves.png, confusion_matrices.png,
   feature_importance.png, outputs/best_model.joblib).
5. Generar outputs/customer_risk_scores.csv.

Pensado para que el proyecto completo se pueda reproducir con:
    python src/run_all.py
"""

import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = BASE_DIR / "src"
NOTEBOOK_PATH = BASE_DIR / "notebooks" / "01_eda.ipynb"


def run_step(description: str, func) -> None:
    print(f"\n{'=' * 70}\n{description}\n{'=' * 70}")
    func()


def build_database() -> None:
    from build_database import build_database as _build

    _build()


def run_sql_analysis() -> None:
    from run_sql_analysis import run_sql_analysis as _run

    _run()


def run_eda_notebook() -> None:
    import nbformat
    from nbclient import NotebookClient

    nb = nbformat.read(NOTEBOOK_PATH, as_version=4)
    client = NotebookClient(nb, timeout=600, kernel_name="python3", resources={"metadata": {"path": str(NOTEBOOK_PATH.parent)}})
    client.execute()
    nbformat.write(nb, NOTEBOOK_PATH)
    print(f"Notebook ejecutado y guardado con outputs: {NOTEBOOK_PATH}")


def train_models() -> None:
    from train_models import main as _main

    _main()


def generate_risk_scores() -> None:
    from generate_risk_scores import main as _main

    _main()


def main() -> None:
    sys.path.insert(0, str(SRC_DIR))

    run_step("1/5 - Construyendo base de datos SQLite", build_database)
    run_step("2/5 - Ejecutando consultas SQL de analisis", run_sql_analysis)
    run_step("3/5 - Ejecutando notebook de EDA", run_eda_notebook)
    run_step("4/5 - Entrenando y comparando modelos", train_models)
    run_step("5/5 - Generando risk scores de clientes", generate_risk_scores)

    print("\nPipeline completo ejecutado sin errores.")


if __name__ == "__main__":
    main()
