"""Testes da limpeza aplicada em train_models.load_and_clean_data."""

from train_models import load_and_clean_data


def test_no_null_values_after_cleaning(churn_db):
    df = load_and_clean_data()
    assert df.isna().sum().sum() == 0


def test_senior_citizen_mapped_to_yes_no(churn_db):
    df = load_and_clean_data()
    assert set(df["SeniorCitizen"].unique()) <= {"Yes", "No"}


def test_churn_target_is_binary_int(churn_db):
    df = load_and_clean_data()
    assert set(df["Churn"].unique()) == {0, 1}


def test_churn_rate_within_known_range(churn_db):
    """Guarda de sanidade: a taxa de churn conhecida do dataset e
    ~26.5%. Se isso sair da faixa, algo mudou na fonte de dados ou na
    logica de limpeza (por exemplo, um mapeamento Yes/No invertido)."""
    df = load_and_clean_data()
    churn_rate = df["Churn"].mean()
    assert 0.20 < churn_rate < 0.32


def test_row_count_preserved(churn_db):
    """A limpeza nao deve descartar linhas (os NULL de TotalCharges
    sao imputados como 0, nao removidos)."""
    df = load_and_clean_data()
    assert len(df) == 7043
