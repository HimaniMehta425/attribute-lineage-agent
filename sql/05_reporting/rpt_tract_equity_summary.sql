-- Layer: REPORTING
-- Source: fct_loans_enriched
-- Fair-lending style equity cut: are majority-minority tracts seeing
-- different pricing/outcomes than other tracts?
select
    is_majority_minority_tract,
    count(*) as loan_count,
    avg(interest_rate) as avg_interest_rate,
    avg(rate_spread) as avg_rate_spread,
    sum(case when is_hoepa_high_cost then 1 else 0 end) as hoepa_loan_count,
    avg(loan_to_income_ratio) as avg_loan_to_income_ratio
from fct_loans_enriched
where is_majority_minority_tract is not null
group by is_majority_minority_tract
