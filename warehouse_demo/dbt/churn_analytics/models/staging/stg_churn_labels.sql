select
    "customerID" as customer_id,
    "Churn" as churn
from {{ source('raw', 'raw_churn_labels') }}
