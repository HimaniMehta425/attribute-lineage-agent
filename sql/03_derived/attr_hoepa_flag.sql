-- Layer: DERIVED ATTRIBUTE
-- Source: stg_loans
-- New attribute: is_hoepa_high_cost -- boolean flag derived from the raw
-- HOEPA status code (1 = high-cost mortgage under HOEPA, 2 = not high-cost,
-- 3 = not applicable). Recruiters/analysts want the boolean, not the code.
select
    loan_id,
    hoepa_status,
    (hoepa_status = 1) as is_hoepa_high_cost
from stg_loans
