"""
Flow do Prefect que orquestra o padrao enterprise completo:

    CRM/ERP (simulado) -> raw tables -> dbt run -> dbt test -> modelo -> scores

Equivalente em conceito a um DAG do Airflow (tarefas com dependencias,
retries, logs por passo), mas com Prefect: um unico processo Python,
sem precisar subir um scheduler + webserver + banco de dados proprio
como o Airflow exige (ver ADR-0007 sobre essa escolha).

Exige Postgres (Docker local ou Neon/Supabase) -- nao roda contra
SQLite, porque o dbt-postgres precisa de um servidor Postgres real. Ver
warehouse_demo/README.md para saber como configurar.

Uso:
    python warehouse_demo/src/flow.py
"""

import subprocess
import sys
from pathlib import Path

WAREHOUSE_DIR = Path(__file__).resolve().parent.parent
BASE_DIR = WAREHOUSE_DIR.parent
DBT_PROJECT_DIR = WAREHOUSE_DIR / "dbt" / "churn_analytics"

sys.path.insert(0, str(BASE_DIR / "src"))
sys.path.insert(0, str(WAREHOUSE_DIR / "src"))

from prefect import flow, task  # noqa: E402

# Resolve o executavel do dbt em relacao ao mesmo interpretador que
# esta rodando este flow (funciona sem depender do venv estar
# "ativado" no shell, que e justamente o cenario quando o Prefect
# lanca isso como processo filho).
_DBT_EXE = Path(sys.executable).parent / ("dbt.exe" if sys.platform == "win32" else "dbt")


def _run_dbt(command: str) -> None:
    result = subprocess.run(
        [str(_DBT_EXE), command, "--project-dir", str(DBT_PROJECT_DIR), "--profiles-dir", str(DBT_PROJECT_DIR)],
        capture_output=True,
        text=True,
    )
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr)
        raise RuntimeError(f"dbt {command} falhou (exit code {result.returncode})")


@task(name="extract-to-raw", retries=2, retry_delay_seconds=5, log_prints=True)
def extract_to_raw() -> None:
    """Simula a extracao CRM/ERP -> camada raw do warehouse."""
    from build_raw_tables import build_raw_tables

    build_raw_tables()


@task(name="dbt-run", log_prints=True)
def dbt_run() -> None:
    _run_dbt("run")


@task(name="dbt-test", log_prints=True)
def dbt_test() -> None:
    """Se os dados nao passarem nos testes de qualidade do dbt, o
    flow inteiro falha aqui e nao chega a treinar/pontuar com dados
    suspeitos."""
    _run_dbt("test")


@task(name="train-model", log_prints=True)
def train_model() -> None:
    from train_from_feature_table import main as train_main

    train_main()


@task(name="score-customers", log_prints=True)
def score_customers() -> None:
    from generate_risk_scores_from_feature_table import main as score_main

    score_main()


@flow(name="churn-enterprise-pipeline", log_prints=True)
def churn_enterprise_pipeline() -> None:
    extract_to_raw()
    dbt_run()
    dbt_test()
    train_model()
    score_customers()
    print("Pipeline enterprise completo executado sem erros.")


if __name__ == "__main__":
    churn_enterprise_pipeline()
