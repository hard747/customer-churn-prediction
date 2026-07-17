-- A limpeza real vive aqui, nao na carga bruta: TotalCharges chega
-- como texto com linhas em branco (11 clientes com tenure = 0, recem
-- cadastrados, ainda sem faturamento acumulado -- mesmo caso ja
-- documentado em src/build_database.py para o pipeline simples).
select
    "customerID" as customer_id,
    "PaymentMethod" as payment_method,
    "MonthlyCharges" as monthly_charges,
    coalesce(nullif(trim("TotalCharges"), '')::numeric, 0.0) as total_charges
from {{ source('raw', 'raw_billing_charges') }}
