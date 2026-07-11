-- Layer: STAGING
-- Source: raw_institutions
select
    lei,
    lender_name,
    try_cast(loan_count_reported as integer) as loan_count_reported,
    cast(activity_year as integer) as activity_year
from raw_institutions
