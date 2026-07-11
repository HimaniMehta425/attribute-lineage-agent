-- Layer: REPORTING
-- Source: fct_loans_enriched
select
    lender_name,
    count(*) as loan_count,
    sum(loan_amount) as total_loan_amount,
    avg(interest_rate) as avg_interest_rate,
    avg(loan_to_value_ratio) as avg_ltv,
    sum(case when is_hoepa_high_cost then 1 else 0 end) as hoepa_loan_count
from fct_loans_enriched
group by lender_name
order by loan_count desc
