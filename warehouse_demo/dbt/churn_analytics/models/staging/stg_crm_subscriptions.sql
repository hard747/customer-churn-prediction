select
    "customerID" as customer_id,
    tenure,
    "PhoneService" as phone_service,
    "MultipleLines" as multiple_lines,
    "InternetService" as internet_service,
    "OnlineSecurity" as online_security,
    "OnlineBackup" as online_backup,
    "DeviceProtection" as device_protection,
    "TechSupport" as tech_support,
    "StreamingTV" as streaming_tv,
    "StreamingMovies" as streaming_movies,
    "Contract" as contract,
    "PaperlessBilling" as paperless_billing
from {{ source('raw', 'raw_crm_subscriptions') }}
