# ADR-0007: Prefect em vez de Airflow para orquestrar o padrão enterprise

**Estado:** Aceita
**Data:** 2026-07-16

## Contexto

`warehouse_demo/` adiciona uma segunda via do pipeline que replica o
padrão real de uma empresa grande: `CRM/ERP → orquestrador → warehouse →
dbt → feature table → modelo → scores`. O diagrama original que motivou
isso usa **Airflow** como orquestrador, que é o mais reconhecido da
indústria. Era preciso decidir se implementar Airflow de verdade ou uma
alternativa.

## Decisão

Usar **Prefect** para orquestrar `warehouse_demo/src/flow.py` (extração
→ `dbt run` → `dbt test` → treinamento → scoring), em vez de Airflow.

## Alternativas consideradas

- **Airflow de verdade** — descartado para este repositório: a forma
  padrão de rodá-lo localmente (`docker-compose` oficial do Apache
  Airflow) sobe ~4 containers só para o orquestrador (webserver,
  scheduler, triggerer, banco de dados próprio de metadata), com um
  consumo de RAM recomendado bem maior do que todo o resto do projeto
  junto. Para um repositório de portfólio pensado para qualquer pessoa
  clonar e rodar sem fricção, esse custo não se justificava frente ao
  Prefect, que demonstra o mesmo conceito (tarefas com dependências,
  retries, logs estruturados por passo) rodando como um único processo
  Python (`python warehouse_demo/src/flow.py`), sem infraestrutura
  adicional.
- **Sem orquestrador, só um script sequencial** (como `run_all.py`) —
  descartado especificamente para esta trilha: o objetivo de
  `warehouse_demo/` é justamente demonstrar o padrão de orquestração com
  retries e observabilidade por tarefa, não apenas executar passos em
  ordem.

## Consequências

- Positivas: `warehouse_demo/src/flow.py` roda com
  `python warehouse_demo/src/flow.py`, sem Docker adicional para o
  orquestrador (o Postgres continua via Docker/Neon, mas isso já era
  necessário para o dbt de qualquer forma). Cada tarefa
  (`extract_to_raw`, `dbt_run`, `dbt_test`, `train_model`,
  `score_customers`) tem retries e logs independentes, igual a um DAG do
  Airflow. Se `dbt_test` falhar (os dados não passam nas validações de
  qualidade), o flow para ali e não chega a treinar com dados suspeitos.
- Negativas / trade-offs: Airflow continua sendo o nome que mais
  recrutadores/entrevistadores reconhecem em comparação ao Prefect. Este
  projeto documenta explicitamente por que o Prefect foi escolhido (esta
  ADR) em vez de esconder a ausência do Airflow.
- Revisar esta decisão se o projeto precisar de agendamento real por
  cron/scheduling persistente com UI (o Prefect também suporta isso via
  Prefect Cloud/Server, mas não está configurado neste repositório —
  atualmente o flow é disparado manualmente) ou se especificamente se
  quisesse demonstrar Airflow pelo seu reconhecimento de mercado, além
  do mérito técnico da escolha.
