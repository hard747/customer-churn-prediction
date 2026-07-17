"""
Testes do ColumnTransformer e um smoke test de treinamento.

O smoke test treina UM modelo simples (LogisticRegression, sem
GridSearchCV) para verificar que o Pipeline completo nao quebra, sem
pagar o custo da busca de hiperparametros completa de
train_models.main() em cada execucao de CI.
"""

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from train_models import (
    CATEGORICAL_FEATURES,
    NUMERIC_FEATURES,
    build_preprocessor,
    load_and_clean_data,
)


def _features(df):
    return df[NUMERIC_FEATURES + CATEGORICAL_FEATURES]


def test_preprocessor_output_has_no_nan(churn_db):
    df = load_and_clean_data()
    X = _features(df)
    transformed = build_preprocessor().fit_transform(X)
    dense = transformed.toarray() if hasattr(transformed, "toarray") else transformed
    assert not np.isnan(dense).any()


def test_preprocessor_expands_categoricals_via_onehot(churn_db):
    df = load_and_clean_data()
    X = _features(df)
    preprocessor = build_preprocessor()
    preprocessor.fit(X)
    feature_names = preprocessor.get_feature_names_out()
    # OneHotEncoder deve gerar mais colunas de saida do que colunas
    # categoricas de entrada (cada categoria com >2 niveis se expande).
    assert len(feature_names) > len(NUMERIC_FEATURES) + len(CATEGORICAL_FEATURES)


def test_smoke_pipeline_fit_predict(churn_db):
    df = load_and_clean_data()
    X = _features(df)
    y = df["Churn"]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )

    pipeline = Pipeline([
        ("preprocessor", build_preprocessor()),
        ("classifier", LogisticRegression(max_iter=1000, random_state=42)),
    ])
    pipeline.fit(X_train, y_train)
    proba = pipeline.predict_proba(X_test)[:, 1]

    assert ((proba >= 0) & (proba <= 1)).all()
    assert len(proba) == len(y_test)


def test_stratified_split_preserves_churn_ratio(churn_db):
    """O split estratificado deve conservar a proporcao de churn do
    dataset completo (tolerancia de 2 pontos percentuais)."""
    df = load_and_clean_data()
    X = _features(df)
    y = df["Churn"]
    _, _, y_train, y_test = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)

    overall_rate = y.mean()
    assert abs(y_train.mean() - overall_rate) < 0.02
    assert abs(y_test.mean() - overall_rate) < 0.02
