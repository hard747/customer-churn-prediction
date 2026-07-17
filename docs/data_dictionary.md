# Dicionário de dados

## 1. Tabela `customers` (fonte: `data/Telco-Customer-Churn.csv`, carregada por `src/build_database.py`)

| Coluna | Tipo | Descrição | Valores / faixa | Notas de limpeza |
|---|---|---|---|---|
| `customerID` | texto | Identificador único do cliente | Formato `NNNN-XXXXX` | Já vem anonimizado no dataset público; não é PII real |
| `gender` | categórica | Gênero declarado | `Male`, `Female` | — |
| `SeniorCitizen` | inteiro (0/1) no CSV bruto | Indica se o cliente é idoso | `0`, `1` | Em `train_models.py`/`generate_risk_scores.py` é remapeado para `No`/`Yes` para ser tratado igual às demais flags categóricas |
| `Partner` | categórica | Tem parceiro(a) registrado(a) | `Yes`, `No` | — |
| `Dependents` | categórica | Tem dependentes econômicos | `Yes`, `No` | — |
| `tenure` | inteiro | Meses de antiguidade como cliente | `0`–`72` | — |
| `PhoneService` | categórica | Tem serviço telefônico | `Yes`, `No` | — |
| `MultipleLines` | categórica | Tem múltiplas linhas | `Yes`, `No`, `No phone service` | — |
| `InternetService` | categórica | Tipo de serviço de internet | `DSL`, `Fiber optic`, `No` | — |
| `OnlineSecurity` | categórica | Serviço de segurança online contratado | `Yes`, `No`, `No internet service` | — |
| `OnlineBackup` | categórica | Serviço de backup online contratado | `Yes`, `No`, `No internet service` | — |
| `DeviceProtection` | categórica | Proteção de dispositivo contratada | `Yes`, `No`, `No internet service` | — |
| `TechSupport` | categórica | Suporte técnico contratado | `Yes`, `No`, `No internet service` | — |
| `StreamingTV` | categórica | Streaming de TV contratado | `Yes`, `No`, `No internet service` | — |
| `StreamingMovies` | categórica | Streaming de filmes contratado | `Yes`, `No`, `No internet service` | — |
| `Contract` | categórica | Tipo de contrato | `Month-to-month`, `One year`, `Two year` | Variável mais associada ao churn (ver EDA) |
| `PaperlessBilling` | categórica | Fatura sem papel | `Yes`, `No` | — |
| `PaymentMethod` | categórica | Método de pagamento | `Electronic check`, `Mailed check`, `Bank transfer (automatic)`, `Credit card (automatic)` | — |
| `MonthlyCharges` | numérico (float) | Cobrança mensal atual | USD, aprox. 18–120 | — |
| `TotalCharges` | numérico (float) | Cobrança total acumulada histórica | USD | **Chega como texto no CSV bruto**, com 11 linhas vazias (`" "`). `build_database.py` converte para numérico (`pd.to_numeric(errors="coerce")`), ficando `NULL` nessas 11 linhas. `train_models.py`/`generate_risk_scores.py` as preenche com `0.0` — correspondem exatamente a clientes com `tenure == 0` (recém cadastrados, sem faturamento acumulado), verificado em `tests/test_build_database.py::test_total_charges_nulls_match_zero_tenure_customers` |
| `Churn` | categórica (texto na tabela) | Variável alvo: o cliente cancelou o serviço | `Yes`, `No` | `train_models.load_and_clean_data()` a mapeia para `1`/`0` para a modelagem |

**Índices:** `idx_contract` sobre `Contract`, `idx_churn` sobre `Churn`
(criados em `build_database.py`, aceleram as consultas de
`sql_queries.sql` agrupadas por essas colunas).

## 2. `outputs/customer_risk_scores.csv` (gerado por `generate_risk_scores.py`)

| Coluna | Tipo | Descrição |
|---|---|---|
| `customerID` | texto | Igual a `customers` |
| `churn_probability` | float, `[0, 1]` | Probabilidade de churn segundo o melhor modelo (XGBoost), arredondada a 4 casas decimais |
| `actual_churn` | `Yes`/`No` | Resultado histórico real (igual a `Churn` em `customers`) — incluído para poder auditar o modelo, **não** para ser usado como feature |
| `risk_decile` | inteiro `1`–`10` | Decil de risco por quantis de `churn_probability`; `10` = 10% dos clientes com maior risco. Calculado com `pd.qcut` |

