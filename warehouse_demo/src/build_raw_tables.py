"""
Simula a camada de extracao "CRM/ERP -> Warehouse (raw)" do fluxo
enterprise real:

    CRM / ERP -> Airflow/Prefect -> Warehouse -> dbt -> Feature Table -> Modelo

Nao existe um Salesforce/SAP real para este projeto de portfolio, entao
este script simula essa fonte **normalizando o mesmo CSV de origem** em
tabelas separadas, como se viessem de sistemas diferentes:

- raw_crm_customers      -> o que um CRM exporia (perfil do cliente)
- raw_crm_subscriptions  -> o que o sistema de assinaturas/ERP exporia
- raw_billing_charges    -> o que o sistema de faturamento exporia
- raw_churn_labels       -> o sinal historico de churn

Usa-se o mesmo customerID como chave real nas quatro tabelas (nao se
inventa um join falso entre datasets nao relacionados). O dbt as
consome como "sources" e monta a feature table final em
warehouse_demo/dbt/.

Deliberadamente separado de src/build_database.py: esse script
continua sendo o pipeline simples (SQLite, configuracao zero, uma
unica tabela `customers`) que e o padrao de todo o projeto. Este e um
pipeline paralelo que demonstra o padrao de arquitetura de uma empresa
grande, pensado para rodar contra Postgres (Docker local ou Neon), nao
SQLite.
"""

import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import text

WAREHOUSE_DIR = Path(__file__).resolve().parent.parent
BASE_DIR = WAREHOUSE_DIR.parent
sys.path.insert(0, str(BASE_DIR / "src"))

from db import get_engine  # noqa: E402

RAW_CSV = BASE_DIR / "data" / "Telco-Customer-Churn.csv"

CRM_CUSTOMERS_COLS = ["customerID", "gender", "SeniorCitizen", "Partner", "Dependents"]
CRM_SUBSCRIPTIONS_COLS = [
    "customerID", "tenure", "PhoneService", "MultipleLines", "InternetService",
    "OnlineSecurity", "OnlineBackup", "DeviceProtection", "TechSupport",
    "StreamingTV", "StreamingMovies", "Contract", "PaperlessBilling",
]
BILLING_CHARGES_COLS = ["customerID", "PaymentMethod", "MonthlyCharges", "TotalCharges"]
CHURN_LABELS_COLS = ["customerID", "Churn"]


def build_raw_tables(csv_path: Path = RAW_CSV) -> None:
    df = pd.read_csv(csv_path)
    engine = get_engine()

    tables = {
        "raw_crm_customers": df[CRM_CUSTOMERS_COLS],
        "raw_crm_subscriptions": df[CRM_SUBSCRIPTIONS_COLS],
        "raw_billing_charges": df[BILLING_CHARGES_COLS],
        "raw_churn_labels": df[CHURN_LABELS_COLS],
    }

    for table_name, table_df in tables.items():
        # DROP ... CASCADE explicito antes do to_sql: em execucoes
        # posteriores a primeira, as views de staging do dbt ja
        # dependem dessas tabelas raw, e pandas.to_sql(if_exists="replace")
        # faz um DROP TABLE simples (sem CASCADE) que o Postgres rejeita
        # com "cannot drop table ... because other objects depend on it".
        # O SQLite nao tem esse problema (nao impoe dependencias entre
        # views e tabelas da mesma forma), por isso so apareceu ao
        # rodar o flow uma segunda vez contra o Postgres.
        with engine.begin() as conn:
            conn.execute(text(f'DROP TABLE IF EXISTS "{table_name}" CASCADE'))
        table_df.to_sql(table_name, engine, if_exists="replace", index=False)
        print(f"{table_name}: {len(table_df)} linhas, colunas {list(table_df.columns)}")

    print(f"\nTabelas raw criadas em: {engine.url}")
    print("Pronto para o dbt consumi-las como sources (ver warehouse_demo/dbt/).")


if __name__ == "__main__":
    build_raw_tables()
