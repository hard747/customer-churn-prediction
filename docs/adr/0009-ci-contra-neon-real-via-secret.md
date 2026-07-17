# ADR-0009: CI contra Neon real via GitHub Secret, escopado a push em main

**Estado:** Aceita
**Data:** 2026-07-17

## Contexto

O projeto foi verificado manualmente contra um Postgres real na nuvem
(Neon) -- primeiro o pipeline simples, depois também o pipeline
enterprise (`warehouse_demo/`, com dbt) -- mas essa verificação era um
evento pontual, não repetível nem visível para quem revisa o
repositório depois. Era preciso decidir como tornar essa prova algo
verificável de forma contínua, sem virar uma alegação estática
(captura de tela, texto no README) nem exigir infraestrutura sempre
ligada.

## Decisão

Adicionar dois jobs em `.github/workflows/ci.yml`, ambos usando a
credencial guardada como GitHub Secret (`NEON_DATABASE_URL`) e ambos
**apenas em push para `main`** (não em `pull_request`, onde secrets de
forks não estão disponíveis por padrão no GitHub Actions):

- **`test-neon`** — roda `build_database.py` + `run_sql_analysis.py` +
  `pytest` contra o Neon (pipeline simples).
- **`test-neon-warehouse`** — deriva as variáveis `PGHOST`/`PGUSER`/
  `PGPASSWORD`/`PGDATABASE` que o dbt precisa a partir da mesma
  `NEON_DATABASE_URL` (um único secret, não cinco), mascarando a senha
  derivada explicitamente nos logs (`::add-mask::`), e roda o flow
  completo de `warehouse_demo/src/flow.py` (extração → `dbt run` →
  `dbt test` → treinamento → scoring) contra o Neon.

## Alternativas consideradas

- **Postgres genérico em CI** (container efêmero do próprio GitHub
  Actions, sem usar o Neon real) — mais simples e não exige secret, mas
  prova algo mais fraco ("funciona com Postgres" em vez de "esta
  instância Neon específica funciona").
- **Pedir 5 secrets separados** (`NEON_PGHOST`, `NEON_PGUSER`, etc.)
  para o job `test-neon-warehouse` em vez de derivá-los da URL única —
  descartado: mais fricção de configuração para quem for reproduzir o
  repositório, sem benefício real (a derivação via `urlparse` é
  trivial e testada localmente antes de ir para CI).
- **Rodar em todo `pull_request`, não só push a main** — descartado:
  PRs de forks não têm acesso a secrets do repositório por padrão
  (comportamento de segurança do GitHub Actions), então os jobs
  falhariam de forma confusa em vez de degradar graciosamente. Escopar
  a `push` + `main` evita esse problema.
- **Serviço online sempre ligado batendo no Neon periodicamente** —
  descartado: contradiz [ADR-0002](0002-pipeline-batch-offline.md)
  (pipeline batch, não serviço contínuo) e adiciona custo/manutenção
  sem benefício real sobre um check de CI.

## Consequências

- Positivas: a prova de que **os dois pipelines** funcionam contra
  Neon real fica **verificável por qualquer pessoa** na aba Actions do
  GitHub, e se repete a cada push -- não é uma alegação estática que
  pode ficar desatualizada.
- Negativas / trade-offs: sem o secret configurado (forks de outras
  pessoas, ou antes de configurá-lo no repositório próprio), `test-neon`
  usa SQLite automaticamente (fallback já existente em `src/db.py`, ver
  [ADR-0001](0001-sqlite-por-defecto-postgres-opcional.md)), enquanto
  `test-neon-warehouse` simplesmente pula a execução do flow (dbt-postgres
  não funciona com SQLite) -- ou seja, o "teste contra Neon" só prova
  algo quando o secret está presente. Cada push a main também gera
  tráfego real contra o plano gratuito do Neon (baixo, mas não zero;
  `test-neon-warehouse` em particular treina 3 modelos, adicionando
  ~2-3 minutos por execução).
- Revisar se o volume de pushes crescer o suficiente para preocupar com
  os limites do plano gratuito do Neon, ou se o repositório passar a
  aceitar contribuições externas via PR (nesse caso, avaliar rodar
  esses jobs só sob aprovação manual de um mantenedor).
