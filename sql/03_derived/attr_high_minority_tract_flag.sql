-- Layer: DERIVED ATTRIBUTE
-- Source: stg_loans
-- New attribute: is_majority_minority_tract -- derived from the census tract
-- demographic fields HMDA already ships (tract_minority_population_percent),
-- used downstream for fair-lending equity reporting.
select
    loan_id,
    tract_minority_population_percent,
    (tract_minority_population_percent >= 50) as is_majority_minority_tract
from stg_loans
