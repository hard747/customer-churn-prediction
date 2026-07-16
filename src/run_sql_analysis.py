"""
Ejecuta las consultas de src/sql_queries.sql contra data/churn.db y
guarda cada resultado como CSV en outputs/sql_analysis/.

El parser de nombres ("-- name: <id>") evita tener las consultas SQL
duplicadas o hardcodeadas en Python: el .sql es la unica fuente de
verdad y este script solo lo interpreta y ejecuta.
"""

import re
import sqlite3
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "churn.db"
SQL_FILE = BASE_DIR / "src" / "sql_queries.sql"
OUTPUT_DIR = BASE_DIR / "outputs" / "sql_analysis"

NAME_MARKER = re.compile(r"--\s*name:\s*(\w+)")


def parse_named_queries(sql_text: str) -> dict[str, str]:
    blocks = NAME_MARKER.split(sql_text)[1:]  # descarta preambulo antes del primer marcador
    queries = {}
    for name, body in zip(blocks[0::2], blocks[1::2]):
        queries[name.strip()] = body.strip()
    return queries


def run_sql_analysis() -> dict[str, pd.DataFrame]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    sql_text = SQL_FILE.read_text(encoding="utf-8")
    queries = parse_named_queries(sql_text)

    results = {}
    with sqlite3.connect(DB_PATH) as conn:
        for name, query in queries.items():
            df = pd.read_sql_query(query, conn)
            results[name] = df
            out_path = OUTPUT_DIR / f"{name}.csv"
            df.to_csv(out_path, index=False)
            print(f"\n=== {name} ===")
            print(df.to_string(index=False))
            print(f"-> guardado en {out_path}")

    return results


if __name__ == "__main__":
    run_sql_analysis()
