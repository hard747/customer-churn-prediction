-- ============================================================
-- Consultas de analisis exploratorio sobre data/churn.db
-- Tabla: customers
-- Cada consulta esta delimitada por un marcador "-- name: <id>"
-- que src/run_sql_analysis.py usa para identificarla y ejecutarla
-- por separado (permite reusar el mismo archivo .sql desde Python
-- sin duplicar texto ni mantener las consultas hardcodeadas).
-- ============================================================

-- name: churn_rate_by_contract
-- Tasa de churn por tipo de contrato.
-- Motivacion: el tipo de contrato es tipicamente el predictor mas
-- fuerte de churn en este dataset (los contratos mes a mes no
-- tienen penalizacion por cancelar).
SELECT
    Contract,
    COUNT(*) AS total_clientes,
    SUM(CASE WHEN Churn = 'Yes' THEN 1 ELSE 0 END) AS clientes_churn,
    ROUND(100.0 * SUM(CASE WHEN Churn = 'Yes' THEN 1 ELSE 0 END) / COUNT(*), 2) AS tasa_churn_pct
FROM customers
GROUP BY Contract
ORDER BY tasa_churn_pct DESC;

-- name: churn_rate_by_payment_method
-- Tasa de churn por metodo de pago.
-- Motivacion: metodos de pago manuales (cheque electronico/postal)
-- suelen asociarse a mayor friccion y, por lo tanto, mayor churn
-- frente a metodos automaticos (tarjeta/transferencia).
SELECT
    PaymentMethod,
    COUNT(*) AS total_clientes,
    SUM(CASE WHEN Churn = 'Yes' THEN 1 ELSE 0 END) AS clientes_churn,
    ROUND(100.0 * SUM(CASE WHEN Churn = 'Yes' THEN 1 ELSE 0 END) / COUNT(*), 2) AS tasa_churn_pct
FROM customers
GROUP BY PaymentMethod
ORDER BY tasa_churn_pct DESC;

-- name: tenure_by_churn_status
-- Antiguedad (tenure) promedio y cargos promedio segun si el cliente
-- se dio de baja o no.
-- Motivacion: clientes nuevos (bajo tenure) son mas propensos a
-- cancelar ("luna de miel" corta); cuantificar la brecha ayuda a
-- dimensionar el problema.
SELECT
    Churn,
    COUNT(*) AS total_clientes,
    ROUND(AVG(tenure), 2) AS tenure_promedio_meses,
    ROUND(AVG(MonthlyCharges), 2) AS cargo_mensual_promedio,
    ROUND(AVG(TotalCharges), 2) AS cargo_total_promedio
FROM customers
GROUP BY Churn;

-- name: churn_rate_by_internet_service
-- Tasa de churn por tipo de servicio de internet.
-- Motivacion: fibra optica suele ser mas cara y, en este dataset,
-- se asocia a mayor insatisfaccion/competencia -> mayor churn.
SELECT
    InternetService,
    COUNT(*) AS total_clientes,
    SUM(CASE WHEN Churn = 'Yes' THEN 1 ELSE 0 END) AS clientes_churn,
    ROUND(100.0 * SUM(CASE WHEN Churn = 'Yes' THEN 1 ELSE 0 END) / COUNT(*), 2) AS tasa_churn_pct,
    ROUND(AVG(MonthlyCharges), 2) AS cargo_mensual_promedio
FROM customers
GROUP BY InternetService
ORDER BY tasa_churn_pct DESC;

-- name: churn_rate_by_tenure_bucket
-- Tasa de churn por rango de antiguedad (buckets de tenure).
-- Motivacion: permite ver si la relacion tenure-churn es lineal o
-- se concentra en un segmento especifico (p. ej. primeros 12 meses).
SELECT
    CASE
        WHEN tenure <= 12 THEN '0-12 meses'
        WHEN tenure <= 24 THEN '13-24 meses'
        WHEN tenure <= 48 THEN '25-48 meses'
        ELSE '49+ meses'
    END AS rango_tenure,
    COUNT(*) AS total_clientes,
    SUM(CASE WHEN Churn = 'Yes' THEN 1 ELSE 0 END) AS clientes_churn,
    ROUND(100.0 * SUM(CASE WHEN Churn = 'Yes' THEN 1 ELSE 0 END) / COUNT(*), 2) AS tasa_churn_pct
FROM customers
GROUP BY rango_tenure
ORDER BY MIN(tenure);
