-- Feature table: um join real (mesmo customer_id) das 3 fontes
-- "operacionais" simuladas + o sinal de churn. Esta e a tabela que o
-- modelo consome (ver warehouse_demo/src/train_from_feature_table.py),
-- equivalente em forma ao que src/train_models.load_and_clean_data()
-- monta em pandas para o pipeline simples -- aqui a limpeza e o join
-- ficam em SQL versionado e testado (dbt test), nao em um notebook.

with customers as (
    select * from {{ ref('stg_crm_customers') }}
),
subscriptions as (
    select * from {{ ref('stg_crm_subscriptions') }}
),
billing as (
    select * from {{ ref('stg_billing_charges') }}
),
labels as (
    select * from {{ ref('stg_churn_labels') }}
)

select
    customers.customer_id,
    customers.gender,
    customers.senior_citizen,
    customers.partner,
    customers.dependents,
    subscriptions.tenure,
    subscriptions.phone_service,
    subscriptions.multiple_lines,
    subscriptions.internet_service,
    subscriptions.online_security,
    subscriptions.online_backup,
    subscriptions.device_protection,
    subscriptions.tech_support,
    subscriptions.streaming_tv,
    subscriptions.streaming_movies,
    subscriptions.contract,
    subscriptions.paperless_billing,
    billing.payment_method,
    billing.monthly_charges,
    billing.total_charges,
    labels.churn
from customers
inner join subscriptions on customers.customer_id = subscriptions.customer_id
inner join billing on customers.customer_id = billing.customer_id
inner join labels on customers.customer_id = labels.customer_id
