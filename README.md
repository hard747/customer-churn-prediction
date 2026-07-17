🇧🇷 Português (atual) · [🇪🇸 Español](README.es.md) · [🇬🇧 English](README.en.md)

# Predição de Churn de Clientes — Telco Customer Churn

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-1.4-F7931E?logo=scikitlearn&logoColor=white)
![XGBoost](https://img.shields.io/badge/XGBoost-2.0-1C6EA4)
![SQLite](https://img.shields.io/badge/SQLite-3-003B57?logo=sqlite&logoColor=white)
![Postgres opcional](https://img.shields.io/badge/Postgres-opcional-336791?logo=postgresql&logoColor=white)
![CI](https://github.com/hard747/customer-churn-prediction/actions/workflows/ci.yml/badge.svg)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-completo-brightgreen)

Projeto end-to-end de análise e predição de fuga de clientes (*churn*)
usando o dataset público **Telco Customer Churn** da IBM. Cobre o fluxo
completo de um projeto de Data Science aplicado a negócios: consultas SQL
de diagnóstico, análise exploratória com visualizações, treinamento e
comparação de modelos de classificação, simulação de impacto de negócio
em \$, e um arquivo de *risk scores* pronto para conectar a um dashboard
do Power BI. Inclui testes automatizados, CI no GitHub Actions e suporte
opcional para Postgres via Docker.

## Sumário

- [Objetivo de negócio](#objetivo-de-negócio)
- [Dataset](#dataset)
- [Estrutura do repositório](#estrutura-do-repositório)
- [Documentação técnica](#documentação-técnica)
- [Como reproduzir](#como-reproduzir)
- [Uso opcional do Postgres](#uso-opcional-do-postgres-em-vez-do-sqlite)
- [Testes e CI](#testes-e-ci)
- [Metodologia e decisões técnicas](#metodologia-e-decisões-técnicas)
- [Resultados](#resultados)
- [Impacto de negócio (simulação em \$)](#impacto-de-negócio-simulação-em-)
- [Risk scores para Power BI](#risk-scores-para-power-bi)
- [Dashboard](#dashboard)
- [Trilha adicional: padrão enterprise](#trilha-adicional-padrão-enterprise-crm--dbt--warehouse)
- [Próximos passos](#próximos-passos)
- [Licença e autoria](#licença-e-autoria)

## Objetivo de negócio

Uma empresa de telecomunicações perde receita recorrente cada vez que um
cliente cancela seu serviço. Reter um cliente existente é
consideravelmente mais barato do que adquirir um novo, mas as equipes de
retenção têm capacidade limitada: não conseguem contatar toda a base de
clientes. Este projeto responde três perguntas:

1. **Quais fatores estão associados ao churn?** (SQL + EDA)
2. **Quais clientes têm maior probabilidade de cancelar *agora*, para
   priorizar ações de retenção?** (modelo preditivo + *risk scores*)
3. **Vale a pena, em termos de \$, direcionar uma campanha de retenção com
   este modelo, e até que profundidade da lista compensa ligar?**
   (simulação de impacto de negócio)

## Dataset

- **Fonte:** [IBM Telco Customer Churn](https://raw.githubusercontent.com/IBM/telco-customer-churn-on-icp4d/master/data/Telco-Customer-Churn.csv)
- **Tamanho:** 7.043 clientes, 21 colunas (demográficas, serviços
  contratados, faturamento e a variável alvo `Churn`).
- **Balanceamento de classes:** ~26.5% de clientes com churn ("Yes") contra
  ~73.5% sem churn ("No") — um desbalanceamento moderado que condiciona
  várias decisões metodológicas explicadas mais abaixo.

## Estrutura do repositório

```
customer-churn-prediction/
├── .github/
│   ├── workflows/ci.yml           # lint + testes em cada push/PR
│   ├── ISSUE_TEMPLATE/            # templates de bug report / feature request
│   └── PULL_REQUEST_TEMPLATE.md
├── docs/
│   ├── architecture.md            # diagramas C4 (contexto, containers) + fluxo de dados
│   ├── adr/                       # Architecture Decision Records
│   ├── data_dictionary.md         # descrição de cada coluna/arquivo gerado
│   └── runbook.md                 # guia operacional: o que fazer se algo falhar
├── data/
│   ├── Telco-Customer-Churn.csv   # dataset bruto
│   └── churn.db                   # SQLite (gerado por build_database.py)
├── notebooks/
│   ├── 01_eda.ipynb               # limpeza + estatística + 10 visualizações
│   └── 02_business_impact.ipynb   # simulação de impacto de negócio em $
├── src/
│   ├── db.py                      # engine SQLAlchemy: SQLite por padrão, Postgres opcional
│   ├── build_database.py          # CSV -> banco de dados
│   ├── sql_queries.sql            # 5 consultas de análise
│   ├── run_sql_analysis.py        # executa sql_queries.sql e salva os resultados
│   ├── train_models.py            # pipeline sklearn: LR, RF, XGBoost + CV
│   ├── generate_risk_scores.py    # scoring de toda a base + decis
│   └── run_all.py                 # orquestra o pipeline completo do zero
├── tests/                         # pytest: dados, pipeline e risk scores
├── reports/
│   └── figures/                   # PNGs gerados pelos notebooks e pelo treinamento
├── outputs/
│   ├── sql_analysis/              # resultados das 5 consultas SQL
│   ├── model_comparison.csv       # métricas dos 3 modelos
│   ├── best_model.joblib          # melhor pipeline treinado (serializado)
│   ├── customer_risk_scores.csv   # probabilidade de churn + decil por cliente
│   └── business_impact_simulation.csv  # valor líquido esperado por profundidade
├── warehouse_demo/                # trilha adicional: padrao enterprise (CRM -> dbt -> warehouse)
├── docker-compose.yml             # Postgres opcional (ver abaixo)
├── .env.example                   # template de credenciais para o Postgres
├── pyproject.toml                 # configuração do ruff (lint)
├── requirements.txt
├── requirements-dev.txt           # + pytest e ruff
├── requirements-warehouse.txt     # + dbt-postgres e prefect (so para warehouse_demo/)
├── CHANGELOG.md
├── CONTRIBUTING.md
└── README.md
```

## Documentação técnica

Este README cobre o quê e os resultados. O *porquê* de cada decisão
técnica não trivial vive em outro lugar, seguindo práticas padrão da
indústria:

- [`docs/architecture.md`](docs/architecture.md) — diagramas C4 (contexto
  e containers) e diagrama de fluxo de dados.
- [`docs/adr/`](docs/adr/README.md) — Architecture Decision Records: o
  que foi decidido, quais alternativas foram consideradas e por que
  foram descartadas.
- [`docs/data_dictionary.md`](docs/data_dictionary.md) — descrição de
  cada coluna do dataset e de cada arquivo gerado pelo pipeline.
- [`docs/runbook.md`](docs/runbook.md) — guia operacional para falhas
  comuns (dependências, Docker, Postgres, testes).
- [`CONTRIBUTING.md`](CONTRIBUTING.md) — convenção de commits, branches e
  quando escrever uma ADR.
- [`CHANGELOG.md`](CHANGELOG.md) — histórico de mudanças (formato Keep a
  Changelog).

## Como reproduzir

Requisitos: Python 3.11 (ou compatível com scikit-learn 1.4 / xgboost 2.0).

```bash
git clone <url-do-seu-repositorio>
cd customer-churn-prediction

python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

pip install -r requirements.txt

# Executa TODO o pipeline do zero com um unico comando:
python src/run_all.py
```

`run_all.py` executa, em ordem: construção do banco de dados, as 5
consultas SQL, o notebook de EDA (com suas 10 figuras), o treinamento e
comparação dos 3 modelos, e a geração de `customer_risk_scores.csv`. Todo
o projeto é recriado a partir do CSV bruto sem passos manuais. O notebook
`02_business_impact.ipynb` (simulação em \$) roda separadamente, depois de
ter `customer_risk_scores.csv` gerado.

## Uso opcional do Postgres em vez do SQLite

Por padrão tudo roda contra SQLite (configuração zero). Se preferir um
motor mais parecido com o que uma empresa real usaria, o projeto suporta
Postgres via Docker sem mudar uma linha de código:

```bash
cp .env.example .env          # DATABASE_URL já aponta para o Postgres do Docker
docker compose up -d          # sobe o Postgres em localhost:5432

python src/run_all.py
```

`src/db.py` centraliza essa decisão: carrega `.env` automaticamente
(via `python-dotenv`) e, se `DATABASE_URL` estiver definida ali, usa
Postgres; se não, usa SQLite. Não é preciso exportar a variável
manualmente no terminal — basta preencher `.env`. Nenhum outro script
sabe (nem se importa) com qual motor está falando.

**Duas pegadinhas reais de portabilidade SQLite → Postgres** que
apareceram durante a migração (documentadas em `src/sql_queries.sql` e
`src/build_database.py`, registradas aqui porque são o tipo de coisa que
só se descobre testando contra um motor real, não lendo documentação):
1. Postgres é sensível a maiúsculas/minúsculas em identificadores sem
   aspas (`Contract` ≠ `contract`); SQLite não é. Todas as colunas com
   maiúsculas ficam entre aspas duplas no `.sql`.
2. `ROUND()` no Postgres não tem sobrecarga para `double precision`,
   apenas para `numeric` — `ROUND(AVG(coluna_float), 2)` falha no
   Postgres e funciona sem problema no SQLite. Resolvido com um
   `CAST(... AS NUMERIC)`.

### Postgres gerenciado na nuvem (Supabase / Neon / Render)

`docker-compose.yml` é para desenvolvimento local. Para ter um Postgres
real acessível de qualquer lugar (sem precisar da sua máquina ligada),
**não é preciso pagar** — [Supabase](https://supabase.com) e
[Neon](https://neon.tech) têm planos gratuitos que sobram para este
dataset (~1 MB, 7.043 linhas). O fluxo é igual nos três:

1. Criar conta gratuita e um projeto/banco de dados novo.
2. Copiar a *connection string* que o dashboard fornece (geralmente em
   "Connection string" ou "Database settings").
3. Adaptar para o formato que `src/db.py` espera (SQLAlchemy + psycopg2):
   `postgresql+psycopg2://usuario:senha@host:porta/banco?sslmode=require`
   (o `?sslmode=require` costuma ser necessário porque esses provedores
   exigem conexão criptografada).
4. Colar essa URL como `DATABASE_URL` no seu `.env` (copiado de
   `.env.example`) e rodar `python src/run_all.py` — zero mudanças de
   código. `.env` nunca é commitado (ver `.gitignore`).

**Sobre qual escolher:** o plano gratuito do **Render** apaga o banco de
dados automaticamente após 90 dias de criado (não só pausa, apaga de
verdade) — má ideia para um projeto de portfólio que você quer manter
vivo quando alguém revisar meses depois. O **Supabase** pausa (não
apaga) projetos gratuitos após uma semana sem uso, e reativa com um
clique no dashboard. O **Neon** tem um modelo *serverless* que escala a
zero automaticamente e acorda sozinho na primeira conexão — é a opção
com menos fricção para este caso de uso. Recomendação: **Neon ou
Supabase antes do Render** para isso.

### Verificado em CI contra Neon real (os dois pipelines)

Este projeto já foi testado ponta a ponta contra um Postgres real na
nuvem (Neon), não só localmente — e não é só uma alegação, são dois
checks verificáveis na aba Actions, que rodam em todo push para `main`:

- **`test-neon`** — popula a tabela `customers`, roda as 5 consultas
  SQL e a suíte de testes do pipeline simples.
- **`test-neon-warehouse`** — roda o flow completo de `warehouse_demo/`
  (extração → `dbt run` → `dbt test`, 25 testes → treinamento → scoring)
  contra a mesma instância Neon.

Para ativar isso no seu próprio fork/clone:
1. No GitHub: `Settings → Secrets and variables → Actions → New repository secret`.
2. Nome: `NEON_DATABASE_URL`. Valor: sua connection string completa
   (`postgresql+psycopg2://usuario:senha@host.neon.tech/banco?sslmode=require`).
   Um único secret basta — `test-neon-warehouse` deriva as variáveis
   `PGHOST`/`PGUSER`/`PGPASSWORD`/`PGDATABASE` que o dbt precisa a
   partir dessa mesma URL (e mascara a senha derivada explicitamente
   nos logs com `::add-mask::`).
3. Sem esse secret configurado (por exemplo, em um fork de outra
   pessoa): `test-neon` cai para SQLite automaticamente; `test-neon-warehouse`
   pula a execução do flow (dbt-postgres não funciona com SQLite —
   ver [ADR-0001](docs/adr/0001-sqlite-por-defecto-postgres-opcional.md)).
   Em nenhum dos dois casos o CI quebra.

## Testes e CI

```bash
pip install -r requirements-dev.txt
pytest tests/ -v          # 20 testes: build_database, limpeza, pipeline, risk scores
ruff check src/ tests/    # lint
```

`.github/workflows/ci.yml` roda os dois comandos (job `test`) em cada
push/PR para `main` — além dos dois jobs contra Neon real descritos
acima (`test-neon`, `test-neon-warehouse`). Os testes de
`generate_risk_scores.py` reutilizam
`outputs/best_model.joblib` (versionado no repositório) em vez de
retreinar os 3 modelos com `GridSearchCV` a cada execução de CI —
treinar leva minutos e não agrega nada para verificar se o *scoring* está
implementado corretamente; para isso existe um *smoke test* que treina um
único modelo simples e rápido, sem busca de hiperparâmetros.

## Metodologia e decisões técnicas

### 1. SQL como primeira camada de análise
Antes de modelar, os dados são carregados em um banco de dados (SQLite
por padrão) e perguntas de negócio são respondidas diretamente em SQL
(`src/sql_queries.sql`): taxa de churn por contrato, por método de
pagamento, por serviço de internet, por antiguidade, e comparação de
tenure/cobranças entre clientes que saem e os que ficam. Isso simula o
fluxo real de um analista que primeiro diagnostica com SQL antes de
investir em um modelo.

### 2. Limpeza de `TotalCharges`
A coluna chega como texto com 11 valores vazios, correspondentes a
clientes com `tenure == 0` (recém cadastrados, sem faturamento
acumulado). É convertida para numérica e esses 11 casos são preenchidos
com `0` — o valor lógico segundo o negócio, não uma imputação
estatística (média/mediana) que inventaria faturamento inexistente.

### 3. Split estratificado (80/20)
O churn está desbalanceado (~26.5% positivos). Um split aleatório simples
pode, por acaso, deixar uma proporção diferente de positivos em treino e
em teste, enviesando tanto o treinamento quanto a avaliação. Estratificar
pela variável alvo (`train_test_split(..., stratify=y)`) garante que
treino e teste conservem a mesma proporção de churn (25.9%/26.5%) do
dataset completo, tornando a comparação de métricas confiável.

### 4. ROC-AUC como métrica principal (não só accuracy)
Com classes desbalanceadas, a **accuracy é enganosa**: um modelo que
sempre prevê "No churn" já obtém ~73.5% de accuracy sem aprender nada
útil. **ROC-AUC** mede a capacidade do modelo de *ordenar* clientes por
risco através de todos os limiares possíveis, independentemente do
balanceamento das classes. É também a métrica relevante para o caso de
uso real: priorizar uma lista de clientes por risco (decis), não apenas
classificar Yes/No com um limiar fixo de 0.5. Por isso o `GridSearchCV`
usa `scoring="roc_auc"` para escolher hiperparâmetros.

### 5. `Pipeline` + `ColumnTransformer`
O pré-processamento (`StandardScaler` para numéricas, `OneHotEncoder`
para categóricas) é encapsulado no mesmo `Pipeline` que o classificador.
Isso evita vazamento de informação (o scaler/encoder é ajustado apenas
com os dados de treino dentro de cada fold da validação cruzada) e
permite reutilizar o objeto completo para inferência sem repetir
transformações manualmente.

### 6. Três modelos, validação cruzada de 5 folds, busca leve
São comparados **Regressão Logística** (linear, interpretável, baseline
forte), **Random Forest** (não linear, robusto a outliers) e **XGBoost**
(gradient boosting, costuma vencer em dados tabulares). Cada um é
ajustado com `GridSearchCV` sobre um grid pequeno de hiperparâmetros e
`StratifiedKFold(n_splits=5)`, equilibrando rigor metodológico com
tempos de execução razoáveis para um projeto reproduzível.

### 7. Acesso a dados desacoplado do motor (SQLite/Postgres)
`src/db.py` é o único lugar que decide com qual banco de dados falar (via
SQLAlchemy). O resto do código nunca importa `sqlite3` nem `psycopg2`
diretamente, apenas pede um `engine`. Isso permite que o projeto continue
funcionando com configuração zero (SQLite), mas também possa ser
executado contra um Postgres real sem tocar na lógica de negócio —
exatamente a separação que permitiria, mais adiante, migrar para um
warehouse na nuvem sem reescrever nada.

## Resultados

### Diagnóstico SQL / EDA — fatores mais associados ao churn

| Fator | Achado |
|---|---|
| Tipo de contrato | Mês a mês: **42.7%** de churn vs. 11.3% (1 ano) e 2.8% (2 anos) |
| Método de pagamento | Cheque eletrônico: **45.3%** de churn vs. 15–19% em métodos automáticos |
| Serviço de internet | Fibra óptica: **41.9%** de churn vs. 19.0% (DSL) e 7.4% (sem internet) |
| Antiguidade | 0–12 meses: **47.4%** de churn vs. 9.5% em clientes com 49+ meses |
| Tenure / cobranças médias | Clientes com churn: 17.98 meses / \$74.44 mensal vs. sem churn: 37.57 meses / \$61.27 mensal |

Resultados completos e reproduzíveis em `outputs/sql_analysis/*.csv` e em
`notebooks/01_eda.ipynb` (10 visualizações em `reports/figures/`).

### Comparação de modelos (holdout 20%, limiar = 0.5)

| Modelo | Accuracy | Precision | Recall | F1 | ROC-AUC |
|---|---|---|---|---|---|
| **XGBoost** | 0.805 | 0.670 | 0.521 | 0.586 | **0.845** |
| Random Forest | 0.808 | 0.697 | 0.487 | 0.573 | 0.843 |
| Regressão Logística | 0.806 | 0.659 | 0.559 | 0.605 | 0.841 |

Tabela completa (inclui melhores hiperparâmetros e ROC-AUC de CV) em
[`outputs/model_comparison.csv`](outputs/model_comparison.csv).

**Modelo vencedor: XGBoost** (ROC-AUC teste = 0.845), embora os três
modelos fiquem muito próximos entre si (ROC-AUC 0.841–0.845), o que
sugere que o sinal preditivo do dataset está perto do seu teto com essas
variáveis e que o tipo de modelo importa menos do que as variáveis
disponíveis.

![Curvas ROC](reports/figures/roc_curves.png)

![Matrizes de confusão](reports/figures/confusion_matrices.png)

### Variáveis mais importantes (XGBoost)

Consistente com o diagnóstico SQL/EDA: contrato mês a mês, fibra óptica
sem suporte técnico/segurança e pagamento por cheque eletrônico são os
sinais mais fortes de risco de churn.

![Importância de variáveis](reports/figures/feature_importance.png)

## Impacto de negócio (simulação em \$)

`notebooks/02_business_impact.ipynb` traduz as probabilidades de churn em
valor esperado em dólares através de um **backtest retrospectivo** (usa o
resultado real conhecido `actual_churn` para simular quão boa teria sido
uma campanha direcionada pelo modelo — técnica padrão de *offline policy
evaluation* para justificar uma campanha antes de executá-la; o notebook
explica essa limitação em detalhe).

Com suposições ilustrativas (custo de contato \$20, 30% de sucesso da
oferta de retenção, valor de retenção = 12 meses de faturamento):

- **Profundidade ótima: contatar 60% da base** (4.225 clientes). Nesse
  ponto o valor líquido esperado é maximizado em **\$398.892**, contra
  **\$176.852** se a seleção fosse aleatória na mesma profundidade — um
  **uplift de ~\$222.040** atribuível exclusivamente ao uso do modelo.
- O valor líquido **não cresce monotonicamente**: passado o 60% começa a
  cair (\$360.011 em 100% da base) porque se paga para contatar clientes
  de baixo risco que de qualquer forma não iam cancelar.
- Com orçamento limitado, 20% da base já captura 53.3% dos churners reais
  com uma opção bem mais barata (ver notebook para o detalhe completo e o
  trade-off valor total vs. eficiência por dólar).

![Valor líquido esperado por profundidade](reports/figures/12_campaign_net_value_by_depth.png)

Tabela completa em
[`outputs/business_impact_simulation.csv`](outputs/business_impact_simulation.csv).

## Risk scores para Power BI

[`outputs/customer_risk_scores.csv`](outputs/customer_risk_scores.csv)
contém, para os 7.043 clientes, sua probabilidade de churn (modelo
XGBoost) e seu decil de risco (10 = maior risco, 1 = menor risco):

| customerID | churn_probability | actual_churn | risk_decile |
|---|---|---|---|
| 7216-EWTRS | 0.9459 | Yes | 10 |
| 5419-JPRRN | 0.9444 | Yes | 10 |
| 0107-YHINA | 0.9361 | Yes | 10 |

Este arquivo foi pensado para se conectar diretamente ao Power BI (ou
Tableau) como fonte de um dashboard de retenção: filtrar por
`risk_decile = 10` fornece a lista de clientes com maior prioridade para
contato. O modelo é treinado apenas com os 80% de treino para que a
avaliação acima seja honesta; o *scoring* final é aplicado sobre 100% dos
clientes porque o objetivo aqui não é medir performance (isso já foi
feito), mas sim produzir uma lista operacional completa.

## Dashboard

![Dashboard de risco de churn no Power BI](reports/figures/powerbi_dashboard.png)

Dashboard construído em Power BI Desktop a partir de
[`outputs/customer_risk_scores.csv`](outputs/customer_risk_scores.csv) e
[`outputs/business_impact_simulation.csv`](outputs/business_impact_simulation.csv),
arquivo `.pbix` disponível em [`powerbi/customer_churn_dashboard.pbix`](powerbi/customer_churn_dashboard.pbix).
Reúne: total de clientes, taxa de churn geral, clientes de alto risco
(decis 9-10) e valor líquido esperado da campanha na profundidade ótima
(60%); a curva de taxa de churn por decil de risco (evidência visual de
que o modelo discrimina bem); a comparação de valor líquido entre a
estratégia do modelo e a seleção aleatória em cada profundidade; uma
tabela acionável dos clientes de maior risco; e um segmentador por decil.

Há também uma segunda versão, em [`reports/dashboard.html`](reports/dashboard.html):
uma página autocontida (sem dependências externas), com os mesmos KPIs e
gráficos, que roda direto no navegador sem precisar instalar nada — veja
ao vivo em **[hard747.github.io/customer-churn-prediction/reports/dashboard.html](https://hard747.github.io/customer-churn-prediction/reports/dashboard.html)**.

## Trilha adicional: padrão enterprise (CRM → dbt → warehouse)

[`warehouse_demo/`](warehouse_demo/README.md) implementa, além do
pipeline simples acima, o padrão real usado em empresas grandes para
este mesmo problema: `CRM/ERP (simulado) → Prefect → Postgres → dbt →
Feature Table → Modelo → Scores`. Inclui um projeto dbt real (staging +
tests + mart, 25/25 tests passando) e um flow de Prefect testado ponta a
ponta contra Postgres. Ver também
[`docs/architecture.md`](docs/architecture.md#71-trilha-adicional-padrão-enterprise-warehouse_demo)
e [ADR-0007](docs/adr/0007-prefect-en-vez-de-airflow.md) /
[ADR-0008](docs/adr/0008-simular-crm-erp-normalizando-mismo-dataset.md).

## Próximos passos

- Testar *cost-sensitive learning* ou ajuste de limiar (em vez de 0.5)
  para otimizar o trade-off precision/recall de acordo com o custo real
  de um falso negativo (cliente que cancela sem ser detectado) vs. um
  falso positivo (contatar alguém que não iria cancelar).
- Registro de experimentos com MLflow e versionamento de dados com DVC.
- Monitoramento de *drift* do modelo (por exemplo, com `evidently`).
- Incorporar variáveis temporais (histórico de uso, tickets de suporte)
  se estivessem disponíveis, além do snapshot estático do dataset.
- Servir o modelo como API (FastAPI) para *scoring* em tempo real.

## Licença e autoria

Distribuído sob licença [MIT](LICENSE). Dataset de uso público (IBM Telco
Customer Churn, para fins educacionais/de portfólio).

**Autor:** Harre Bams Ayma Aranda — único autor deste repositório.
