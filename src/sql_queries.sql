-- ============================================================
-- Consultas de analise exploratoria sobre a tabela customers
-- (SQLite por padrao, ou Postgres se DATABASE_URL estiver definida).
-- Cada consulta e delimitada por um marcador "-- name: <id>" que
-- src/run_sql_analysis.py usa para identifica-la e executa-la
-- separadamente (permite reusar o mesmo arquivo .sql a partir do
-- Python sem duplicar texto nem manter as consultas hardcoded).
--
-- Notas de portabilidade SQLite <-> Postgres:
-- 1) Os nomes de coluna com maiusculas (Contract, Churn,
--    PaymentMethod, MonthlyCharges, TotalCharges, InternetService)
--    vao entre aspas duplas. O SQLite e insensivel a maiusculas em
--    identificadores sem aspas, mas o Postgres nao: sem aspas, o
--    Postgres os procura em minusculo e falha. Aspas duplas e
--    sintaxe ANSI SQL padrao, funciona igual nos dois motores.
-- 2) ROUND(AVG(coluna_float), 2) e convertido explicitamente para
--    NUMERIC. O Postgres nao tem uma sobrecarga de ROUND() para
--    double precision (so para numeric), entao AVG() sobre uma
--    coluna float sem conversao falha com "function round(double
--    precision, integer) does not exist". O SQLite, por ser de
--    tipagem dinamica, nunca teve esse problema, por isso so
--    apareceu ao testar contra o Postgres.
-- ============================================================

-- name: churn_rate_by_contract
-- Taxa de churn por tipo de contrato.
-- Motivacao: o tipo de contrato costuma ser o preditor mais forte de
-- churn neste dataset (contratos mes a mes nao tem penalidade por
-- cancelamento).
SELECT
    "Contract",
    COUNT(*) AS total_clientes,
    SUM(CASE WHEN "Churn" = 'Yes' THEN 1 ELSE 0 END) AS clientes_churn,
    ROUND(100.0 * SUM(CASE WHEN "Churn" = 'Yes' THEN 1 ELSE 0 END) / COUNT(*), 2) AS tasa_churn_pct
FROM customers
GROUP BY "Contract"
ORDER BY tasa_churn_pct DESC;

-- name: churn_rate_by_payment_method
-- Taxa de churn por metodo de pagamento.
-- Motivacao: metodos de pagamento manuais (cheque eletronico/postal)
-- costumam se associar a mais friccao e, portanto, mais churn frente
-- a metodos automaticos (cartao/transferencia).
SELECT
    "PaymentMethod",
    COUNT(*) AS total_clientes,
    SUM(CASE WHEN "Churn" = 'Yes' THEN 1 ELSE 0 END) AS clientes_churn,
    ROUND(100.0 * SUM(CASE WHEN "Churn" = 'Yes' THEN 1 ELSE 0 END) / COUNT(*), 2) AS tasa_churn_pct
FROM customers
GROUP BY "PaymentMethod"
ORDER BY tasa_churn_pct DESC;

-- name: tenure_by_churn_status
-- Antiguidade (tenure) media e cobrancas medias segundo se o cliente
-- cancelou ou nao.
-- Motivacao: clientes novos (tenure baixo) sao mais propensos a
-- cancelar ("lua de mel" curta); quantificar a diferenca ajuda a
-- dimensionar o problema.
SELECT
    "Churn",
    COUNT(*) AS total_clientes,
    ROUND(AVG(tenure), 2) AS tenure_promedio_meses,
    ROUND(CAST(AVG("MonthlyCharges") AS NUMERIC), 2) AS cargo_mensual_promedio,
    ROUND(CAST(AVG("TotalCharges") AS NUMERIC), 2) AS cargo_total_promedio
FROM customers
GROUP BY "Churn";

-- name: churn_rate_by_internet_service
-- Taxa de churn por tipo de servico de internet.
-- Motivacao: fibra optica costuma ser mais cara e, neste dataset, se
-- associa a mais insatisfacao/concorrencia -> mais churn.
SELECT
    "InternetService",
    COUNT(*) AS total_clientes,
    SUM(CASE WHEN "Churn" = 'Yes' THEN 1 ELSE 0 END) AS clientes_churn,
    ROUND(100.0 * SUM(CASE WHEN "Churn" = 'Yes' THEN 1 ELSE 0 END) / COUNT(*), 2) AS tasa_churn_pct,
    ROUND(CAST(AVG("MonthlyCharges") AS NUMERIC), 2) AS cargo_mensual_promedio
FROM customers
GROUP BY "InternetService"
ORDER BY tasa_churn_pct DESC;

-- name: churn_rate_by_tenure_bucket
-- Taxa de churn por faixa de antiguidade (buckets de tenure).
-- Motivacao: permite ver se a relacao tenure-churn e linear ou se
-- concentra em um segmento especifico (p. ex. primeiros 12 meses).
SELECT
    CASE
        WHEN tenure <= 12 THEN '0-12 meses'
        WHEN tenure <= 24 THEN '13-24 meses'
        WHEN tenure <= 48 THEN '25-48 meses'
        ELSE '49+ meses'
    END AS rango_tenure,
    COUNT(*) AS total_clientes,
    SUM(CASE WHEN "Churn" = 'Yes' THEN 1 ELSE 0 END) AS clientes_churn,
    ROUND(100.0 * SUM(CASE WHEN "Churn" = 'Yes' THEN 1 ELSE 0 END) / COUNT(*), 2) AS tasa_churn_pct
FROM customers
GROUP BY rango_tenure
ORDER BY MIN(tenure);
