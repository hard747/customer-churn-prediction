# ADR-0006: Backtest retrospectivo para estimar impacto de negócio

**Estado:** Aceita
**Data:** 2026-07-16

## Contexto

O projeto precisa responder se vale a pena, em termos de dólares,
direcionar uma campanha de retenção com o modelo. Não existe um feedback
loop real (ver limites explícitos em `docs/architecture.md`): nunca se
mediu o resultado de uma campanha real baseada neste modelo, porque o
modelo nunca foi implantado em produção.

## Decisão

Construir `notebooks/02_business_impact.ipynb` como um **backtest
retrospectivo**: usar `actual_churn` (o resultado histórico já
conhecido, presente no dataset) para simular quão efetiva teria sido uma
campanha direcionada pelo modelo, comparada com seleção aleatória na
mesma profundidade. Isso é documentado explicitamente como *offline
policy evaluation*, não como medição de impacto real, tanto no notebook
quanto no README.

## Alternativas consideradas

- **Não fazer nenhuma análise de impacto de negócio** — descartado:
  deixar as métricas só em ROC-AUC/F1 não responde à pergunta que
  realmente importa para quem decide investir na campanha ("quanto
  dinheiro se ganha ou se perde?").
- **Apresentar os números como impacto real medido** — descartado por
  ser enganoso: sem uma campanha real executada e medida, qualquer
  número em dólares é uma simulação sob suposições, não um fato. Optou-se
  por ser explícito sobre essa limitação em vez de escondê-la.
- **Modelar o problema completo como um problema de otimização de
  orçamento (linear programming, etc.)** — descartado por complexidade
  não justificada: a simulação por decis de profundidade já identifica o
  ponto ótimo com granularidade suficiente para o propósito do projeto.

## Consequências

- Positivas: o projeto demonstra pensamento de negócio (traduzir
  probabilidade em \$ esperado), não só métricas de ML, sem inflar
  artificialmente a credibilidade dos resultados.
- Negativas / trade-offs: as suposições de negócio (`CONTACT_COST`,
  `OFFER_SUCCESS_RATE`, `RETENTION_VALUE_MONTHS`) são ilustrativas, não
  dados reais de nenhuma empresa — qualquer número derivado delas deve
  ser tratado como uma demonstração de método, não como um número para
  tomar decisões de orçamento real.
- Revisar esta decisão se o projeto chegar a ser implantado e rodar uma
  campanha real: nesse ponto, substituir o backtest por uma medição real
  (idealmente com um grupo de controle) e esta ADR deveria ser marcada
  como substituída.
