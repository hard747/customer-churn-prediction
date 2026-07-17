"""
Testes de generate_risk_scores.py.

Dependem de outputs/best_model.joblib, que esta versionado no
repositorio (nao e retreinado em cada execucao de CI: treinar os 3
modelos com GridSearchCV leva minutos e nao agrega nada para verificar
se o *scoring* esta bem implementado). Se esse arquivo nao existir --
por exemplo, em um clone superficial antes de rodar
train_models.py -- os testes sao pulados em vez de falhar.
"""

from pathlib import Path

import pandas as pd
import pytest

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = BASE_DIR / "outputs" / "best_model.joblib"

pytestmark = pytest.mark.skipif(
    not MODEL_PATH.exists(),
    reason="outputs/best_model.joblib nao existe (rodar src/train_models.py primeiro)",
)


@pytest.fixture(scope="module")
def risk_scores_df(churn_db):
    from generate_risk_scores import main

    main()
    return pd.read_csv(BASE_DIR / "outputs" / "customer_risk_scores.csv")


def test_all_customers_scored(risk_scores_df):
    assert len(risk_scores_df) == 7043


def test_customer_id_is_unique(risk_scores_df):
    assert risk_scores_df["customerID"].is_unique


def test_churn_probability_in_valid_range(risk_scores_df):
    assert risk_scores_df["churn_probability"].between(0, 1).all()


def test_risk_decile_in_valid_range(risk_scores_df):
    assert risk_scores_df["risk_decile"].between(1, 10).all()
    assert set(risk_scores_df["risk_decile"].unique()) == set(range(1, 11))


def test_higher_decile_means_higher_average_probability(risk_scores_df):
    """Sanity check da logica de decis: o decil 10 deve ter, em media,
    maior probabilidade de churn do que o decil 1."""
    avg_by_decile = risk_scores_df.groupby("risk_decile")["churn_probability"].mean()
    assert avg_by_decile[10] > avg_by_decile[1]
