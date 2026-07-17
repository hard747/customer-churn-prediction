# Changelog

Formato baseado no [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/),
versionado segundo o [Semantic Versioning](https://semver.org/lang/pt-BR/).

Enquanto o repositório não tiver releases (`git tag`) publicados, todo o
trabalho é registrado sob `[Unreleased]`. Ao criar a primeira tag (p.
ex. `v0.1.0`), renomear esta seção para `## [0.1.0] - AAAA-MM-DD` e abrir
uma `[Unreleased]` nova e vazia acima para o próximo ciclo de mudanças.

## [Unreleased]

### Added — pipeline base
- Carga do CSV bruto para o banco de dados (`src/build_database.py`) com
  limpeza de `TotalCharges`.
- 5 consultas SQL de diagnóstico (`src/sql_queries.sql` +
  `src/run_sql_analysis.py`).
- Notebook de EDA com 10 visualizações (`notebooks/01_eda.ipynb`).
- Pipeline de treinamento com Regressão Logística, Random Forest e
  XGBoost, validação cruzada de 5 folds e busca de hiperparâmetros
  (`src/train_models.py`). Modelo vencedor: XGBoost, ROC-AUC teste = 0.845.
- Geração de `outputs/customer_risk_scores.csv` com decis de risco para
  conectar ao Power BI (`src/generate_risk_scores.py`).
- Orquestrador `src/run_all.py` para reproduzir todo o pipeline com um
  único comando.

### Added — qualidade e CI
- Suíte de 20 testes com `pytest` (`tests/`), cobrindo carga de dados,
  limpeza, pipeline de pré-processamento e risk scores.
- Lint com `ruff` (`pyproject.toml`).
- CI no GitHub Actions (`.github/workflows/ci.yml`): lint + testes em
  cada push/PR para `main`.

### Added — Postgres opcional
- `src/db.py`: camada de acesso a dados via SQLAlchemy, SQLite por
  padrão, Postgres se `DATABASE_URL` estiver definida.
- `docker-compose.yml` + `.env.example` para subir Postgres local.
- Corrigidos dois bugs de portabilidade SQLite→Postgres descobertos
  durante a migração: sensibilidade a maiúsculas em identificadores sem
  aspas, e `ROUND()` sem sobrecarga para `double precision` (ver
  [ADR-0001](docs/adr/0001-sqlite-por-defecto-postgres-opcional.md)).

### Added — impacto de negócio
- Notebook `02_business_impact.ipynb`: backtest retrospectivo que
  traduz as probabilidades de churn em valor líquido esperado em \$,
  identifica a profundidade ótima de segmentação de campanha (60% da
  base) e seu uplift frente à seleção aleatória (~\$222.040).

### Added — internacionalização e documentação
- `README.md` (português, padrão), `README.es.md` (espanhol) e
  `README.en.md` (inglês) — três versões completas do README.
- `docs/architecture.md`: diagramas C4 (contexto, containers) e fluxo de
  dados, gerados como imagens PNG reais a partir de
  `docs/diagrams/src/*.mmd`.
- `docs/adr/`: Architecture Decision Records das decisões técnicas
  principais.
- `docs/data_dictionary.md`, `docs/runbook.md`.
- Templates de GitHub Issues e Pull Requests.
- `src/db.py` carrega `.env` automaticamente (`python-dotenv`) — não é
  mais necessário exportar `DATABASE_URL` manualmente no terminal.

### Added — trilha enterprise (`warehouse_demo/`)
- Segundo pipeline paralelo que implementa o padrão real de uma empresa
  grande: `CRM/ERP (simulado) → Prefect → Postgres → dbt → Feature Table
  → Modelo → Scores` (ver [ADR-0007](docs/adr/0007-prefect-en-vez-de-airflow.md),
  [ADR-0008](docs/adr/0008-simular-crm-erp-normalizando-mismo-dataset.md)).
- `warehouse_demo/src/build_raw_tables.py`: simula a extração CRM/ERP
  normalizando o CSV original em 4 tabelas raw (`raw_crm_customers`,
  `raw_crm_subscriptions`, `raw_billing_charges`, `raw_churn_labels`).
- `warehouse_demo/dbt/churn_analytics/`: projeto dbt-postgres real
  (4 staging models + 1 mart `fct_customer_features`, 25 testes de
  qualidade de dados, todos passando).
- `warehouse_demo/src/train_from_feature_table.py`,
  `generate_risk_scores_from_feature_table.py`: reutilizam a lógica de
  `src/train_models.py` (refatorado para aceitar colunas
  parametrizadas) contra a feature table do dbt.
- `warehouse_demo/src/flow.py`: orquestração com Prefect, testada ponta
  a ponta contra Postgres real (extração → dbt run → dbt test →
  treinamento → scoring, sem erros).

### Changed — internacionalização de código
- Comentários e docstrings de todo o código-fonte (`src/`, `tests/`,
  `warehouse_demo/`, notebooks, SQL/dbt) traduzidos de espanhol para
  português. Nomes de arquivos, variáveis e funções continuam em inglês
  (convenção padrão de código, inalterada).

### Added — verificação contra Neon real (os dois pipelines)
- Pipeline simples testado end-to-end contra Postgres real na nuvem
  (Neon): base populada, 5 consultas SQL, treinamento dos 3 modelos,
  risk scores e notebook de impacto de negócio rodando sem erros contra
  a instância real.
- Pipeline enterprise (`warehouse_demo/`) também testado contra a mesma
  instância Neon: 10 tabelas/views criadas (4 raw + 4 staging + 1 mart
  + `customers`), 25/25 tests do dbt passando, flow completo do Prefect
  sem erros (ver [ADR-0009](docs/adr/0009-ci-contra-neon-real-via-secret.md)).
- Dois jobs em `.github/workflows/ci.yml`, ambos via GitHub Secret
  `NEON_DATABASE_URL` (um único secret) em todo push para `main` —
  prova contínua e verificável, não uma alegação estática:
  - `test-neon`: pipeline simples.
  - `test-neon-warehouse`: pipeline enterprise, deriva as variáveis
    `PG*` que o dbt precisa a partir da mesma URL e mascara a senha
    derivada nos logs (`::add-mask::`).
