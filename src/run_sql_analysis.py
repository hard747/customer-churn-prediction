"""
Executa as consultas de src/sql_queries.sql contra o banco de dados
(SQLite por padrao, ou Postgres se DATABASE_URL estiver definida — ver
src/db.py) e salva cada resultado como CSV em outputs/sql_analysis/.

O parser de nomes ("-- name: <id>") evita ter as consultas SQL
duplicadas ou hardcoded em Python: o .sql e a unica fonte de verdade e
este script apenas o interpreta e executa.
"""

import re
from pathlib import Path

import pandas as pd

from db import get_engine

BASE_DIR = Path(__file__).resolve().parent.parent
SQL_FILE = BASE_DIR / "src" / "sql_queries.sql"
OUTPUT_DIR = BASE_DIR / "outputs" / "sql_analysis"

NAME_MARKER = re.compile(r"--\s*name:\s*(\w+)")


def parse_named_queries(sql_text: str) -> dict[str, str]:
    blocks = NAME_MARKER.split(sql_text)[1:]  # descarta o preambulo antes do primeiro marcador
    queries = {}
    for name, body in zip(blocks[0::2], blocks[1::2]):
        queries[name.strip()] = body.strip()
    return queries


def run_sql_analysis() -> dict[str, pd.DataFrame]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    sql_text = SQL_FILE.read_text(encoding="utf-8")
    queries = parse_named_queries(sql_text)

    results = {}
    engine = get_engine()
    with engine.connect() as conn:
        for name, query in queries.items():
            df = pd.read_sql_query(query, conn)
            results[name] = df
            out_path = OUTPUT_DIR / f"{name}.csv"
            df.to_csv(out_path, index=False)
            print(f"\n=== {name} ===")
            print(df.to_string(index=False))
            print(f"-> salvo em {out_path}")

    return results


if __name__ == "__main__":
    run_sql_analysis()
