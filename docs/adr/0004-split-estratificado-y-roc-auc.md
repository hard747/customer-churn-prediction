# ADR-0004: Split estratificado e ROC-AUC como métrica de seleção

**Estado:** Aceita
**Data:** 2026-07-16

## Contexto

O dataset tem classes desbalanceadas: ~26.5% de clientes com churn
("Yes") contra ~73.5% sem churn ("No"). Um split aleatório simples pode,
por acaso, deixar proporções diferentes de positivos em treino e teste.
Com esse desbalanceamento, `accuracy` é uma métrica enganosa: um modelo
trivial que sempre prevê "No churn" já obtém ~73.5% de accuracy sem
aprender nada.

## Decisão

1. Usar `train_test_split(..., stratify=y)` para que treino e teste
   conservem a mesma proporção de churn do dataset completo.
2. Usar `roc_auc` como métrica de `scoring` no `GridSearchCV` e como
   critério principal para escolher o melhor modelo entre os três
   candidatos, em vez de `accuracy`.

## Alternativas consideradas

- **Accuracy como métrica principal** — descartado: não distingue entre
  um modelo útil e um que só aprendeu a prever a classe majoritária.
- **Undersampling/oversampling (SMOTE, etc.)** — descartado nesta fase:
  adiciona complexidade e risco de overfitting sintético; com um
  desbalanceamento moderado (não extremo, ~1:3) os modelos usados já
  lidam razoavelmente bem com o sinal sem precisar de resampling, e o
  `class_weight="balanced"` fica disponível como hiperparâmetro
  explorado no `GridSearchCV` para `LogisticRegression`.
- **F1-score como métrica principal** — descartado como critério de
  *seleção* de modelo (continua sendo reportado junto às demais
  métricas): F1 depende de um limiar fixo (0.5), e o caso de uso real
  (`customer_risk_scores.csv`, decis de risco) precisa que o modelo
  ordene bem os clientes por risco através de *todos* os limiares, não
  que classifique bem em um único ponto de corte.

## Consequências

- Positivas: a comparação entre os 3 modelos é confiável (positivos:
  25.9%/26.5% treino/teste, praticamente idêntico ao dataset completo).
  ROC-AUC é diretamente relevante para o produto final (ranking de risco
  por decil), não apenas uma métrica acadêmica.
- Negativas / trade-offs: ROC-AUC não diz nada sobre o ponto de corte
  ótimo para decisões binárias (Yes/No) — para isso ainda seria
  necessária uma análise de limiar, listada como trabalho futuro no
  README.
- Revisar se o desbalanceamento de classes mudar substancialmente (por
  exemplo, se retreinado com dados onde o churn é <5% ou >50%): nesse
  caso reavaliar se continua sendo a métrica correta ou se convém usar
  PR-AUC.
