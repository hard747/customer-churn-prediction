"""
Carga el CSV crudo de Telco Customer Churn a una base de datos SQLite.

Por que limpiar antes de cargar a SQLite:
- La columna TotalCharges viene como texto y tiene 11 registros con
  cadenas vacias (" ") en vez de numeros. Son clientes con tenure = 0
  (dados de alta el mismo mes, aun sin facturacion acumulada). Si se
  cargan como texto, SQLite no puede promediar/sumar esa columna en
  las consultas SQL, asi que se convierte a NUMERIC y las cadenas
  vacias pasan a NULL (no se imputan ni se eliminan filas aqui: esa
  decision de modelado se toma explicitamente en el notebook de EDA).
"""

import sqlite3
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_CSV = BASE_DIR / "data" / "Telco-Customer-Churn.csv"
DB_PATH = BASE_DIR / "data" / "churn.db"
TABLE_NAME = "customers"


def build_database(csv_path: Path = RAW_CSV, db_path: Path = DB_PATH) -> None:
    df = pd.read_csv(csv_path)

    # TotalCharges llega como object por las cadenas vacias mencionadas arriba.
    df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce")

    with sqlite3.connect(db_path) as conn:
        df.to_sql(TABLE_NAME, conn, if_exists="replace", index=False)
        conn.execute(f"CREATE INDEX IF NOT EXISTS idx_contract ON {TABLE_NAME}(Contract)")
        conn.execute(f"CREATE INDEX IF NOT EXISTS idx_churn ON {TABLE_NAME}(Churn)")

    print(f"Base de datos creada en: {db_path}")
    print(f"Filas cargadas en tabla '{TABLE_NAME}': {len(df)}")


if __name__ == "__main__":
    build_database()
