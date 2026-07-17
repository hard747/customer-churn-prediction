"""
Fixtures compartilhadas. Adiciona src/ ao path para poder importar os
modulos do pipeline (build_database, train_models, etc.) da mesma
forma que run_all.py faz, sem instalar o projeto como pacote.
"""

import sys
from pathlib import Path

import pytest

BASE_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = BASE_DIR / "src"
sys.path.insert(0, str(SRC_DIR))


@pytest.fixture(scope="session")
def churn_db():
    """Constroi data/churn.db uma unica vez por sessao de testes, a
    partir do CSV bruto. As demais fixtures/testes apenas leem de la."""
    from build_database import build_database

    build_database()
    return BASE_DIR / "data" / "churn.db"
