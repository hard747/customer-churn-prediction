# Predicción de Churn de Clientes — Telco Customer Churn

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-1.4-F7931E?logo=scikitlearn&logoColor=white)
![XGBoost](https://img.shields.io/badge/XGBoost-2.0-1C6EA4)
![SQLite](https://img.shields.io/badge/SQLite-3-003B57?logo=sqlite&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-completo-brightgreen)

Proyecto end-to-end de análisis y predicción de fuga de clientes (*churn*)
usando el dataset público **Telco Customer Churn** de IBM. Cubre el flujo
completo de un proyecto de Data Science aplicado a negocio: consultas SQL
de diagnóstico, análisis exploratorio con visualizaciones, entrenamiento y
comparación de modelos de clasificación, y un archivo de *risk scores*
listo para conectar a un dashboard de Power BI.

## Tabla de contenidos

- [Objetivo de negocio](#objetivo-de-negocio)
- [Dataset](#dataset)
- [Estructura del repositorio](#estructura-del-repositorio)
- [Cómo reproducirlo](#cómo-reproducirlo)
- [Metodología y decisiones técnicas](#metodología-y-decisiones-técnicas)
- [Resultados](#resultados)
- [Risk scores para Power BI](#risk-scores-para-power-bi)
- [Próximos pasos](#próximos-pasos)
- [Licencia y autoría](#licencia-y-autoría)

## Objetivo de negocio

Una empresa de telecomunicaciones pierde ingresos recurrentes cada vez que
un cliente cancela su servicio. Retener a un cliente existente es
considerablemente más barato que adquirir uno nuevo, pero los equipos de
retención tienen capacidad limitada: no pueden contactar a toda la base de
clientes. Este proyecto responde dos preguntas:

1. **¿Qué factores están asociados al churn?** (SQL + EDA)
2. **¿Qué clientes tienen mayor probabilidad de cancelar *ahora*, para
   priorizar acciones de retención?** (modelo predictivo + *risk scores*)

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
├── data/
│   ├── Telco-Customer-Churn.csv   # dataset crudo
│   └── churn.db                   # SQLite (se genera con build_database.py)
├── notebooks/
│   └── 01_eda.ipynb               # limpieza + estadística + 10 visualizaciones
├── src/
│   ├── build_database.py          # CSV -> SQLite
│   ├── sql_queries.sql            # 5 consultas de análisis
│   ├── run_sql_analysis.py        # ejecuta sql_queries.sql y guarda resultados
│   ├── train_models.py            # pipeline sklearn: LR, RF, XGBoost + CV
│   ├── generate_risk_scores.py    # scoring de toda la base + deciles
│   └── run_all.py                 # orquesta el pipeline completo de cero
├── reports/
│   └── figures/                   # PNGs generados por el notebook y el training
├── outputs/
│   ├── sql_analysis/              # resultados de las 5 consultas SQL
│   ├── model_comparison.csv       # métricas de los 3 modelos
│   ├── best_model.joblib          # mejor pipeline entrenado (serializado)
│   └── customer_risk_scores.csv   # probabilidad de churn + decil por cliente
├── requirements.txt
└── README.md
```

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

`run_all.py` ejecuta en orden: construcción de `data/churn.db`, las 5
consultas SQL, el notebook de EDA (con sus 10 figuras), el entrenamiento
y comparación de los 3 modelos, y la generación de `customer_risk_scores.csv`.
Todo el proyecto se recrea desde el CSV crudo sin pasos manuales.

## Metodología y decisiones técnicas

### 1. SQL como primera capa de análisis
Antes de modelar, se cargan los datos a `data/churn.db` (SQLite) y se
responden preguntas de negocio directamente en SQL (`src/sql_queries.sql`):
tasa de churn por contrato, por método de pago, por servicio de internet,
por antigüedad, y comparación de tenure/cargos entre clientes que se van y
los que se quedan. Esto simula el flujo real de un analista que primero
diagnostica con SQL antes de invertir en un modelo.

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

## Próximos pasos

- Probar *cost-sensitive learning* o ajuste de umbral (en vez de 0.5)
  para optimizar el trade-off precision/recall según el costo real de un
  falso negativo (cliente que se va sin ser detectado) vs. un falso
  positivo (contactar a alguien que no iba a cancelar).
- Incorporar variables temporales (histórico de uso, tickets de soporte)
  si estuvieran disponibles, más allá del snapshot estático del dataset.
- Servir el modelo como API (FastAPI) para *scoring* en tiempo real.

## Licencia y autoría

Distribuido bajo licencia [MIT](LICENSE). Dataset de uso público (IBM Telco
Customer Churn, con fines educativos/de portafolio).

**Autor:** [Tu Nombre] — único autor de este repositorio.
