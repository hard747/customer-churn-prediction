# Architecture Decision Records (ADR)

Registro de decisões técnicas significativas, com seu contexto e
consequências — formato padrão da indústria (Michael Nygard,
["Documenting Architecture Decisions"](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)).

Uma ADR não documenta *o que* o código faz (isso está no código e no
README), mas sim *por que* se escolheu um caminho entre vários possíveis,
em um momento dado, com a informação disponível naquele momento. Uma
decisão pode ficar obsoleta — nesse caso se adiciona uma ADR nova
marcada como `Supersedes ADR-000X`, nunca se apaga ou reescreve uma ADR
antiga.

## Índice

| ADR | Título | Estado |
|---|---|---|
| [0001](0001-sqlite-por-defecto-postgres-opcional.md) | SQLite por padrão, Postgres opcional via SQLAlchemy | Aceita |
| [0002](0002-pipeline-batch-offline.md) | Pipeline batch/offline, sem API em tempo real | Aceita |
| [0003](0003-separar-scripts-de-notebooks.md) | Separar lógica reproduzível (scripts) de exploração (notebooks) | Aceita |
| [0004](0004-split-estratificado-y-roc-auc.md) | Split estratificado e ROC-AUC como métrica de seleção | Aceita |
| [0005](0005-serializar-pipeline-sin-servicio-de-inferencia.md) | Serializar o Pipeline treinado em vez de expor um serviço de inferência | Aceita |
| [0006](0006-backtest-retrospectivo-impacto-negocio.md) | Backtest retrospectivo para estimar impacto de negócio | Aceita |
| [0007](0007-prefect-en-vez-de-airflow.md) | Prefect em vez de Airflow para orquestrar o padrão enterprise | Aceita |
| [0008](0008-simular-crm-erp-normalizando-mismo-dataset.md) | Simular CRM/ERP normalizando o mesmo dataset, em vez de somar um novo | Aceita |
| [0009](0009-ci-contra-neon-real-via-secret.md) | CI contra Neon real via GitHub Secret, escopado a push em main | Aceita |

## Como adicionar uma ADR nova

1. Copiar [`template.md`](template.md) para `000N-titulo-curto-em-kebab-case.md`.
2. Preencher Contexto, Decisão e Consequências.
3. Adicionar a linha correspondente na tabela acima.
4. Se substituir uma ADR anterior, anotar em ambas (`Supersedes` /
   `Superseded by`).
