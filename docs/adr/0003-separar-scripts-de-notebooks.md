# ADR-0003: Separar lógica reproduzível (scripts) de exploração (notebooks)

**Estado:** Aceita
**Data:** 2026-07-16

## Contexto

O projeto precisa tanto de exploração visual/narrativa (EDA, impacto de
negócio) quanto de lógica que precisa rodar de forma confiável, repetível
e testável (carga de dados, treinamento, scoring). Misturar as duas
coisas em notebooks é um antipadrão conhecido: o estado de um notebook
depende da ordem em que as células foram executadas, é difícil de
testar com `pytest`, e complica o diff no controle de versão.

## Decisão

Toda a lógica que precisa ser reproduzível, testável ou reutilizável vive
em `src/*.py` (funções puras/orquestráveis, importáveis a partir de
`tests/`). Os notebooks (`notebooks/01_eda.ipynb`, `02_business_impact.ipynb`)
apenas consomem essas funções ou leem os artefatos que elas produzem —
ficam limitados a exploração, visualização e narrativa para humanos.

## Alternativas consideradas

- **Tudo em notebooks** — descartado: impossível de testar com `pytest`
  de forma confiável, e `run_all.py` não poderia orquestrar o pipeline
  completo com um único comando sem executar notebooks inteiros para
  cada passo intermediário.
- **Tudo em scripts, sem notebooks** — descartado: perde-se o valor da
  narrativa visual passo a passo que um notebook comunica melhor que um
  script para EDA e para explicar o raciocínio de negócio.

## Consequências

- Positivas: `tests/` pode importar e testar `build_database`,
  `load_and_clean_data`, `build_preprocessor`, etc. sem executar nenhum
  notebook. Os notebooks ficam curtos e legíveis porque não reimplementam
  lógica, apenas a usam.
- Negativas / trade-offs: qualquer mudança na lógica de limpeza ou
  scoring precisa ser feita em `src/`, não diretamente no notebook — um
  pouco mais de fricção para experimentação rápida e exploratória.
- Revisar se um notebook começar a definir funções não triviais que se
  repetem entre células: é um sinal de que essa lógica deveria ser
  movida para `src/`.
