[🇧🇷 Português](README.md) · 🇪🇸 Español (actual) · [🇬🇧 English](README.en.md)

# Predicción de Churn de Clientes — Telco Customer Churn

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-1.4-F7931E?logo=scikitlearn&logoColor=white)
![XGBoost](https://img.shields.io/badge/XGBoost-2.0-1C6EA4)
![SQLite](https://img.shields.io/badge/SQLite-3-003B57?logo=sqlite&logoColor=white)
![Postgres opcional](https://img.shields.io/badge/Postgres-opcional-336791?logo=postgresql&logoColor=white)
![CI](https://github.com/hard747/customer-churn-prediction/actions/workflows/ci.yml/badge.svg)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-completo-brightgreen)

Proyecto end-to-end de análisis y predicción de fuga de clientes (*churn*)
usando el dataset público **Telco Customer Churn** de IBM. Cubre el flujo
completo de un proyecto de Data Science aplicado a negocio: consultas SQL
de diagnóstico, análisis exploratorio con visualizaciones, entrenamiento y
comparación de modelos de clasificación, simulación de impacto de negocio
en \$, y un archivo de *risk scores* listo para conectar a un dashboard de
Power BI. Incluye tests automatizados, CI en GitHub Actions y soporte
opcional para Postgres vía Docker.

## Tabla de contenidos

- [Objetivo de negocio](#objetivo-de-negocio)
- [Dataset](#dataset)
- [Estructura del repositorio](#estructura-del-repositorio)
- [Documentación técnica](#documentación-técnica)
- [Cómo reproducirlo](#cómo-reproducirlo)
- [Uso opcional de Postgres](#uso-opcional-de-postgres-en-vez-de-sqlite)
- [Tests y CI](#tests-y-ci)
- [Metodología y decisiones técnicas](#metodología-y-decisiones-técnicas)
- [Resultados](#resultados)
- [Impacto de negocio (simulación en \$)](#impacto-de-negocio-simulación-en-)
- [Risk scores para Power BI](#risk-scores-para-power-bi)
- [Dashboard](#dashboard)
- [Track adicional: patrón enterprise](#track-adicional-patrón-enterprise-crm--dbt--warehouse)
- [Próximos pasos](#próximos-pasos)
- [Licencia y autoría](#licencia-y-autoría)

## Objetivo de negocio

Una empresa de telecomunicaciones pierde ingresos recurrentes cada vez que
un cliente cancela su servicio. Retener a un cliente existente es
considerablemente más barato que adquirir uno nuevo, pero los equipos de
retención tienen capacidad limitada: no pueden contactar a toda la base de
clientes. Este proyecto responde tres preguntas:

1. **¿Qué factores están asociados al churn?** (SQL + EDA)
2. **¿Qué clientes tienen mayor probabilidad de cancelar *ahora*, para
   priorizar acciones de retención?** (modelo predictivo + *risk scores*)
3. **¿Vale la pena, en términos de \$, dirigir una campaña de retención con
   este modelo, y hasta qué profundidad de la lista conviene llamar?**
   (simulación de impacto de negocio)

## Dataset

- **Fuente:** [IBM Telco Customer Churn](https://raw.githubusercontent.com/IBM/telco-customer-churn-on-icp4d/master/data/Telco-Customer-Churn.csv)
- **Tamaño:** 7,043 clientes, 21 columnas (demográficas, servicios
  contratados, facturación y variable objetivo `Churn`).
- **Balance de clases:** ~26.5% de clientes con churn ("Yes") frente a
  ~73.5% sin churn ("No") — un desbalance moderado que condiciona varias
  decisiones metodológicas explicadas más abajo.

## Estructura del repositorio

```
customer-churn-prediction/
├── .github/
│   ├── workflows/ci.yml           # lint + tests en cada push/PR
│   ├── ISSUE_TEMPLATE/            # plantillas de bug report / feature request
│   └── PULL_REQUEST_TEMPLATE.md
├── docs/
│   ├── architecture.md            # diagramas C4 (contexto, contenedores) + flujo de datos
│   ├── adr/                       # Architecture Decision Records
│   ├── data_dictionary.md         # descripción de cada columna/archivo generado
│   └── runbook.md                 # guía operativa: qué hacer si algo falla
├── data/
│   ├── Telco-Customer-Churn.csv   # dataset crudo
│   └── churn.db                   # SQLite (se genera con build_database.py)
├── notebooks/
│   ├── 01_eda.ipynb               # limpieza + estadística + 10 visualizaciones
│   └── 02_business_impact.ipynb   # simulación de impacto de negocio en $
├── src/
│   ├── db.py                      # engine SQLAlchemy: SQLite por defecto, Postgres opcional
│   ├── build_database.py          # CSV -> base de datos
│   ├── sql_queries.sql            # 5 consultas de análisis
│   ├── run_sql_analysis.py        # ejecuta sql_queries.sql y guarda resultados
│   ├── train_models.py            # pipeline sklearn: LR, RF, XGBoost + CV
│   ├── generate_risk_scores.py    # scoring de toda la base + deciles
│   └── run_all.py                 # orquesta el pipeline completo de cero
├── tests/                         # pytest: datos, pipeline y risk scores
├── reports/
│   └── figures/                   # PNGs generados por los notebooks y el training
├── outputs/
│   ├── sql_analysis/              # resultados de las 5 consultas SQL
│   ├── model_comparison.csv       # métricas de los 3 modelos
│   ├── best_model.joblib          # mejor pipeline entrenado (serializado)
│   ├── customer_risk_scores.csv   # probabilidad de churn + decil por cliente
│   └── business_impact_simulation.csv  # valor neto esperado por profundidad
├── warehouse_demo/                # track adicional: patron enterprise (CRM -> dbt -> warehouse)
├── docker-compose.yml             # Postgres opcional (ver mas abajo)
├── .env.example                   # plantilla de credenciales para Postgres
├── pyproject.toml                 # configuración de ruff (lint)
├── requirements.txt
├── requirements-dev.txt           # + pytest y ruff
├── requirements-warehouse.txt     # + dbt-postgres y prefect (solo para warehouse_demo/)
├── CHANGELOG.md
├── CONTRIBUTING.md
└── README.md
```

## Documentación técnica

Este README cubre el qué y los resultados. El *por qué* de cada decisión
técnica no trivial vive aparte, siguiendo prácticas estándar de la
industria:

- [`docs/architecture.md`](docs/architecture.md) — diagramas C4 (contexto
  y contenedores) y diagrama de flujo de datos.
- [`docs/adr/`](docs/adr/README.md) — Architecture Decision Records: qué
  se decidió, qué alternativas se consideraron y por qué se descartaron.
- [`docs/data_dictionary.md`](docs/data_dictionary.md) — descripción de
  cada columna del dataset y de cada archivo generado por el pipeline.
- [`docs/runbook.md`](docs/runbook.md) — guía operativa ante fallos
  comunes (dependencias, Docker, Postgres, tests).
- [`CONTRIBUTING.md`](CONTRIBUTING.md) — convención de commits, branches
  y cuándo escribir una ADR.
- [`CHANGELOG.md`](CHANGELOG.md) — historial de cambios (formato Keep a
  Changelog).

## Cómo reproducirlo

Requisitos: Python 3.11 (o compatible con scikit-learn 1.4 / xgboost 2.0).

```bash
git clone <url-de-tu-repositorio>
cd customer-churn-prediction

python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

pip install -r requirements.txt

# Ejecuta TODO el pipeline de cero con un solo comando:
python src/run_all.py
```

`run_all.py` ejecuta en orden: construcción de la base de datos, las 5
consultas SQL, el notebook de EDA (con sus 10 figuras), el entrenamiento
y comparación de los 3 modelos, y la generación de `customer_risk_scores.csv`.
Todo el proyecto se recrea desde el CSV crudo sin pasos manuales. El
notebook `02_business_impact.ipynb` (simulación de \$) se corre aparte,
despues de tener `customer_risk_scores.csv` generado.

## Uso opcional de Postgres en vez de SQLite

Por defecto todo corre contra SQLite (cero configuración). Si preferís un
motor más parecido a lo que usaría una empresa real, el proyecto soporta
Postgres vía Docker sin cambiar una línea de código:

```bash
cp .env.example .env          # DATABASE_URL ya viene apuntando al Postgres de Docker
docker compose up -d          # levanta Postgres en localhost:5432

python src/run_all.py
```

`src/db.py` centraliza esta decisión: carga `.env` automáticamente
(vía `python-dotenv`) y, si `DATABASE_URL` quedó definida ahí, usa
Postgres; si no, usa SQLite. No hace falta exportar la variable a mano
en la terminal — con completar `.env` alcanza. Ningún otro script sabe
(ni le importa) contra qué motor está hablando.

**Dos gotchas reales de portabilidad SQLite → Postgres** que aparecieron
al migrar (documentados en `src/sql_queries.sql` y `src/build_database.py`,
dejados aquí porque son el tipo de cosa que solo se descubre probando
contra un motor real, no leyendo la documentación):
1. Postgres es sensible a mayúsculas en identificadores sin comillas
   (`Contract` ≠ `contract`); SQLite no. Todas las columnas con mayúsculas
   van entre comillas dobles en el `.sql`.
2. `ROUND()` en Postgres no tiene sobrecarga para `double precision`, solo
   para `numeric` — `ROUND(AVG(columna_float), 2)` falla en Postgres y
   funciona sin problema en SQLite. Se resuelve con un `CAST(... AS NUMERIC)`.

### Postgres administrado en la nube (Supabase / Neon / Render)

`docker-compose.yml` es para desarrollo local. Para tener un Postgres real
accesible desde cualquier lado (sin tu máquina prendida), **no hace falta
pagar** — [Supabase](https://supabase.com) y [Neon](https://neon.tech)
tienen planes gratuitos que alcanzan de sobra para este dataset (~1 MB,
7,043 filas). El flujo es igual en los tres:

1. Crear cuenta gratuita y un proyecto/base de datos nuevo.
2. Copiar el *connection string* que te da el dashboard (normalmente bajo
   "Connection string" o "Database settings").
3. Adaptarlo al formato que espera `src/db.py` (SQLAlchemy + psycopg2):
   `postgresql+psycopg2://usuario:password@host:puerto/basededatos?sslmode=require`
   (el `?sslmode=require` suele ser necesario porque estos proveedores
   exigen conexión cifrada).
4. Pegar esa URL como `DATABASE_URL` en tu `.env` (copiado de
   `.env.example`) y correr `python src/run_all.py` — cero cambios de
   código. `.env` nunca se commitea (ver `.gitignore`).

**Sobre cuál elegir:** el plan gratuito de **Render** borra la base de
datos automáticamente a los 90 días de creada (no solo la pausa, la
elimina) — mala idea para un proyecto de portafolio que querés que siga
vivo cuando alguien lo revise meses después. **Supabase** pausa (no
borra) los proyectos gratuitos tras una semana sin uso, y se reactivan
con un clic desde el dashboard. **Neon** tiene un modelo *serverless* que
escala a cero automáticamente y se despierta solo con la primera conexión
— es la opción con menos fricción para este caso de uso. Recomendación:
**Neon o Supabase antes que Render** para esto.

### Verificado en CI contra Neon real (los dos pipelines)

Este proyecto ya fue probado de punta a punta contra un Postgres real
en la nube (Neon), no solo localmente — y no es solo una afirmación,
son dos checks verificables en la pestaña Actions, que corren en cada
push a `main`:

- **`test-neon`** — puebla la tabla `customers`, corre las 5 consultas
  SQL y la suite de tests del pipeline simple.
- **`test-neon-warehouse`** — corre el flow completo de
  `warehouse_demo/` (extracción → `dbt run` → `dbt test`, 25 tests →
  entrenamiento → scoring) contra la misma instancia Neon.

Para activar esto en tu propio fork/clon:
1. En GitHub: `Settings → Secrets and variables → Actions → New repository secret`.
2. Nombre: `NEON_DATABASE_URL`. Valor: tu connection string completa
   (`postgresql+psycopg2://usuario:password@host.neon.tech/basededatos?sslmode=require`).
   Un único secret alcanza — `test-neon-warehouse` deriva las variables
   `PGHOST`/`PGUSER`/`PGPASSWORD`/`PGDATABASE` que dbt necesita a partir
   de esa misma URL (y enmascara la contraseña derivada explícitamente
   en los logs con `::add-mask::`).
3. Sin ese secret configurado (por ejemplo, en un fork de otra
   persona): `test-neon` cae a SQLite automáticamente; `test-neon-warehouse`
   se salta la ejecución del flow (dbt-postgres no funciona con SQLite —
   ver [ADR-0001](docs/adr/0001-sqlite-por-defecto-postgres-opcional.md)).
   En ningún caso el CI se rompe.

## Tests y CI

```bash
pip install -r requirements-dev.txt
pytest tests/ -v          # 20 tests: build_database, limpieza, pipeline, risk scores
ruff check src/ tests/    # lint
```

`.github/workflows/ci.yml` corre ambos comandos (job `test`) en cada
push/PR a `main` — además de los dos jobs contra Neon real descritos
arriba (`test-neon`, `test-neon-warehouse`).
Los tests de `generate_risk_scores.py` reutilizan `outputs/best_model.joblib`
(versionado en el repo) en vez de reentrenar los 3 modelos con
`GridSearchCV` en cada corrida de CI — entrenar toma minutos y no aporta
nada a verificar que el *scoring* esté bien implementado; para eso hay un
*smoke test* que entrena un único modelo simple y rápido sin búsqueda de
hiperparámetros.

## Metodología y decisiones técnicas

### 1. SQL como primera capa de análisis
Antes de modelar, se cargan los datos a una base de datos (SQLite por
defecto) y se responden preguntas de negocio directamente en SQL
(`src/sql_queries.sql`): tasa de churn por contrato, por método de pago,
por servicio de internet, por antigüedad, y comparación de tenure/cargos
entre clientes que se van y los que se quedan. Esto simula el flujo real
de un analista que primero diagnostica con SQL antes de invertir en un
modelo.

### 2. Limpieza de `TotalCharges`
La columna llega como texto con 11 valores vacíos, correspondientes a
clientes con `tenure == 0` (recién dados de alta, sin facturación
acumulada). Se convierte a numérico y esos 11 casos se completan con `0`
—el valor lógico según el negocio, no una imputación estadística
(media/mediana) que inventaría facturación inexistente.

### 3. Split estratificado (80/20)
El churn está desbalanceado (~26.5% positivos). Un split aleatorio simple
puede, por azar, dejar una proporción distinta de positivos en train y en
test, sesgando tanto el entrenamiento como la evaluación. Estratificar por
la variable objetivo (`train_test_split(..., stratify=y)`) garantiza que
train y test conserven la misma proporción de churn (25.9%/26.5%) que el
dataset completo, haciendo la comparación de métricas confiable.

### 4. ROC-AUC como métrica principal (no solo accuracy)
Con clases desbalanceadas, la **accuracy es engañosa**: un modelo que
siempre prediga "No churn" ya obtiene ~73.5% de accuracy sin aprender
nada. **ROC-AUC** mide la capacidad del modelo para *ordenar* clientes por
riesgo a través de todos los umbrales posibles, independientemente del
balance de clases. Es además la métrica relevante para el caso de uso
real: priorizar una lista de clientes por riesgo (deciles), no solo
clasificar Yes/No con un umbral fijo de 0.5. Por eso `GridSearchCV` usa
`scoring="roc_auc"` para elegir hiperparámetros.

### 5. `Pipeline` + `ColumnTransformer`
El preprocesamiento (`StandardScaler` para numéricas, `OneHotEncoder` para
categóricas) se encapsula en el mismo `Pipeline` que el clasificador. Esto
evita fuga de información (el scaler/encoder se ajusta solo con los datos
de entrenamiento dentro de cada fold de la validación cruzada) y permite
reutilizar el objeto completo para inferencia sin repetir transformaciones
a mano.

### 6. Tres modelos, validación cruzada de 5 folds, búsqueda ligera
Se comparan **Regresión Logística** (lineal, interpretable, baseline
fuerte), **Random Forest** (no lineal, robusto a outliers) y **XGBoost**
(gradient boosting, suele ganar en datos tabulares). Cada uno se ajusta
con `GridSearchCV` sobre un grid pequeño de hiperparámetros y
`StratifiedKFold(n_splits=5)`, balanceando rigurosidad metodológica con
tiempos de ejecución razonables para un proyecto reproducible.

### 7. Acceso a datos desacoplado del motor (SQLite/Postgres)
`src/db.py` es el único lugar que decide contra qué base de datos hablar
(vía SQLAlchemy). El resto del código nunca importa `sqlite3` ni
`psycopg2` directamente, solo pide un `engine`. Esto permite que el
proyecto siga funcionando con cero configuración (SQLite) pero también se
pueda ejecutar contra un Postgres real sin tocar la lógica de negocio —
justo la separación que le permitiría, más adelante, migrar a un
warehouse en la nube sin reescribir nada.

## Resultados

### Diagnóstico SQL / EDA — factores más asociados al churn

| Factor | Hallazgo |
|---|---|
| Tipo de contrato | Mes a mes: **42.7%** de churn vs. 11.3% (1 año) y 2.8% (2 años) |
| Método de pago | Cheque electrónico: **45.3%** de churn vs. 15–19% en métodos automáticos |
| Servicio de internet | Fibra óptica: **41.9%** de churn vs. 19.0% (DSL) y 7.4% (sin internet) |
| Antigüedad | 0–12 meses: **47.4%** de churn vs. 9.5% en clientes con 49+ meses |
| Tenure / cargos promedio | Clientes con churn: 17.98 meses / \$74.44 mensual vs. sin churn: 37.57 meses / \$61.27 mensual |

Resultados completos y reproducibles en `outputs/sql_analysis/*.csv` y en
`notebooks/01_eda.ipynb` (10 visualizaciones en `reports/figures/`).

### Comparación de modelos (holdout 20%, umbral = 0.5)

| Modelo | Accuracy | Precision | Recall | F1 | ROC-AUC |
|---|---|---|---|---|---|
| **XGBoost** | 0.805 | 0.670 | 0.521 | 0.586 | **0.845** |
| Random Forest | 0.808 | 0.697 | 0.487 | 0.573 | 0.843 |
| Regresión Logística | 0.806 | 0.659 | 0.559 | 0.605 | 0.841 |

Tabla completa (incluye mejores hiperparámetros y ROC-AUC de CV) en
[`outputs/model_comparison.csv`](outputs/model_comparison.csv).

**Modelo ganador: XGBoost** (ROC-AUC test = 0.845), aunque los tres modelos
quedan muy cerca entre sí (ROC-AUC 0.841–0.845), lo que sugiere que la
señal predictiva del dataset está cerca de su techo con estas variables y
que el tipo de modelo importa menos que las variables disponibles.

![Curvas ROC](reports/figures/roc_curves.png)

![Matrices de confusión](reports/figures/confusion_matrices.png)

### Variables más importantes (XGBoost)

Consistente con el diagnóstico SQL/EDA: contrato mes a mes, fibra óptica
sin soporte técnico/seguridad y pago por cheque electrónico son las
señales más fuertes de riesgo de churn.

![Importancia de variables](reports/figures/feature_importance.png)

## Impacto de negocio (simulación en \$)

`notebooks/02_business_impact.ipynb` traduce las probabilidades de churn a
valor esperado en dólares mediante un **backtest retrospectivo** (usa el
resultado real conocido `actual_churn` para simular qué tan buena habría
sido una campaña dirigida por el modelo — técnica estándar de *offline
policy evaluation* para justificar una campaña antes de correrla; el
notebook explica esta limitación en detalle).

Con supuestos ilustrativos (costo de contacto \$20, 30% de éxito de la
oferta de retención, valor de retención = 12 meses de facturación):

- **Profundidad óptima: contactar al 60% de la base** (4,225 clientes).
  Ahí el valor neto esperado se maximiza en **\$398,892**, frente a
  **\$176,852** si se seleccionara al azar a la misma profundidad — un
  **uplift de ~\$222,040** atribuible únicamente a usar el modelo.
- El valor neto **no crece monótonamente**: pasado el 60% empieza a caer
  (\$360,011 al 100% de la base) porque se paga por contactar clientes de
  bajo riesgo que de todas formas no iban a cancelar.
- Con presupuesto limitado, el 20% de la base ya captura el 53.3% de los
  churners reales con una opción mucho más barata (ver notebook para el
  detalle completo y el trade-off valor total vs. eficiencia por dólar).

![Valor neto esperado por profundidad](reports/figures/12_campaign_net_value_by_depth.png)

Tabla completa en
[`outputs/business_impact_simulation.csv`](outputs/business_impact_simulation.csv).

## Risk scores para Power BI

[`outputs/customer_risk_scores.csv`](outputs/customer_risk_scores.csv)
contiene, para los 7,043 clientes, su probabilidad de churn (modelo
XGBoost) y su decil de riesgo (10 = mayor riesgo, 1 = menor riesgo):

| customerID | churn_probability | actual_churn | risk_decile |
|---|---|---|---|
| 7216-EWTRS | 0.9459 | Yes | 10 |
| 5419-JPRRN | 0.9444 | Yes | 10 |
| 0107-YHINA | 0.9361 | Yes | 10 |

Este archivo está pensado para conectarse directamente a Power BI (o
Tableau) como fuente de un dashboard de retención: filtrar por
`risk_decile = 10` da la lista de clientes con mayor prioridad para
contactar. El modelo se entrena solo con el 80% de train para que la
evaluación de arriba sea honesta; el *scoring* final se aplica sobre el
100% de los clientes porque el objetivo aquí no es medir performance
(eso ya se hizo) sino producir una lista operativa completa.

## Dashboard

![Dashboard de riesgo de churn en Power BI](reports/figures/powerbi_dashboard.png)

Dashboard construido en Power BI Desktop a partir de
[`outputs/customer_risk_scores.csv`](outputs/customer_risk_scores.csv) y
[`outputs/business_impact_simulation.csv`](outputs/business_impact_simulation.csv),
archivo `.pbix` disponible en [`powerbi/customer_churn_dashboard.pbix`](powerbi/customer_churn_dashboard.pbix).
Reúne: total de clientes, tasa de churn general, clientes de alto riesgo
(deciles 9-10) y valor neto esperado de la campaña en la profundidad
óptima (60%); la curva de tasa de churn por decil de riesgo (evidencia
visual de que el modelo discrimina bien); la comparación de valor neto
entre la estrategia del modelo y la selección aleatoria en cada
profundidad; una tabla accionable de los clientes de mayor riesgo; y un
segmentador por decil.

También hay una segunda versión, en [`reports/dashboard.html`](reports/dashboard.html):
una página autocontenida (sin dependencias externas), con los mismos KPIs
y gráficos, que corre directo en el navegador sin instalar nada — verla
en vivo en **[hard747.github.io/customer-churn-prediction/reports/dashboard.html](https://hard747.github.io/customer-churn-prediction/reports/dashboard.html)**.

## Track adicional: patrón enterprise (CRM → dbt → warehouse)

[`warehouse_demo/`](warehouse_demo/README.md) implementa, aparte del
pipeline simple de arriba, el patrón real que usan empresas grandes para
este mismo problema: `CRM/ERP (simulado) → Prefect → Postgres → dbt →
Feature Table → Modelo → Scores`. Incluye un proyecto dbt real (staging
+ tests + mart, 25/25 tests pasando) y un flow de Prefect probado de
punta a punta contra Postgres. Ver también
[`docs/architecture.md`](docs/architecture.md#71-trilha-adicional-padrão-enterprise-warehouse_demo)
y [ADR-0007](docs/adr/0007-prefect-en-vez-de-airflow.md) /
[ADR-0008](docs/adr/0008-simular-crm-erp-normalizando-mismo-dataset.md).

## Próximos pasos

- Probar *cost-sensitive learning* o ajuste de umbral (en vez de 0.5)
  para optimizar el trade-off precision/recall según el costo real de un
  falso negativo (cliente que se va sin ser detectado) vs. un falso
  positivo (contactar a alguien que no iba a cancelar).
- Registro de experimentos con MLflow y versionado de datos con DVC.
- Monitoreo de *drift* del modelo (por ejemplo, con `evidently`).
- Incorporar variables temporales (histórico de uso, tickets de soporte)
  si estuvieran disponibles, más allá del snapshot estático del dataset.
- Servir el modelo como API (FastAPI) para *scoring* en tiempo real.

## Licencia y autoría

Distribuido bajo licencia [MIT](LICENSE). Dataset de uso público (IBM Telco
Customer Churn, con fines educativos/de portafolio).

**Autor:** Harre Bams Ayma Aranda — único autor de este repositorio.
