-- Layer: REPORTING
-- Source: fct_loans_enriched
select
    dti_bucket,
    ltv_bucket,
    count(*) as loan_count,
    avg(interest_rate) as avg_interest_rate,
    avg(loan_to_income_ratio) as avg_loan_to_income_ratio
from fct_loans_enriched
where dti_bucket is not null and ltv_bucket is not null
group by dti_bucket, ltv_bucket
order by dti_bucket, ltv_bucket