## 3. `outputs/model_comparison.csv` (gerado por `train_models.py`)

| Coluna | Tipo | Descrição |
|---|---|---|
| `model` | texto | Nome do modelo (`LogisticRegression`, `RandomForest`, `XGBoost`) |
| `accuracy`, `precision`, `recall`, `f1`, `roc_auc` | float | Métricas sobre o holdout de teste (20%), limiar 0.5 exceto `roc_auc` |
| `cv_best_roc_auc` | float | Melhor ROC-AUC médio do `GridSearchCV` (5-fold) durante a busca de hiperparâmetros |
| `best_params` | texto (dict serializado) | Hiperparâmetros vencedores para aquele modelo |

## 4. `outputs/business_impact_simulation.csv` (gerado por `02_business_impact.ipynb`)

| Coluna | Tipo | Descrição |
|---|---|---|
| `strategy` | texto | `Modelo` (ordenado por `churn_probability`) ou `Aleatorio` (baseline) |
| `depth_pct` | inteiro, `10`–`100` | % da base contatada, de maior a menor risco |
| `n_contacted` | inteiro | Clientes contatados até essa profundidade |
| `n_true_churners_contacted` | inteiro | Dos contatados, quantos realmente iam cancelar (`actual_churn == Yes`) |
| `cost` | float (USD) | `n_contacted * CONTACT_COST` |
| `expected_revenue_saved` | float (USD) | Receita esperada salva, ver fórmula no notebook |
| `net_value` | float (USD) | `expected_revenue_saved - cost` |

## 5. Variáveis de ambiente

| Variável | Obrigatória | Descrição |
|---|---|---|
| `DATABASE_URL` | Não (padrão: SQLite local) | String de conexão do SQLAlchemy. Se definida, `src/db.py` a usa em vez do SQLite. Formato: `postgresql+psycopg2://usuario:senha@host:porta/banco` |
| `PGHOST`, `PGPORT`, `PGUSER`, `PGPASSWORD`, `PGDATABASE`, `PGSSLMODE` | Só para `warehouse_demo/` | Mesmas credenciais de `DATABASE_URL`, mas como campos separados — o `profiles.yml` do dbt precisa deles assim, não como uma única URL |

## 6. Tabelas de `warehouse_demo/` (padrão enterprise — ver `warehouse_demo/README.md`)

Exigem Postgres real (não funcionam com SQLite). Carregadas por
`warehouse_demo/src/build_raw_tables.py` e transformadas pelo projeto
dbt em `warehouse_demo/dbt/churn_analytics/`.

| Tabela | Camada | Colunas | Notas |
|---|---|---|---|
| `raw_crm_customers` | raw | `customerID`, `gender`, `SeniorCitizen`, `Partner`, `Dependents` | Simula export de CRM. Mesmos tipos brutos do CSV original |
| `raw_crm_subscriptions` | raw | `customerID`, `tenure`, serviços contratados, `Contract`, `PaperlessBilling` | Simula export de ERP/assinaturas |
| `raw_billing_charges` | raw | `customerID`, `PaymentMethod`, `MonthlyCharges`, `TotalCharges` | Simula billing. `TotalCharges` chega como texto com linhas vazias (igual ao CSV bruto) — limpeza real em `stg_billing_charges`, não aqui |
| `raw_churn_labels` | raw | `customerID`, `Churn` | Sinal histórico |
| `stg_crm_customers`, `stg_crm_subscriptions`, `stg_billing_charges`, `stg_churn_labels` | staging (dbt, views) | Igual às raw mas com nomes em snake_case e tipos limpos (`TotalCharges` já convertido para numérico, sem nulos) | Ver os `.sql` em `models/staging/` |
| `fct_customer_features` | mart (dbt, tabela) | Join das 4 staging tables por `customer_id`: `tenure`, `monthly_charges`, `total_charges`, `gender`, `senior_citizen`, `partner`, `dependents`, serviços, `contract`, `payment_method`, `churn` | É a tabela que `train_from_feature_table.py` consome, equivalente à `customers` do pipeline simples mas montada em SQL versionado (dbt) em vez de em pandas |
