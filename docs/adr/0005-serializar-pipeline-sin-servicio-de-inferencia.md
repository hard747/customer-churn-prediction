# ADR-0005: Serializar o Pipeline treinado em vez de expor um serviço de inferência

**Estado:** Aceita
**Data:** 2026-07-16

## Contexto

Consistente com a [ADR-0002](0002-pipeline-batch-offline.md) (pipeline
batch, não tempo real), o modelo treinado precisa ser reutilizado em
dois lugares: `generate_risk_scores.py` (scoring de toda a base) e
potencialmente em execuções futuras sem retreinar. É necessária uma
forma de persistir não só os pesos do modelo, mas também o
pré-processamento (`ColumnTransformer`) que o acompanha, para evitar
"train/serve skew" (o pré-processamento na inferência divergir do usado
no treinamento).

## Decisão

Serializar com `joblib` o `Pipeline` completo do scikit-learn
(pré-processamento + classificador) como um único objeto em
`outputs/best_model.joblib`, junto com metadados (`model_name`,
`feature_cols`). `generate_risk_scores.py` carrega esse arquivo e chama
diretamente `.predict_proba()` sobre dados brutos.

## Alternativas consideradas

- **Salvar o modelo e o pré-processador separadamente** — descartado:
  duplica a responsabilidade de mantê-los sincronizados; com `Pipeline`,
  o sklearn já garante que viajam juntos.
- **Expor um serviço de inferência (FastAPI + endpoint `/predict`)** —
  descartado nesta fase pelo mesmo motivo da
  [ADR-0002](0002-pipeline-batch-offline.md): não há um consumidor que
  precise de predições síncronas por request; o consumidor é um CSV para
  um dashboard de BI.
- **Formato ONNX / PMML para portabilidade entre linguagens** —
  descartado: adiciona complexidade sem necessidade real, já que tanto o
  treinamento quanto o consumo do modelo acontecem no mesmo ambiente
  Python.

## Consequências

- Positivas: um único arquivo versionado no repositório
  (`outputs/best_model.joblib`, ~240 KB) é suficiente para reproduzir o
  scoring sem retreinar — isso, além disso, é o que permite que os
  testes de CI (`tests/test_risk_scores.py`) rodem em segundos em vez de
  minutos.
- Negativas / trade-offs: `joblib.load()` de um pipeline do scikit-learn
  não é seguro de carregar se o arquivo vier de uma fonte não confiável
  (deserialização arbitrária de Python) — aceitável aqui porque o
  arquivo é gerado e versionado pelo próprio repositório, não recebido de
  terceiros. Também não há versionamento do esquema do modelo: se
  `feature_cols` mudar, um `best_model.joblib` antigo poderia falhar
  silenciosamente contra um `churn.db` com colunas diferentes.
- Revisar esta decisão se for necessário servir predições a um sistema
  externo em tempo real, ou se o modelo precisar ser consumido a partir
  de uma linguagem diferente de Python.
