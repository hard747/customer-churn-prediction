-- Staging: normaliza tipos e nomes, ainda sem logica de negocio.
select
    "customerID" as customer_id,
    gender,
    case when "SeniorCitizen" = 1 then 'Yes' else 'No' end as senior_citizen,
    "Partner" as partner,
    "Dependents" as dependents
from {{ source('raw', 'raw_crm_customers') }}
