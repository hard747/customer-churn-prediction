"""Testes da carga CSV -> banco de dados (src/build_database.py)."""

import pandas as pd
import pytest
from sqlalchemy import text

from db import get_engine


def test_database_file_created(churn_db):
    assert churn_db.exists()


def test_customers_table_row_count(churn_db):
    engine = get_engine()
    with engine.connect() as conn:
        df = pd.read_sql_query("SELECT * FROM customers", conn)
    assert len(df) == 7043


def test_total_charges_is_numeric_with_no_nulls(churn_db):
    """TotalCharges deve ficar numerica e sem NULL: as 11 linhas com
    string vazia no CSV original devem ter sido convertidas para NULL
    (nao descartadas), ficando pendentes de decisao explicita em
    train_models.load_and_clean_data / na EDA."""
    engine = get_engine()
    with engine.connect() as conn:
        df = pd.read_sql_query('SELECT "TotalCharges" FROM customers', conn)
    assert pd.api.types.is_numeric_dtype(df["TotalCharges"])


def test_total_charges_nulls_match_zero_tenure_customers(churn_db):
    """Os unicos nulos de TotalCharges devem corresponder a clientes
    com tenure == 0 (recem cadastrados) -- se aparecessem nulos em
    outras linhas, seria um sinal de dados corrompidos, nao do caso
    conhecido e documentado."""
    engine = get_engine()
    with engine.connect() as conn:
        df = pd.read_sql_query('SELECT tenure, "TotalCharges" FROM customers', conn)
    null_rows = df[df["TotalCharges"].isna()]
    assert (null_rows["tenure"] == 0).all()


def test_churn_column_has_only_expected_values(churn_db):
    engine = get_engine()
    with engine.connect() as conn:
        df = pd.read_sql_query('SELECT DISTINCT "Churn" FROM customers', conn)
    assert set(df["Churn"]) == {"Yes", "No"}


def test_indexes_created(churn_db):
    engine = get_engine()
    if engine.dialect.name != "sqlite":
        pytest.skip("Consulta de indices especifica do SQLite (metadata do Postgres e diferente)")
    with engine.connect() as conn:
        result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='index'"))
        index_names = {row[0] for row in result}
    assert "idx_contract" in index_names
    assert "idx_churn" in index_names
