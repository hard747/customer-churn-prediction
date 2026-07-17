"""
Ponto unico de acesso ao banco de dados.

Por padrao usa SQLite (data/churn.db) para que o projeto continue
funcionando com configuracao zero ao clonar o repositorio. Se a
variavel de ambiente DATABASE_URL estiver definida (por exemplo,
apontando para Neon, Supabase, ou o Postgres levantado com
docker-compose.yml), essa conexao e usada em vez disso. O resto do
codigo (build_database.py, run_sql_analysis.py, train_models.py,
generate_risk_scores.py) nao precisa saber com qual motor esta
falando: sempre pede um engine com get_engine() e usa
pandas.read_sql_query/to_sql, que funcionam igual com SQLAlchemy sobre
SQLite ou sobre Postgres.

load_dotenv() le o arquivo .env (se existir) e carrega suas variaveis
no ambiente do processo -- assim basta preencher o .env (copiado de
.env.example) para que DATABASE_URL fique disponivel, sem precisar
exporta-la manualmente no terminal toda vez.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import Engine, create_engine

BASE_DIR = Path(__file__).resolve().parent.parent
SQLITE_PATH = BASE_DIR / "data" / "churn.db"

load_dotenv(BASE_DIR / ".env")


def get_engine() -> Engine:
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        return create_engine(database_url)
    return create_engine(f"sqlite:///{SQLITE_PATH}")
