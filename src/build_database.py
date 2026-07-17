"""
Carrega o CSV bruto do Telco Customer Churn para um banco de dados.

Por padrao o banco e SQLite (data/churn.db); se DATABASE_URL apontar
para um Postgres (ver docker-compose.yml), esse motor e usado em vez
disso via src/db.py, sem mudar mais nada neste script.

Por que limpar antes de carregar no banco:
- A coluna TotalCharges vem como texto e tem 11 registros com strings
  vazias (" ") em vez de numeros. Sao clientes com tenure = 0 (dados
  de alta no mesmo mes, ainda sem faturamento acumulado). Se
  carregadas como texto, o motor nao consegue calcular media/soma
  dessa coluna nas consultas SQL, entao ela e convertida para NUMERIC
  e as strings vazias viram NULL (nao sao imputadas nem as linhas sao
  removidas aqui: essa decisao de modelagem e tomada explicitamente
  no notebook de EDA).
"""

from pathlib import Path

import pandas as pd
from sqlalchemy import text

from db import get_engine

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_CSV = BASE_DIR / "data" / "Telco-Customer-Churn.csv"
TABLE_NAME = "customers"


def build_database(csv_path: Path = RAW_CSV) -> None:
    df = pd.read_csv(csv_path)

    # TotalCharges chega como object por causa das strings vazias mencionadas acima.
    df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce")

    engine = get_engine()
    df.to_sql(TABLE_NAME, engine, if_exists="replace", index=False)
    with engine.begin() as conn:
        # Nomes de coluna entre aspas duplas: pandas.to_sql cria as
        # colunas respeitando maiusculas/minusculas (p.ex. "Contract"), e
        # o Postgres (diferente do SQLite) e sensivel a maiusculas em
        # identificadores sem aspas -- sem aspas aqui, o Postgres procura
        # "contract" em minusculo e falha com "column does not exist".
        conn.execute(text(f'CREATE INDEX IF NOT EXISTS idx_contract ON {TABLE_NAME}("Contract")'))
        conn.execute(text(f'CREATE INDEX IF NOT EXISTS idx_churn ON {TABLE_NAME}("Churn")'))

    print(f"Banco de dados criado em: {engine.url}")
    print(f"Linhas carregadas na tabela '{TABLE_NAME}': {len(df)}")


if __name__ == "__main__":
    build_database()
