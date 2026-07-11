-- Layer: DERIVED ATTRIBUTE
-- Source: stg_loans
-- New attribute: rate_spread_tier -- buckets the APOR rate spread into
-- pricing tiers used for fair-lending / higher-priced-loan monitoring.
select
    loan_id,
    rate_spread,
    case
        when rate_spread is null then 'not_reported'
        when rate_spread <= 0 then 'at_or_below_apor'
        when rate_spread <= 1.5 then 'prime'
        when rate_spread <= 3 then 'near_prime'
        else 'higher_priced'
    end as rate_spread_tier
from stg_loans
