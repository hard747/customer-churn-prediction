"""
Orquestra o pipeline completo do zero, em ordem:

1. Construir o banco de dados a partir do CSV bruto (SQLite por
   padrao, ou Postgres se DATABASE_URL estiver definida -- ver src/db.py).
2. Executar as consultas SQL de analise (outputs/sql_analysis/*.csv).
3. Executar o notebook de EDA (gera reports/figures/*.png).
4. Treinar e comparar os 3 modelos (outputs/model_comparison.csv,
   reports/figures/roc_curves.png, confusion_matrices.png,
   feature_importance.png, outputs/best_model.joblib).
5. Gerar outputs/customer_risk_scores.csv.
6. Executar o notebook de impacto de negocio (simulacao em $,
   reports/figures/11_cumulative_gains.png e 12_campaign_net_value_by_depth.png).

Pensado para que o projeto completo possa ser reproduzido com:
    python src/run_all.py
"""

import sys
from pathlib import Path

import nbformat
from nbclient import NotebookClient

BASE_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = BASE_DIR / "src"
EDA_NOTEBOOK = BASE_DIR / "notebooks" / "01_eda.ipynb"
BUSINESS_IMPACT_NOTEBOOK = BASE_DIR / "notebooks" / "02_business_impact.ipynb"


def run_step(description: str, func) -> None:
    print(f"\n{'=' * 70}\n{description}\n{'=' * 70}")
    func()


def build_database() -> None:
    from build_database import build_database as _build

    _build()


def run_sql_analysis() -> None:
    from run_sql_analysis import run_sql_analysis as _run

    _run()


def run_notebook(notebook_path: Path) -> None:
    nb = nbformat.read(notebook_path, as_version=4)
    client = NotebookClient(
        nb, timeout=600, kernel_name="python3",
        resources={"metadata": {"path": str(notebook_path.parent)}},
    )
    client.execute()
    nbformat.write(nb, notebook_path)
    print(f"Notebook executado e salvo com outputs: {notebook_path}")


def train_models() -> None:
    from train_models import main as _main

    _main()


def generate_risk_scores() -> None:
    from generate_risk_scores import main as _main

    _main()


def main() -> None:
    sys.path.insert(0, str(SRC_DIR))

    run_step("1/6 - Construindo banco de dados", build_database)
    run_step("2/6 - Executando consultas SQL de analise", run_sql_analysis)
    run_step("3/6 - Executando notebook de EDA", lambda: run_notebook(EDA_NOTEBOOK))
    run_step("4/6 - Treinando e comparando modelos", train_models)
    run_step("5/6 - Gerando risk scores dos clientes", generate_risk_scores)
    run_step("6/6 - Executando notebook de impacto de negocio", lambda: run_notebook(BUSINESS_IMPACT_NOTEBOOK))

    print("\nPipeline completo executado sem erros.")


if __name__ == "__main__":
    main()
