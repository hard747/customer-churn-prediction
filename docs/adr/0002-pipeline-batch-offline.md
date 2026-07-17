# ADR-0002: Pipeline batch/offline, sem API em tempo real

**Estado:** Aceita
**Data:** 2026-07-16

## Contexto

O resultado final do projeto (`customer_risk_scores.csv`) alimenta um
dashboard do Power BI usado pela equipe de retenção para priorizar quem
contatar. O dataset de origem é um snapshot estático (uma foto dos
clientes em um momento dado), não um stream de eventos ao vivo.

## Decisão

Construir o sistema como um pipeline batch que roda sob demanda
(`python src/run_all.py`), sem expor um serviço HTTP nem processar
eventos em tempo real.

## Alternativas consideradas

- **API REST (FastAPI) servindo predições ao vivo** — descartado nesta
  fase: o caso de uso real (scoring semanal/mensal para um dashboard de
  BI) não exige baixa latência por cliente individual, e adicionar um
  serviço exposto implica autenticação, versionamento de API e
  disponibilidade — complexidade não justificada pelo problema atual.
  Fica listado no README como trabalho futuro caso o caso de uso mude
  (p. ex., mostrar o risco de churn em tempo real quando um agente de
  suporte atende um cliente).
- **Processamento de eventos em streaming (Kafka, etc.)** — descartado:
  não há uma fonte de eventos em tempo real neste problema; o dataset é
  um snapshot.

## Consequências

- Positivas: arquitetura muito mais simples, sem necessidade de
  gerenciar disponibilidade, autenticação nem escalonamento horizontal.
  O batch scoring é, além disso, o padrão real que muitas empresas usam
  para churn (não é uma simplificação irreal do problema).
- Negativas / trade-offs: não há forma de consultar o risco de um
  cliente "na hora" fora de rodar o pipeline completo; o arquivo de
  scores fica desatualizado até a próxima execução manual/agendada.
- Revisar esta decisão se surgir um caso de uso que precise do risco de
  churn no momento exato de uma interação com o cliente (p. ex., um
  agente de call center vendo o risco na tela enquanto atende a
  ligação).
