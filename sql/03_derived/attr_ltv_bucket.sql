-- Layer: DERIVED ATTRIBUTE
-- Source: stg_loans
-- New attribute: ltv_bucket -- standard underwriting LTV tiers, not present
-- in the raw HMDA extract.
select
    loan_id,
    loan_to_value_ratio,
    case
        when loan_to_value_ratio is null then null
        when loan_to_value_ratio <= 60 then '<=60'
        when loan_to_value_ratio <= 80 then '60-80'
        when loan_to_value_ratio <= 90 then '80-90'
        when loan_to_value_ratio <= 97 then '90-97'
        else '>97'
    end as ltv_bucket
from stg_loans
